from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.gameManager import GameManager


async def _test(gm: "GameManager"):
    pass


async def test(gm: "GameManager"):

    print("-" * 20)
    print("Test sandbox")
    print("-" * 20)

    await _test(gm)

    print("-" * 20)
    print("Test sandbox done")
    print("-" * 20)
