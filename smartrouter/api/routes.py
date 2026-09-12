import httpx
from fastapi import APIRouter, Header, HTTPException, Response

from smartrouter.api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    UsageReportResponse,
)
from smartrouter.router.dispatcher import RouterDispatcher

router = APIRouter()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    response: Response,
    x_smartrouter_shadow: bool = Header(default=False),
) -> ChatCompletionResponse:
    try:
        dispatcher = RouterDispatcher()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        completion_response, model_id, score = await dispatcher.dispatch(request, shadow_mode=x_smartrouter_shadow)
        response.headers["X-SmartRouter-Model"] = model_id
        response.headers["X-SmartRouter-Score"] = f"{score:.3f}"
        return completion_response
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        detail = f"Upstream API error: {e.response.text}"
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/usage", response_model=UsageReportResponse)
async def get_usage_report() -> UsageReportResponse:
    # Dummy zero-ed values as instructed for now
    return UsageReportResponse(
        total_requests=0,
        total_spent_usd=0.0,
        hypothetical_spent_usd=0.0,
        total_saved_usd=0.0,
        shadow_mode_active=False,
    )
