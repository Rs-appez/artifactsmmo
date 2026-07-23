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

    @property
    def max_level(self) -> int:
        return 50

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

    def get_base_xp(self, level: int) -> int:
        if self.is_crafting:
            return self._get_crafting_base_xp(level)
        elif self.is_gathering:
            return self._get_gathering_base_xp(level)
        else:
            raise ValueError(f"JobType {self.value} does not have a base XP defined.")

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

    def get_xp_coefficient(self, level: int) -> int:
        if self.is_gathering:
            return 8
        elif not self.is_crafting:
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
