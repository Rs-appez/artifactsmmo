from functools import cache
from typing import TYPE_CHECKING

from models.enums import Element
from utils.elements import parse_element

if TYPE_CHECKING:
    from models.dataclass import Item, Monster

TOP_K_WEAPONS = 5

WEIGHTS = {
    "dmg": 2.0,
    "elemental_dmg": 2.0,
    "elemental_res": 1.0,
    "hp": 0.1,
    "critical_strike": 1.0,
    "haste": 1.0,
    "initiative": 0.2,
    "prospecting": 0.05,
}


def _damage_multiplier(element: Element, monster: "Monster") -> float:
    return max(0, 100 - monster.resistance.get(element, 0)) / 100


@cache
def score_weapon(weapon: "Item", monster: "Monster") -> float:
    score = 0.0
    for effect, value in weapon.effects.items():
        code = effect.code
        element = parse_element(code, "attack_")
        if element is not None:
            score += value * _damage_multiplier(element, monster)
        elif code in WEIGHTS:
            score += value * WEIGHTS[code]
    return score
