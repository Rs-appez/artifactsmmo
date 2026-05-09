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
