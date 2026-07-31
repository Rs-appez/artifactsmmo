import asyncio
import statistics

import optuna

from exceptions import ImpossibleCombatException
from models import Character, Encyclopedia
from models.enums import Element
from utils import score_equip

# Best weights: {'dmg': 1.0389225499769783, 'elemental_dmg': 0.007953581501006923, 'elemental_res': 0.0704281291853448, 'hp': 0.3534455259932312, 'critical_strike': 0.23801522900159033, 'haste': 0.11147023021313206, 'initiative': 0.06472881701997382, 'prospecting': 0.7186397562799901, 'inventory_space': 2.682934916352533}
# Best weights: {'dmg': 0.013145991851320643, 'elemental_dmg': 0.07132672768858948, 'elemental_res': 0.44779281473733545, 'hp': 2.036347896825664, 'critical_strike': 0.588703593415659, 'haste': 0.7477130824961893, 'initiative': 1.2082293383908649, 'prospecting': 6.939245591441435, 'inventory_space': 0.003987960404127009}
# Best weights: {'dmg': 0.2381954899102118, 'elemental_dmg': 0.015935630031624334, 'elemental_res': 0.01372708611143425, 'hp': 0.027368731952388432, 'critical_strike': 0.1784077023432074, 'haste': 0.015664450486591562, 'initiative': 0.005153505811121585, 'prospecting': 0.012578877688669514, 'inventory_space': 0.021378389306156605}
# Best weights: {'dmg': 0.8491895926588633, 'elemental_dmg': 0.028292055006966986, 'elemental_res': 0.048053675304441684, 'hp': 0.07873570675826837, 'critical_strike': 0.10490798628389231, 'haste': 1.235351877944175, 'initiative': 0.05491382993376367, 'prospecting': 0.08025219727648436}

# ---------------------------------------------------------------
# Your game-specific pieces — fill these in
# ---------------------------------------------------------------
ITEMS = set()
TRAIN_MONSTERS = set()
HOLDOUT_MONSTERS = set()

TRAIN_MONSTERS_NAMES = [
    "pig",
    "goblin",
    "skeleton",
    "vampire",
    "death_knight",
    "desert_scorpion",
]

HOLDOUT_MONSTERS_NAMES = ["orc", "red_slime", "sheep", "wolf", "sand_snake", "chicken"]


def simulate_battles(monster, build, n_battles=100):
    """Your existing simulator. Returns (win_rate, avg_turns) for
    this build against this monster. Use fixed seeds per monster."""
    chara = Character(
        _name="dummy",
        _surname="dummy",
        _cooldown=None,  # ty:ignore[invalid-argument-type]
        _xp=0,
        _max_xp=0,
        _level=50,
        _wisdom=0,
        _prospecting=0,
    )
    stats = {
        "hp": 0,
        "initiative": 0,
        "critical_strike": 0,
        "dmg": 0,
        "prospecting": 0,
        "inventory_space": 0,
    }
    for elem in Element:
        stats[f"dmg_{elem.value}"] = 0
        stats[f"res_{elem.value}"] = 0

    for item in build:
        for effect, value in item.effects.items():
            stats[effect.code] = stats.get(effect.code, 0) + value

    chara._hp = stats["hp"] + 365
    chara._max_hp = chara._hp
    chara._initiative = stats["initiative"]
    chara._critical_strike = stats["critical_strike"]
    chara._prospecting = stats["prospecting"]
    chara._inventory_max_items = stats["inventory_space"] + 100
    for elem in Element:
        chara._attack[elem] = (
            stats[f"dmg_{elem.value}"]
            + stats["dmg"]
            + stats.get(f"attack_{elem.value}", 0)
        )
        chara._resistance[elem] = stats[f"res_{elem.value}"]

    nb_wins = 0
    total_turns = 0

    for _ in range(n_battles):
        try:
            win = chara.will_win_against(monster)
            if win:
                nb_wins += 1
        except ImpossibleCombatException:
            pass
        finally:
            total_turns += chara._compute_nb_turns_to_kill(monster)

    return nb_wins / n_battles, total_turns / nb_wins if nb_wins > 0 else 1000


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
ALL_KEYS = list(score_equip.WEIGHTS.keys())  # the 9 tunable weights [1]


