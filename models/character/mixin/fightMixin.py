from typing import Protocol, TYPE_CHECKING

from config import HEADERS
from models.character.decorators import refresh_after, request_action
from models.dataclass import Monster
from utils.math_fight import calc_resistance, damage_on

if TYPE_CHECKING:
    from models.character import Character


class FightMixin(Protocol):
    def will_win_against(self: "Character", monster: Monster) -> bool:
        damage = damage_on(self, monster)
        nb_turns_to_kill = (monster.hp) // damage
        if monster.initiative >= self.initiative:
            nb_turns_to_kill += 1

        damage_taken = damage_on(monster, self) * nb_turns_to_kill
        damage_taken += (damage_taken * 0.5) * (monster.critical_strike / 100)

        if damage_taken >= self.max_hp:
            raise Exception(f"can't win against {monster.name}")

        return damage_taken < self.hp

    @request_action
    @refresh_after
    async def fight(self: "Character") -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                f"{self.url}/action/fight",
                headers=HEADERS,
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
                f"󰓥 {self.surname} Fought and {'won' if result else 'lost'} against {fight['opponent']}"
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
                f"{self.url}/action/rest",
                headers=HEADERS,
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
