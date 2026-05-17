from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol
import uuid

from models import Encyclopedia
from models.character.decorators import refresh_after, request_action
from models.dataclass import Effect, Item, Monster
from models.dataclass.bank import Bank
from models.enums import JobType

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class StuffMixin(Protocol):
    _weapon: Item | None = None
    _effects: dict[Effect, int] = field(default_factory=dict)

    @property
    def weapon(self) -> Item | None:
        return self._weapon

    @property
    def effects(self) -> dict[Effect, int]:
        return self._effects.copy()

    @request_action
    @refresh_after
    async def equip(
        self: "Character", item: Item, quantity: int = 1
    ) -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/equip",
                json={"code": item.code, "slot": item.type, "quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} equip : {e}")
            return False, None

    @request_action
    @refresh_after
    async def unequip(
        self: "Character", slot: str, quantity: int = 1
    ) -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/unequip",
                json={"slot": slot, "quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} unequip : {e}")
            return False, None

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
            if self.weapon is not None and self.weapon.is_for_job(job):
                return

            for item in self.inventory:
                if item.is_for_job(job):
                    if not await self.equip(item):
                        print(
                            f"❌ {self.surname} failed to equip {item.name} to gather"
                        )
                    print(f"🛠️  {self.surname} equipped {item.name} to gather")
                    return

            async with Bank.get_tool(self, job) as (bank_token, best_tool):
                if not self.is_inventory_full and self.weapon is not None:
                    _ = await self.unequip("weapon")
                _ = await self.deposit_all_in_bank()
                if await self.withdraw_item_from_bank(bank_token):
                    if not await self.equip(best_tool):
                        print(f"❌ {self.surname} failed to equip {job.value}_tool")
                    _ = await self.deposit_all_in_bank()

        except Exception as e:
            print(f"❌ {self.surname} Toolize : {e}")
