from asyncio import Lock
import uuid
import asyncio
from dataclasses import dataclass

from httpx import AsyncClient

from collections import defaultdict
from config import ARTIFACTSMMO_URL, HEADERS
from models.dataclass import Item
from models.encyclopedia import Encyclopedia


def lock_bank(func):
    async def wrapper(self, *args, **kwargs):
        async with Bank.locked():
            return await func(self, *args, **kwargs)

    return wrapper


@dataclass
class Bank:
    __bankelock = Lock()
    __url = f"{ARTIFACTSMMO_URL}/my/bank"
    __reserved_items = defaultdict(int)
    __tokens = defaultdict(dict)

    _gold: int
    _slots: int
    _expansions: int
    _expansion_cost: int
    _items: dict[Item, int]

    @classmethod
    def locked(cls) -> Lock:
        return cls.__bankelock

    @property
    def gold(self) -> int:
        return self._gold

    @property
    def items(self) -> dict[Item, int]:
        return self._items.copy()

    @classmethod
    def get_reserved_items(cls, token: uuid.UUID) -> dict[Item, int]:
        return cls.__tokens.get(token, {}).copy()

    @classmethod
    def get_reserved_items_partial(
        cls, token: uuid.UUID, items: list[tuple[Item, int]]
    ) -> uuid.UUID:
        reserved_items = cls.__tokens.get(token, {})
        for item, quantity in items:
            if reserved_items.get(item, 0) < quantity:
                raise Exception(f"Not enough {item.name} reserved for token {token}")

        for item, quantity in items:
            reserved_items[item] -= quantity

        new_token = uuid.uuid4()
        cls.__tokens[new_token] = {item: quantity for item, quantity in items}
        return new_token

    @classmethod
    async def check_bank(cls) -> "Bank":

        load = asyncio.gather(
            cls.__get_details(),
            cls.__get_items(),
        )

        details, items = await load

        return cls(
            _gold=details["gold"],
            _slots=details["slots"],
            _expansions=details["expansions"],
            _expansion_cost=details["next_expansion_cost"],
            _items=items,
        )

    @classmethod
    @lock_bank
    async def reserve_items(
        cls, items: list[tuple[Item, int]], imediately_needed: bool = True
    ) -> uuid.UUID:
        return await cls._reserve_items(items, imediately_needed)

    @classmethod
    async def _reserve_items(
        cls, items: list[tuple[Item, int]], imediately_needed: bool = True
    ) -> uuid.UUID:
        if imediately_needed:
            bank = await cls.check_bank()
            have_enough, missing_item = bank.have_items(items)
            if not have_enough and missing_item is not None:
                raise Exception(f"Not enough {missing_item.name} in bank")
        for item, quantity in items:
            cls.__reserved_items[item] += quantity

        token = uuid.uuid4()
        cls.__tokens[token] = {item: quantity for item, quantity in items}
        return token

    @classmethod
    @lock_bank
    async def unreserve_items(cls, token: uuid.UUID):
        cls._unreserve_items(token)

    @classmethod
    def _unreserve_items(cls, token: uuid.UUID):
        """
        Unreserve items without locking, should only be used internally when we are sure to already have the lock
        """
        if token not in cls.__tokens:
            return
        items = cls.__tokens.pop(token)
        for item, quantity in items.items():
            cls.__reserved_items[item] -= quantity

    @classmethod
    async def __get_details(cls) -> dict:
        try:
            async with AsyncClient() as client:
                response = await client.get(cls.__url, headers=HEADERS)
                data = response.json()
                if "error" in data:
                    raise Exception(data["error"]["message"])
                return data["data"]
        except Exception as e:
            print(f"❌ Failed to get bank details: {e}")
            return {}

    @classmethod
    async def __get_items(cls) -> dict[Item, int]:
        try:
            async with AsyncClient() as client:
                page = 1
                max_pages = 2
                list_items = {}
                while page <= max_pages:
                    response = await client.get(
                        f"{cls.__url}/items",
                        headers=HEADERS,
                        params={"size": 100, "page": page},
                    )
                    data = response.json()
                    if "error" in data:
                        raise Exception(data["error"]["message"])
                    items_data = data["data"]
                    list_items.update(
                        {
                            await Encyclopedia.get_item_by_code(item["code"]): item[
                                "quantity"
                            ]
                            for item in items_data
                        }
                    )
                    page += 1
                    max_pages = data["pages"]
                return list_items

        except Exception as e:
            print(f"❌ Failed to get bank items: {e}")
            return {}

    def have_items(self, items: list[tuple[Item, int]]) -> tuple[bool, Item | None]:
        for item, quantity in items:
            if self._items.get(item, 0) - self.__reserved_items[item] < quantity:
                return False, item
        return True, None
