from typing import TYPE_CHECKING

from models.dataclass import Item

if TYPE_CHECKING:
    from models.character import Character


class CraftMixin:
    async def craft(self: "Character", item: Item, quantity: int) -> bool:
        if not self.has_job(item.job, item.craft_level):
            print(
                f"❌ Cannot craft {item.name}, requires {item.job} level {item.craft_level}"
            )
            return False
        if quantity <= 0:
            print(f"❌ Cannot craft non-positive quantity of items: {quantity}")
            return False

        try:
            await self.post_api(
                "/crafting", json_data={"code": item.code, "quantity": quantity}
            )
            print(f"󱤲 {self.surname} Crafted {quantity}x {item.name}")
            return True
        except Exception as e:
            print(f"❌ {self.surname} Craft : {e}")
            return False

    async def decraft(self: "Character", item: Item, quantity: int) -> bool:
        if quantity <= 0:
            print(f"❌ Cannot decraft non-positive quantity of items: {quantity}")
            return False

        if not self.has_in_inventory({item: quantity}):
            print(f"❌ Cannot decraft {quantity}x {item.name}")
            return False

        try:
            await self.post_api(
                "/recycling", json_data={"code": item.code, "quantity": quantity}
            )
            print(f"󰑌 {self.surname} Decrafted {quantity}x {item.name}")
            return True
        except Exception as e:
            print(f"❌ {self.surname} Decraft : {e}")
            return False
