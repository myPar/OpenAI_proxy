from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "token-abc123"
openai_api_base = "http://localhost:8000/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)
model="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

# Round 1
messages = [
            # {   "role":"system",
            #     "content": "you are mathematic assistant, you solve mathematic tasks. The final answer should be printed on the last line as a number.",
            # },
            {
                "role": "user", 
                "content": "Последовательность называется сбалансированной, если каждый открывающий символ имеет соответствующий ему закрывающий, и пары скобок правильно вложены друг в друга. Проверьте последовательность скобок: '] ] { ) [ } } ( } ) { ) ( [ ] ( [ { { )' на сбалансированность. Если последовательность сбалансирована - выведите 1, иначе 0."
            }
           ]
# For granite, add: `extra_body={"chat_template_kwargs": {"thinking": True}}`
response = client.chat.completions.create(model=model, messages=messages)
reasoning_content = response.choices[0].message.reasoning_content
content = response.choices[0].message.content

print("reasoning_content:", reasoning_content)
print("content:", content)