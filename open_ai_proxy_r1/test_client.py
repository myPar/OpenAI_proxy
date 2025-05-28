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
            #     "content": "you are mathematic assistant, you solve mathematic tasks.",
            # },
            {
                "role": "user", 
                "content": "Опираясь на логику и общеизвестные факты, ответьте на вопрос: Кто, вероятно, использует свою кровеносную систему?\nA. лошадь после гонки\nB. дерево, стоящее в лесу\nC. машина во время автосоревнования\nD. скала на молекулярном уровне\nВ качестве ответа запишите только букву верного варианта: A, B, C или D без дополнительных объяснений.\nОтвет:"
            }
           ]
# For granite, add: `extra_body={"chat_template_kwargs": {"thinking": True}}`
response = client.chat.completions.create(model=model, messages=messages)
reasoning_content = response.choices[0].message.reasoning_content
content = response.choices[0].message.content

print("reasoning_content:", reasoning_content)
print("content:", content)