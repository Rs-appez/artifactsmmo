from models import Character, Encyclopedia

from models.dataclass import Item
from models.enums import JobType


async def nb_craft_needed_for_level_up(
    character: Character, item: Item | str, target_level: int | None = None
) -> int:

    if isinstance(item, str):
        if item_object := await Encyclopedia.get_item_by_code(item):
            item = item_object
        else:
            raise ValueError(f"Item with code {item} not found.")

    if item.job == JobType.NO_JOB:
        raise ValueError("Item has no job associated with it.")
    if not target_level:
        target_level = character.get_job_level(item.job) + 1

    target_level = min(target_level, item.job.max_level)

    if target_level <= character.get_job_level(item.job):
        return 0

    nb_craft_needed = 0
    current_level = character.get_job_level(item.job)

    while current_level < target_level:
        nb_craft_needed += character.nb_action_needed_for_level_up(item)
        current_level += 1

    return nb_craft_needed
