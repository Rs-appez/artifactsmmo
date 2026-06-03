class NotWorthableTaskException(Exception):
    def __init__(self, message="Not worthable task."):
        self.message = message
        super().__init__(self.message)
