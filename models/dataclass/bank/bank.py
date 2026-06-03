import asyncio
import uuid
from asyncio import Lock
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from httpx import AsyncClient

from config import ARTIFACTSMMO_URL, HEADERS
from exceptions import NotEnoughInBankException
from models.dataclass import Item
from models.encyclopedia import Encyclopedia

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
    __reserved_items = defaultdict[Item, int](int)
    __tokens = defaultdict[uuid.UUID, dict[Item, int]](dict)
    __missing_promises = defaultdict[uuid.UUID, dict[Item, int]](dict)

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
        return {
            item: quantity - self.__reserved_items[item]
            for item, quantity in self._items.items()
        }

    @classmethod
    @asynccontextmanager
    async def reserve_items(
        cls,
        items: dict[Item, int],
        imediately_needed: bool = True,
        inventory: dict[Item, int] | None = None,
    ):
        async with cls.locked():
            token = await cls._reserve_items(
                items, imediately_needed=imediately_needed, inventory=inventory
            )
        try:
            yield token
        finally:
            cls._unreserve_items(token)

    @classmethod
    async def _reserve_items(
        cls,
        items: dict[Item, int],
        imediately_needed: bool = True,
        bank: "Bank | None" = None,
        inventory: dict[Item, int] | None = None,
    ) -> uuid.UUID:
        if bank is None:
            bank = await cls.__check_bank()
        missing_items = bank.__get_missing_items(items, inventory=inventory)

        if imediately_needed and missing_items:
            raise NotEnoughInBankException(
                f"Not enough items in bank to reserve {items}, missing : "
                + ", ".join(
                    f"{item.name} x{quantity}"
                    for item, quantity in missing_items.items()
                )
            )
        for item, quantity in items.items():
            item_in_inventory = inventory.get(item, 0) if inventory is not None else 0
            cls.__reserved_items[item] += quantity - item_in_inventory

        token = uuid.uuid4()
        cls.__tokens[token] = {item: quantity for item, quantity in items.items()}
        if missing_items:
            cls.__missing_promises[token] = missing_items

        return token

    @staticmethod
    def show_reservations() -> dict[uuid.UUID, dict[Item, int]]:
        """
        Check the current reservations in the bank
        (only for display purposes, does not guarantee that the items are still reserved when you want to use them)
        """
        return {token: items for token, items in Bank.__tokens.items()}

    @staticmethod
    async def get_missing_promise(token: uuid.UUID) -> dict[Item, int]:
        """
        Get the missing promise for a given token, i.e. the quantity of items that were not reserved because not enough in bank
        """
        return Bank.__missing_promises.get(token, {}).copy()

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

    def __get_missing_items(
        self, items: dict[Item, int], inventory: dict[Item, int] | None = None
    ) -> dict[Item, int]:
        missing_item: dict[Item, int] = {}
        for item, quantity in items.items():
            quantity_in_bank = self.items.get(item, 0)
            quantity_in_inventory = (
                inventory.get(item, 0) if inventory is not None else 0
            )
            if quantity_in_bank < quantity - quantity_in_inventory:
                missing_item[item] = quantity - quantity_in_bank - quantity_in_inventory

        return missing_item

    @classmethod
    def _get_reserved_items(cls, token: uuid.UUID) -> dict[Item, int]:
        return cls.__tokens.get(token, {}).copy()

    @classmethod
    @asynccontextmanager
    async def get_reserved_items_partial(cls, token: uuid.UUID, items: dict[Item, int]):
        async with cls.locked():
            new_token = cls.__get_reserved_items_partial(token, items)
        try:
            yield new_token
        finally:
            cls._unreserve_items(new_token)

    @classmethod
    def __get_reserved_items_partial(
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
    def _unreserve_items(cls, token: uuid.UUID):
        """
        Unreserve items without locking, should only be used internally when we are sure to already have the lock
        """
        if token not in cls.__tokens:
            return
        items = cls.__tokens.pop(token)
        _ = cls.__missing_promises.pop(token, None)
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
