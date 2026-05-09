from typing import Protocol, TYPE_CHECKING

from config import HEADERS
from models.character.decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


class FightMixin(Protocol):
    _last_damage_taken: int = 0

    @property
    def last_damage_taken(self: "Character") -> int:
        return self._last_damage_taken

    def reset_damage_taken(self: "Character"):
        self._last_damage_taken = 0

    @request_action
    @refresh_after
    async def fight(self: "Character") -> tuple[bool, dict | None]:
        try:
            current_hp = self.hp
            damage_taken = 0
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
                    damage_taken = current_hp - character_data["hp"]
                    break

            self._last_damage_taken = damage_taken
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
