from fastapi import APIRouter

from smartrouter.api.models import UsageReportResponse
from smartrouter.core.usage import get_usage_report

router = APIRouter()


@router.get("/v1/usage", response_model=UsageReportResponse)
async def get_usage_report_route() -> UsageReportResponse:
    return get_usage_report()
