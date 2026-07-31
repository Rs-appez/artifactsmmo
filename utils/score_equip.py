from functools import cache
from typing import TYPE_CHECKING

from models.enums import Element

if TYPE_CHECKING:
    from models.dataclass import Item, Monster

TOP_K_WEAPONS = 5
WEIGHTS = {
    "dmg": 1.274033258119729,
    "elemental_dmg": 0.08583063944661747,
    "elemental_res": 0.050624965014169535,
    "hp": 0.1325939823954532,
    "critical_strike": 0.9789483154407386,
    "initiative": 0.13160696417676848,
    "prospecting": 0.03224571781920886,
    "inventory_space": 0.000001,
    "haste": 0.000001,
}
# mine
# WEIGHTS = {
#     "dmg": 2.0,
#     "elemental_dmg": 2.0,
#     "elemental_res": 1.0,
#     "hp": 0.5,
#     "critical_strike": 1.0,
#     "initiative": 0.5,
#     "prospecting": 0.01,
# }


def _damage_multiplier(element: Element, monster: "Monster") -> float:
    return max(0, 100 - monster.resistance.get(element, 0)) / 100


@cache
def _score_weapon(weapon: "Item", monster: "Monster") -> float:
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


def score_weapon(weapon: "Item", monster: "Monster") -> float:
    """Score a weapon against a monster. Higher is better."""
    return _score_weapon(weapon, monster)


@cache
def _score_equipment(
    equipment: "Item", monster: "Monster", weapon_elems: frozenset[Element]
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


def score_equipment(
    equipment: "Item", monster: "Monster", weapon_elems: frozenset[Element]
) -> float:
    """Score a piece of equipment against a monster. Higher is better."""
    return _score_equipment(equipment, monster, weapon_elems)


@cache
def __build_set(
    weapon: "Item",
    armor_by_slot: frozenset[frozenset["Item"]],
    monster: "Monster",
) -> tuple[set["Item"], float]:
    """Best armor set around one weapon. Returns (set, total_score)."""
    elems = frozenset(weapon.atk_element)
    equipment = {weapon}
    total = score_weapon(weapon, monster)

    for candidates in armor_by_slot:
        best = max(candidates, key=lambda i: score_equipment(i, monster, elems))
        equipment.add(best)
        total += score_equipment(best, monster, elems)

    return equipment, total


def _build_set(
    weapon: "Item",
    armor_by_slot: frozenset[frozenset["Item"]],
    monster: "Monster",
) -> tuple[set["Item"], float]:
    """Best armor set around one weapon. Returns (set, total_score)."""
    return __build_set(weapon, armor_by_slot, monster)


@cache
def _best_equips_for_monster(
    monster: "Monster", items: frozenset["Item"], top_k: int
) -> set["Item"]:
    weapons = [i for i in items if i.is_weapon]
    if not weapons:
        return set()
    weapons.sort(key=lambda w: score_weapon(w, monster), reverse=True)

    armor_by_slot: dict[str, list[Item]] = {}
    for item in items:
        if item.is_equipment:
            armor_by_slot.setdefault(item.type, []).append(item)

    armor_by_slot_set = frozenset(frozenset(v) for v in armor_by_slot.values())

    # try top K weapons, keep the best full combo
    best_set: set["Item"] = set()
    best_total = float("-inf")
    for weapon in weapons[:top_k]:
        equipment, total = _build_set(weapon, armor_by_slot_set, monster)
        if total > best_total:
            best_set, best_total = equipment, total

    return best_set


def best_equips_for_monster(
    monster: "Monster",
    items: frozenset["Item"],
    top_k: int = TOP_K_WEAPONS,
) -> set["Item"]:
    """Best equipment set for a character against a monster. Returns a dict of slot -> item."""
    return _best_equips_for_monster(monster, items, top_k)
