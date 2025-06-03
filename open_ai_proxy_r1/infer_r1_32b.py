from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "token-abc123"
openai_api_base = "http://localhost:8001/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

# Round 1
messages = [{"role": "user", "content": "write me quick sort algorithm on c++ programming language"}]
# For granite, add: `extra_body={"chat_template_kwargs": {"thinking": True}}`
# For Qwen3 series, if you want to disable thinking in reasoning mode, add:
# extra_body={"chat_template_kwargs": {"enable_thinking": False}}
response = client.chat.completions.create(model=model, messages=messages, temperature=0.6)

reasoning_content = response.choices[0].message.reasoning_content
content = response.choices[0].message.content

print("reasoning_content:", reasoning_content)
print("content:", content)