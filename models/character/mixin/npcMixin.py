from typing import TYPE_CHECKING, Protocol

from models.dataclass import Item

if TYPE_CHECKING:
    from models.character import Character


class NpcMixin(Protocol):
    async def buy_from_npc(self: "Character", item: Item, quantity: int) -> bool:
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be greater than 0")
            await self.post_api(
                "/npc/buy", json={"code": item.code, "quantity": quantity}
            )
            print(f"🛒 Bought {quantity}x {item.name} from NPC")
            return True
        except Exception as e:
            print(f"❌ {self.surname} buy_from_npc : {e}")
            return False

    async def sell_to_npc(self: "Character", item: Item, quantity: int) -> bool:
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be greater than 0")

            await self.post_api(
                "/npc/sell", json={"code": item.code, "quantity": quantity}
            )
            print(f"💰 Sold {quantity}x {item.name} to NPC")

            return True
        except Exception as e:
            print(f"❌ {self.surname} sell_to_npc : {e}")
            return False
