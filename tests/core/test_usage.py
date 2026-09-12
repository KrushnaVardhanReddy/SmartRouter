from smartrouter.core.usage import get_usage_report

def test_get_usage_report():
    report = get_usage_report()
    assert report.total_requests == 0
    assert report.total_spent_usd == 0.0
    assert report.hypothetical_spent_usd == 0.0
    assert report.total_saved_usd == 0.0
    assert report.shadow_mode_active is False
