from enum import Enum


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

    @staticmethod
    def get_base_xp(level: int) -> int:
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
