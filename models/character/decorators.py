import functools
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Concatenate, ParamSpec, TypeVar

from utils.find_nearest import find_nearest_bank

if TYPE_CHECKING:
    from models.character import Character

P = ParamSpec("P")
R = TypeVar("R")
SelfT = TypeVar("SelfT", bound="Character")


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class ActionError(Exception):
    """Base class for *expected* in-game action failures (API rejections, etc.)."""


class BankUnreachableError(ActionError):
    """Raised when the character cannot reach the bank."""


# --------------------------------------------------------------------------- #
# Cooldown / availability
# --------------------------------------------------------------------------- #
def request_action(
    func: Callable[Concatenate[SelfT, P], Awaitable[R]],
) -> Callable[Concatenate[SelfT, P], Awaitable[R]]:
    """Wait until the character is off cooldown before running the action."""

    @functools.wraps(func)
    async def wrapper(self: SelfT, *args: P.args, **kwargs: P.kwargs) -> R:
        await self.available
        return await func(self, *args, **kwargs)

    return wrapper


# --------------------------------------------------------------------------- #
# Bank movement
# --------------------------------------------------------------------------- #
def need_bank(
    func: Callable[Concatenate[SelfT, P], Awaitable[R]],
) -> Callable[Concatenate[SelfT, P], Awaitable[R]]:
    """Move to the nearest bank before the action; optionally return afterward.

    `comeback` is read at *call time* from the method's kwargs, so each
    invocation can decide whether to return to the origin location.
    """

    @functools.wraps(func)
    async def wrapper(self: SelfT, *args: P.args, **kwargs: P.kwargs) -> R:
        origin = self.location
        bank_location = await find_nearest_bank(self.location)
        comeback = kwargs.pop("comeback", False)
        if not await self.move(bank_location):
            raise BankUnreachableError(
                f"{self.surname} could not reach bank at {bank_location}"
            )

        result = await func(self, *args, **kwargs)

        if comeback:
            await self.move(origin)

        return result

    return wrapper


# --------------------------------------------------------------------------- #
# State refresh
# --------------------------------------------------------------------------- #
def refresh_after(
    func: Callable[Concatenate[SelfT, P], Awaitable[dict]],
) -> Callable[Concatenate[SelfT, P], Awaitable[None]]:
    """Refresh the character from the dict the wrapped API call returns."""

    @functools.wraps(func)
    async def wrapper(self: SelfT, *args: P.args, **kwargs: P.kwargs) -> None:
        character_data = await func(self, *args, **kwargs)
        if character_data is not None:
            await self.update_from_dict(character_data)

    return wrapper


# --------------------------------------------------------------------------- #
# Uniform error handling for action methods
# --------------------------------------------------------------------------- #
def safe_action(action_name: str):
    """Catch *expected* action failures, log them, and return False.

    Only catches `ActionError` — programming errors propagate so real bugs
    are never silently swallowed as "failed actions".
    """

    def decorator(
        func: Callable[Concatenate[SelfT, P], Awaitable[bool]],
    ) -> Callable[Concatenate[SelfT, P], Awaitable[bool]]:
        @functools.wraps(func)
        async def wrapper(self: SelfT, *args: P.args, **kwargs: P.kwargs) -> bool:
            try:
                return await func(self, *args, **kwargs)
            except ActionError as e:
                print(f"❌ {self.surname} {action_name}: {e}")
                return False

        return wrapper

    return decorator
