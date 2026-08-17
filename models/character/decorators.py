import functools
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Concatenate, ParamSpec, TypeVar

from config import SANDBOX
from utils.find_nearest import find_nearest_bank
from utils.reset_cooldown import reset_cooldown

if TYPE_CHECKING:
    from models.character import Character

P = ParamSpec("P")
R = TypeVar("R")
C = TypeVar("C", bound="Character")


def request_action(
    func: Callable[Concatenate[C, P], Awaitable[R]],
) -> Callable[Concatenate[C, P], Awaitable[R]]:
    @functools.wraps(func)
    async def wrapper(self: C, *args: P.args, **kwargs: P.kwargs) -> R:
        if SANDBOX:
            await reset_cooldown(self)
        await self.available
        return await func(self, *args, **kwargs)

    return wrapper


def need_bank(
    func: Callable[Concatenate[C, P], Awaitable[R]],
) -> Callable[Concatenate[C, P], Awaitable[R | None]]:
    @functools.wraps(func)
    async def wrapper(self: C, *args: P.args, **kwargs: P.kwargs) -> R | None:
        bank_location = await find_nearest_bank(self.location)
        current_location = self.location
        await self.move(bank_location)
        result = await func(self, *args, **kwargs)
        if kwargs.get("comeback"):
            if not await self.move(current_location):
                print("❌ Failed to move back to original location")

        return result

    return wrapper


def refresh_after(
    func: Callable[Concatenate[C, P], Awaitable[dict]],
) -> Callable[Concatenate[C, P], Awaitable[None]]:
    @functools.wraps(func)
    async def wrapper(self: C, *args: P.args, **kwargs: P.kwargs) -> None:
        character_data = await func(self, *args, **kwargs)
        if character_data is not None:
            await self.update_from_dict(character_data)

    return wrapper
