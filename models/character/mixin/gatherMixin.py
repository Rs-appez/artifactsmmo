from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from models.character import Character


class GatherMixin(Protocol):
    async def gather(self: "Character") -> bool:
        try:
            await self.post_api("/gathering")
            return True
        except Exception as e:
            print(f"❌ {self.surname} gather : {e}")
            return False
