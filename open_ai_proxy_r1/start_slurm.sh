#!/bin/bash
#SBATCH --job-name=qwen_doc_filter
#SBATCH --partition=a100
#SBATCH --output=output
#SBATCH --error=output.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1

# conda
. "/userspace/bak2/miniconda3/etc/profile.d/conda.sh"
conda activate MERA_vllm

# cuda
export PATH=/usr/local/cuda-11/bin${PATH:+:${PATH}}

# while job is running, you can exec:
# srun --pty --overlap --jobid <jobid> bash
#
# this will give you cli for that node, where you can use nvidia-smi


# if you have to use pip, you must set cache directory before "pip install":
export PIP_CACHE_DIR="/userspace/bak2/pip/.cache"

# other cache dirs can be set in the same manner:
export HF_HOME="/userspace/bak2/hf"
export VLLM_NO_USAGE_STATS=1
export VLLM_CACHE_ROOT="/userspace/bak2/vllm_cache"

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
    if curl -s http://localhost:8001/v1/models | grep -q '"object"'; then
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
