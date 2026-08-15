from enum import StrEnum, auto


class ZoneType(StrEnum):
    DEFAULT = auto()
    SANDWHISPER = auto()
    ENCHANTED_FOREST = auto()

    @classmethod
    def from_map_name(cls, map_name: str) -> "ZoneType":
        if "Sandwhisper" in map_name:
            return cls.SANDWHISPER
        elif "Enchanted Forest" in map_name:
            return cls.ENCHANTED_FOREST
        else:
            return cls.DEFAULT
