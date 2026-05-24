from contextlib import asynccontextmanager

from typing import TYPE_CHECKING

from models import Encyclopedia
from models.dataclass import Item
from models.dataclass.bank import Bank
from models.enums import JobType

if TYPE_CHECKING:
    from models.character import Character

_check_bank = Bank._Bank__check_bank  # pyright: ignore[reportAttributeAccessIssue]
_reserve_items = Bank._reserve_items  # pyright: ignore[reportPrivateUsage]
_unreserve_items = Bank._unreserve_items  # pyright: ignore[reportPrivateUsage]


@asynccontextmanager
async def get_max_items(
    character: Character, item: Item, keep_free_slots: int = 0, per_stack: int = 1
):
    async with Bank.locked():
        bank = await _check_bank()
        item_quantity = min(
            bank.items.get(item, 0), character.inventory_max_items - keep_free_slots
        )
        item_quantity = (item_quantity // per_stack) * per_stack
        if item_quantity <= 0:
            raise Exception(f"No {item.name} found in bank for character")
        token = await _reserve_items(
            {item: item_quantity}, bank=bank, inventory=character.inventory
        )
    try:
        yield token, item_quantity
    finally:
        _unreserve_items(token)


@asynccontextmanager
async def get_food(character: Character, quantity: int):
    async with Bank.locked():
        bank = await _check_bank()
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

        token = await _reserve_items(packed_food, bank=bank)
    try:
        yield token
    finally:
        _unreserve_items(token)


@asynccontextmanager
async def get_tool(character: Character, job: JobType):
    async with Bank.locked():
        bank = await _check_bank()
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
        token = await _reserve_items({best_tool: 1}, bank=bank)
    try:
        yield token, best_tool
    finally:
        _unreserve_items(token)


@asynccontextmanager
async def get_best_wisdom_item():
    async with Bank.locked():
        bank = await _check_bank()
        wisdom_effect = await Encyclopedia.get_effect_by_code("wisdom")
        wisdom_items = {
            item
            for item in bank.items
            if item.is_equipment and wisdom_effect in item.effects
        }
        if not wisdom_items:
            raise Exception(f"No wisdom item found in bank")

        best_wisdom_item = max(wisdom_items, key=lambda item: item.wisdom)
        token = await _reserve_items({best_wisdom_item: 1}, bank=bank)
    try:
        yield token, best_wisdom_item
    finally:
        _unreserve_items(token)
