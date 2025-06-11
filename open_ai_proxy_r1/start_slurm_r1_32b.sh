#!/bin/bash
#SBATCH --job-name=mera_r1
#SBATCH --partition=a100
#SBATCH --output=output
#SBATCH --error=output.err
#SBATCH --nodes=1
#SBATCH --nodelist=ngpu09
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
export HF_TOKEN=""
export VLLM_NO_USAGE_STATS=1
export VLLM_CACHE_ROOT="/userspace/bak2/vllm_cache"
export CUDA_VISIBLE_DEVICES=0,1

# run vllm server:
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
    --enable-reasoning --reasoning-parser deepseek_r1 --tensor-parallel-size 2 --api-key='token-abc123' --port 8001 &
# cache pid for killing in future:
VLLM_PID=$!
echo "vLLM PID: $VLLM_PID"
echo $VLLM_PID > vllm.pid

# wait till vllm server is up
echo "Waiting for vLLM server to start..."
for i in {1..60000}; do
    if curl -s -H "Authorization: Bearer token-abc123" http://localhost:8001/v1/models | grep -q '"object"'; then
        echo "vLLM server is up!"
        break
    fi
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

python /userspace/bak2/r1_32b/OpenAI_proxy/open_ai_proxy_r1/test_client.py
kill $VLLM_PID
kill $PROXY_PID