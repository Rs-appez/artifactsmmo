from contextlib import contextmanager
from dataclasses import dataclass
from math import ceil, floor
from typing import TYPE_CHECKING, Generator

from config import BERSERKER_RAGE_THRESHOLD, GREED_THRESHOLD
from models.dataclass import Effect, Monster
from models.enums import Element

if TYPE_CHECKING:
    from models.character import Character


@dataclass(frozen=True)
class _EntityData:
    _hp: int
    _max_hp: int
    _initiative: int
    _resistance: frozenset[tuple[Element, int]]
    _attack: frozenset[tuple[Element, int]]
    _critical_strike: int
    _effects: frozenset[tuple[Effect, int]]


@dataclass
class _EntityMetadata:
    initiative: int
    hp_left: int
    max_hp: int
    effects: dict[Effect, int]
    resistance: dict[Element, int]
    attack: dict[Element, int]
    critical_strike: int

    nb_turns: int = 0
    has_critical_strike: bool = False

    previous_hp: int = 0

    effect_burn: float = 0
    effect_shield: int = 0
    has_trigger_berserker_rage: bool = False

    def __post_init__(self):
        self.previous_hp = self.hp_left
        self.effect_burn = sum(value for value in self.attack.values())

    def compute_greed(self, value: int) -> None:
        if self.nb_turns == 0:
            return
        last_pourcent_hp = (
            ceil((self.previous_hp / self.max_hp) * 100) // GREED_THRESHOLD
        )
        current_pourcent_hp = (
            ceil((self.hp_left / self.max_hp) * 100) // GREED_THRESHOLD
        )

        diff = last_pourcent_hp - current_pourcent_hp
        self.attack = {
            element: floor(atk * ((value / 100) * diff + 1) + 0.5)
            for element, atk in self.attack.items()
        }

    def compute_berserker_rage(self, value: int) -> None:
        if self.has_trigger_berserker_rage:
            return
        current_pourcent_hp = ceil((self.hp_left / self.max_hp) * 100)

        if current_pourcent_hp < BERSERKER_RAGE_THRESHOLD:
            self.has_trigger_berserker_rage = True
            self.attack = {
                element: floor(atk * ((value / 100) + 1) + 0.5)
                for element, atk in self.attack.items()
            }


