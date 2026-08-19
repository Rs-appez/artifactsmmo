class ImpossibleCraftException(Exception):
    """Exception raised when an impossible crafting recipe is attempted."""

    def __init__(self, message="This crafting recipe is impossible to complete."):
        self.message = message
        super().__init__(self.message)
