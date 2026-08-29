from enum import Enum


class Layer(Enum):
    INTERIOR = "interior"
    OVERWORLD = "overworld"
    UNDERGROUND = "underground"


class TaskType(Enum):
    ITEM = "items"
    MONSTER = "monsters"


class Element(Enum):
    EARTH = "earth"
    FIRE = "fire"
    WATER = "water"
    AIR = "air"


class EquipentType(Enum):
    WEAPON = "weapon"
    HELMET = "helmet"
    SHIELD = "shield"
    BODY_ARMOR = "body_armor"
    AMULET = "amulet"
    LEG_ARMOR = "leg_armor"
    BOOTS = "boots"
    RING = "ring"
    BAG = "bag"
    RUNE = "rune"
    ARTIFACT = "artifact"


class NPCType(Enum):
    TRADER = "trader"
    MERCHANT = "merchant"


class Day(Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
