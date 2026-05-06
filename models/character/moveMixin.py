from typing import TYPE_CHECKING, Protocol

from config import HEADERS

from .decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


class MoveMixin(Protocol):
    @request_action
    @refresh_after
    async def move(
        self: "Character", position: tuple[int, int]
    ) -> tuple[bool, dict | None]:
        if position == self.location:
            return True, None
        try:
            response = await self.client.post(
                f"{self.url}/action/move",
                json={"x": position[0], "y": position[1]},
                headers=HEADERS,
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                if data["error"]["code"] == 490:
                    return True, None
                raise Exception(data["error"]["message"])

            destination = data["data"]["destination"]
            character_data = data["data"]["character"]

            print(
                f"🏃{self.name} Moved to ({destination['x']}, {destination['y']}) on {destination['name']}"
            )
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None
