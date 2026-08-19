from enum import StrEnum, auto

SUB_ZONE_MAP = {
    "Sandwhisper": ["Empress House", "Sandwhisper Isle"],
    "Enchanted Forest": ["Enchanted Forest"],
}


class ZoneType(StrEnum):
    DEFAULT = auto()
    SANDWHISPER = auto()
    ENCHANTED_FOREST = auto()

    @classmethod
    def from_map_name(cls, map_name: str) -> "ZoneType":
        if map_name in SUB_ZONE_MAP["Sandwhisper"]:
            return cls.SANDWHISPER
        elif map_name in SUB_ZONE_MAP["Enchanted Forest"]:
            return cls.ENCHANTED_FOREST
        else:
            return cls.DEFAULT
