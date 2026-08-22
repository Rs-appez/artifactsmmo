from math import floor

from utils.simulate_fight.simulateData import FightMetadata


def compute_effects(attacker: bool, raw_dmg: int, data: FightMetadata) -> int:
    """
    Computes the effects of the attacker and the opponent
    Return the damage taken by the current attacker
    """

    dmg = 0

    attacker_effects = data.get_effects(attacker)
    oppenent_effects = data.get_effects(not attacker)

    for effect, value in attacker_effects.items():
        match effect.code:
            # healing effect
            case "reconstitution":
                if data.get_nb_turns(attacker) % value == 0:
                    data.reconstitution(attacker)
            case "healing":
                if data.get_nb_turns(attacker) % 3 == 0:
                    dmg -= floor(((value / 100) * data.get_max_hp(attacker)) + 0.5)

            case "lifesteal":
                if data.has_critical_strike(attacker):
                    dmg -= floor((value / 100) * raw_dmg + 0.5)

            # shield effect
            case "barrier":
                if data.get_turns == 1 or data.get_nb_turns(attacker) % 5 == 0:
                    data.gain_shield(attacker, value)

    for effect, value in oppenent_effects.items():
        match effect.code:
            # damage effect
            case "poison":
                if data.get_nb_turns(not attacker) > 0:
                    antipoison = sum(
                        attacker_effects[effect]
                        for effect in attacker_effects
                        if effect.code == "antipoison"
                    )
                    dmg += max(0, value - antipoison)
            case "burn":
                if data.get_nb_turns(not attacker) > 0:
                    dmg += floor(
                        (value / 100) * data.get_burn_damage(not attacker) + 0.5
                    )
                    data.reduce_burn_damage(not attacker)

            # alter stats effect
            case "corrupted":
                for element, atk_value in data.get_attacks(attacker).items():
                    res = data.get_resistances(not attacker).get(element, 0)
                    if res < 100 and atk_value > 0:
                        data.reduce_resistance(not attacker, element, value)

    return dmg
