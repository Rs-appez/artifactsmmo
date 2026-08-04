from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING

from models import Encyclopedia
from models.dataclass import Effect, Item, Monster
from models.dataclass.bank import (
    Bank,
    get_bag,
    get_best_equipment,
    get_best_stat_item,
    get_tool,
)
from models.enums import EquipentType, JobType

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class StuffMixin:
    _effects: dict[Effect, int] = field(default_factory=dict)

    _equipped_items: dict[EquipentType, Item | None] = field(default_factory=dict)

    _bag: Item | None = None
    _ring_1: Item | None = None
    _ring_2: Item | None = None
    _artifact_1: Item | None = None
    _artifact_2: Item | None = None
    _artifact_3: Item | None = None

    @property
    def weapon(self) -> Item | None:
        return self._equipped_items.get(EquipentType.WEAPON, None)

    @property
    def effects(self) -> dict[Effect, int]:
        return self._effects.copy()

    @property
    def get_rings(self) -> tuple[Item | None, Item | None]:
        return self._ring_1, self._ring_2

    @property
    def get_artifacts(self) -> tuple[Item | None, Item | None, Item | None]:
        return self._artifact_1, self._artifact_2, self._artifact_3

    @property
    def equipped_items(self) -> list[Item]:
        all_equipped_items = [
            item
            for item in chain(
                self._equipped_items.values(),
                self.get_rings,
                self.get_artifacts,
                [self._bag],
            )
            if item is not None
        ]
        return all_equipped_items

    def get_equipped_item_by_slot(self, slot: EquipentType) -> Item | None:
        return self._equipped_items.get(slot, None)

    async def equip(
        self: "Character", item: Item, quantity: int = 1, slot: str | None = None
    ) -> bool:
        try:
            await self.post_api(
                "/equip",
                json_data=[
                    {
                        "code": item.code,
                        "slot": item.type if slot is None else slot,
                        "quantity": quantity,
                    }
                ],
            )
            return True
        except Exception as e:
            print(f"❌ {self.surname} equip : {e}")
            return False

    async def unequip(self: "Character", slot: str, quantity: int = 1) -> bool:
        try:
            await self.post_api(
                "/unequip",
                json_data=[
                    {"slot": slot, "quantity": quantity},
                ],
            )

            return True
        except Exception as e:
            print(f"❌ {self.surname} unequip : {e}")
            return False

    async def _equip_set_items(self: "Character", items: dict[Item, int]) -> None:
        for item, quantity in items.items():
            if item.type == EquipentType.RING.value:
                rings = self.get_rings
                if quantity == 2:
                    if rings[0] is None or rings[0] != item:
                        if not await self.equip(item, slot="ring1"):
                            print(
                                f"❌ {self.surname} failed to equip {item.name} in ring1"
                            )
                    if rings[1] is None or rings[1] != item:
                        if not await self.equip(item, slot="ring2"):
                            print(
                                f"❌ {self.surname} failed to equip {item.name} in ring2"
                            )
                elif item not in rings:
                    if rings[0] is None or rings[0] not in items:
                        if not await self.equip(item, slot="ring1"):
                            print(
                                f"❌ {self.surname} failed to equip {item.name} in ring1"
                            )
                    elif rings[1] is None or rings[1] not in items:
                        if not await self.equip(item, slot="ring2"):
                            print(
                                f"❌ {self.surname} failed to equip {item.name} in ring2"
                            )
            elif item.type == EquipentType.ARTIFACT.value:
                artifacts = self.get_artifacts
                if item not in artifacts:
                    for i in range(len(artifacts)):
                        if artifacts[i] is None or artifacts[i] not in items:
                            if not await self.equip(item, slot=f"artifact{i + 1}"):
                                print(
                                    f"❌ {self.surname} failed to equip {item.name} in artifact{i + 1}"
                                )
                            break
            elif self.get_equipped_item_by_slot(EquipentType(item.type)) != item:
                if not await self.equip(item):
                    print(f"❌ {self.surname} failed to equip {item.name}")

        for item in self.equipped_items:
            if item not in items and not item.is_tool:
                await self.unequip(item.type)

    async def weaponize(self: "Character", monster: Monster) -> None:
        try:
            async with get_best_equipment(self, monster) as (
                bank_token,
                best_equipment_set,
            ):
                if len(Bank.get_token_info(bank_token)) == 0:
                    return
                print(
                    f"⚔️ {self.surname} is going to search best equipment in bank for {monster.name}"
                )
                if self.need_deposit(bank_token):
                    await self.deposit_all_in_bank(with_gold=False)
                await self.withdraw_item_from_bank(bank_token)
            await self._equip_set_items(best_equipment_set)
            await self.deposit_all_in_bank(with_gold=False)
        except Exception as e:
            print(f"❌ {self.surname} Weaponize : {e}")

    async def toolize(self: "Character", job: JobType) -> None:
        try:
            best_tool = (
                self.weapon
                if self.weapon is not None and self.weapon.is_for_job(job)
                else None
            )

            best_tool_in_inventory = max(
                [
                    item
                    for item in self.inventory
                    if item.is_for_job(job) and item.can_be_used_by(self)
                ],
                key=lambda item: item.effects.get(job.value, 0),
                default=None,
            )
            if best_tool is not None and best_tool_in_inventory is not None:
                if not await best_tool.is_better_for_job_than(
                    best_tool_in_inventory, job
                ):
                    best_tool = best_tool_in_inventory

            elif best_tool_in_inventory is not None:
                best_tool = best_tool_in_inventory

            has_go_to_bank = False
            async with get_tool(self, job) as (bank_token, best_tool_in_bank):
                if best_tool is None or (
                    best_tool_in_bank is not None
                    and await best_tool_in_bank.is_better_for_job_than(best_tool, job)
                ):
                    best_tool = best_tool_in_bank
                    if self.inventory_free_space < 1:
                        _ = await self.deposit_all_in_bank(with_gold=False)

                    if not await self.withdraw_item_from_bank(bank_token):
                        print(
                            f"❌ {self.surname} failed to withdraw tool from bank for toolize"
                        )
                        return
                    has_go_to_bank = True

            if best_tool is not None and best_tool != self.weapon:
                if not await self.equip(best_tool):
                    print(f"❌ {self.surname} failed to equip tool")

            if has_go_to_bank:
                await self.deposit_all_in_bank(with_gold=False)

        except Exception as e:
            print(f"❌ {self.surname} Toolize : {e}")

    async def bagize(self: "Character") -> None:
        try:
            bag_effect = await Encyclopedia.get_effect_by_code("inventory_space")
            best_bag = max(
                [
                    item
                    for item in self.inventory
                    if item.type == EquipentType.BAG.value
                ],
                key=lambda item: item.effects.get(bag_effect, 0),
                default=None,
            )
            async with get_bag(self) as (bank_token, best_bag_in_bank):
                if best_bag is None or (
                    best_bag_in_bank.effects.get(bag_effect, 0)
                    > best_bag.effects.get(bag_effect, 0)
                ):
                    best_bag = best_bag_in_bank
                    if self.is_inventory_full:
                        _ = await self.deposit_all_in_bank(with_gold=False)

                    if not await self.withdraw_item_from_bank(bank_token):
                        print(
                            f"❌ {self.surname} failed to withdraw bag from bank for bagize"
                        )
                        return

            if best_bag is not None and (
                self._bag is None
                or self._bag.effects.get(bag_effect, 0)
                < best_bag.effects.get(bag_effect, 0)
            ):
                if not await self.equip(best_bag):
                    print(f"❌ {self.surname} failed to equip bag")
                await self.deposit_all_in_bank(with_gold=False)

        except Exception as e:
            print(f"❌ {self.surname} Bagize : {e}")

    async def maximaze_stats(self: "Character", stats: Effect) -> None:
        async with get_best_stat_item(self, stats) as (bank_token, best_item):
            if len(Bank.get_token_info(bank_token)) == 0:
                return
            print(f"👚 {self.surname} is going to search {stats.name} items in bank")

            if self.need_deposit(bank_token):
                await self.deposit_all_in_bank()
            if not await self.withdraw_item_from_bank(bank_token):
                print(
                    f"❌ {self.surname} failed to withdraw item from bank for maximaze stats"
                )
                return

        await self._equip_set_items(best_item)
        await self.deposit_all_in_bank()
