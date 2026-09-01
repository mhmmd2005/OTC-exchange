class OTCQuoteService:
    """Placeholder for OTC quote evaluation logic."""

    @staticmethod
    def status_is_terminal(status):
        return status in {"accepted", "expired", "rejected", "cancelled"}
