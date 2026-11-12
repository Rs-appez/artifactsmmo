from datetime import date, datetime
from typing import ClassVar

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models.dataclass import Offering
from models.enums import JobType


class Altar:
    _jobs: ClassVar[set[JobType]] = set()
    _xp_reward_percent: ClassVar[float]
    _date: ClassVar[date]
    _expiration_date: ClassVar[datetime]
    _offerings: ClassVar[set[Offering]] = set()

    @property
    def jobs(self) -> set[JobType]:
        return self._jobs

    @classmethod
    def has_job(cls, job: JobType) -> bool:
        return job in cls._jobs

    @classmethod
    async def load_altar(cls) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ARTIFACTSMMO_URL}/seasonal_offerings", headers=HEADERS, timeout=30
            )
            data = response.json()
            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            data = data.get("data", {})
            cls._jobs = {JobType(job) for job in data.get("skills", [])}
            cls._xp_reward_percent = data.get("xp_reward_percent")
            cls._date = date.fromisoformat(data.get("date"))
            cls._expiration_date = datetime.fromisoformat(data.get("expiration_date"))
            cls._offerings = {
                await Offering.from_dict(offering)
                for offering in data.get("offerings", [])
            }
