. /home/cossmo/miniconda3/etc/profile.d/conda.sh
conda activate vllm_venv

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
