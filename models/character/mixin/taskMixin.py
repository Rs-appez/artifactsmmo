from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from models.character.decorators import refresh_after, request_action
from models.dataclass import Item, TaskQuest
from models.encyclopedia import Encyclopedia

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class TaskMixin(Protocol):
    _task: TaskQuest | None = None

    @property
    def task(self) -> TaskQuest | None:
        return self._task

    @property
    def task_resources_left(self: "Character") -> int:
        if not self.task:
            return 0
        return self.task.quantity_left

    @request_action
    @refresh_after
    async def accept_task(self: "Character") -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/task/new",
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} Accept task : {e}")
            return False, None

    @request_action
    @refresh_after
    async def complete_task(self: "Character") -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/task/complete",
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} Complete task : {e}")
            return False, None

    @request_action
    @refresh_after
    async def trade_with_task_master(
        self: "Character", item: Item, quantity: int
    ) -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/task/trade",
                json={"quantity": quantity, "code": item.code},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} Trade with task master : {e}")
            return False, None

    @request_action
    @refresh_after
    async def give_up_task(self: "Character") -> tuple[bool, dict | None]:
        try:
            if not self.task:
                raise Exception("No active task to give up")
            if await Encyclopedia.get_item_by_code("tasks_coin") not in self.inventory:
                raise Exception("Cannot give up task without a tasks coin in inventory")
            response = await self.client.post(
                "/task/cancel",
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} Give up task : {e}")
            return False, None

    @request_action
    @refresh_after
    async def exchange_task_coin(self: "Character") -> tuple[bool, dict | None]:
        try:
            task_coin = await Encyclopedia.get_item_by_code("task_coin")
            if not self.has_in_inventory({task_coin: 6}):
                return False, None
            response = await self.client.post(
                "/task/exchange",
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} Exchange task coin : {e}")
            return False, None
