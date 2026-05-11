from typing import TYPE_CHECKING, Protocol

from config import HEADERS
from models import Encyclopedia
from models.character.decorators import refresh_after, request_action
from models.dataclass import Item, Monster
from models.dataclass.bank import Bank
from models.enums import JobType

if TYPE_CHECKING:
    from models.character import Character


class StuffMixin(Protocol):
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
            print(f"❌ {e}")
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
            print(f"❌ {e}")
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

        # temporary need refactor
        better_weapon = await Encyclopedia.get_item_by_code("sticky_sword")
        await Bank.reserve_items([(better_weapon, 1)])
        try:
            _ = await self.deposit_all_in_bank()
            if await self.withdraw_item_from_bank([(better_weapon, 1)]):
                if not await self.equip(better_weapon):
                    print(f"❌ {self.surname} failed to equip sticky sword")
        finally:
            await Bank.unreserve_items([(better_weapon, 1)])

    async def toolize(self: "Character", job: JobType) -> None:
        if self.weapon is not None and self.weapon.is_for_job(job):
            return

        for item in self.inventory:
            if item.is_for_job(job):
                if not await self.equip(item):
                    print(f"❌ {self.surname} failed to equip {item.name} to gather")
                print(f"🛠️  {self.surname} equipped {item.name} to gather")
                return

        # temporary need refactor
        best_tool = await self.get_better_tool(job)
        if best_tool is None:
            print(f"❌ {self.surname} has no better tool to equip for {job.value}")
            return
        try:
            _ = await self.deposit_all_in_bank()
            if await self.withdraw_item_from_bank([(best_tool, 1)]):
                if not await self.equip(best_tool):
                    print(f"❌ {self.surname} failed to equip {job.value}_tool")
        finally:
            await Bank.unreserve_items([(best_tool, 1)])

    async def get_better_weapon(self: "Character", mob: Monster) -> Item:  # pyright: ignore[reportReturnType]
        pass

    async def get_better_tool(self: "Character", job: JobType) -> Item | None:
        async with Bank.locked():
            bank = await Bank.check_bank()
            better_items = [
                item
                for item in bank.items
                if item.is_for_job(job) and (item.level <= self.level)
            ]
            best_tool = (
                max(better_items, key=lambda item: item.level) if better_items else None
            )
            if best_tool is not None:
                await Bank.reserve_items([(best_tool, 1)])
            return best_tool
