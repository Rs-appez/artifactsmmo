class DontHaveLevelException(Exception):
    def __init__(self, message="You don't have a level yet."):
        self.message = message
        super().__init__(self.message)
