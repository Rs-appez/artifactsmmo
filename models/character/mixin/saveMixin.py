from typing import TYPE_CHECKING, Protocol
import dill

if TYPE_CHECKING:
    from models.character import Character


class SaveMixin(Protocol):
    async def save(self: "Character"):
        pass
