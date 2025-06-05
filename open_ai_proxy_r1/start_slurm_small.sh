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
export CUDA_VISIBLE_DEVICES=0,1,2,3

# run vllm server:
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B \
    --enable-reasoning --reasoning-parser deepseek_r1 --tensor-parallel-size 4 --api-key='token-abc123' --port 8001 &
# cache pid for killing in future:
VLLM_PID=$!
echo "vLLM PID: $VLLM_PID"
echo $VLLM_PID > vllm.pid

# wait till vllm server is up
echo "Waiting for vLLM server to start..."
for i in {1..6000}; do
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

cd /userspace/bak2/MERA_space/MERA
export OPENAI_API_KEY="token-abc123" 
export MERA_FOLDER="/userspace/bak2/mera_results/api-R1-1.5B"
export MERA_MODEL_STRING="model=deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B,num_concurrent=128,base_url=http://localhost:8000/v1/chat/completions,tokenizer_backend=huggingface,tokenizer=deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B,timeout=600"
export MERA_COMMON_SETUP="--model local-chat-completions --batch_size=1 --predict_only --log_samples --seed 1234 --verbosity DEBUG --apply_chat_template"
export SYSTEM_PROMPT="Реши задачу по инструкции ниже. Не давай никаких объяснений и пояснений к своему ответу. Не пиши ничего лишнего. Пиши только то, что указано в инструкции. Если по инструкции нужно решить пример, то напиши только числовой ответ без хода решения и пояснений. Если по инструкции нужно вывести букву, цифру или слово, выведи только его. Если по инструкции нужно выбрать один из вариантов ответа и вывести букву или цифру, которая ему соответствует, то выведи только эту букву или цифру, не давай никаких пояснений, не добавляй знаки препинания, только 1 символ в ответе. Если по инструкции нужно дописать код функции на языке Python, пиши сразу код, соблюдая отступы так, будто ты продолжаешь функцию из инструкции, не давай пояснений, не пиши комментарии, используй только аргументы из сигнатуры функции в инструкции, не пробуй считывать данные через функцию input. Не извиняйся, не строй диалог. Выдавай только ответ и ничего больше."
bash scripts/run_benchmark_gen.sh