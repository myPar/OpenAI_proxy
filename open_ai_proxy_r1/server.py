from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
from settings import app_settings
from contextlib import asynccontextmanager
from exceptions import FatalServerException, FormatServerException
from tools import *


chat_roles = {'user', 'assistant', 'system'}
client = None  # global reference for reuse


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = httpx.AsyncClient(timeout=app_settings.server_settings.CLIENT_TIMEOUT)
    yield
    await client.aclose()

app = FastAPI(lifespan=lifespan)


# legacy api, <think> token can't be added manually, only model itself will do it or not
@app.post("/v1/completions")
async def proxy_completions(request: Request):
    body = await request.json()
    headers = {
        "Authorization": f"Bearer {app_settings.server_settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    # math preprocessing:
    if app_settings.server_settings.MATHEMATIC:
        body['prompt'] = preprocess_math(body['prompt'])
    if app_settings.server_settings.DEFAULT_MODEL_SETTINGS:
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

    # preprocess chat:
    if "messages" in body:
        try:
            check_chat_format(body["messages"])
            # first - preprocess math
            if app_settings.server_settings.MATHEMATIC:
                body["messages"] = preprocess_math_chat(body["messages"])
            if app_settings.server_settings.PREPROCESS_FEW_SHOT:
                # includes system prompt preprocess
                body["messages"] = preprocess_few_shot(body["messages"])
            else:
                # if no few-shot preprocess just do system prompt preprocess
                body["messages"] = preprocess_system_prompt_chat(body["messages"])
        except FatalServerException as e:
            return e.get_json()
        except FormatServerException as e:
            #TODO: add logging
            # format is invalid - no preprocessing
            if app_settings.server_settings.PROPER_CHAT_FORMAT:
                return e.get_json()
    else:
        e = FormatServerException('no messages in the request')
        # TODO: add logging
        if app_settings.server_settings.PROPER_CHAT_FORMAT:
            return e.get_json()
    headers = {
        "Authorization": f"Bearer {app_settings.server_settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if app_settings.server_settings.DEFAULT_MODEL_SETTINGS:
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
