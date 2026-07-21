#!/bin/bash
# =============================================================================
# vLLM GPU server for the Nepali emissions advisor
# =============================================================================
# Runs Llama 3.1 8B (or Qwen2.5 7B for better Nepali) on a single GPU.
# Optimized for cost-effective A100/L40/RTX6000 deployment.
# =============================================================================
set -euo pipefail

MODEL="${LLM_MODEL:-Qwen/Qwen2.5-7B-Instruct}"
QUANT="${QUANTIZATION:-awq}"  # awq for A100, gptq for older GPUs
PORT="${VLLM_PORT:-8001}"
GPU_MEM="${GPU_MEMORY_UTILIZATION:-0.90}"
MAX_LEN="${MAX_MODEL_LEN:-8192}"

echo "Starting vLLM server"
echo "  Model:        $MODEL"
echo "  Quantization: $QUANT"
echo "  Port:         $PORT"
echo "  Max length:   $MAX_LEN"

exec python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --port "$PORT" \
    --host 0.0.0.0 \
    --quantization "$QUANT" \
    --max-model-len "$MAX_LEN" \
    --gpu-memory-utilization "$GPU_MEM" \
    --served-model-name "nepal-decarb-advisor" \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --chat-template /opt/nepal_decarb_pro/deploy/vllm/chat_template.jinja
