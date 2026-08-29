from zoneinfo import ZoneInfo
from dataclasses import dataclass
from datetime import time, timedelta

from models.dataclass import Monster
from models.enums import Day


@dataclass(frozen=True)
class Raid:
    name: str
    code: str
    boss: Monster
    days: set[Day]
    start_time: time
    duration: timedelta

    @classmethod
    async def from_dict(cls, data):
        from models import Encyclopedia

        boss = await Encyclopedia.get_monster_by_code(data["monster"])
        days = {Day(day) for day in data["schedule"]["weekdays"]}

        start_hour = data["schedule"]["start_hour_utc"]
        start_minute = data["schedule"]["start_minute_utc"]
        start_time = time(hour=start_hour, minute=start_minute, tzinfo=ZoneInfo("UTC"))

        duration_hours = data["schedule"]["duration_hours"]
        duration = timedelta(hours=duration_hours)

        return cls(
            name=data["name"],
            code=data["code"],
            boss=boss,
            days=days,
            start_time=start_time,
            duration=duration,
        )
