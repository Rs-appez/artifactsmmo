from models import Character
from .gather import gather


async def copper_farm(character: Character):
    await gather(character, (2, 0))


async def iron_farm(character: Character):
    await gather(character, (1, 7))
