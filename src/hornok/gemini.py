"""Gemini vision backend for the same STOP/GO protocol.

The client is constructed only when ``GEMINI_API_KEY`` is set. Nothing in the
round-3 CPU run calls this module. A 429 or 503 is an infrastructure retry:
the scored completion is the first successful response, not a new draw after a
parsed answer.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from hornok.harness import GenerationError
from hornok.parse import strip_echo

# The 18 Oct 2026 bundle run stored 40 unparsed gate rows because thinking
# tokens consumed max_output_tokens=64. This floor is an output cap, not a
# new prompt. Callers may ask for more. They cannot ask for less.
OUTPUT_TOKEN_FLOOR = 1024
# Try to turn thinking off. Models that reject a budget of 0 get the lowest
# thinking level the API enum offers, then a request with no thinking config.
THINKING_ORDER = ("off", "minimal", "unset")

_RETRY_CODES = {429, 500, 503}
_MAX_ATTEMPTS = 6
_SKIP_FLASH = (
    "tts",
    "image",
    "live",
    "embed",
    "audio",
    "transcribe",
    "robot",
    "computer",
    "aqa",
    "nano",
    "banana",
)


def gemini_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return key or None


def gemini_model_id() -> str | None:
    """Return GEMINI_MODEL when the caller set it. Otherwise None.

    There is no hardcoded default. A missing override is resolved by listing
    models, and that list is requested only when an API key is present.
    """
    return os.environ.get("GEMINI_MODEL", "").strip() or None


def select_flash_model(models: list) -> str:
    """Pick a non-lite Flash model. Higher version, then a stable id.

    Flash-Lite names are left for ``select_flash_lite_model``. A higher version
    number on a Lite id does not take the primary slot.
    """
    ranked: list[tuple] = []
    for item in models:
        if isinstance(item, str):
            raw, actions = item, None
        else:
            raw = str(item.get("name") or "")
            actions = item.get("supported_actions")
        short = raw.split("/")[-1].strip()
        low = short.lower()
        if "flash" not in low or "lite" in low or any(bad in low for bad in _SKIP_FLASH):
            continue
        if actions is not None and not _can_generate(actions):
            continue
        nums = tuple(int(piece) for piece in re.findall(r"\d+", short))
        stable = 0 if any(flag in low for flag in ("preview", "exp", "latest")) else 1
        lite = 0 if "lite" in low else 1
        ranked.append((nums, stable, lite, short))
    if not ranked:
        raise GenerationError(
            "The API listed no Flash model that can generate content. "
            "Set GEMINI_MODEL to an id from that list."
        )
    ranked.sort()
    return ranked[-1][3]


def resolve_flash_model(client) -> str:
    """List models on this client and choose a non-lite Flash id."""
    return select_flash_model(list_model_records(client))


def _can_generate(actions) -> bool:
    text = " ".join(str(action) for action in actions)
    lowered = text.lower().replace("_", "")
    return "generatecontent" in lowered


class QuotaError(GenerationError):
    """The account is out of quota. Callers stop and keep the rows already stored."""


def is_quota_error(exc: BaseException) -> bool:
    """True for a hard quota or billing stop, not a short rate limit."""
    message = str(exc).lower()
    markers = (
        "quota",
        "billing",
        "exceeded your current",
        "insufficient_quota",
        "check your plan",
        "resource has been exhausted",
    )
    return any(marker in message for marker in markers)


def select_flash_lite_model(models: list) -> str | None:
    """Pick a Flash-Lite id, or None when the list has no such model."""
    ranked: list[tuple] = []
    for item in models:
        if isinstance(item, str):
            raw, actions = item, None
        else:
            raw = str(item.get("name") or "")
            actions = item.get("supported_actions")
        short = raw.split("/")[-1].strip()
        low = short.lower()
        if "flash" not in low or "lite" not in low or any(bad in low for bad in _SKIP_FLASH):
            continue
        if actions is not None and not _can_generate(actions):
            continue
        nums = tuple(int(piece) for piece in re.findall(r"\d+", short))
        stable = 0 if any(flag in low for flag in ("preview", "exp", "latest")) else 1
        ranked.append((nums, stable, short))
    if not ranked:
        return None
    ranked.sort()
    return ranked[-1][2]


def list_model_records(client) -> list[dict]:
    """Read the live model list. Raises GenerationError if the call fails."""
    listed = []
    try:
        pager = client.models.list()
    except Exception as exc:
        raise GenerationError(f"Could not list Gemini models: {exc}") from exc
    try:
        for model in pager:
            listed.append(
                {
                    "name": getattr(model, "name", None),
                    "supported_actions": getattr(model, "supported_actions", None),
                }
            )
    except Exception as exc:
        raise GenerationError(f"Could not read the Gemini model list: {exc}") from exc
    return listed


def effective_output_tokens(requested: int) -> int:
    """Keep a short cap from being eaten by a thought."""
    return max(int(requested), OUTPUT_TOKEN_FLOOR)


def thinking_rejected(exc: BaseException) -> bool:
    """True when the model refused the thinking setting, not the image."""
    message = str(exc).lower()
    markers = (
        "thinking_budget",
        "thinkingbudget",
        "thinking_level",
        "thinkinglevel",
        "thinking budget",
        "thinking level",
        "thinking is not supported",
        "thinking config",
    )
    return any(marker in message for marker in markers)


def parsed_action(parsed: object) -> str | None:
    """Read a schema object. Prose is not an action."""
    if isinstance(parsed, dict):
        action = parsed.get("action")
    else:
        action = getattr(parsed, "action", None)
    if action in {"STOP", "GO"}:
        return str(action)
    return None


def completion_text(response: object, *, schema: bool) -> str:
    """Prefer the schema object. Fall back to non-thought text."""
    if schema:
        action = parsed_action(getattr(response, "parsed", None))
        if action:
            return json.dumps({"action": action}, separators=(",", ":"))
    text = getattr(response, "text", None) or ""
    return text.strip()


def call_meta(response: object, mode: str, tokens: int) -> dict:
    """Diagnostics for the smoke command. Not a score."""
    candidates = getattr(response, "candidates", None) or []
    candidate = candidates[0] if candidates else None
    usage = getattr(response, "usage_metadata", None)
    finish = getattr(candidate, "finish_reason", None)
    return {
        "thinking": mode,
        "max_output_tokens": tokens,
        "finish_reason": None if finish is None else str(finish),
        "thoughts_token_count": getattr(usage, "thoughts_token_count", None),
        "candidates_token_count": getattr(usage, "candidates_token_count", None),
    }


class GeminiVLM:
    def __init__(self, model_id: str | None = None, api_key: str | None = None):
        key = api_key if api_key is not None else gemini_api_key()
        if not key:
            raise GenerationError("GEMINI_API_KEY is not set. The Gemini backend was not called.")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise GenerationError(
                "google-genai is not installed. Install the eval extra or pip install google-genai."
            ) from exc
        self._types = types
        self._client = genai.Client(api_key=key)
        override = model_id or gemini_model_id()
        self.model_id = override or resolve_flash_model(self._client)
        self._thinking_mode: str | None = None
        self.last_meta: dict = {}

    def generate(
        self,
        image_path: Path,
        prompt: str,
        *,
        schema: bool = True,
        max_output_tokens: int = OUTPUT_TOKEN_FLOOR,
    ) -> str:
        delay = 2.0
        last: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                return self._once(
                    image_path,
                    prompt,
                    schema=schema,
                    max_output_tokens=max_output_tokens,
                )
            except QuotaError:
                raise
            except Exception as exc:
                if is_quota_error(exc):
                    raise QuotaError(f"Gemini quota stopped the run: {exc}") from exc
                if not _retryable(exc) or attempt + 1 == _MAX_ATTEMPTS:
                    if _retryable(exc):
                        raise GenerationError(
                            f"Gemini rate limit persisted after {_MAX_ATTEMPTS} attempts: {exc}"
                        ) from exc
                    raise GenerationError(f"Gemini request failed: {exc}") from exc
                time.sleep(delay)
                delay *= 2
                last = exc
        raise GenerationError(f"Gemini request failed: {last}")

    def _thinking_config(self, mode: str):
        types = self._types
        if mode == "off":
            return types.ThinkingConfig(thinking_budget=0)
        if mode == "minimal":
            return types.ThinkingConfig(thinking_level="MINIMAL")
        return None

    def _config(self, *, schema: bool, max_output_tokens: int, mode: str):
        """JSON mime type plus the STOP/GO schema. Temperature is not sent."""
        types = self._types
        kwargs: dict = {"max_output_tokens": max_output_tokens}
        thinking = self._thinking_config(mode)
        if thinking is not None:
            kwargs["thinking_config"] = thinking
        if schema:
            kwargs["response_mime_type"] = "application/json"
            # response_schema is the field generateContent enforces.
            # response_json_schema is an alternative and must not be sent with it.
            kwargs["response_schema"] = {
                "type": "OBJECT",
                "properties": {
                    "action": {"type": "STRING", "enum": ["STOP", "GO"]},
                },
                "required": ["action"],
            }
        try:
            return types.GenerateContentConfig(**kwargs)
        except TypeError:
            if schema:
                kwargs.pop("response_schema", None)
                kwargs["response_json_schema"] = {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["STOP", "GO"]},
                    },
                    "required": ["action"],
                }
            return types.GenerateContentConfig(**kwargs)

    def _once(
        self,
        image_path: Path,
        prompt: str,
        *,
        schema: bool,
        max_output_tokens: int = OUTPUT_TOKEN_FLOOR,
    ) -> str:
        image = Path(image_path).read_bytes()
        suffix = Path(image_path).suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        tokens = effective_output_tokens(max_output_tokens)
        modes = (self._thinking_mode,) if self._thinking_mode else THINKING_ORDER
        last_reject: Exception | None = None
        for mode in modes:
            config = self._config(schema=schema, max_output_tokens=tokens, mode=mode)
            try:
                response = self._client.models.generate_content(
                    model=self.model_id,
                    contents=[
                        self._types.Part.from_bytes(data=image, mime_type=mime),
                        prompt,
                    ],
                    config=config,
                )
            except Exception as exc:
                if thinking_rejected(exc):
                    last_reject = exc
                    continue
                raise
            text = strip_echo(completion_text(response, schema=schema), prompt)
            self._thinking_mode = mode
            self.last_meta = call_meta(response, mode, tokens)
            if not text:
                raise GenerationError("Gemini returned an empty completion")
            return text
        raise GenerationError(f"Gemini rejected every thinking setting: {last_reject}")


def _retryable(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code in _RETRY_CODES:
        return True
    message = str(exc).lower()
    return (
        "429" in message
        or "resource_exhausted" in message
        or "503" in message
        or "unavailable" in message
    )
