from pydantic import BaseModel
import pydantic_core
import json
from typing import List
from enum import Enum


class FewShotMode(str, Enum):
    NO_PREPROCESS = "NO_PREPROCESS"
    PREPROCESS = "PREPROCESS"
    DROP = "DROP"


class ModelSettings(BaseModel):
    temperature: float
    stop: list
    top_p: float
    max_completion_tokens: int


class ServerSettings(BaseModel):
    VLLM_SERVER_URL: str
    OPENAI_API_KEY: str
    RETURN_THINK_DATA: bool # weather return reasoning_content field or not
    POSTPROCESS: bool       # use output postprocessing or not
    MATHEMATIC: bool        # weather to ask to solve mathematic task or not
    CODE: bool              # code benchmarks postprocessing settings
    FEW_SHOT_MODE: FewShotMode # few shot preprocess mode: "NO_PREPROCESS", "PREPROCESS", "DROP"
    PROPER_CHAT_FORMAT: bool # if the chat messages order/format is invalid and this field is enabled an error response will be returned
    DEFAULT_MODEL_SETTINGS: bool # use default (recommended model parameters)
    CLIENT_TIMEOUT: int # timeout in seconds for the http client


class AppSettings(BaseModel):
    server_settings: ServerSettings
    model_settings: ModelSettings


with open('settings.json', encoding='utf-8') as f:
    json_data = f.read()


app_settings = AppSettings.model_validate(pydantic_core.from_json(json_data))
