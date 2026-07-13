from models import Character, Encyclopedia
from models.enums import JobType
from routines import gather


async def xp_skill(character: Character, job: JobType | str, target_level: int = -1):
    if isinstance(job, str):
        job = JobType(job)

    if job.is_crafting:
        await _xp_craft_skill(character, job, target_level)
    elif job.is_gathering:
        await _xp_gather_skill(character, job, target_level)
    else:
        raise ValueError(f"Job {job} is neither crafting nor gathering.")


async def _xp_craft_skill(character: Character, job: JobType, target_level):
    if not job.is_crafting:
        raise ValueError(f"Job {job} is not a crafting job.")
    raise NotImplementedError("This function is not yet implemented.")


async def _xp_gather_skill(character: Character, job: JobType, target_level):
    if not job.is_gathering:
        raise ValueError(f"Job {job} is not a gathering job.")

    while target_level == -1 or character.get_job_level(job) < target_level:
        current_level = character.get_job_level(job)
        item_target = max(
            [
                item
                for item in await Encyclopedia.get_all_items_by_job(job, current_level)
                if item.is_gatherable_resource
            ],
            key=lambda item: item.level,
        )

        need_for_level_up = character.nb_gather_needed_for_level_up(item_target)

        await gather(character, item_target, need_for_level_up)
