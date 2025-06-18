from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, model_validator, ValidationError
from settings import app_settings

model_config = app_settings.model_settings


class R1Settings(BaseModel):
    # custom r1 fields:
    math: Optional[bool] = False    # pre and post process
    return_think_data: Optional[bool] = False


# /v1/completions model
class CompletionRequest(BaseModel):
    prompt: Union[str, List[str]]
    temperature: Optional[float] = Field(default=model_config.temperature, ge=0.0, le=2.0)
    max_completion_tokens: Optional[int] = Field(default=model_config.max_completion_tokens, ge=1)
    top_p: Optional[float] = Field(default=model_config.top_p, gt=0.0, le=1.0)
    stop: Optional[Union[str, List[str]]] = None
    n: Optional[int] = Field(default=1, ge=1)
    stream: Optional[bool] = False
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    best_of: Optional[int] = None
    logit_bias: Optional[dict] = None
    user: Optional[str] = None
    r1_settings: Optional[R1Settings] = R1Settings()


# /v1/chat/completions model
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    #name: Optional[str] = None


class R1SettingsChat(BaseModel):
    # custom r1 fields:
    math: Optional[bool] = False    # pre and post process
    return_think_data: Optional[bool] = True
    few_shot_mode: Literal["DROP", "PREPROCESS", "NO_PREPROCESS"] = "PREPROCESS"


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=model_config.temperature, ge=0.0, le=2.0)
    max_completion_tokens: Optional[int] = Field(default=model_config.max_completion_tokens, ge=1)
    top_p: Optional[float] = Field(default=model_config.top_p, gt=0.0, le=1.0)
    stop: Optional[Union[str, List[str]]] = []
    n: Optional[int] = Field(default=1, ge=1)
    stream: Optional[bool] = False
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[dict] = None
    user: Optional[str] = None
    tools: Optional[List[dict]] = None  # You can expand this if your API supports tools
    # custom r1 fields:
    r1_settings: Optional[R1SettingsChat] = R1SettingsChat()


    @model_validator(mode='after')
    def check_messages(self):
        if not self.messages or not isinstance(self.messages, list) or len(self.messages) < 1:
            raise ValueError("messages field must be a non-empty list")
        if self.tools is not None:
            raise ValueError("tools calling are not supported in vllm backend for r1 model series")
        return self
