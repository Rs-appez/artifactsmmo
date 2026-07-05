from exceptions import TimeoutButSuccessException
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from models.dataclass import Item, TaskQuest
from models.encyclopedia import Encyclopedia

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class TaskMixin:
    _task: TaskQuest | None = None

    @property
    def task(self) -> TaskQuest | None:
        return self._task

    @property
    def task_resources_left(self: "Character") -> int:
        if not self.task:
            return 0
        return self.task.quantity_left

    async def accept_task(self: "Character") -> bool:
        try:
            await self.post_api("/task/new")
            return True
        except TimeoutButSuccessException:
            return True
        except Exception as e:
            print(f"❌ {self.surname} Accept task : {e}")
            return False

    async def complete_task(self: "Character") -> bool:
        try:
            await self.post_api("/task/complete")
            return True
        except TimeoutButSuccessException:
            return True
        except Exception as e:
            print(f"❌ {self.surname} Complete task : {e}")
            return False

    async def trade_with_task_master(
        self: "Character", item: Item, quantity: int
    ) -> bool:
        try:
            await self.post_api(
                "/task/trade",
                json={"quantity": quantity, "code": item.code},
            )
            return True
        except TimeoutButSuccessException:
            return True
        except Exception as e:
            print(f"❌ {self.surname} Trade with task master : {e}")
            return False

    async def give_up_task(self: "Character") -> bool:
        try:
            if not self.task:
                raise Exception("No active task to give up")
            if await Encyclopedia.get_item_by_code("tasks_coin") not in self.inventory:
                raise Exception("Cannot give up task without a tasks coin in inventory")

            await self.post_api(
                "/task/cancel",
            )
            return True
        except TimeoutButSuccessException:
            return True
        except Exception as e:
            print(f"❌ {self.surname} Give up task : {e}")
            return False

    async def exchange_task_coin(self: "Character") -> bool:
        try:
            task_coin = await Encyclopedia.get_item_by_code("tasks_coin")
            if not task_coin:
                raise Exception("Task coin not found in encyclopedia")
            if not self.has_in_inventory({task_coin: 6}):
                return False

            await self.post_api(
                "/task/exchange",
            )
            return True
        except TimeoutButSuccessException:
            return True
        except Exception as e:
            print(f"❌ {self.surname} Exchange task coin : {e}")
            return False
