from asyncio import Lock
from dataclasses import dataclass

from models.dataclass import Item


def lock_bank(func):
    async def wrapper(self, *args, **kwargs):
        async with Bank.locked():
            return await func(self, *args, **kwargs)

    return wrapper


@dataclass
class Bank:
    __bankelock = Lock()
    _gold: int
    _slots: int
    _expansions: int
    _expansion_cost: int
    _items: dict[Item, int]

    @classmethod
    def locked(cls) -> Lock:
        return cls.__bankelock

    async def check_bank(self) -> dict:
        return {
            "gold": self._gold,
            "slots": self._slots,
            "expansions": self._expansions,
            "expansion_cost": self._expansion_cost,
            "items": self._items.copy(),
        }
