from openai import OpenAI
import openai

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "token-abc123"
openai_api_base = "http://localhost:8000/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)
model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

def openai_chat_request(test_name, messages):
    print(f"\n===== [CHAT] {test_name} =====")
    try:
        response = client.chat.completions.create(model=model, messages=messages)
        message = response.choices[0].message
        reasoning_content = getattr(message, "reasoning_content", "<no reasoning_content>")
        content = message.content
        print("reasoning_content:", reasoning_content)
        print("content:", content)
    except openai.BadRequestError as e:
        print("BadRequestError:", e.response.status_code)
        print(e.response.json())


def openai_completion_request(test_name, prompt):
    print(f"\n===== [COMPLETION] {test_name} =====")
    try:
        response = client.completions.create(model=model, prompt=prompt, max_tokens=100)
        print("completion:", response.choices[0].text)
    except openai.BadRequestError as e:
        print("BadRequestError:", e.response.status_code)
        print(e.response.json())


openai_chat_request("Error: Duplicate 'system' messages", [
    { "role": "system", "content": "ты ассистент для интеллектуальной викторины." },
    { "role": "system", "content": "кто ты?" }
])

openai_chat_request("Error: Empty messages", [])

openai_chat_request("Error: Starts with assistant", [
    { "role": "assistant", "content": "Привет" },
    { "role": "user", "content": "Кто ты?" }
])

openai_chat_request("Error: No system message", [
    { "role": "user", "content": "Кто ты?" },
    { "role": "user", "content": "Сколько будет 1+1?" }
])

# Normal cases
openai_chat_request("Normal: Single user prompt", [
    { "role": "system", "content": "ты ассистент для интеллектуальной викторины." },
    { "role": "user", "content": "Сколько будет 1+100?" }
])

openai_chat_request("Normal: Multi-turn history", [
    { "role": "system", "content": "ты ассистент для интеллектуальной викторины." },
    { "role": "user", "content": "Сколько будет 1+100?" },
    { "role": "assistant", "content": "101" },
    { "role": "user", "content": "Сколько ног у лошади?" }
])

openai_chat_request("Normal: Logic MCQ", [
    { "role": "system", "content": "ты ассистент для интеллектуальной викторины." },
    { "role": "user", "content": "Выбери один правильный вариант ответа. Напиши только букву ответа. Кто использует кровеносную систему?\nA. лошадь\nB. дерево\nC. машина\nD. скала\nОтвет:" }
])

# ───── Completion Endpoint Tests ─────
openai_completion_request("Simple math", "Сколько будет 2 + 2?\nОтвет:")
openai_completion_request("Trivia question", "Кто написал роман «Война и мир»?\nОтвет:")
openai_completion_request("Error: Empty prompt", "")