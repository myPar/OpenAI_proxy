from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
from settings import app_settings
from contextlib import asynccontextmanager
from exceptions import FatalServerException, FormatServerException
from tools import *
from pydantic import ValidationError
import sys
from dtos import CompletionRequest, ChatCompletionRequest


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
    try:
        request_dto = CompletionRequest.model_validate(body)
    except ValidationError as e:
        ex = FormatServerException(str(e))
        return ex.get_json()
    headers = {
        "Authorization": f"Bearer {app_settings.server_settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    # math preprocessing:
    request_dto.prompt = preprocess_math(request_dto)
    try:
        response = await client.post(f"{app_settings.server_settings.VLLM_SERVER_URL}/v1/completions", 
                                    json=request_dto.model_dump(exclude={'r1_settings'}), headers=headers)
    except httpx.HTTPError as vllm_ex:
        ex = FatalServerException(str(vllm_ex))
        return ex.get_json()
            
    result = response.json()

    # Postprocess output
    if "choices" in result:
        for choice in result["choices"]:
            choice["text"] = postprocess_output(choice["text"], 
                                                request_dto.r1_settings.math
                                                )

    return JSONResponse(content=result, status_code=response.status_code)


@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request):
    # validate request:
    body = await request.json()
    try:
        request_dto = ChatCompletionRequest.model_validate(body)
    except ValidationError as e:
        ex = FormatServerException(str(e))
        return ex.get_json()
    try:
        check_chat_format(request_dto)
        # first - preprocess math
        request_dto.messages = preprocess_few_shot(request_dto)
        request_dto.messages = preprocess_math_chat(request_dto)
    except FormatServerException as e:
        # format is invalid - no preprocessing
        if app_settings.server_settings.PROPER_CHAT_FORMAT:
            return e.get_json()
    headers = {
        "Authorization": f"Bearer {app_settings.server_settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        response = await client.post(f"{app_settings.server_settings.VLLM_SERVER_URL}/v1/chat/completions", 
                                    json=request_dto.model_dump(exclude={'r1_settings'}),
                                    headers=headers
                                    )
    except httpx.HTTPError as vllm_ex:
        ex = FatalServerException(str(vllm_ex))
        return ex.get_json()
    result = response.json()
 
    # Postprocess output
    if "choices" in result:
        for choice in result["choices"]:
            if "message" in choice:
                if "reasoning_content" in choice["message"] and not request_dto.r1_settings.return_think_data: # remove think data field from the response
                    choice["message"].pop("reasoning_content")
                choice["message"]["content"] = postprocess_output(choice["message"]["content"], 
                                                                  request_dto.r1_settings.math
                                                                  )
    return JSONResponse(content=result, status_code=response.status_code)


@app.get("/ping")
async def ping():
    return {"message": f"pong"}
