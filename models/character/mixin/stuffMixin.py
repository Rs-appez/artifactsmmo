from typing import TYPE_CHECKING, Protocol

from config import HEADERS
from models import Encyclopedia
from models.character.decorators import refresh_after, request_action
from models.dataclass import Item

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
                f"{self.url}/action/equip/",
                headers=HEADERS,
                json={"code": item.code, "slot": item.type, "quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            print(f"⚔️  {self.surname} equipped {item.name}")
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
        _ = await self.deposit_all_in_bank()
        if await self.withdraw_item_from_bank([("sticky_sword", 1)]):
            if not await self.equip(
                await Encyclopedia.get_item_by_code("sticky_sword")
            ):
                print(f"❌ {self.surname} failed to equip sticky sword")
