# OpenAI-Compatible Proxy Server for vLLM

Этот репозиторий содержит прокси-сервер для работы с DeepSeek-r1 и его дистиллятами, совместимый с OpenAI API, который перенаправляет запросы к локальному серверу [vLLM](https://github.com/vllm-project/vllm).

- Совместим с OpenAI API (`/v1/completions`, `/v1/chat/completions`)
- Перемещает `system` prompt в `user` (рекомендуется для deepseek-r1 и его дистиллятов)
- Опциональная очистка вывода (`\boxed{...}` → просто `...`)
- опциональное удаление reasoning (`reasoning_content`) из ответа
- Настройка температуры

### Установка зависимостей

клонируем репозиторий:
```bash
git clone https://github.com/myPar/OpenAI_proxy.git
cd open_ai_proxy_r1
```

Создайте `conda` venv и установите зависимости:

```bash
conda create -n vllm_venv python=3.12 -y
conda activate vllm_venv
pip install -r requirements.txt
```

### Запуск

Запустите `start.sh`:

```bash
bash start.sh
```

Скрипт:
- запускает `vllm serve`
- ожидает готовность vLLM-сервера
- запускает FastAPI-прокси на порту `8000`

## Примеры запросов

### Chat Completion

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer token-abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    "messages": [
      {"role": "system", "content": "Ты математический помощник."},
      {"role": "user", "content": "Реши уравнение x^2 = и обоснуй решение."}
    ]
  }'
```

### Completion

```bash
curl http://localhost:8000/v1/completions \
  -H "Authorization: Bearer token-abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    "prompt": "Реши уравнение x^2 = "
  }'
```

## Постобработка

Если включена опция `POSTPROCESS: true`, результат очищается:
- Для поля `content` извлекается содержимое из `\boxed{...}` (если есть)
- Убираются лишние пробелы и переводы строк

## Переменные
__settings.json__ содержит следующие переменные:
- `VLLM_SERVER_URL` — URL vLLM-сервера
- `OPENAI_API_KEY` — токен авторизации openAI
- `RETURN_THINK_DATA` — оставлять reasoning блок в ответе
- `POSTPROCESS` — включить постобработку
- `temperature` — температура генерации

## Пинг

Проверка работоспособности:

```bash
curl http://localhost:8000/ping
# {"message": "pong"}
```

## выключение

в `proxy.pid` и `vllm.pid` будут помещены id процессов для fast-api прокси и для vllm-сервера соответственно. Поскольку оба процесса запускаются в фоновом режиме, требуется сделать для каждого `kill pid` если хотите завершить работу.
