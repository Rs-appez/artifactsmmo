from typing import TYPE_CHECKING
from models.dataclass import Map, Monster, Resource
from models.enums import JobType, Layer, TaskType
from models.locationRegistry import LocationRegistry

if TYPE_CHECKING:
    from models.character import Character


def __manhattan_distance(pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def __find_nearest_location(locations: set[Map], target: Map) -> Map:
    return min(
        locations,
        key=lambda pos: __manhattan_distance((pos.x, pos.y), (target.x, target.y)),
    )


async def find_nearest_lootable(
    character: Character, lootables: set[Resource | Monster]
) -> Map:
    pos = set()
    for lootable in lootables:
        lootble_locations = await LocationRegistry.get_locations(lootable)
        if not lootble_locations:
            raise ValueError(f"No locations found for {lootable.name}")
        pos.add(__find_nearest_location(lootble_locations, character.location))
    return __find_nearest_location(pos, character.location)


async def find_nearest_workshop(character: Character, job: JobType) -> Map:
    workshop_locations = await LocationRegistry.get_workshop_locations(job)
    if not workshop_locations:
        raise ValueError(f"No workshop locations found for job {job.value}")
    return __find_nearest_location(workshop_locations, character.location)


async def find_nearest_bank(location: Map) -> Map:
    bank_locations = await LocationRegistry.get_bank_locations()
    if not bank_locations:
        raise ValueError("No bank locations found")
    return __find_nearest_location(bank_locations, location)


async def find_nearest_tasks_master(character: Character, task_type: TaskType) -> Map:
    tasks_master_locations = await LocationRegistry.get_tasks_master_locations(
        task_type
    )
    if not tasks_master_locations:
        raise ValueError(
            f"No task master locations found for task type {task_type.value}"
        )
    return __find_nearest_location(tasks_master_locations, character.location)


async def find_nearest_transition(postion: Map, layer: Layer) -> Map:
    transition_locations = await LocationRegistry.get_transition_locations(layer)
    if not transition_locations:
        raise ValueError(f"No transition locations found for layer {layer.value}")
    return __find_nearest_location(
        {
            location
            for location in transition_locations
            if location.layer == postion.layer
        },
        postion,
    )
