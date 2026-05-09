from dataclasses import dataclass


from models.dataclass import Item, Monster
from models.enums import TaskType


@dataclass
class TaskQuest:
    quantity_left: int
    cible: Item | Monster | None = None

    @classmethod
    async def from_dict(cls, data: dict) -> "TaskQuest":
        from models import Encyclopedia

        task_type = TaskType(data["task_type"])
        cible = None
        if task_type == TaskType.ITEM:
            cible = await Encyclopedia.get_item_by_code(data["task"])
        elif task_type == TaskType.MONSTER:
            cible = await Encyclopedia.get_monster_by_code(data["task"])

        tast_left = data["task_total"] - data["task_progress"]
        return cls(
            quantity_left=tast_left,
            cible=cible,
        )
