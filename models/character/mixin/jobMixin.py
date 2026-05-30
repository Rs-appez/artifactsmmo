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
        if self.get_job_level(item.job) >= item.craft_level + 11:
            return False
        return True
