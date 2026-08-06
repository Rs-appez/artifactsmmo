from functools import cache
from typing import TYPE_CHECKING

from config import CRITICAL_STRIKE_MULTIPLIER
from models.enums import Element

if TYPE_CHECKING:
    from models.dataclass import Item, Monster

TOP_K_WEAPONS = 5
WEIGHTS = {
    "dmg": 1.25,
    "elemental_dmg": 1.25,
    "elemental_res": 3.00,
    "hp": 0.01,
    "critical_strike": 0.05,
    "initiative": 0.02,
    "haste": 0.50,
    "wisdom": 0.001,
    "prospecting": 0.01,
    "inventory_space": 0.0000001,
}

SLOT_RULES: dict[str, tuple[int, bool]] = {  # slot: (qty, duplicates_allowed)
    "ring": (2, True),
    "artifact": (3, False),
}
DEFAULT_RULE = (1, False)


def _damage_multiplier(element: Element, monster: "Monster") -> float:
    return max(0, 100 - monster.resistance.get(element, 0)) / 100


def _weapon_attacks(weapon: "Item") -> frozenset[tuple[Element, float]]:
    """(element, base attack) pairs dealt by the weapon each turn."""
    return frozenset(
        (elem, value)
        for effect, value in weapon.effects.items()
        if (elem := effect.get_atk_element) is not None
    )


@cache
def _score_weapon(weapon: "Item", monster: "Monster") -> float:
    if not weapon.is_weapon:
        raise ValueError(f"Item {weapon.name} is not a weapon")
    score = 0.0
    dmg = 0
    critical_strike = 0
    for effect, value in weapon.effects.items():
        element = effect.get_atk_element
        if element is not None:
            dmg += value * _damage_multiplier(element, monster)
        elif effect.code == "critical_strike":
            critical_strike += value
        elif effect.code in WEIGHTS:
            score += value * WEIGHTS[effect.code]
    return score + (dmg * CRITICAL_STRIKE_MULTIPLIER * critical_strike / 100)


def score_weapon(weapon: "Item", monster: "Monster") -> float:
    """Score a weapon against a monster. Higher is better."""
    return _score_weapon(weapon, monster)


@cache
def _score_equipment(
    equipment: "Item",
    monster: "Monster",
    weapon_attacks: frozenset[tuple[Element, float]],  # was weapon_elems
) -> float:
    if not equipment.is_equipment:
        raise ValueError(f"Item {equipment.name} is not equipment")
    score = 0.0
    base = {e: atk * _damage_multiplier(e, monster) for e, atk in weapon_attacks}
    total_base = sum(base.values())

    for effect, value in equipment.effects.items():
        code = effect.code
        if code == "dmg":
            score += total_base * value / 100
        elif (elem := effect.get_dmg_element) is not None:
            score += base.get(elem, 0.0) * value / 100
        elif code == "critical_strike":
            score += total_base * CRITICAL_STRIKE_MULTIPLIER * value / 100
        elif (elem := effect.get_res_element) is not None:
            score += (
                value * WEIGHTS["elemental_res"] * monster.attack.get(elem, 0) / 100
            )
        elif code in WEIGHTS:
            score += value * WEIGHTS[code]
    return score


def score_equipment(
    equipment: "Item",
    monster: "Monster",
    weapon_elems: frozenset[tuple[Element, float]],
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
    elems = _weapon_attacks(weapon)
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
        print(f" {monster.name} - {weapon.name} combo score: {total:.2f}")
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
