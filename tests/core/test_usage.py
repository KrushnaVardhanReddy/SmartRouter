from smartrouter.core.usage import UsageTracker


def test_usage_tracker_initial_state():
    tracker = UsageTracker()
    assert tracker.total_requests == 0
    assert tracker.total_spent_usd == 0.0
    assert tracker.hypothetical_spent_usd == 0.0
    assert tracker.total_saved_usd == 0.0

def test_usage_tracker_record_usage():
    tracker = UsageTracker()

    tracker.record_usage(0.001, 0.02)
    assert tracker.total_requests == 1
    assert tracker.total_spent_usd == 0.001
    assert tracker.hypothetical_spent_usd == 0.02
    assert tracker.total_saved_usd == 0.019

    tracker.record_usage(0.02, 0.02)
    assert tracker.total_requests == 2
    assert tracker.total_spent_usd == 0.021
    assert tracker.hypothetical_spent_usd == 0.04
    # Total saved should only increase if hypothetical > actual
    assert tracker.total_saved_usd == 0.019

def test_usage_tracker_clear():
    tracker = UsageTracker()
    tracker.record_usage(0.001, 0.02)

    tracker.clear()
    assert tracker.total_requests == 0
    assert tracker.total_spent_usd == 0.0
    assert tracker.hypothetical_spent_usd == 0.0
    assert tracker.total_saved_usd == 0.0
