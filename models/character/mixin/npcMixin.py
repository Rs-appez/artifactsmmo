from typing import TYPE_CHECKING, Protocol

from models.character.decorators import request_action, refresh_after
from models.dataclass import Item

if TYPE_CHECKING:
    from models.character import Character


class NpcMixin(Protocol):
    @request_action
    @refresh_after
    async def buy_from_npc(
        self: "Character", item: Item, quantity: int
    ) -> tuple[bool, dict | None]:
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be greater than 0")

            response = await self.client.post(
                "/npc/buy",
                json={
                    "code": item.code,
                    "quantity": quantity,
                },
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            print(f"🛒 Bought {quantity}x {item.name} from NPC")
            return True, data["data"]["character"]
        except Exception as e:
            print(f"❌ {self.surname} buy_from_npc : {e}")
            return False, None

    @request_action
    @refresh_after
    async def sell_to_npc(
        self: "Character", item: Item, quantity: int
    ) -> tuple[bool, dict | None]:
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be greater than 0")

            response = await self.client.post(
                "/npc/sell",
                json={
                    "code": item.code,
                    "quantity": quantity,
                },
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            print(f"💰 Sold {quantity}x {item.name} to NPC")
            return True, data["data"]["character"]
        except Exception as e:
            print(f"❌ {self.surname} sell_to_npc : {e}")
            return False, None
