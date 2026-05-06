from collections.abc import Awaitable, Callable
from typing import ParamSpec, Protocol

from models.bank import nearest_bank
from models.character import CharacterData


def request_action(func):
    async def wrapper(self, *args, **kwargs):
        await self.available
        return await func(self, *args, **kwargs)

    return wrapper


def need_bank(func):
    async def wrapper(self, *args, **kwargs):
        bank_location = nearest_bank(self.layer, self.location)
        current_location = self.location
        if current_location != bank_location and not await self.move(bank_location):
            print("❌ Failed to move to bank")
            return
        result = await func(self, *args, **kwargs)
        if (
            "comeback" in kwargs
            and kwargs["comeback"]
            and current_location != bank_location
        ):
            if not await self.move(current_location):
                print("❌ Failed to move back to original location")

        return result

    return wrapper


P = ParamSpec("P")


def refresh_after(
    func: Callable[P, Awaitable[tuple[bool, dict | None]]],
) -> Callable[P, Awaitable[bool]]:
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        result, character_data = await func(*args, **kwargs)
        if character_data is not None:
            character_class = args[0]
            if hasattr(character_class, "refresh_data"):
                character_class.refresh_data(CharacterData.from_dict(character_data))
        return result

    return wrapper
