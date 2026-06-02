from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from models.dataclass import Item
from models.enums import JobType

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class JobMixin(Protocol):
    _jobs: dict[JobType, int] = field(default_factory=dict)

    def get_job_level(self: "Character", job_name: str | JobType) -> int:
        job = JobType(job_name) if isinstance(job_name, str) else job_name
        return self._jobs.get(job, 0)

    def has_job(self: "Character", job_name: str | JobType, level=1) -> bool:
        job = JobType(job_name) if isinstance(job_name, str) else job_name
        return self._jobs.get(job, 0) >= level

    def will_gain_xp_with(self: "Character", item: Item) -> bool:
        job_level = self.get_job_level(item.job)
        if job_level == 50:
            return False
        item_level = item.craft_level or item.level
        if job_level > item_level + 10:
            return False
        return True
