from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, Header, HTTPException, Response
from fastapi.responses import StreamingResponse

from smartrouter.api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    UsageReportResponse,
)
from smartrouter.core.config import get_settings
from smartrouter.core.usage import usage_tracker
from smartrouter.router.dispatcher import RouterDispatcher

router = APIRouter()


@router.post("/v1/chat/completions", response_model=None)
async def create_chat_completion(
    request: ChatCompletionRequest,
    response: Response,
    x_smartrouter_shadow: bool = Header(default=False),
) -> ChatCompletionResponse | StreamingResponse:
    try:
        dispatcher = RouterDispatcher()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        completion_response, model_id, score = await dispatcher.dispatch(request, shadow_mode=x_smartrouter_shadow)
        if isinstance(completion_response, AsyncGenerator):
            headers = {
                "X-SmartRouter-Model": model_id,
                "X-SmartRouter-Score": f"{score:.3f}",
            }
            return StreamingResponse(
                completion_response, media_type="text/event-stream", headers=headers
            )

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
    settings = get_settings()
    return UsageReportResponse(
        total_requests=usage_tracker.total_requests,
        total_spent_usd=usage_tracker.total_spent_usd,
        hypothetical_spent_usd=usage_tracker.hypothetical_spent_usd,
        total_saved_usd=usage_tracker.total_saved_usd,
        shadow_mode_active=settings.router.shadow_mode,
    )
