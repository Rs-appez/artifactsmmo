from models import Character
from .gather import gather


async def ash_farm(character: Character):
    await gather(character, (6, 1))


async def spruce_farm(character: Character):
    await gather(character, (2, 6))
