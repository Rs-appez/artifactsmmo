from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING

from models.dataclass import Effect, Monster
from models.enums import Element

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class _FightMetadata:
    has_been_setup: bool = False

    char_nb_turns: int = 0
    char_hp_left: int = 0
    char_resistance: dict[Element, int] = field(default_factory=dict)
    char_attack: dict[Element, int] = field(default_factory=dict)
    char_critical_strike: int = 0

    monster_nb_turns: int = 0
    monster_hp_left: int = 0
    monster_resistance: dict[Element, int] = field(default_factory=dict)
    monster_attack: dict[Element, int] = field(default_factory=dict)
    monster_critical_strike: int = 0

    def setup(self, data: "SimulateData") -> None:
        if self.has_been_setup:
            raise ValueError("Metadata has already been setup.")

        self.char_nb_turns = 0
        self.char_hp_left = data._char_hp
        self.char_resistance = dict(data._char_resistance)
        self.char_attack, self.char_critical_strike = (
            dict(data._char_attack),
            data._char_critical_strike,
        )

        self.monster_nb_turns = 0
        self.monster_hp_left = data._monster_hp
        self.monster_resistance = dict(data._monster_resistance)
        self.monster_attack, self.monster_critical_strike = (
            dict(data._monster_attack),
            data._monster_critical_strike,
        )

        self.has_been_setup = True

    def reset(self, data: "SimulateData") -> None:
        self.has_been_setup = False
        self.setup(data)

    def __hash__(self) -> int:
        return 1


@dataclass(frozen=True)
class SimulateData:
    _char_hp: int
    _char_max_hp: int
    _char_initiative: int
    _char_resistance: frozenset[tuple[Element, int]]
    _char_attack: frozenset[tuple[Element, int]]
    _char_critical_strike: int
    _char_effects: frozenset[tuple[Effect, int]]

    _monster_hp: int
    _monster_max_hp: int
    _monster_initiative: int
    _monster_resistance: frozenset[tuple[Element, int]]
    _monster_attack: frozenset[tuple[Element, int]]
    _monster_critical_strike: int
    _monster_effects: frozenset[tuple[Effect, int]]

    _metadata: _FightMetadata = field(
        default_factory=_FightMetadata, init=False, repr=False
    )

    @staticmethod
    def _need_setup(func):
        """Decorator to ensure metadata has been setup before calling method."""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self._metadata.has_been_setup:
                self._generate_metadata()
            return func(self, *args, **kwargs)

        return wrapper

    @property
    def get_turns(self) -> int:
        return self._metadata.char_nb_turns + self._metadata.monster_nb_turns

    @_need_setup
    def get_attacks(self, is_player: bool) -> tuple[dict[Element, int], int]:
        return (
            (self._metadata.char_attack, self._char_critical_strike)
            if is_player
            else (self._metadata.monster_attack, self._monster_critical_strike)
        )

    @_need_setup
    def get_resistances(self, is_player: bool) -> dict[Element, int]:
        return (
            self._metadata.char_resistance
            if is_player
            else self._metadata.monster_resistance
        )

    @_need_setup
    def get_effects(self, is_player: bool) -> dict[Effect, int]:
        return dict(self._char_effects) if is_player else dict(self._monster_effects)

    @_need_setup
    def get_hp(self, is_player: bool) -> int:
        return (
            self._metadata.char_hp_left if is_player else self._metadata.monster_hp_left
        )

    @_need_setup
    def get_max_hp(self, is_player: bool) -> int:
        return self._char_max_hp if is_player else self._monster_max_hp

    @_need_setup
    def get_initiative(self, is_player: bool) -> int:
        return self._char_initiative if is_player else self._monster_initiative

    @_need_setup
    def increment_turns(self, is_player: bool) -> None:
        if is_player:
            self._metadata.char_nb_turns += 1
        else:
            self._metadata.monster_nb_turns += 1

    @_need_setup
    def take_damage(self, is_player: bool, damage: int) -> None:
        if is_player:
            self._metadata.char_hp_left -= damage
        else:
            self._metadata.monster_hp_left -= damage

    def _generate_metadata(self) -> None:
        self._metadata.setup(self)

    def reset_metadata(self) -> None:
        self._metadata.reset(self)

    @classmethod
    def from_models(cls, char: "Character", monster: "Monster") -> "SimulateData":
        return cls(
            _char_hp=char.hp,
            _char_max_hp=char.max_hp,
            _char_initiative=char.initiative,
            _char_resistance=frozenset(char.resistance.items()),
            _char_attack=frozenset(char.attack.items()),
            _char_critical_strike=char.critical_strike,
            _char_effects=frozenset(char.effects.items()),
            _monster_hp=monster.hp,
            _monster_max_hp=monster.hp,
            _monster_initiative=monster.initiative,
            _monster_resistance=frozenset(monster.resistance.items()),
            _monster_attack=frozenset(monster.attack.items()),
            _monster_critical_strike=monster.critical_strike,
            _monster_effects=frozenset(monster.effects.items()),
        )


@dataclass(frozen=True)
class SimulateResult:
    win_rate: float
    average_turns: float
    average_char_hp_left: float
    average_monster_hp_left: float
