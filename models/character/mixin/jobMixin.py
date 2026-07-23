from dataclasses import dataclass, field
from math import ceil, floor
from typing import TYPE_CHECKING

from models.dataclass import Item
from models.enums import JobType

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class JobMixin:
    _jobs: dict[JobType, dict[str, int]] = field(default_factory=dict)

    def get_job_level(self: "Character", job_name: str | JobType) -> int:
        job = JobType(job_name) if isinstance(job_name, str) else job_name
        return self._jobs.get(job, {}).get("level", 0)

    def get_job_xp(self: "Character", job_name: str | JobType) -> int:
        job = JobType(job_name) if isinstance(job_name, str) else job_name
        return self._jobs.get(job, {}).get("xp", 0)

    def get_job_next_level_xp(self: "Character", job_name: str | JobType) -> int:
        job = JobType(job_name) if isinstance(job_name, str) else job_name
        return self._jobs.get(job, {}).get("next_level_xp", 0)

    def has_job(self: "Character", job_name: str | JobType, level=1) -> bool:
        return self.get_job_level(job_name) >= level

    def can_genenerate(self: "Character", item: Item) -> bool:
        job_level = self.get_job_level(item.job)
        item_level = item.craft_level or item.level
        return job_level >= item_level

    def will_gain_xp_with(self: "Character", item: Item) -> bool:
        job_level = self.get_job_level(item.job)
        if job_level == 50:
            return False
        item_level = item.craft_level or item.level
        if job_level > item_level + 10:
            return False
        return True

    def nb_xp_per_gather(self: "Character", item: Item) -> int:
        if not self.will_gain_xp_with(item):
            return 0

        job_level = self.get_job_level(item.job)
        item_level = item.craft_level or item.level

        return floor(
            (item.job.get_base_xp(item_level) + (item_level / job_level) * 8)
            * JobType.get_wisdom_bonus(self.wisdom)
            + 0.5
        )

    def nb_gather_needed_for_level_up(self: "Character", item: Item) -> int:

        current_xp = self.get_job_xp(item.job)
        target_xp = self.get_job_next_level_xp(item.job)

        xp_per_gather = self.nb_xp_per_gather(item)

        if xp_per_gather == 0:
            return 0

        return ceil((target_xp - current_xp) / xp_per_gather)
