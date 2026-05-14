from typing import TYPE_CHECKING, Protocol

from exceptions import ImpossibleCombatException
from models.character.decorators import refresh_after, request_action
from models.dataclass import Item, Monster
from utils.math_fight import damage_on

if TYPE_CHECKING:
    from models.character import Character


class FightMixin(Protocol):
    def will_win_against(self: "Character", monster: Monster) -> bool:
        damage = damage_on(self, monster)
        damage += (damage * 0.5) * (self.critical_strike / 100)
        nb_turns_to_kill = (monster.hp) // damage
        if monster.initiative >= self.initiative:
            nb_turns_to_kill += 1

        damage_taken = damage_on(monster, self) * nb_turns_to_kill
        damage_taken += (damage_taken * 0.5) * (monster.critical_strike / 100)

        if damage_taken >= self.max_hp:
            raise ImpossibleCombatException(f"can't win against {monster.name}")

        return damage_taken * 1.3 < self.hp

    @request_action
    @refresh_after
    async def fight(self: "Character") -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/fight",
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
            print(
                f"{'󰓥 ' if result else ' '} {self.surname} Fought and {'won' if result else 'lost'} against {fight['opponent']}"
            )

            return result, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None

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
            print(f"❌ {e}")
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
            print(f"❌ {e}")
            return False, None

    async def regenerate_hp(self: "Character") -> None:
        food = self.get_food
        if not food:
            print(f"❌ {self.surname} has no food to regenerate hp")
            return
        missing_hp = self.missing_hp

        for item, quantity in sorted(
            food.items(), key=lambda x: x[0].heal, reverse=True
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
