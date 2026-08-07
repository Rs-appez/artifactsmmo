import asyncio
from dataclasses import dataclass, field
from math import ceil, floor
from typing import TYPE_CHECKING

from exceptions import ImpossibleCombatException, TimeoutButSuccessException
from models.character.decorators import request_action
from models.dataclass import Monster
from models.enums import Element
from utils.math_fight import damage_on

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class FightMixin:
    _hp: int = 0
    _max_hp: int = 0
    _initiative: int = 0
    _resistance: dict[Element, int] = field(default_factory=dict)
    _attack: dict[Element, int] = field(default_factory=dict)
    _critical_strike: int = 0

    _ready_to_fight_boss: bool = False

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def missing_hp(self) -> int:
        return self._max_hp - self._hp

    @property
    def resistance(self) -> dict[Element, int]:
        return self._resistance.copy()

    @property
    def attack(self) -> dict[Element, int]:
        return self._attack.copy()

    @property
    def critical_strike(self) -> int:
        return self._critical_strike

    @property
    def initiative(self) -> int:
        return self._initiative

    @property
    def is_ready_to_fight_boss(self: "Character"):
        return self._ready_to_fight_boss

    @is_ready_to_fight_boss.setter
    def is_ready_to_fight_boss(self: "Character", value: bool):
        self._ready_to_fight_boss = value

    @property
    async def waiting_for_fight(self: "Character"):
        while self._ready_to_fight_boss:
            await asyncio.sleep(0.2)

    @request_action
    async def set_ready_to_fight(self: "Character"):
        self._ready_to_fight_boss = True

    async def fight(
        self: "Character", teammate: list[Character] | None = None
    ) -> tuple[bool, dict]:
        """
        Fight with the character and optionally with teammates.
        Returns a tuple of (result, fight_data) where result is True if the fight was won, False otherwise, and fight_data contains additional information about the fight.
        """

        try:
            result_data = {"fight": {}}
            await self.post_api(
                "/fight",
                json_data={
                    "participants": [
                        mate.name for mate in teammate if mate.name != self.name
                    ]
                }
                if teammate
                else None,
                retreive_data=result_data,
            )

            result: bool = result_data["fight"]["result"] == "win"
            participants = [mate.surname for mate in teammate] if teammate else []
            print(
                f"{'󰓥 ' if result else ' '} {','.join(participants) if participants else self.surname} Fought and {'won' if result else 'lost'}"
            )

            return (result, result_data["fight"])
        except Exception as e:
            print(f"❌ {self.surname} fight : {e}")
            return (False, {})

    async def rest(self: "Character") -> bool:
        try:
            await self.post_api("/rest")
            return True
        except TimeoutButSuccessException:
            return True
        except Exception as e:
            print(f"❌ {self.surname} Rest : {e}")
            return False

    async def regenerate_hp(self: "Character") -> None:
        food = self.get_food
        if not food:
            print(f"❌ {self.surname} has no food to regenerate hp")
            return
        missing_hp = self.missing_hp

        for i, (item, quantity) in enumerate(
            sorted(food.items(), key=lambda x: x[0].heal, reverse=True)
        ):
            qty_to_eat = min(quantity, missing_hp // item.heal)
            if qty_to_eat > 0:
                if not await self.use_item(item, qty_to_eat):
                    print(f"❌ Failed to eat {item.name} x{qty_to_eat}")
                    continue
                missing_hp -= item.heal * qty_to_eat
                print(f" {self.surname} eats {qty_to_eat} {item.name} to recover hp")
                if missing_hp <= 0:
                    break
            elif i == 0:
                _ = await self.use_item(item, 1)
            else:
                raise Exception(
                    f"{item.name} cannot heal any more hp for {self.surname}"
                )

    def will_win_against(self: "Character", monster: Monster) -> bool:

        nb_turns_to_kill = self._compute_nb_turns_to_kill(monster)
        damage_taken = self._compute_damage_taken(monster, nb_turns_to_kill)
        health_regen = self._compute_health_regen(nb_turns_to_kill)

        if damage_taken >= self.max_hp + health_regen:
            raise ImpossibleCombatException(f"can't win against {monster.name}")
        return damage_taken < self.hp + health_regen

    def _compute_nb_turns_to_kill(self: "Character", monster: Monster) -> int:
        damage = damage_on(self, monster)
        for effect, value in monster.effects.items():
            match effect.code:
                case "corrupted":
                    damage *= 1.5
                case _:
                    continue
        bonus_damage = self._compute_effects_damage()
        damage += (damage * 0.5) * (self.critical_strike * 0.75 / 100)
        if damage + bonus_damage <= 0:
            raise ImpossibleCombatException(
                f"{self.surname} cannot deal damage to {monster.name}"
            )
        nb_turns_to_kill = (monster.hp) // (damage + bonus_damage)
        if monster.initiative > self.initiative:
            nb_turns_to_kill += 1
        elif monster.initiative == self.initiative:
            if monster.hp > self.hp:
                nb_turns_to_kill += 1

        return ceil(nb_turns_to_kill)

    def _compute_damage_taken(
        self: "Character", monster: Monster, nb_turns_to_kill: int
    ) -> float:
        bonus_damage = self._compute_monster_damage_effects(monster)
        damage_taken = (damage_on(monster, self) + bonus_damage) * nb_turns_to_kill
        damage_taken += (damage_taken * 0.5) * (
            min(monster.critical_strike * 1.5, 100) / 100
        )

        return damage_taken

    def _compute_health_regen(self: "Character", nb_turns_to_kill: int) -> int:

        total_regen = 0
        for effect, value in self.effects.items():
            match effect.code:
                case "healing":
                    total_regen += (value / 100) * self.max_hp * (nb_turns_to_kill // 3)
                case _:
                    continue

        return floor(total_regen)

    def _compute_monster_damage_effects(self: "Character", monster: Monster) -> float:
        bonus_damage = 0
        for effect, value in monster.effects.items():
            match effect.code:
                case "poison":
                    antipoison = sum(
                        self.effects[effect]
                        for effect in self.effects
                        if effect.code == "antipoison"
                    )
                    bonus_damage += max(0, value - antipoison)
                case _:
                    continue

        return bonus_damage

    def _compute_effects_damage(self: "Character") -> float:
        bonus_damage = 0
        for effect, value in self.effects.items():
            match effect.code:
                case "burn":
                    bonus_damage += (value * 0.75 / 100) * sum(self.attack.values())
                case _:
                    continue

        return bonus_damage
