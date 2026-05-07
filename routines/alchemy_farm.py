from models import Character
from .gather import gather


async def sunflower_farm(character: Character):
    await gather(character, (2, 2))


async def nettle_farm(character: Character):
    await gather(character, (7, 14))
