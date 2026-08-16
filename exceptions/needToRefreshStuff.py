class NeedToRefreshStuffException(Exception):
    def __init__(self, message="Need to refresh stuff."):
        self.message = message
        super().__init__(self.message)
