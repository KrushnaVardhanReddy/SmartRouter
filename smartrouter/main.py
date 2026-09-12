import httpx
from fastapi import FastAPI, HTTPException

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
    try:
        client = OpenRouterClient()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        response = await client.generate(request)
        return response
    except httpx.HTTPStatusError as e:
        # Pass through the upstream HTTP error status code and details if possible
        status_code = e.response.status_code
        detail = f"Upstream API error: {e.response.text}"
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
