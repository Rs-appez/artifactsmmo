from functools import cache
from math import floor
from random import choice, randint

from config import CRITICAL_STRIKE_MULTIPLIER
from utils.math_fight import calc_resistance

from .simulateData import SimulateData, SimulateResult


def _is_player_start(data: SimulateData) -> bool:
    if data.char_initiative > data.monster_initiative:
        return True
    elif data.char_initiative < data.monster_initiative:
        return False
    elif data.char_hp > data.monster_hp:
        return True
    elif data.char_hp < data.monster_hp:
        return False
    else:
        return choice([True, False])


def _compute_damage(attacker: str, data: SimulateData) -> int:
    damage = 0
    target = "monster" if attacker == "char" else "char"
    attacks, critical_strike = data.get_attacks(attacker)
    attacker_effects = data.get_effects(attacker)

    target_resistances = data.get_resistances(target)
    target_effects = data.get_effects(target)

    for element, attack_value in attacks:
        resistance = target_resistances.get(element, 0)
        damage += calc_resistance(attack_value, resistance)

    if randint(1, 100) <= critical_strike:
        damage *= CRITICAL_STRIKE_MULTIPLIER

    return floor(damage + 0.5)


def _fight(tenta_data: dict[str, int], data: SimulateData):

    char_turn = _is_player_start(data)
    while tenta_data["char_hp"] > 0 and tenta_data["monster_hp"] > 0:
        tenta_data["nb_turns"] += 1

        attacker = "char" if char_turn else "monster"
        dmg = _compute_damage(attacker, data)
        tenta_data["char_hp" if not char_turn else "monster_hp"] -= dmg

        char_turn = not char_turn


@cache
def _simulate(data: SimulateData, n: int = 100) -> SimulateResult:

    char_wins = 0
    total_char_hp = 0
    total_monster_hp = 0
    total_turns = 0

    for _ in range(n):
        tenta_data = {
            "nb_turns": 0,
            "char_hp": data.char_hp,
            "monster_hp": data.monster_hp,
        }

        _fight(tenta_data, data)

        if tenta_data["char_hp"] > 0:
            char_wins += 1
        total_char_hp += tenta_data["char_hp"]
        total_monster_hp += tenta_data["monster_hp"]
        total_turns += tenta_data["nb_turns"]

    return SimulateResult(
        win_rate=(char_wins / n) * 100,
        average_turns=total_turns / n,
        average_char_hp_left=total_char_hp / n,
        average_monster_hp_left=total_monster_hp / n,
    )


def simulate(data: SimulateData, n: int = 100) -> SimulateResult:
    if n <= 0:
        raise ValueError("n must be greater than 0")
    return _simulate(data, n)