def apply_weights(weights: dict) -> None:
    score_equip.WEIGHTS.update(weights)


def clear_caches() -> None:
    # These four functions are @cache'd but read the global WEIGHTS,
    # so stale scores must be flushed after every weight change [1]
    score_equip._score_weapon.cache_clear()
    score_equip._score_equipment.cache_clear()
    score_equip.__build_set.cache_clear()
    score_equip._best_equips_for_monster.cache_clear()


def sum_stat(build, code: str) -> float:
    # effects is a dict of effect -> value, with effect.code [1]
    return sum(v for item in build for e, v in item.effects.items() if e.code == code)


# ---------------------------------------------------------------
# evaluate: "how good are the weights currently installed?"
# ---------------------------------------------------------------
def evaluate(monsters) -> tuple[float, dict]:
    win_rates, turns, prosp, inv = [], [], [], []
    details = {}

    for m in monsters:
        # builds the best set; top_k defaults to TOP_K_WEAPONS = 5 [1]
        build = score_equip.best_equips_for_monster(
            m, frozenset(item for item in ITEMS if item.level <= m.level + 5)
        )
        wr, avg_turns = simulate_battles(m, build)

        win_rates.append(wr)
        turns.append(avg_turns)
        prosp.append(sum_stat(build, "prospecting"))
        inv.append(sum_stat(build, "inventory_space"))
        details[getattr(m, "name", str(m))] = {
            "win_rate": wr,
            "turns": avg_turns,
            "prospecting": prosp[-1],
            "inventory_space": inv[-1],
        }

    # Priority ladder: win rate >> turns >> prospecting >> inventory space.
    # Turns are rounded so near-ties let prospecting break them.
    fitness = (
        min(win_rates) * 1_000_000  # worst monster must be 100%
        - round(statistics.mean(turns)) * 1_000
        + min(prosp) * 1
        + min(inv) * 0.01
    )
    return fitness, details


# ---------------------------------------------------------------
# objective: the only function Optuna talks to
# ---------------------------------------------------------------
def objective(trial: optuna.Trial) -> float:
    weights = {k: trial.suggest_float(k, 1e-3, 10.0, log=True) for k in ALL_KEYS}
    apply_weights(weights)
    clear_caches()

    fitness, details = evaluate(TRAIN_MONSTERS)
    trial.set_user_attr(
        "details", details
    )  # per-monster breakdown for later inspection
    return fitness


async def main():
    await Encyclopedia.initialize()
    ITEMS.update(
        item
        for item in Encyclopedia._items.values()
        if item.is_equipment or item.is_weapon
    )
    for m_name in TRAIN_MONSTERS_NAMES:
        TRAIN_MONSTERS.add(await Encyclopedia.get_monster_by_code(m_name))

    for m_name in HOLDOUT_MONSTERS_NAMES:
        HOLDOUT_MONSTERS.add(await Encyclopedia.get_monster_by_code(m_name))

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.CmaEsSampler(),
    )
    study.enqueue_trial(
        dict(score_equip.WEIGHTS)
    )  # seed with your hand-tuned weights [1]
    study.optimize(objective, n_trials=1000, show_progress_bar=True)

    print("Best weights:", study.best_params)
    print("Train breakdown:", study.best_trial.user_attrs["details"])

    # Final honest check on monsters the optimizer never saw
    apply_weights(study.best_params)
    clear_caches()
    holdout_fitness, holdout_details = evaluate(HOLDOUT_MONSTERS)
    print("Holdout breakdown:", holdout_details)


# ---------------------------------------------------------------
# Run the search
# ---------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
