from enum import Enum
from typing import TYPE_CHECKING

from config import MAX_LEVEL_JOB

if TYPE_CHECKING:
    from models.dataclass import Item

_XP_RANGES = [
    (1, 150, 100),
    (4, 450, 250),
    (9, 1700, 400),
    (14, 3700, 700),
    (19, 7200, 1000),
    (24, 12200, 1200),
    (29, 18200, 1500),
    (34, 25700, 1800),
    (40, 36500, 2100),
    (45, 47000, 1800),
]


class JobType(Enum):
    NO_JOB = "no_job"
    FIGHTING = ""
    MINING = "mining"
    WOODCUTTING = "woodcutting"
    FISHING = "fishing"
    WEAPONCRAFTING = "weaponcrafting"
    GEARCRAFTING = "gearcrafting"
    JEWELRYCRAFTING = "jewelrycrafting"
    COOKING = "cooking"
    ALCHEMY = "alchemy"

    @property
    def is_crafting(self) -> bool:
        return self in {
            JobType.WEAPONCRAFTING,
            JobType.GEARCRAFTING,
            JobType.JEWELRYCRAFTING,
            JobType.COOKING,
        }

    @property
    def is_gathering(self) -> bool:
        return self in {
            JobType.MINING,
            JobType.WOODCUTTING,
            JobType.FISHING,
            JobType.ALCHEMY,
        }

    @property
    def has_drop(self) -> bool:
        return self in {
            JobType.MINING,
            JobType.WOODCUTTING,
            JobType.FISHING,
        }

    @property
    def max_level(self) -> int:
        return MAX_LEVEL_JOB

    @property
    def job_xp_multiplier(self) -> float:
        if self in {JobType.MINING, JobType.WOODCUTTING, JobType.FISHING}:
            return 0.1
        elif self in {
            JobType.WEAPONCRAFTING,
            JobType.GEARCRAFTING,
            JobType.JEWELRYCRAFTING,
            JobType.ALCHEMY,
        }:
            return 1
        elif self == JobType.COOKING:
            return 0.5
        else:
            return 1

    @staticmethod
    def character_job_types() -> list["JobType"]:
        return [
            JobType.MINING,
            JobType.WOODCUTTING,
            JobType.FISHING,
            JobType.WEAPONCRAFTING,
            JobType.GEARCRAFTING,
            JobType.JEWELRYCRAFTING,
            JobType.COOKING,
            JobType.ALCHEMY,
        ]

    def get_base_xp(self, item: Item) -> int:
        level = item.craft_level or item.level
        if item.is_craftable:
            return self._get_crafting_base_xp(level)
        elif item.is_gatherable_resource:
            return self._get_gathering_base_xp(level)
        else:
            raise ValueError(f"Item {item.name} is neither craftable nor gatherable.")

    def _get_gathering_base_xp(self, level: int) -> int:
        if level < 1:
            raise ValueError("Level must be greater than or equal to 1.")
        if level < 10:
            return 5
        elif level < 20:
            return 10
        elif level < 30:
            return 13
        elif level < 35:
            return 16
        elif level < 40:
            return 20
        elif level < 45:
            return 28
        elif level < 50:
            return 36
        else:
            return 0

    def _get_crafting_base_xp(self, level: int) -> int:
        if level < 1:
            raise ValueError("Level must be greater than or equal to 1.")
        if level < 5:
            return 50
        elif level < 10:
            return 100
        elif level < 15:
            return 200
        elif level < 20:
            return 325
        elif level < 25:
            return 450
        elif level < 30:
            return 550
        elif level < 35:
            return 650
        elif level < 40:
            return 750
        elif level < 45:
            return 850
        elif level < 50:
            return 1000
        else:
            return 0

    def get_xp_coefficient(self, item: Item) -> int:
        level = item.craft_level or item.level
        if item.is_gatherable_resource:
            return 8
        elif not item.is_craftable:
            raise ValueError(
                f"JobType {self.value} does not have an XP coefficient defined."
            )

        if level < 1:
            raise ValueError("Level must be greater than or equal to 1.")

        if level < 5:
            return 25
        elif level < 10:
            return 30
        elif level < 15:
            return 35
        elif level < 20:
            return 40
        elif level < 25:
            return 45
        elif level < 30:
            return 50
        elif level < 35:
            return 55
        elif level < 40:
            return 60
        elif level < 45:
            return 65
        elif level < 50:
            return 70
        else:
            return 0

    @staticmethod
    def get_wisdom_bonus(wisdom: int) -> float:
        return 1 + (wisdom / 1000)

    @staticmethod
    def get_next_level_xp(level: int) -> int:
        if level < 1:
            raise ValueError("Level must be greater than or equal to 1.")

        if level >= MAX_LEVEL_JOB:
            return 0

        l_start, xp_base, delta = max(r for r in _XP_RANGES if r[0] <= level)
        return xp_base + delta * (level - l_start)
