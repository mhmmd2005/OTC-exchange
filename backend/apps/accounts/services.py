class AccountService:
    """Application service placeholder for future account workflows."""

    @staticmethod
    def normalize_full_name(full_name):
        return " ".join(full_name.split()).strip() if full_name else ""
