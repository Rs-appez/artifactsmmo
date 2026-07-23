from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from models.dataclass import Item
from models.enums import JobType
from utils.xp_craft_calculator import nb_action_needed_for_level_up, nb_xp_per_action

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

    def has_job(self: "Character", job_name: str | JobType, level=1) -> bool:
        return self.get_job_level(job_name) >= level

    def can_genenerate(self: "Character", item: Item) -> bool:
        job_level = self.get_job_level(item.job)
        item_level = item.craft_level or item.level
        return job_level >= item_level

    def will_gain_xp_with(self: "Character", item: Item) -> bool:
        return nb_xp_per_action(self.get_job_level(item.job), self.wisdom, item) > 0

    def nb_action_needed_for_level_up(self: "Character", item: Item) -> int:

        return nb_action_needed_for_level_up(
            self.get_job_level(item.job),
            self.get_job_xp(item.job),
            JobType.get_next_level_xp(self.get_job_level(item.job)),
            self.wisdom,
            item,
        )[0]
