from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from models.dataclass import Map

from ..decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class MoveMixin(Protocol):
    _location: Map | None = None

    @property
    def location(self: "Character") -> Map:
        if self._location is None:
            raise Exception("Location is not set for this character")
        return self._location

    @request_action
    @refresh_after
    async def move(self: "Character", destination: Map) -> tuple[bool, dict | None]:
        if destination == self.location:
            return True, None
        try:
            response = await self.client.post(
                "/move",
                json={"map_id": destination.map_id},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                if data["error"]["code"] == 490:
                    return True, None
                raise Exception(data["error"]["message"])

            arrived = data["data"]["destination"]
            character_data = data["data"]["character"]

            print(
                f"🏃 {self.surname} Moved to ({arrived['x']}, {arrived['y']}) on {arrived['name']}"
            )
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None
            destination = data["data"]["destination"]
            character_data = data["data"]["character"]

            print(
                f"🏃{self.surname} Moved to ({destination['x']}, {destination['y']}) on {destination['name']}"
            )
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None
