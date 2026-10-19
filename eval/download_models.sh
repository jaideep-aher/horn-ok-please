#!/usr/bin/env bash
# Download the scored checkpoints and build the Q4_0 GGUF.
# Weights are gitignored. Requires huggingface_hub, llama-quantize, and network.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODELS="${HORNOK_MODELS:-$ROOT/models}"
LLAMA_QUANTIZE="${HORNOK_LLAMA_QUANTIZE:-$ROOT/vendor/llama-b11716/llama-quantize}"
mkdir -p "$MODELS/gguf"
python - << PY
from huggingface_hub import snapshot_download, hf_hub_download
import os
root = os.environ.get("HORNOK_MODELS", "$MODELS")
snapshot_download(
    "HuggingFaceTB/SmolVLM-256M-Instruct",
    local_dir=f"{root}/SmolVLM-256M-Instruct",
    ignore_patterns=["*.md", "onnx/**", "*.ot"],
)
snapshot_download(
    "HuggingFaceTB/SmolVLM-500M-Instruct",
    local_dir=f"{root}/SmolVLM-500M-Instruct",
    ignore_patterns=["*.md", "onnx/**", "*.ot"],
)
for repo, name in (
    ("ggml-org/SmolVLM-256M-Instruct-GGUF", "SmolVLM-256M-Instruct-f16.gguf"),
    ("ggml-org/SmolVLM-256M-Instruct-GGUF", "mmproj-SmolVLM-256M-Instruct-f16.gguf"),
    ("ggml-org/Qwen2.5-VL-3B-Instruct-GGUF", "Qwen2.5-VL-3B-Instruct-Q8_0.gguf"),
    ("ggml-org/Qwen2.5-VL-3B-Instruct-GGUF", "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"),
    ("ggml-org/Qwen2.5-VL-3B-Instruct-GGUF", "mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf"),
    ("ggml-org/gemma-3-4b-it-GGUF", "gemma-3-4b-it-Q8_0.gguf"),
    ("ggml-org/gemma-3-4b-it-GGUF", "gemma-3-4b-it-Q4_K_M.gguf"),
    ("ggml-org/gemma-3-4b-it-GGUF", "mmproj-model-f16.gguf"),
    ("ggml-org/InternVL2_5-1B-GGUF", "InternVL2_5-1B-Q8_0.gguf"),
    ("ggml-org/InternVL2_5-1B-GGUF", "mmproj-InternVL2_5-1B-f16.gguf"),
):
    hf_hub_download(repo, filename=name, local_dir=f"{root}/gguf")
print("downloads complete")
PY
F16="$MODELS/gguf/SmolVLM-256M-Instruct-f16.gguf"
Q4="$MODELS/gguf/SmolVLM-256M-Instruct-Q4_0.gguf"
if [[ ! -f "$Q4" ]]; then
  export LD_LIBRARY_PATH="$(dirname "$LLAMA_QUANTIZE")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  "$LLAMA_QUANTIZE" "$F16" "$Q4" Q4_0
fi
echo "ready: $Q4"
