from smartrouter.api.models import UsageReportResponse


def get_usage_report() -> UsageReportResponse:
    return UsageReportResponse(
        total_requests=0,
        total_spent_usd=0.0,
        hypothetical_spent_usd=0.0,
        total_saved_usd=0.0,
        shadow_mode_active=False,
    )
