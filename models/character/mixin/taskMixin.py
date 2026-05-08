from typing import Protocol

from models.dataclass import Item, Monster


class TaskMixin(Protocol):
    tastk_objectif: Item | Monster | None = None
    task_quantity: int | None = None
