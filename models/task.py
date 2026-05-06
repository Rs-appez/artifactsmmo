from models import GameManager, Item
from .enums import TaskType
from dataclasses import dataclass


@dataclass
class Task:
    type: TaskType
    quantity_left: int
    item: Item | None = None

    @classmethod
    async def from_dict(cls, data: dict) -> "Task":
        task_type = TaskType(data["task_type"])
        item = None
        if task_type is TaskType.ITEM:
            item = await GameManager.get_item_by_code(data["task"])
        tast_left = data["task_total"] - data["task_progress"]
        return cls(
            type=task_type,
            quantity_left=tast_left,
            item=item,
        )
