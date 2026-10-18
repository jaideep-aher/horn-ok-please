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
for name in (
    "SmolVLM-256M-Instruct-f16.gguf",
    "mmproj-SmolVLM-256M-Instruct-f16.gguf",
):
    hf_hub_download(
        "ggml-org/SmolVLM-256M-Instruct-GGUF",
        filename=name,
        local_dir=f"{root}/gguf",
    )
print("downloads complete")
PY
F16="$MODELS/gguf/SmolVLM-256M-Instruct-f16.gguf"
Q4="$MODELS/gguf/SmolVLM-256M-Instruct-Q4_0.gguf"
if [[ ! -f "$Q4" ]]; then
  export LD_LIBRARY_PATH="$(dirname "$LLAMA_QUANTIZE")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  "$LLAMA_QUANTIZE" "$F16" "$Q4" Q4_0
fi
echo "ready: $Q4"
