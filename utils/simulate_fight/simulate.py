from functools import cache
from math import floor
from random import choice, randint

from config import CRITICAL_STRIKE_MULTIPLIER
from utils.math_fight import calc_resistance

from .computeEffect import compute_effects
from .simulateData import FightMetadata, SimulateData, SimulateResult


def _is_player_start(data: FightMetadata) -> bool:
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


def _compute_damage(char_turn: bool, data: FightMetadata) -> int:
    damage = 0
    attacks = data.get_attacks(char_turn)
    target_resistances = data.get_resistances(not char_turn)

    for element, attack_value in attacks.items():
        if attack_value <= 0:
            continue
        resistance = target_resistances.get(element, 0)
        damage += calc_resistance(attack_value, resistance)

    if data.has_critical_strike(char_turn):
        damage *= CRITICAL_STRIKE_MULTIPLIER

    return floor(damage + 0.5)


def _fight(data: FightMetadata):

    char_turn = _is_player_start(data)
    while data.get_hp(True) > 0 and data.get_hp(False) > 0 and data.get_turns < 100:
        data.increment_turns(char_turn)

        has_crit = randint(1, 100) <= data.get_critical_strike(char_turn)
        data.set_critical_strike(char_turn, has_crit)

        dmg = _compute_damage(char_turn, data)
        self_effect_dmg = compute_effects(char_turn, dmg, data)

        data.take_damage(not char_turn, dmg)
        data.take_damage(char_turn, self_effect_dmg)

        char_turn = not char_turn


@cache
def _simulate(data: SimulateData, n: int) -> SimulateResult:

    char_wins = 0
    total_char_hp = 0
    total_monster_hp = 0
    total_turns = 0

    for _ in range(n):
        with data.generate_metadata() as metadata:
            _fight(metadata)

            if metadata.get_hp(False) <= 0:
                char_wins += 1
            total_char_hp += metadata.get_hp(True)
            total_monster_hp += metadata.get_hp(False)
            total_turns += metadata.get_turns

    return SimulateResult(
        win_rate=(char_wins / n) * 100,
        average_turns=total_turns / n,
        average_char_hp_left=total_char_hp / n,
        average_monster_hp_left=total_monster_hp / n,
    )


def simulate(data: SimulateData, n: int = 1000) -> SimulateResult:
    if n <= 0:
        raise ValueError("n must be greater than 0")
    return _simulate(data, n)
