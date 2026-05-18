class NotEnoughInBankException(Exception):
    def __init__(self, message="Not enough money in the bank account."):
        self.message = message
        super().__init__(self.message)
