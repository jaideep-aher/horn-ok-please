"""Model backends. Torch and llama.cpp are imported only when a backend is built."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from hornok.parse import strip_echo

LLAMA_BIN = Path(
    os.environ.get(
        "HORNOK_LLAMA_BIN",
        "/workspace/vendor/llama-b11716/llama-mtmd-cli",
    )
)


def models_root() -> Path:
    return Path(os.environ.get("HORNOK_MODELS", "/workspace/models"))


class GenerationError(RuntimeError):
    pass


class TransformersVLM:
    """Hugging Face SmolVLM (or compatible) in float32, greedy decoding."""

    def __init__(self, model_id: str, name: str, revision: str | None = None):
        import torch
        from transformers import AutoProcessor

        self.name = name
        self.model_id = model_id
        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(model_id, revision=revision)
        self.model = _load_causal_vlm(model_id, torch, revision)
        self.model.eval()
        if getattr(self.model.generation_config, "pad_token_id", None) is None:
            eos = self.processor.tokenizer.eos_token_id
            self.model.generation_config.pad_token_id = eos

    def generate(self, image_path: Path, prompt: str, max_new_tokens: int = 96) -> str:
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        templated = self.processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        inputs = self.processor(text=templated, images=[image], return_tensors="pt")
        with self.torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
            )
        new_tokens = output[0][inputs["input_ids"].shape[-1] :]
        text = self.processor.decode(new_tokens, skip_special_tokens=True)
        return strip_echo(text, prompt)

    def close(self) -> None:
        del self.model
        self.torch.cuda.empty_cache() if self.torch.cuda.is_available() else None


class LlamaCppVLM:
    """llama.cpp multimodal CLI. One process per image; temperature 0."""

    def __init__(self, name: str, model_path: Path, mmproj_path: Path, threads: int = 4):
        self.name = name
        self.model_path = Path(model_path)
        self.mmproj_path = Path(mmproj_path)
        self.threads = threads
        if not LLAMA_BIN.is_file():
            raise GenerationError(f"llama-mtmd-cli not found at {LLAMA_BIN}")
        if not self.model_path.is_file() or not self.mmproj_path.is_file():
            raise GenerationError(f"missing GGUF weights for {name}")

    def generate(self, image_path: Path, prompt: str, max_new_tokens: int = 96) -> str:
        cmd = [
            str(LLAMA_BIN),
            "-m",
            str(self.model_path),
            "--mmproj",
            str(self.mmproj_path),
            "--image",
            str(image_path),
            "-p",
            prompt,
            "-n",
            str(max_new_tokens),
            "--temp",
            "0",
            "-t",
            str(self.threads),
            "--jinja",
            "--no-mmproj-offload",
        ]
        env = os.environ.copy()
        lib_dir = str(LLAMA_BIN.parent)
        env["LD_LIBRARY_PATH"] = lib_dir + os.pathsep + env.get("LD_LIBRARY_PATH", "")
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                stdin=subprocess.DEVNULL,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise GenerationError(f"{self.name} timed out on {image_path.name}") from exc
        if completed.returncode != 0:
            tail = (completed.stderr or completed.stdout or "")[-800:]
            raise GenerationError(f"{self.name} exited {completed.returncode}: {tail}")
        # stdout is the completion. stderr is the llama.cpp log.
        # --log-disable also suppresses the completion, so it is not used.
        text = (completed.stdout or "").strip()
        if not text:
            tail = (completed.stderr or "")[-400:]
            raise GenerationError(f"{self.name} returned an empty completion: {tail}")
        return strip_echo(text, prompt)

    def close(self) -> None:
        return None


def _load_causal_vlm(model_id: str, torch, revision: str | None):
    import transformers

    errors: list[str] = []
    for cls_name in ("AutoModelForImageTextToText", "AutoModelForVision2Seq"):
        cls = getattr(transformers, cls_name, None)
        if cls is None:
            continue
        for kwargs in ({"dtype": torch.float32}, {"torch_dtype": torch.float32}):
            try:
                return cls.from_pretrained(model_id, revision=revision, **kwargs)
            except TypeError as exc:
                errors.append(f"{cls_name} {kwargs}: {exc}")
            except Exception as exc:  # model-class mismatch, try the next loader
                errors.append(f"{cls_name} {kwargs}: {exc}")
                break
    raise GenerationError(f"could not load {model_id}: {' | '.join(errors)}")


def build_backend(name: str):
    """Construct a pre-registered backend by short name."""
    root = models_root()
    gguf = root / "gguf"
    if name == "smolvlm-256m-hf":
        return TransformersVLM(str(root / "SmolVLM-256M-Instruct"), name)
    if name == "smolvlm-500m-hf":
        return TransformersVLM(str(root / "SmolVLM-500M-Instruct"), name)
    if name == "smolvlm-256m-f16":
        return LlamaCppVLM(
            name,
            gguf / "SmolVLM-256M-Instruct-f16.gguf",
            gguf / "mmproj-SmolVLM-256M-Instruct-f16.gguf",
        )
    if name == "smolvlm-256m-q4":
        return LlamaCppVLM(
            name,
            gguf / "SmolVLM-256M-Instruct-Q4_0.gguf",
            gguf / "mmproj-SmolVLM-256M-Instruct-f16.gguf",
        )
    if name == "smolvlm2-256m-hf":
        # Pre-registered fallback only if SmolVLM-500M fails to load.
        return TransformersVLM("HuggingFaceTB/SmolVLM2-256M-Video-Instruct", name)
    raise KeyError(f"unknown model {name}")
