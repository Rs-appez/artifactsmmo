from math import floor

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import Character
    from models.dataclass import Monster


def calc_attack(atk: int, dmg: int) -> int:
    return floor(atk * (1 + dmg / 100) + 0.5)


def calc_resistance(atk: int, res: int) -> int:
    return floor(atk * (1 - res / 100) + 0.5)


def damage_on(attacker: "Character | Monster", target: "Character | Monster") -> int:
    damage = 0
    for element, attack_value in attacker.attack.items():
        resistance = target.resistance.get(element, 0)
        damage += calc_resistance(attack_value, resistance)
    return damage
