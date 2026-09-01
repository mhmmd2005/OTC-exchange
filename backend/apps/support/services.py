class SupportService:
    """Placeholder for support workflow automation."""

    @staticmethod
    def default_priority(category):
        return "medium" if category in {"wallet", "account"} else "low"
