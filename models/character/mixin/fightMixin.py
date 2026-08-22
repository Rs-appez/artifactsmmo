import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from exceptions import TimeoutButSuccessException
from models.character.decorators import request_action
from models.dataclass import Monster
from models.enums import Element
from utils.simulate_fight import SimulateData, simulate

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

    def how_much_hp_can_regenerate(self: "Character") -> int:
        food = self.get_food
        if not food:
            return 0
        missing_hp = self.missing_hp
        total_heal = 0

        for item, quantity in sorted(
            food.items(), key=lambda x: x[0].heal, reverse=True
        ):
            qty_to_eat = min(quantity, missing_hp // item.heal)
            total_heal += qty_to_eat * item.heal
            missing_hp -= qty_to_eat * item.heal
            if missing_hp <= 0:
                break

        return total_heal

    async def regenerate_hp(self: "Character", full: bool) -> None:
        food = self.get_food
        if not food:
            print(f"❌ {self.surname} has no food to regenerate hp")
            return
        missing_hp = self.missing_hp

        for i, (item, quantity) in enumerate(
            sorted(food.items(), key=lambda x: x[0].heal, reverse=True)
        ):
            qty_to_eat = min(quantity, missing_hp // item.heal)
            if missing_hp % item.heal != 0 and quantity > qty_to_eat and full:
                qty_to_eat += 1
            if qty_to_eat > 0:
                if not await self.use_item(item, qty_to_eat):
                    print(f"❌ Failed to eat {item.name} x{qty_to_eat}")
                    continue
                missing_hp -= item.heal * qty_to_eat
                print(f" {self.surname} eats {qty_to_eat} {item.name} to recover hp")
                if missing_hp <= 0:
                    break
            elif i == 0:
                raise Exception(
                    f"{item.name} cannot heal any more hp for {self.surname}"
                )

    def will_win_against(
        self: "Character",
        monster: Monster,
        max_hp: bool = False,
        custom_hp: int | None = None,
    ) -> bool:

        simulateData = SimulateData.from_models(
            self, monster, char_max_hp=max_hp, custom_hp=custom_hp
        )
        win_rate = simulate(simulateData).win_rate

        return win_rate >= 99.0

    async def get_ready_to_fight(self: "Character", mob: Monster):
        await self.weaponize(mob)
        try:
            if not self.has_food:
                await self.get_food_from_bank()
        except Exception:
            pass
