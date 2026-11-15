import asyncio
from datetime import date, datetime
from typing import ClassVar

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models.dataclass import Item, Monster, Offering, Resource
from models.enums import JobType


class Altar:
    _jobs: ClassVar[set[JobType]] = set()
    _xp_reward_percent: ClassVar[float]
    _date: ClassVar[date]
    _expiration_date: ClassVar[datetime]
    _offerings: ClassVar[set[Offering]] = set()

    _is_syncing = asyncio.Event()
    _sync_task: ClassVar[asyncio.Task | None] = None

    @property
    async def jobs(self) -> set[JobType]:
        await self._is_syncing.wait()
        return self._jobs

    @classmethod
    async def has_job(cls, job: JobType) -> bool:
        await cls._is_syncing.wait()
        return job in cls._jobs

    @classmethod
    async def get_offering(cls, target: Resource | Monster | Item) -> Offering | None:
        await cls._is_syncing.wait()
        return next(
            (offering for offering in cls._offerings if offering.target == target), None
        )

    @classmethod
    def sync_altar(cls) -> None:
        """Starts the background task that keeps the altar data up to date."""
        if cls._sync_task is None or cls._sync_task.done():
            cls._sync_task = asyncio.create_task(cls._sync_altar())

    @classmethod
    async def _sync_altar(cls) -> None:
        retry_delay = 5
        while True:
            try:
                await cls._load_altar()
            except Exception as e:
                print(f"Altar sync failed: {e}, retrying in {retry_delay}s")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)
                continue

            retry_delay = 5
            now = datetime.now(cls._expiration_date.tzinfo)
            delay = (cls._expiration_date - now).total_seconds()
            await asyncio.sleep(max(delay, 0) + 0.2)

    @classmethod
    async def _load_altar(cls) -> None:
        cls._is_syncing.clear()
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
            cls._expiration_date = datetime.fromisoformat(data.get("expires_at"))
            cls._offerings = {
                await Offering.from_dict(offering)
                for offering in data.get("offerings", [])
            }
        cls._is_syncing.set()
