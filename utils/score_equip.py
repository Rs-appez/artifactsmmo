from functools import cache
from typing import TYPE_CHECKING

from models.enums import Element

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
    if not weapon.is_weapon:
        raise ValueError(f"Item {weapon.name} is not a weapon")
    score = 0.0
    for effect, value in weapon.effects.items():
        element = effect.get_atk_element
        if element is not None:
            score += value * _damage_multiplier(element, monster)
        elif effect.code in WEIGHTS:
            score += value * WEIGHTS[effect.code]
    return score


@cache
def score_equipment(
    equipment: "Item", monster: "Monster", weapon_elems: set[Element]
) -> float:
    if not equipment.is_equipment:
        raise ValueError(f"Item {equipment.name} is not equipment")
    score = 0.0
    for effect, value in equipment.effects.items():
        code = effect.code

        if code in WEIGHTS:
            score += value * WEIGHTS[code]

        elif elem := effect.get_dmg_element:
            if elem in weapon_elems:
                score += (
                    value * WEIGHTS["elemental_dmg"] * _damage_multiplier(elem, monster)
                )

        elif elem := effect.get_res_element:
            score += (
                value * WEIGHTS["elemental_res"] * monster.attack.get(elem, 0) / 100
            )

    return score
