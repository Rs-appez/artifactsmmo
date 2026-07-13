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
