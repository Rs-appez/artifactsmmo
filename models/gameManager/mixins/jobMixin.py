from typing import Protocol

from models.enums import JobType


class JobMixin(Protocol):
    jobs = {
        JobType.FISHING: "jane",
    }
