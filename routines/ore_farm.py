from models import Character
from models.enums import JobType
from .gather import gather


async def copper_farm(character: Character):
    await character.toolize(JobType.MINING)
    await gather(character, (2, 0))


async def iron_farm(character: Character):
    await character.toolize(JobType.MINING)
    await gather(character, (1, 7))


async def coal_farm(character: Character):
    await character.toolize(JobType.MINING)
    await gather(character, (1, 6))
