import heapq
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

from models import Encyclopedia
from models.dataclass import Effect, Item, Monster
from models.dataclass.bank import Bank
from models.enums import EquipentType, JobType
from utils.score_equip import best_equips_for_monster

if TYPE_CHECKING:
    from models.character import Character


@asynccontextmanager
async def get_max_items(
    character: Character, item: Item, keep_free_slots: int = 0, per_stack: int = 1
) -> AsyncGenerator[tuple[uuid.UUID, int], None]:
    async with Bank.locked():
        bank = await Bank._check_bank()
        item_quantity = min(
            bank.items.get(item, 0), character.inventory_max_items - keep_free_slots
        )
        item_quantity = (item_quantity // per_stack) * per_stack
        if item_quantity <= 0:
            raise Exception(f"No {item.name} found in bank for character")
        token = await Bank._reserve_items(
            {item: item_quantity}, bank=bank, inventory=character.inventory
        )
    try:
        yield token, item_quantity
    finally:
        Bank._unreserve_items(token)


@asynccontextmanager
async def get_food(
    character: Character, quantity: int
) -> AsyncGenerator[uuid.UUID, None]:
    async with Bank.locked():
        bank = await Bank._check_bank()
        food_items = {
            item: quantity
            for item, quantity in bank.items.items()
            if item.is_food and item.can_be_used_by(character)
            if quantity > 0
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

        token = await Bank._reserve_items(packed_food, bank=bank)
    try:
        yield token
    finally:
        Bank._unreserve_items(token)


@asynccontextmanager
async def get_tool(
    character: Character, job: JobType
) -> AsyncGenerator[tuple[uuid.UUID, Item], None]:
    async with Bank.locked():
        bank = await Bank._check_bank()
        tool_items = {
            item
            for item in bank.items
            if item.is_for_job(job) and item.can_be_used_by(character)
        }
        if not tool_items:
            raise Exception(f"No tool found for job {job.value} in bank")

        job_effect = await Encyclopedia.get_effect_by_code(job.value)
        best_tool = min(tool_items, key=lambda item: item.effects.get(job_effect, 0))
        token = await Bank._reserve_items({best_tool: 1}, bank=bank)
    try:
        yield token, best_tool
    finally:
        Bank._unreserve_items(token)


async def _reserve_unequipped_items(
    character: Character, bank: Bank, items: dict[Item, int]
) -> uuid.UUID:
    reserved_items = {
        item: qty for item, qty in items.items() if item not in character.equipped_items
    }

    rings = character.get_rings
    best_rings = [
        (item, qty)
        for item, qty in items.items()
        if item.type == EquipentType.RING.value
    ]
    if (
        len(best_rings) == 1
        and rings.count(best_rings[0]) == 1
        and best_rings[0][1] > 1
    ):
        reserved_items[best_rings[0][0]] = 1

    token = await Bank._reserve_items(reserved_items, bank=bank)
    return token


@asynccontextmanager
async def get_best_stat_item(
    character: Character, wanted_effect: Effect
) -> AsyncGenerator[tuple[uuid.UUID, dict[Item, int]], None]:
    async with Bank.locked():
        bank = await Bank._check_bank()
        all_items = {
            item: qty
            for item, qty in bank.items.items()
            if item.is_equipment
            and item.can_be_used_by(character)
            and wanted_effect in item.effects
        }
        for item in character.equipped_items:
            all_items[item] = all_items.get(item, 0) + 1

        best_equipment = {
            equipmentType: max(
                (item for item in all_items if item.type == equipmentType.value),
                key=lambda item: item.effects.get(wanted_effect, 0),
                default=None,
            )
            for equipmentType in EquipentType
            if equipmentType not in [EquipentType.RING, EquipentType.ARTIFACT]
        }
        best_rings = Counter(
            heapq.nlargest(
                2,
                (
                    item
                    for item, qty in all_items.items()
                    if item.type == EquipentType.RING.value
                    for _ in range(qty)
                ),
                key=lambda item: item.effects.get(wanted_effect, 0),
            )
        ).items()
        best_artifact = heapq.nlargest(
            3,
            (item for item in all_items if item.type == EquipentType.ARTIFACT.value),
            key=lambda item: item.effects.get(wanted_effect, 0),
        )

        better_items = {item: 1 for item in best_equipment.values() if item is not None}
        better_items.update({item: qty for item, qty in best_rings})
        better_items.update({item: 1 for item in best_artifact})

        better_items = {
            item: qty
            for item, qty in better_items.items()
            if item.effects.get(wanted_effect, 0) > 0
        }

        token = await _reserve_unequipped_items(character, bank, better_items)
    try:
        yield token, better_items
    finally:
        Bank._unreserve_items(token)


@asynccontextmanager
async def get_bag(character: Character) -> AsyncGenerator[tuple[uuid.UUID, Item], None]:
    inventory_bag_effect = await Encyclopedia.get_effect_by_code("inventory_space")
    current_bag = character.get_equipped_item_by_slot(EquipentType.BAG)
    async with Bank.locked():
        bank = await Bank._check_bank()
        bag_items = {
            item
            for item in bank.items
            if item.type == "bag"
            and (
                current_bag is None
                or item.effects.get(inventory_bag_effect, 0)
                > current_bag.effects.get(inventory_bag_effect, 0)
            )
        }

        if not bag_items:
            raise Exception("No bag found in bank for character")

    best_bag = max(
        bag_items,
        key=lambda item: item.effects.get(inventory_bag_effect, 0),
    )
    token = await Bank._reserve_items({best_bag: 1}, bank=bank)
    try:
        yield token, best_bag
    finally:
        Bank._unreserve_items(token)


@asynccontextmanager
async def get_best_equipment(
    character: Character, monster: "Monster"
) -> AsyncGenerator[tuple[uuid.UUID, dict[Item, int]], None]:
    async with Bank.locked():
        bank = await Bank._check_bank()
        items = {
            item: qty
            for item, qty in bank.items.items()
            if (item.is_equipment) and item.can_be_used_by(character)
        }

        for item in character.equipped_items:
            items[item] = items.get(item, 0) + 1

        items_to_score = frozenset((item, qty) for item, qty in items.items())
        best_equipment_set = best_equips_for_monster(monster, items_to_score)
        token = await _reserve_unequipped_items(character, bank, best_equipment_set)

    try:
        yield token, best_equipment_set
    finally:
        Bank._unreserve_items(token)
