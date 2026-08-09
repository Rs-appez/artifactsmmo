from functools import cache
from math import floor
from random import choice, randint

from config import CRITICAL_STRIKE_MULTIPLIER
from utils.math_fight import calc_resistance

from .computeEffect import compute_hp_effects
from .simulateData import SimulateData, SimulateResult


def _is_player_start(data: SimulateData) -> bool:
    char_initiative = data.get_initiative(True)
    char_hp = data.get_hp(True)

    monster_hp = data.get_hp(False)
    monster_initiative = data.get_initiative(False)

    if char_initiative > monster_initiative:
        return True
    elif char_initiative < monster_initiative:
        return False
    elif char_hp > monster_hp:
        return True
    elif char_hp < monster_hp:
        return False
    else:
        return choice([True, False])


def _compute_damage(char_turn: bool, data: SimulateData) -> int:
    damage = 0
    attacks, critical_strike = data.get_attacks(char_turn)
    target_resistances = data.get_resistances(not char_turn)

    for element, attack_value in attacks.items():
        resistance = target_resistances.get(element, 0)
        damage += calc_resistance(attack_value, resistance)

    if randint(1, 100) <= critical_strike:
        damage *= CRITICAL_STRIKE_MULTIPLIER

    return floor(damage + 0.5)


def _fight(data: SimulateData):

    char_turn = _is_player_start(data)
    while data.get_hp(True) > 0 and data.get_hp(False) > 0:
        data.increment_turns(char_turn)

        self_effect_dmg = compute_hp_effects(char_turn, data)
        dmg = _compute_damage(char_turn, data)

        data.take_damage(not char_turn, dmg)
        data.take_damage(char_turn, self_effect_dmg)

        char_turn = not char_turn


@cache
def _simulate(data: SimulateData, n: int = 100) -> SimulateResult:

    char_wins = 0
    total_char_hp = 0
    total_monster_hp = 0
    total_turns = 0

    for _ in range(n):
        data.reset_metadata()

        _fight(data)

        if data.get_hp(True) > 0:
            char_wins += 1
        total_char_hp += data.get_hp(True)
        total_monster_hp += data.get_hp(False)
        total_turns += data.get_turns

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
