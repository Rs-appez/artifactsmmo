import asyncio
import functools
import uuid
from asyncio import Lock
from collections import defaultdict
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncGenerator, Concatenate, ParamSpec, TypeVar

from httpx import AsyncClient

from config import ARTIFACTSMMO_URL, HEADERS, SANDBOX
from exceptions import NotEnoughInBankException
from models.dataclass import Item
from models.encyclopedia import Encyclopedia
from utils.reset_cooldown import reset_cooldown

if TYPE_CHECKING:
    from models.character import Character


P = ParamSpec("P")
R = TypeVar("R")
C = TypeVar("C", bound="Character")


def lock_bank(
    func: Callable[Concatenate[C, P], Awaitable[R]],
) -> Callable[Concatenate[C, P], Awaitable[R]]:
    @functools.wraps(func)
    async def wrapper(self: C, *args: P.args, **kwargs: P.kwargs) -> R:
        if SANDBOX:
            await reset_cooldown(self)
        await self.available
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
    __items: dict[Item, int]

    @classmethod
    def locked(cls) -> Lock:
        return cls.__bankelock

    @classmethod
    async def refresh_bank(cls) -> None:
        async with cls.locked():
            load = asyncio.gather(
                cls.__get_details(),
                cls.__get_items(),
            )

            details, items = await load
            cls._gold = details["gold"]
            cls._slots = details["slots"]
            cls._expansions = details["expansions"]
            cls._expansion_cost = details["next_expansion_cost"]
            cls.__items = items

    @classmethod
    async def gold(cls) -> int:
        async with cls.locked():
            return cls._gold

    @classmethod
    @asynccontextmanager
    async def items(cls) -> AsyncGenerator[dict[Item, int], None]:
        async with cls.locked():
            yield cls._items()

    @classmethod
    def _items(cls) -> dict[Item, int]:
        return {
            item: qty
            for item, quantity in cls.__items.items()
            if (qty := max(quantity - cls.__reserved_items[item], 0)) > 0
        }

    @classmethod
    async def _deposit_gold(cls, quantity: int) -> None:
        cls._gold += quantity

    @classmethod
    async def _withdraw_gold(cls, quantity: int) -> None:
        cls._gold -= quantity

    @classmethod
    async def _deposit_items(cls, items: dict[Item, int]) -> None:
        for item, quantity in items.items():
            cls.__items[item] = cls.__items.get(item, 0) + quantity

    @classmethod
    async def _withdraw_items(cls, items: dict[Item, int]) -> None:
        for item, quantity in items.items():
            cls.__items[item] -= quantity

    @classmethod
    @asynccontextmanager
    async def reserve_items(
        cls,
        items: dict[Item, int],
        imediately_needed: bool = True,
        inventory: dict[Item, int] | None = None,
        tokens_to_revoke: set[uuid.UUID] | None = None,
        auto_unreserve_token: bool = True,
    ) -> AsyncGenerator[uuid.UUID, None]:
        async with cls.locked():
            if tokens_to_revoke:
                for token in tokens_to_revoke:
                    cls._unreserve_items(token)
            token = await cls._reserve_items(
                items, imediately_needed=imediately_needed, inventory=inventory
            )
        try:
            yield token
        finally:
            if auto_unreserve_token:
                cls._unreserve_items(token)

    @classmethod
    async def _reserve_items(
        cls,
        items: dict[Item, int],
        imediately_needed: bool = True,
        inventory: dict[Item, int] | None = None,
    ) -> uuid.UUID:
        missing_items = cls.__get_missing_items(items, inventory=inventory)

        if imediately_needed and missing_items:
            raise NotEnoughInBankException(
                missing_items,
                f"Not enough items in bank to reserve {items}, missing : "
                + ", ".join(
                    f"{item.name} x{quantity}"
                    for item, quantity in missing_items.items()
                ),
            )
        for item, quantity in items.items():
            cls.__reserved_items[item] += quantity

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
    def get_token_info(token: uuid.UUID) -> dict[Item, int]:
        """
        Get the reserved items for a given token
        """
        return Bank.__tokens.get(token, {}).copy()

    @staticmethod
    async def get_missing_promise(token: uuid.UUID) -> dict[Item, int]:
        """
        Get the missing promise for a given token, i.e. the quantity of items that were not reserved because not enough in bank
        """
        return Bank.__missing_promises.get(token, {}).copy()

    @classmethod
    def __get_missing_items(
        cls, items: dict[Item, int], inventory: dict[Item, int] | None = None
    ) -> dict[Item, int]:
        missing_item: dict[Item, int] = {}
        for item, quantity in items.items():
            quantity_in_bank = cls._items().get(item, 0)
            quantity_in_inventory = (
                inventory.get(item, 0) if inventory is not None else 0
            )
            if quantity_in_bank < quantity - quantity_in_inventory:
                missing_item[item] = quantity - quantity_in_bank - quantity_in_inventory

        return missing_item

    @classmethod
    @asynccontextmanager
    async def get_reserved_items_partial(
        cls, token: uuid.UUID, items: dict[Item, int]
    ) -> AsyncGenerator[uuid.UUID, None]:
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
                response = await client.get(cls.__url, headers=HEADERS, timeout=5.0)
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
                list_items: dict[Item, int] = {}
                while page <= max_pages:
                    response = await client.get(
                        f"{cls.__url}/items",
                        headers=HEADERS,
                        params={"size": 100, "page": page},
                        timeout=5.0,
                    )
                    data = response.json()
                    if "error" in data:
                        raise Exception(data["error"]["message"])
                    items_data = data["data"]
                    list_items.update(
                        {
                            item_obj: qty
                            for item in items_data
                            if (
                                item_obj := await Encyclopedia.get_item_by_code(
                                    item["code"]
                                )
                            )
                            and (qty := item.get("quantity", 0))
                            and qty > 0
                        }
                    )
                    page += 1
                    max_pages = data["pages"]
                return list_items

        except Exception as e:
            print(f"❌ Failed to get bank items: {e}")
            return {}
