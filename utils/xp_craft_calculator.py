from math import ceil, floor
from typing import TYPE_CHECKING

from models import Encyclopedia
from models.dataclass import Item
from models.enums import JobType

if TYPE_CHECKING:
    from models.character import Character


def nb_xp_per_action(character_job_level: int, wisdom: int, item: Item) -> int:
    item_level = item.craft_level or item.level
    xp_multiplier = item.job.job_xp_multiplier if item.craft_level else 1

    if (
        character_job_level == item.job.max_level
        or character_job_level > item_level + 10
    ):
        return 0

    return floor(
        (
            item.job.get_base_xp(item_level)
            + (item_level / character_job_level)
            * item.job.get_xp_coefficient(item_level)
        )
        * xp_multiplier
        * JobType.get_wisdom_bonus(wisdom)
        + 0.5
    )


def nb_action_needed_for_level_up(
    character_job_level: int,
    character_job_xp: int,
    character_target_xp: int,
    wisdom: int,
    item: Item,
) -> tuple[int, int]:

    xp_per_action = nb_xp_per_action(character_job_level, wisdom, item)

    if xp_per_action == 0:
        return 0, xp_per_action

    return ceil(
        max(0, character_target_xp - character_job_xp) / xp_per_action
    ), xp_per_action


async def nb_craft_needed_for_level_up(
    character: "Character", item: Item | str, target_level: int | None = None
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
    current_xp = character.get_job_xp(item.job)

    while current_level < target_level:
        nb_craft, xp_gained = nb_action_needed_for_level_up(
            current_level,
            current_xp,
            JobType.get_next_level_xp(current_level),
            character.wisdom,
            item,
        )
        nb_craft_needed += nb_craft
        current_xp = (current_xp + nb_craft * xp_gained) % JobType.get_next_level_xp(
            current_level
        )
        current_level += 1

    return nb_craft_needed
