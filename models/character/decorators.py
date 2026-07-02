from collections.abc import Awaitable, Callable
from typing import ParamSpec

from utils.find_nearest import find_nearest_bank


def request_action(func):
    async def wrapper(self, *args, **kwargs):
        await self.available
        return await func(self, *args, **kwargs)

    return wrapper


def need_bank(func):
    async def wrapper(self, *args, **kwargs):
        bank_location = await find_nearest_bank(self.location)
        current_location = self.location
        if not await self.move(bank_location):
            print("❌ Failed to move to bank")
            return
        result = await func(self, *args, **kwargs)
        if "comeback" in kwargs and kwargs["comeback"]:
            if not await self.move(current_location):
                print("❌ Failed to move back to original location")

        return result

    return wrapper


P = ParamSpec("P")


def refresh_after(
    func: Callable[P, Awaitable[dict]],
) -> Callable[P, Awaitable[None]]:
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        character_data = await func(*args, **kwargs)
        if character_data is not None:
            character_class = args[0]
            if hasattr(character_class, "update_from_dict"):
                await character_class.update_from_dict(character_data)

    return wrapper
