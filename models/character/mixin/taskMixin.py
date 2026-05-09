from typing import Protocol, TYPE_CHECKING

from config import HEADERS
from models.character.decorators import refresh_after, request_action
from models.dataclass import Item

if TYPE_CHECKING:
    from models.character import Character


class TaskMixin(Protocol):
    @property
    def task_resources_left(self: "Character") -> int:
        if not self.task:
            return 0
        return self.task.quantity_left

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

    @request_action
    @refresh_after
    async def trade_with_task_master(
        self: "Character", item: Item, quantity: int
    ) -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                f"{self.url}/action/task/trade",
                headers=HEADERS,
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
