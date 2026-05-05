from models import Character
from .gather import gather


async def gudgeon_farm(character: Character):
    await gather(character, (4, 2))


async def shrimp_farm(character: Character):
    await gather(character, (5, 2))
