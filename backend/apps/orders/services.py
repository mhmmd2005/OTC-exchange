class OrderService:
    """Placeholder service for incoming order lifecycle operations."""

    @staticmethod
    def validate_order_side(side):
        return side in {"buy", "sell"}
