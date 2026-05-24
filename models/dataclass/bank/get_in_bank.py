import heapq
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from models.dataclass import Effect, Item
from models.dataclass.bank import Bank
from models.enums import EquipentType, JobType

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
async def get_best_stat_item(character: Character, wanted_effect: Effect):
    async with Bank.locked():
        bank = await _check_bank()
        better_items_in_bank = defaultdict(int)
        best_equipment = {
            equipmentType: max(
                (
                    item
                    for item in bank.items
                    if item.is_equipment
                    and item.can_be_used_by(character)
                    and wanted_effect in item.effects
                    and item.equipment_type == equipmentType
                ),
                key=lambda item: item.effects.get(wanted_effect, 0),
                default=None,
            )
            for equipmentType in EquipentType
            if equipmentType not in [EquipentType.RING, EquipentType.ARTIFACT]
        }
        best_rings = heapq.nlargest(
            2,
            (
                (item, qty)
                for item, qty in bank.items.items()
                if item.is_equipment
                and item.can_be_used_by(character)
                and wanted_effect in item.effects
                and item.equipment_type == EquipentType.RING
            ),
            key=lambda item: item[0].effects.get(wanted_effect, 0),
        )
        # TODO : handle artifacts
        best_artifact = heapq.nlargest(
            3,
            (
                (item, qty)
                for item, qty in bank.items.items()
                if item.is_equipment
                and item.can_be_used_by(character)
                and wanted_effect in item.effects
                and item.equipment_type == EquipentType.ARTIFACT
            ),
            key=lambda item: item[0].effects.get(wanted_effect, 0),
        )

        for equipment_type, equipement in best_equipment.items():
            if equipement is not None:
                current_item = character.get_equipped_item_by_slot(equipment_type)
                if current_item is None or current_item.effects.get(
                    wanted_effect, 0
                ) < equipement.effects.get(wanted_effect, 0):
                    better_items_in_bank[equipement] = 1

        current_ring_1, current_ring_2 = character.get_rings
        current_ring_1_stat = (
            current_ring_1.effects.get(wanted_effect, 0) if current_ring_1 else 0
        )
        current_ring_2_stat = (
            current_ring_2.effects.get(wanted_effect, 0) if current_ring_2 else 0
        )
        if len(best_rings) > 0 and best_rings[0][1] > 1:
            if best_rings[0][0].effects.get(wanted_effect, 0) > current_ring_1_stat:
                better_items_in_bank[best_rings[0][0]] += 1
            if best_rings[0][0].effects.get(wanted_effect, 0) > current_ring_2_stat:
                better_items_in_bank[best_rings[0][0]] += 1
        elif len(best_rings) > 1:
            if best_rings[1][0].effects.get(wanted_effect, 0) > current_ring_2_stat:
                better_items_in_bank[best_rings[1][0]] += 1

        token = await _reserve_items(better_items_in_bank, bank=bank)
    try:
        yield token, better_items_in_bank
    finally:
        _unreserve_items(token)
