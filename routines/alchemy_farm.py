from models import Character
from models.enums import JobType
from .gather import gather


async def sunflower_farm(character: Character):
    await character.toolize(JobType.ALCHEMY)
    await gather(character, (2, 2))


async def nettle_farm(character: Character):
    await character.toolize(JobType.ALCHEMY)
    await gather(character, (7, 14))
