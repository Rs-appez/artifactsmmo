from typing import Protocol, TYPE_CHECKING

from config import HEADERS
from models.character.decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


class TaskMixin(Protocol):
    @request_action
    @refresh_after
    async def accept_task(self: "Character") -> tuple[bool, dict | None]:
        try:
            response = await self.client.get(
                f"{self.url}/action/task/new",
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

    @request_action
    @refresh_after
    async def complete_task(self: "Character") -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                f"{self.url}/action/task/complete",
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
