from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ResponseFormat(BaseModel):
    type: Literal["text", "json_object"] = Field(default="text")


class ChatCompletionRequest(BaseModel):
    model: str | None = Field(
        default=None, description="ID of the model to use. SmartRouter intercepts this."
    )
    messages: list[ChatMessage]
    temperature: float = Field(default=1.0)
    max_tokens: int | None = Field(default=None)
    stream: bool = Field(default=False)
    response_format: ResponseFormat | None = Field(default=None)


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str | None = Field(default=None)


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = Field(default="chat.completion")
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage | None = Field(default=None)


class UsageReportResponse(BaseModel):
    total_requests: int
    total_spent_usd: float
    hypothetical_spent_usd: float
    total_saved_usd: float
    shadow_mode_active: bool
