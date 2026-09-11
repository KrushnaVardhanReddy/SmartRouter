
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str | None = Field(default=None, description="ID of the model to use. SmartRouter intercepts this.")
    messages: list[ChatMessage]
    temperature: float = Field(default=1.0)
    max_tokens: int | None = None
    stream: bool = Field(default=False)

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str | None = None

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
    usage: ChatCompletionUsage | None = None
