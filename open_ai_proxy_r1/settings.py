from pydantic import BaseModel
import pydantic_core
import json
from typing import List


class ModelSettings(BaseModel):
    temperature: float
    stop: list
    top_p: float
    max_completion_tokens: int

class ServerSettings(BaseModel):
    VLLM_SERVER_URL: str
    OPENAI_API_KEY: str
    RETURN_THINK_DATA: bool
    POSTPROCESS: bool

class AppSettings(BaseModel):
    server_settings: ServerSettings
    model_settings: ModelSettings


with open('settings.json', encoding='utf-8') as f:
    json_data = f.read()


app_settings = AppSettings.model_validate(pydantic_core.from_json(json_data))
