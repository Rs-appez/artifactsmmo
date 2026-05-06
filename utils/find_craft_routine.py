from typing import Callable
from models import Item
import routines

craft_mapping = {"cooking": routines.craft_cooking}


def find_craft_routine(item: Item) -> Callable | None:
    return craft_mapping.get(item.job, None)
