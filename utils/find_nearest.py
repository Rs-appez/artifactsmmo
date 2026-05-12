from typing import TYPE_CHECKING
from models.dataclass import Monster, Resource
from models.enums import JobType
from models.locationRegistry import LocationRegistry

if TYPE_CHECKING:
    from models.character import Character


def __manhattan_distance(pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def __find_nearest_location(
    locations: set[tuple[int, int]], target: tuple[int, int]
) -> tuple[int, int]:
    return min(
        locations,
        key=lambda pos: __manhattan_distance(pos, target),
    )


async def find_nearest_lootable(
    character: Character, lootable: Resource | Monster
) -> tuple[int, int]:
    lootble_locations = await LocationRegistry.get_locations(lootable)
    if not lootble_locations:
        raise ValueError(f"No locations found for {lootable.name}")
    return __find_nearest_location(lootble_locations, character.location)


async def find_nearest_workshop(character: Character, job: JobType) -> tuple[int, int]:
    workshop_locations = await LocationRegistry.get_workshop_locations(job)
    if not workshop_locations:
        raise ValueError(f"No workshop locations found for job {job.value}")
    return __find_nearest_location(workshop_locations, character.location)


async def find_nearest_bank(location: tuple[int, int]) -> tuple[int, int]:
    bank_locations = await LocationRegistry.get_bank_locations()
    if not bank_locations:
        raise ValueError("No bank locations found")
    return __find_nearest_location(bank_locations, location)