class FightMetadata:
    entities: dict[str, _EntityMetadata]
    entities_map: dict[bool, str] = {True: "char", False: "monster"}

    def __init__(self, data: frozenset[tuple[str, _EntityData]]) -> None:
        self.entities = {
            name: _EntityMetadata(
                initiative=entity._initiative,
                hp_left=entity._hp,
                max_hp=entity._max_hp,
                effects=dict(entity._effects),
                resistance=dict(entity._resistance),
                attack=dict(entity._attack),
                critical_strike=entity._critical_strike,
            )
            for name, entity in data
        }

    @property
    def get_turns(self) -> int:
        return sum(entity.nb_turns for entity in self.entities.values())

    def get_initiative(self, is_player: bool) -> int:
        return self.entities[self.entities_map[is_player]].initiative

    def get_attacks(self, is_player: bool) -> dict[Element, int]:
        return self.entities[self.entities_map[is_player]].attack

    def get_critical_strike(self, is_player: bool) -> int:
        return self.entities[self.entities_map[is_player]].critical_strike

    def get_resistances(self, is_player: bool) -> dict[Element, int]:
        return self.entities[self.entities_map[is_player]].resistance

    def reduce_resistance(self, is_player: bool, element: Element, value: int) -> None:
        self.entities[self.entities_map[is_player]].resistance[element] -= value

    def get_hp(self, is_player: bool) -> int:
        return self.entities[self.entities_map[is_player]].hp_left

    def get_max_hp(self, is_player: bool) -> int:
        return self.entities[self.entities_map[is_player]].max_hp

    def get_nb_turns(self, is_player: bool) -> int:
        return self.entities[self.entities_map[is_player]].nb_turns

    def increment_turns(self, is_player: bool) -> None:
        self.entities[self.entities_map[is_player]].nb_turns += 1

    def take_damage(self, is_player: bool, damage: int) -> None:

        def handle_shield(damage: int) -> int:
            shield = self.entities[self.entities_map[is_player]].effect_shield
            if shield > 0:
                if damage <= shield:
                    self.entities[self.entities_map[is_player]].effect_shield -= damage
                    return 0
                else:
                    self.entities[self.entities_map[is_player]].effect_shield = 0
                    return damage - shield
            return damage

        damage = handle_shield(damage)

        self.entities[self.entities_map[is_player]].previous_hp = self.entities[
            self.entities_map[is_player]
        ].hp_left

        self.entities[self.entities_map[is_player]].hp_left = min(
            self.entities[self.entities_map[is_player]].hp_left - damage,
            self.entities[self.entities_map[is_player]].max_hp,
        )

        self.handle_lost_hp_effects(is_player)

    # memory

    def set_critical_strike(self, is_player: bool, value: bool) -> None:
        self.entities[self.entities_map[is_player]].has_critical_strike = value

    def has_critical_strike(self, is_player: bool) -> bool:
        return self.entities[self.entities_map[is_player]].has_critical_strike

    # effects

    def get_effects(self, is_player: bool) -> dict[Effect, int]:
        return self.entities[self.entities_map[is_player]].effects

    def get_burn_damage(self, is_player: bool) -> float:
        return self.entities[self.entities_map[is_player]].effect_burn

    def reduce_burn_damage(self, is_player: bool) -> None:
        self.entities[self.entities_map[is_player]].effect_burn *= 0.9

    def gain_shield(self, is_player: bool, value: int) -> None:
        self.entities[self.entities_map[is_player]].effect_shield += value

    def reconstitution(self, is_player: bool) -> None:
        self.entities[self.entities_map[is_player]].hp_left = self.entities[
            self.entities_map[is_player]
        ].max_hp

    def handle_lost_hp_effects(self, is_player: bool) -> None:
        attacker_effects = self.get_effects(is_player)
        for effect, value in attacker_effects.items():
            match effect.code:
                case "greed":
                    self.entities[self.entities_map[is_player]].compute_greed(value)
                case "berserker_rage":
                    self.entities[self.entities_map[is_player]].compute_berserker_rage(
                        value
                    )


@dataclass(frozen=True)
class SimulateData:
    _entity_data: frozenset[tuple[str, _EntityData]]

    @contextmanager
    def generate_metadata(self) -> Generator[FightMetadata, None]:
        metadata = FightMetadata(self._entity_data)
        yield metadata

    @classmethod
    def from_models(
        cls,
        char: "Character",
        monster: "Monster",
        char_max_hp: bool = False,
        custom_hp: int | None = None,
    ) -> "SimulateData":
        char_data = _EntityData(
            _hp=custom_hp
            if custom_hp is not None
            else (char.max_hp if char_max_hp else char.hp),
            _max_hp=char.max_hp,
            _initiative=char.initiative,
            _resistance=frozenset(char.resistance.items()),
            _attack=frozenset(char.attack.items()),
            _critical_strike=char.critical_strike,
            _effects=frozenset(char.effects.items()),
        )
        monster_data = _EntityData(
            _hp=monster.hp,
            _max_hp=monster.hp,
            _initiative=monster.initiative,
            _resistance=frozenset(monster.resistance.items()),
            _attack=frozenset(monster.attack.items()),
            _critical_strike=monster.critical_strike,
            _effects=frozenset(monster.effects.items()),
        )
        return cls(
            _entity_data=frozenset(
                {
                    ("char", char_data),
                    ("monster", monster_data),
                }
            )
        )


@dataclass(frozen=True)
class SimulateResult:
    win_rate: float
    average_turns: float
    average_char_hp_left: float
    average_monster_hp_left: float
