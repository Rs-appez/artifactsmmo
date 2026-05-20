import asyncio
from dataclasses import dataclass, field
from math import ceil, floor
from typing import TYPE_CHECKING, Protocol

from exceptions import ImpossibleCombatException
from models.character.decorators import refresh_after, request_action
from models.dataclass import Item, Monster
from models.enums import Element
from utils.math_fight import damage_on

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class FightMixin(Protocol):
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

    @property
    async def waiting_for_fight(self: "Character"):
        while self._ready_to_fight_boss:
            await asyncio.sleep(1)

    @request_action
    async def set_ready_to_fight(self: "Character"):
        self._ready_to_fight_boss = True

    @request_action
    @refresh_after
    async def fight(
        self: "Character", teammate: list[Character] | None = None
    ) -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/fight",
                json={
                    "participants": [
                        mate.name for mate in teammate if mate.name != self.name
                    ]
                }
                if teammate
                else None,
            )
            data = response.json()["data"]

            fight = data["fight"]
            characters = data["characters"]
            character_data = None
            for character in characters:
                if character["name"] == self.name:
                    character_data = character
                    break

            result = True if fight["result"] == "win" else False
            participants = [mate.surname for mate in teammate] if teammate else []
            print(
                f"{'󰓥 ' if result else ' '} {','.join(participants) if participants else self.surname} Fought and {'won' if result else 'lost'} against {fight['opponent']}"
            )

            return result, character_data
        except Exception as e:
            print(f"❌ {self.surname} fight : {e}")
            return False, None
        finally:
            self._ready_to_fight_boss = False

    @request_action
    @refresh_after
    async def rest(self: "Character") -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/rest",
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} Rest : {e}")
            return False, None

    @request_action
    @refresh_after
    async def eat(
        self: "Character", item: Item, quantity: int
    ) -> tuple[bool, dict | None]:
        try:
            if item.type != "consumable":
                raise Exception(f"{item.name} is not a consumable item")
            if quantity <= 0:
                raise Exception(
                    f"Cannot eat non-positive quantity of {item.name}: {quantity}"
                )
            response = await self.client.post(
                "/use",
                json={"quantity": quantity, "code": item.code},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} Eat : {e}")
            return False, None

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
                if not await self.eat(item, qty_to_eat):
                    print(f"❌ Failed to eat {item.name} x{qty_to_eat}")
                    continue
                missing_hp -= item.heal * qty_to_eat
                print(f" {self.surname} eats {qty_to_eat} {item.name} to recover hp")
                if missing_hp <= 0:
                    break
            elif i == 0:
                _ = await self.eat(item, 1)
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
        damage += (damage * 0.5) * (self.critical_strike * 0.75 / 100)
        nb_turns_to_kill = (monster.hp) // damage
        if monster.initiative > self.initiative:
            nb_turns_to_kill += 1
        elif monster.initiative == self.initiative:
            if monster.hp > self.max_hp:
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
