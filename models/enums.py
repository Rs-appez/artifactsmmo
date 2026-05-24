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


class EquipentType(Enum):
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
