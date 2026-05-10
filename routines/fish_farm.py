from models import Character
from models.enums import JobType
from .gather import gather


async def gudgeon_farm(character: Character):
    await character.toolize(JobType.FISHING)
    await gather(character, (4, 2))


async def shrimp_farm(character: Character):
    await character.toolize(JobType.FISHING)
    await gather(character, (5, 2))


async def trout_farm(character: Character):
    await character.toolize(JobType.FISHING)
    await gather(character, (7, 12))
