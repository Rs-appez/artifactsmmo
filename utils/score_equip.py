from functools import cache
from typing import TYPE_CHECKING

from models.enums import Element

if TYPE_CHECKING:
    from models.dataclass import Item, Monster

TOP_K_WEAPONS = 5
# WEIGHTS = {
#     "dmg": 1.274033258119729,
#     "elemental_dmg": 1.274033258119729,
#     "elemental_res": 0.050624965014169535,
#     "hp": 0.1325939823954532,
#     "critical_strike": 0.9789483154407386,
#     "initiative": 0.13160696417676848,
#     "prospecting": 0.03224571781920886,
#     "inventory_space": 0.000001,
#     "haste": 0.000001,
# }
# mine
WEIGHTS = {
    "dmg": 1.25,
    "elemental_dmg": 1.25,
    "elemental_res": 3.00,
    "hp": 0.10,
    "critical_strike": 0.75,
    "initiative": 0.02,
    "haste": 0.35,
    "wisdom": 0.00001,
    "prospecting": 0.0001,
    "inventory_space": 0.0000001,
}

SLOT_RULES: dict[str, tuple[int, bool]] = {  # slot: (qty, duplicates_allowed)
    "ring": (2, True),
    "artifact": (3, False),
}
DEFAULT_RULE = (1, False)


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

        if code == "dmg":
            total_effectiveness = sum(
                _damage_multiplier(elem, monster) for elem in weapon_elems
            )
            score += value * WEIGHTS["dmg"] * total_effectiveness

        elif elem := effect.get_dmg_element:
            if elem in weapon_elems:
                score += (
                    value * WEIGHTS["elemental_dmg"] * _damage_multiplier(elem, monster)
                )

        elif elem := effect.get_res_element:
            score += (
                value * WEIGHTS["elemental_res"] * monster.attack.get(elem, 0) / 100
            )

        elif code in WEIGHTS:
            score += value * WEIGHTS[code]

    return score


def score_equipment(
    equipment: "Item", monster: "Monster", weapon_elems: frozenset[Element]
) -> float:
    """Score a piece of equipment against a monster. Higher is better."""
    return _score_equipment(equipment, monster, weapon_elems)


def _best_picks(
    candidates: frozenset[tuple["Item", int]],
    monster: "Monster",
    weapon_elems: frozenset[Element],
    count: int,
    allow_duplicates: bool,
) -> list["Item"]:
    """Top `count` picks from a slot, honouring quantities and uniqueness."""
    ranked = sorted(
        candidates,
        key=lambda c: score_equipment(c[0], monster, weapon_elems),
        reverse=True,
    )
    picks: list["Item"] = []
    for item, qty in ranked:
        remaining = count - len(picks)
        if remaining <= 0:
            break
        take = min(qty, remaining) if allow_duplicates else 1
        picks.extend([item] * take)
    return picks


@cache
def __build_set(
    weapon: "Item",
    armor_by_slot: frozenset[frozenset[tuple["Item", int]]],
    monster: "Monster",
) -> tuple[dict["Item", int], float]:
    """Best armor set around one weapon. Returns ({item: qty}, total_score)."""
    elems = frozenset(weapon.atk_element)
    equipment: dict["Item", int] = {weapon: 1}
    total = score_weapon(weapon, monster)

    for candidates in armor_by_slot:
        slot = next(iter(candidates))[0].type
        count, allow_dup = SLOT_RULES.get(slot, DEFAULT_RULE)
        for item in _best_picks(candidates, monster, elems, count, allow_dup):
            equipment[item] = equipment.get(item, 0) + 1
            total += score_equipment(item, monster, elems)

    return equipment, total


def _build_set(
    weapon: "Item",
    armor_by_slot: frozenset[frozenset[tuple["Item", int]]],
    monster: "Monster",
) -> tuple[dict["Item", int], float]:
    """Best armor set around one weapon. Returns (set, total_score)."""
    return __build_set(weapon, armor_by_slot, monster)


@cache
def _best_equips_for_monster(
    monster: "Monster", items: frozenset[tuple["Item", int]], top_k: int
) -> dict["Item", int]:
    weapons = [i[0] for i in items if i[0].is_weapon]
    if not weapons:
        return {}
    weapons.sort(key=lambda w: score_weapon(w, monster), reverse=True)

    armor_by_slot: dict[str, list[tuple["Item", int]]] = {}
    for item, qty in items:
        if (
            item.is_equipment
            and not item.is_weapon
            and not item.is_tool
            and not item.is_rune
        ):
            armor_by_slot.setdefault(item.type, []).append((item, qty))

    armor_by_slot_set = frozenset(frozenset(v) for v in armor_by_slot.values())

    # try top K weapons, keep the best full combo
    best_set: dict["Item", int] = {}
    best_total = float("-inf")
    for weapon in weapons[:top_k]:
        equipment, total = _build_set(weapon, armor_by_slot_set, monster)
        if total > best_total:
            best_set, best_total = equipment, total

    return best_set


def best_equips_for_monster(
    monster: "Monster",
    items: frozenset[tuple["Item", int]],
    top_k: int = TOP_K_WEAPONS,
) -> dict["Item", int]:
    """Best equipment set for a character against a monster. Returns a dict of slot -> item."""
    return _best_equips_for_monster(monster, items, top_k)
