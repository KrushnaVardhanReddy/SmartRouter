class UsageTracker:
    def __init__(self) -> None:
        self.total_requests = 0
        self.total_spent_usd = 0.0
        self.hypothetical_spent_usd = 0.0
        self.total_saved_usd = 0.0

    def record_usage(self, actual_cost: float, hypothetical_cost: float) -> None:
        self.total_requests += 1
        self.total_spent_usd += actual_cost
        self.hypothetical_spent_usd += hypothetical_cost
        self.total_saved_usd += max(0.0, hypothetical_cost - actual_cost)

    def clear(self) -> None:
        self.total_requests = 0
        self.total_spent_usd = 0.0
        self.hypothetical_spent_usd = 0.0
        self.total_saved_usd = 0.0


usage_tracker = UsageTracker()
