from typing import Protocol, TYPE_CHECKING

from config import HEADERS
from models.dataclass import Item
from models.character.decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


class CraftMixin(Protocol):
    @request_action
    @refresh_after
    async def craft(
        self: "Character", item: Item, quantity: int
    ) -> tuple[bool, dict | None]:
        if not self.has_job(item.job, item.craft_level):
            print(
                f"❌ Cannot craft {item.name}, requires {item.job} level {item.craft_level}"
            )
            return False, None
        if quantity <= 0:
            print(f"❌ Cannot craft non-positive quantity of items: {quantity}")
            return False, None

        try:
            response = await self.client.post(
                "/crafting",
                json={"code": item.code, "quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            print(f"✅ {self.surname} Crafted {quantity}x {item.name}")
            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} Craft : {e}")
            return False, None
