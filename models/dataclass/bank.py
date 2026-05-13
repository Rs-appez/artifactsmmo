import asyncio
import uuid
from asyncio import Lock
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from httpx import AsyncClient

from config import ARTIFACTSMMO_URL, HEADERS
from models.dataclass import Item
from models.encyclopedia import Encyclopedia
from models.enums import JobType

if TYPE_CHECKING:
    from models.character import Character


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

    @staticmethod
    def check_reservations() -> dict[uuid.UUID, dict[Item, int]]:
        return Bank.__tokens.copy()

    @classmethod
    async def __check_bank(cls) -> "Bank":

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

    def __have_items(self, items: dict[Item, int]) -> tuple[bool, Item | None]:
        for item, quantity in items.items():
            if self._items.get(item, 0) - self.__reserved_items[item] < quantity:
                return False, item
        return True, None

    @classmethod
    def get_reserved_items(cls, token: uuid.UUID) -> dict[Item, int]:
        return cls.__tokens.get(token, {}).copy()

    @classmethod
    def get_reserved_items_partial(
        cls, token: uuid.UUID, items: dict[Item, int]
    ) -> uuid.UUID:
        reserved_items = cls.__tokens.get(token, {})
        for item, quantity in items.items():
            if reserved_items.get(item, 0) < quantity:
                raise Exception(f"Not enough {item.name} reserved for token {token}")

        for item, quantity in items.items():
            reserved_items[item] -= quantity

        new_token = uuid.uuid4()
        cls.__tokens[new_token] = {item: quantity for item, quantity in items.items()}
        return new_token

    @classmethod
    @lock_bank
    async def reserve_items(
        cls, items: dict[Item, int], imediately_needed: bool = True
    ) -> uuid.UUID:
        return await cls._reserve_items(items, imediately_needed)

    @classmethod
    async def _reserve_items(
        cls,
        items: dict[Item, int],
        imediately_needed: bool = True,
        bank: "Bank | None" = None,
    ) -> uuid.UUID:
        if imediately_needed:
            if bank is None:
                bank = await cls.__check_bank()
            have_enough, missing_item = bank.__have_items(items)
            if not have_enough and missing_item is not None:
                raise Exception(f"Not enough {missing_item.name} in bank")
        for item, quantity in items.items():
            cls.__reserved_items[item] += quantity

        token = uuid.uuid4()
        cls.__tokens[token] = {item: quantity for item, quantity in items.items()}
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
    @lock_bank
    async def get_food(cls, character: Character, quantity: int) -> uuid.UUID:
        bank = await cls.__check_bank()
        food_items = {
            item: quantity
            for item, quantity in bank.items.items()
            if item.is_food and item.can_be_used_by(character)
        }
        if not food_items:
            raise Exception("No food found in bank for character")
        packed_food = {}
        for item, available_quantity in sorted(
            food_items.items(), key=lambda x: x[1], reverse=True
        ):
            if quantity <= 0:
                break
            use_quantity = min(available_quantity, quantity)
            packed_food[item] = use_quantity
            quantity -= use_quantity

        return await cls._reserve_items(packed_food, bank=bank)

    @classmethod
    @lock_bank
    async def get_tool(
        cls, character: Character, job: JobType
    ) -> tuple[uuid.UUID, Item]:
        bank = await cls.__check_bank()
        tool_items = {
            item
            for item in bank.items
            if item.is_for_job(job)
            and item.level <= character.level
            and item.can_be_used_by(character)
        }
        if not tool_items:
            raise Exception(f"No tool found for job {job.value} in bank")

        best_tool = max(tool_items, key=lambda item: item.level)
        return (await cls._reserve_items({best_tool: 1}, bank=bank), best_tool)

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
