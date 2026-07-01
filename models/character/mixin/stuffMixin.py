from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from models import Encyclopedia
from models.dataclass import Effect, Item
from models.dataclass.bank import Bank, get_tool
from models.dataclass.bank.get_in_bank import get_best_stat_item
from models.enums import EquipentType, JobType

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class StuffMixin(Protocol):
    _effects: dict[Effect, int] = field(default_factory=dict)

    _equipped_items: dict[EquipentType, Item] = field(default_factory=dict)

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
                json=[
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
                json=[
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
            current_better_tool = None
            if self.weapon is not None and self.weapon.is_for_job(job):
                current_better_tool = self.weapon

            for item in self.inventory:
                if item.is_for_job(job) and item.can_be_used_by(self):
                    if current_better_tool is None or await item.is_better_for_job_than(
                        current_better_tool
                    ):
                        current_better_tool = item

            try:
                async with get_tool(self, job) as (bank_token, best_tool_in_bank):
                    print(
                        f"🛠️  {self.surname} is going to search {job.value}_tool in bank"
                    )
                    if not self.is_inventory_full and self.weapon is not None:
                        _ = await self.unequip("weapon")
                    _ = await self.deposit_all_in_bank()
                    if not await self.withdraw_item_from_bank(bank_token):
                        raise Exception(
                            f"❌ {self.surname} failed to withdraw {job.value}_tool from bank"
                        )
            except Exception:
                best_tool_in_bank = None

            if current_better_tool is not None and best_tool_in_bank is not None:
                if await best_tool_in_bank.is_better_for_job_than(current_better_tool):
                    current_better_tool = best_tool_in_bank
            elif best_tool_in_bank is not None:
                current_better_tool = best_tool_in_bank

            if current_better_tool is None:
                print(f"❌ {self.surname} has no tool for job {job.value}")
                return

            if not await self.equip(current_better_tool):
                print(f"❌ {self.surname} failed to equip {job.value}_tool")
            _ = await self.deposit_all_in_bank()

        except Exception as e:
            print(f"❌ {self.surname} Toolize : {e}")

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
