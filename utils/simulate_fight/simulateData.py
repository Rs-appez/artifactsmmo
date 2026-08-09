from functools import cache
from dataclasses import dataclass
from typing import TYPE_CHECKING

from models.dataclass import Effect, Monster
from models.enums import Element

if TYPE_CHECKING:
    from models.character import Character


@dataclass(frozen=True)
class SimulateData:
    char_hp: int
    char_max_hp: int
    char_initiative: int
    char_resistance: frozenset[tuple[Element, int]]
    char_attack: frozenset[tuple[Element, int]]
    char_critical_strike: int
    char_effects: frozenset[Effect]

    monster_hp: int
    monster_initiative: int
    monster_resistance: frozenset[tuple[Element, int]]
    monster_attack: frozenset[tuple[Element, int]]
    monster_critical_strike: int
    monster_effects: frozenset[Effect]

    def get_attacks(self, attacker: str) -> tuple[frozenset[tuple[Element, int]], int]:
        if attacker == "char":
            return self.char_attack, self.char_critical_strike
        elif attacker == "monster":
            return self.monster_attack, self.monster_critical_strike
        else:
            raise ValueError(f"Invalid attacker: {attacker}")

    def get_resistances(self, target: str) -> dict[Element, int]:
        if target == "char":
            return dict(self.char_resistance)
        elif target == "monster":
            return dict(self.monster_resistance)
        else:
            raise ValueError(f"Invalid target: {target}")

    def get_effects(self, target: str) -> frozenset[Effect]:
        if target == "char":
            return self.char_effects
        elif target == "monster":
            return self.monster_effects
        else:
            raise ValueError(f"Invalid target: {target}")

    @classmethod
    def from_models(cls, char: "Character", monster: "Monster") -> "SimulateData":
        return cls(
            char_hp=char.hp,
            char_max_hp=char.max_hp,
            char_initiative=char.initiative,
            char_resistance=frozenset(char.resistance.items()),
            char_attack=frozenset(char.attack.items()),
            char_critical_strike=char.critical_strike,
            char_effects=frozenset(char.effects),
            monster_hp=monster.hp,
            monster_initiative=monster.initiative,
            monster_resistance=frozenset(monster.resistance.items()),
            monster_attack=frozenset(monster.attack.items()),
            monster_critical_strike=monster.critical_strike,
            monster_effects=frozenset(monster.effects),
        )


@dataclass(frozen=True)
class SimulateResult:
    win_rate: float
    average_turns: float
    average_char_hp_left: float
    average_monster_hp_left: float
