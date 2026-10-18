"""Persistent llama-server backend for round 2.

One process stays loaded across images. Driving requests use the action
grammar. Literacy uses a separate process with no grammar, because a global
grammar would force BRAKE / SLOW / CONTINUE / CHANGE_LANE.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from hornok.harness import LLAMA_BIN, GenerationError
from hornok.parse import strip_echo

SERVER_BIN = LLAMA_BIN.parent / "llama-server"


class LlamaServerVLM:
    def __init__(
        self,
        name: str,
        model_path: Path,
        mmproj_path: Path,
        *,
        port: int = 18021,
        grammar_file: Path | None = None,
        image_tokens: int = 512,
        threads: int = 4,
        n_ctx: int = 4096,
        log_path: Path | None = None,
    ):
        self.name = name
        self.model_path = Path(model_path)
        self.mmproj_path = Path(mmproj_path)
        self.port = port
        self.grammar_file = Path(grammar_file) if grammar_file else None
        self.image_tokens = image_tokens
        self.threads = threads
        self.n_ctx = n_ctx
        self.log_path = log_path
        self.proc: subprocess.Popen | None = None
        self._log_handle = None
        if not SERVER_BIN.is_file():
            raise GenerationError(f"llama-server not found at {SERVER_BIN}")
        if not self.model_path.is_file() or not self.mmproj_path.is_file():
            raise GenerationError(f"missing GGUF weights for {name}")

    def start(self) -> None:
        if self.proc is not None:
            return
        cmd = [
            str(SERVER_BIN),
            "-m",
            str(self.model_path),
            "--mmproj",
            str(self.mmproj_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
            "-ngl",
            "0",
            "--no-mmproj-offload",
            "-t",
            str(self.threads),
            "-c",
            str(self.n_ctx),
            "--image-min-tokens",
            str(self.image_tokens),
            "--image-max-tokens",
            str(self.image_tokens),
            "--jinja",
            "-np",
            "1",
        ]
        if self.grammar_file is not None:
            cmd.extend(["--grammar-file", str(self.grammar_file)])
        env = os.environ.copy()
        lib_dir = str(SERVER_BIN.parent)
        env["LD_LIBRARY_PATH"] = lib_dir + os.pathsep + env.get("LD_LIBRARY_PATH", "")
        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = self.log_path.open("a", encoding="utf-8")
        self.proc = subprocess.Popen(
            cmd,
            stdout=self._log_handle or subprocess.DEVNULL,
            stderr=subprocess.STDOUT if self._log_handle else subprocess.DEVNULL,
            env=env,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        deadline = time.time() + 180
        url = f"http://127.0.0.1:{self.port}/health"
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise GenerationError(f"{self.name} server exited during startup")
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(1)
        self.close()
        raise GenerationError(f"{self.name} server did not become healthy")

    def generate(self, image_path: Path, prompt: str, max_new_tokens: int = 8) -> str:
        if self.proc is None:
            self.start()
        image_bytes = Path(image_path).read_bytes()
        encoded = base64.b64encode(image_bytes).decode("ascii")
        suffix = "png" if str(image_path).lower().endswith(".png") else "jpeg"
        body = {
            "temperature": 0,
            "top_k": 1,
            "seed": 1,
            "max_tokens": max_new_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/{suffix};base64,{encoded}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[-500:]
            raise GenerationError(f"{self.name} HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise GenerationError(f"{self.name} request failed: {exc}") from exc
        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GenerationError(f"{self.name} missing completion: {payload!r}"[:500]) from exc
        text = strip_echo(text or "", prompt)
        if not text:
            raise GenerationError(f"{self.name} returned an empty completion")
        return text

    def close(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None
