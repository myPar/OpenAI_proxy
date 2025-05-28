from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import os
from settings import app_settings
from contextlib import asynccontextmanager
import re


client = None  # global reference for reuse


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = httpx.AsyncClient(timeout=600)
    yield
    await client.aclose()

app = FastAPI(lifespan=lifespan)


def preprocess_prompt(prompt: str) -> str:
    return prompt


def extract_boxed_content(text):
    match = re.search(r'\\boxed\{(.*?)}', text)
    if match:
        return match.group(1)
    return text


def postprocess_output(text: str, postprocess:bool) -> str:
    if text is None:
        return ""
    if postprocess:
        text = extract_boxed_content(text)
        text = text.strip()
    return text


# moving system prompt content to user prompt and remove system prompt at all
def preprocess_chat_prompts(messages: list) -> list:
    i = 0
    result_messages = []
    sys_prompt = None

    while i < len(messages):
        msg = messages[i]
        if msg['role'] == 'system':
            # set system prompt to empty string
            sys_prompt = msg['content']
            i += 1
            continue
        elif msg['role'] == 'user':
            # for mathematic problems add recommended prefix for r1:
            if app_settings.server_settings.MATHEMATIC:
                msg['content'] = "You will be given a problem. Please reason step by step, and put your final answer within \\boxed{}:\n" + msg['content']
            # add last system prompt to user as recommended for r1:                
            if sys_prompt is not None and sys_prompt.strip() != "":
                msg['content'] = sys_prompt + '\n' + msg['content']
                
        result_messages.append(msg)
        i += 1

    return result_messages

# legacy api, <think> token can't be added manually, only model itself will do it or not
@app.post("/v1/completions")
async def proxy_completions(request: Request):
    body = await request.json()
    headers = {
        "Authorization": f"Bearer {app_settings.server_settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body["temperature"] = app_settings.model_settings.temperature   # set temperature to recommended value
    body["stop"] = app_settings.model_settings.stop   # set stop field
    body["max_completion_tokens"] = app_settings.model_settings.max_completion_tokens
    body["top_p"] = app_settings.model_settings.top_p    
    response = await client.post(f"{app_settings.server_settings.VLLM_SERVER_URL}/v1/completions", json=body, headers=headers)
    result = response.json()
    print(f"body: {body}")
    print(f"result: {result}")
    # Postprocess output
    if "choices" in result:
        for choice in result["choices"]:
            choice["text"] = postprocess_output(choice["text"], app_settings.server_settings.POSTPROCESS)

    return JSONResponse(content=result, status_code=response.status_code)


@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request):
    body = await request.json()
    # Preprocess system prompt (or any message role-based logic)
    if "messages" in body:
        body["messages"] = preprocess_chat_prompts(body["messages"])    # move system prompt content to user prompt
        # if body["messages"][-1]['role'] == 'user':
        #     body["messages"].append({'role':'assistant', 'content':'<think>\n'})    # add think token manually as recommended

    headers = {
        "Authorization": f"Bearer {app_settings.server_settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body["temperature"] = app_settings.model_settings.temperature   # set temperature to recommended value
    body["stop"] = app_settings.model_settings.stop   # set stop field
    body["max_completion_tokens"] = app_settings.model_settings.max_completion_tokens
    body["top_p"] = app_settings.model_settings.top_p

    response = await client.post(f"{app_settings.server_settings.VLLM_SERVER_URL}/v1/chat/completions", json=body, headers=headers)
    result = response.json()
    print(f"body: {body}")
    print(f"result: {result}")
 
    # Postprocess output
    if "choices" in result:
        for choice in result["choices"]:
            if "message" in choice:
                if "reasoning_content" in choice["message"] and not app_settings.server_settings.RETURN_THINK_DATA: # remove think data field from the response
                    choice["message"].pop("reasoning_content")
                choice["message"]["content"] = postprocess_output(choice["message"]["content"], app_settings.server_settings.POSTPROCESS)

    return JSONResponse(content=result, status_code=response.status_code)


@app.get("/ping")
async def ping():
    return {"message": f"pong"}
