from models import Character
from models.dataclass import Item
from models.enums import JobType


def nb_craft_needed_for_level_up(
    character: Character, item: Item, target_level: int | None = None
) -> int:

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
