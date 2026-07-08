from enum import StrEnum, auto


class SubscriptionsType(StrEnum):
    EVENT_SPAWN = auto()
    EVENT_REMOVED = auto()
    RAID_STARTED = auto()
    RAID_ENDED = auto()
    GRANDEXCHANGE_SELL_ORDER = auto()
    GRANDEXCHANGE_BUY_ORDER = auto()
    GRANDEXCHANGE_BUY = auto()
    GRANDEXCHANGE_SELL = auto()
    GRANDEXCHANGE_CANCEL_SELL_ORDER = auto()
    GRANDEXCHANGE_CANCEL_BUY_ORDER = auto()
    PENDING_ITEM_RECEIVED = auto()
    ONLINE_CHARACTERS = auto()
    VERSION = auto()
    ANNOUNCEMENT = auto()
    ACHIEVEMENT_UNLOCKED = auto()
    ACCOUNT_LOGIN = auto()
    SEASON_REWARD_UNLOCKED = auto()
    TEST = auto()
