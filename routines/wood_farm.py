from models import Character
from models.enums import JobType
from .gather import gather


async def ash_farm(character: Character):
    await character.toolize(JobType.WOODCUTTING)
    await gather(character, (6, 1))


async def spruce_farm(character: Character):
    await character.toolize(JobType.WOODCUTTING)
    await gather(character, (2, 6))


async def birch_farm(character: Character):
    await character.toolize(JobType.WOODCUTTING)
    await gather(character, (3, 5))
