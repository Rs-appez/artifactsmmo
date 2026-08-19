from models.dataclass import Item


class NotEnoughInBankException(Exception):
    def __init__(
        self,
        missing_items: dict[Item, int],
        message="Not enough resources in the bank account.",
    ):
        self.message = message
        self.missing_items = missing_items
        super().__init__(self.message)
