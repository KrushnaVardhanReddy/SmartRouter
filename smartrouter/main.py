from fastapi import FastAPI

from smartrouter.api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from smartrouter.router.clients import OpenRouterClient

app = FastAPI(title="SmartRouter", version="1.0.0")


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
) -> ChatCompletionResponse:
    client = OpenRouterClient()
    return await client.generate(request)
