from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from models import Encyclopedia
from models.dataclass import Effect, Item
from models.dataclass.bank import Bank, get_tool, get_best_stat_item, get_bag
from models.enums import EquipentType, JobType

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class StuffMixin:
    _effects: dict[Effect, int] = field(default_factory=dict)

    _equipped_items: dict[EquipentType, Item] = field(default_factory=dict)

    _bag: Item | None = None
    _weapon: Item | None = None
    _ring_1: Item | None = None
    _ring_2: Item | None = None
    _artifact_1: Item | None = None
    _artifact_2: Item | None = None
    _artifact_3: Item | None = None

    @property
    def weapon(self) -> Item | None:
        return self._weapon

    @property
    def effects(self) -> dict[Effect, int]:
        return self._effects.copy()

    @property
    def get_rings(self) -> tuple[Item | None, Item | None]:
        return self._ring_1, self._ring_2

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

    async def weaponize(self: "Character") -> None:
        if self.weapon is not None and self.weapon.is_weapon:
            return

        for item in self.inventory:
            if item.is_weapon:
                if not await self.equip(item):
                    print(f"❌ {self.surname} failed to equip {item.name} to fight")
                print(f"⚔️  {self.surname} equipped {item.name} to fight")
                return
        return

        # temporary need refactor
        better_weapon = await Encyclopedia.get_item_by_code("sticky_sword")
        bank_token = await Bank.reserve_items({better_weapon: 1})
        try:
            _ = await self.deposit_all_in_bank()
            if await self.withdraw_item_from_bank(bank_token):
                if not await self.equip(better_weapon):
                    print(f"❌ {self.surname} failed to equip sticky sword")
        except Exception as e:
            await Bank.unreserve_items(bank_token)

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
                    if self.inventory_free_slots < 1:
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
        # TODO : handle artifacts
        async with get_best_stat_item(self, stats) as (bank_token, best_item):
            if not best_item:
                return
            print(f"👚 {self.surname} is going to search {stats.name} items in bank")

            if self.is_inventory_full:
                await self.deposit_all_in_bank()
            if not await self.withdraw_item_from_bank(bank_token):
                print(
                    f"❌ {self.surname} failed to withdraw item from bank for maximaze stats"
                )
                return

        for item in best_item:
            if item.type in [EquipentType.RING.value, EquipentType.ARTIFACT.value]:
                continue
            if not await self.equip(item):
                print(f"❌ {self.surname} failed to equip {item.name}")

        rings = [
            (item[0], item[1])
            for item in best_item.items()
            if item[0].type == EquipentType.RING.value
        ]
        if rings:
            if rings[0][1] == 2:
                _ = await self.equip(rings[0][0], slot="ring1")
                _ = await self.equip(rings[0][0], slot="ring2")
            else:
                _ = await self.equip(rings[0][0], slot="ring1")
                if len(rings) > 1:
                    _ = await self.equip(rings[1][0], slot="ring2")

        await self.deposit_all_in_bank()
