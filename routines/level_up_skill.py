from typing import TYPE_CHECKING

from models import Encyclopedia
from models.dataclass import Item
from models.enums import JobType
from routines import craft, gather
from utils.xp_craft_calculator import nb_craft_needed_for_level_up

if TYPE_CHECKING:
    from models.character import Character


async def xp_skill(
    character: Character,
    job: JobType | str,
    target_level: int | str = -1,
    item_target: Item | str | None = None,
):
    if isinstance(job, str):
        job = JobType(job)

    if isinstance(target_level, str):
        target_level = int(target_level)

    if job.is_crafting:
        if item_target is None:
            raise ValueError("item_target must be provided for crafting jobs.")
        if isinstance(item_target, str):
            item_target = await Encyclopedia.get_item_by_code(item_target)
            if item_target is None:
                raise ValueError(f"Item {item_target} not found in Encyclopedia.")
        await _xp_craft_skill(character, job, target_level, item_target)
    elif job.is_gathering:
        await _xp_gather_skill(character, job, target_level)
    else:
        raise ValueError(f"Job {job} is neither crafting nor gathering.")


async def _xp_craft_skill(
    character: Character, job: JobType, target_level: int, item_target: Item
):
    if not job.is_crafting:
        raise ValueError(f"Job {job} is not a crafting job.")

    need_for_level_up = await nb_craft_needed_for_level_up(
        character, item_target, target_level
    )
    await craft(character, item_target, need_for_level_up, recycling_after=True)


async def _xp_gather_skill(character: Character, job: JobType, target_level: int):
    if not job.is_gathering:
        raise ValueError(f"Job {job} is not a gathering job.")

    while target_level == -1 or character.get_job_level(job) < target_level:
        current_level = character.get_job_level(job)
        resource_target = max(
            [
                resource
                for resource in await Encyclopedia.get_all_resources_by_job(
                    job, current_level
                )
                if not await resource.is_event_resource
            ],
            key=lambda item: item.level,
        )

        item_target = min(
            resource_target.drops,
            key=lambda item_id: resource_target.drops[item_id]["rate"],
        )

        need_for_level_up = character.nb_action_needed_for_level_up(item_target)

        await gather(character, item_target, need_for_level_up)
