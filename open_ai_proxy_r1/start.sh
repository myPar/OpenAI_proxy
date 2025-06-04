#!/bin/bash
. /home/cossmo/miniconda3/etc/profile.d/conda.sh
conda activate vllm_venv
export HF_TOKEN="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"

# run vllm server:
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B \
    --enable-reasoning --reasoning-parser deepseek_r1 --api-key='token-abc123' --port 8001 &
# cache pid for killing in future:
VLLM_PID=$!
echo "vLLM PID: $VLLM_PID"
echo $VLLM_PID > vllm.pid

# wait till vllm server is up
echo "Waiting for vLLM server to start..."
for i in {1..600}; do
    if curl -s -H "Authorization: Bearer token-abc123" http://localhost:8001/v1/models | grep -q '"object"'; then
        echo "vLLM server is up!"
        break
    fi
    echo "⏳ vLLM server not ready yet... retrying ($i)"
    sleep 1
done

# run proxy
fastapi run server.py &
# cache pid for killing in future
PROXY_PID=$!
echo "PROXY PID: $PROXY_PID"
echo $PROXY_PID > proxy.pid

# wait till proxy server up
echo "Waiting proxy server to start..."
for i in {1..240}; do
    if curl -s http://localhost:8000/ping | grep -q '"pong"'; then
        echo "proxy server is up!"
        break
    fi
    echo "⏳ proxy server not ready yet... retrying ($i)"
    sleep 1
done
