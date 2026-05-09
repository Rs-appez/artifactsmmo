class ImpossibleCombatException(Exception):
    def __init__(self, message="Combat is impossible."):
        self.message = message
        super().__init__(self.message)
