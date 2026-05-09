from locations import monster_task_master, item_task_master
from models import Character
from models.dataclass import Item
from models.enums import TaskType


async def complete_task(character: Character, type: TaskType) -> None:

    match type:
        case TaskType.MONSTER:
            task_master = monster_task_master
        case TaskType.ITEM:
            task_master = item_task_master

    if character.task is None:
        if not await character.move(task_master):
            print("Failed to move to task master")
            return
        if not await character.accept_task():
            print("Failed to accept task")
            return

    match type:
        case TaskType.MONSTER:
            await __monster_task()
        case TaskType.ITEM:
            await __item_task(character)


async def __item_task(character: Character) -> None:
    if character.task is None:
        print("❌ No task accepted")
        return
    if isinstance(character.task.cible, Item):
        item: Item = character.task.cible
    else:
        print("❌ Task cible is not an item")
        return
    while character.task_resources_left > 0:
        await character.deposit_all_in_bank(comeback=False)
        nb_resources_for_the_trip = min(
            character.task_resources_left, character.inventory_max_items
        )
        if not await character.withdraw_item_from_bank(
            [(item.code, nb_resources_for_the_trip)]
        ):
            return
        if not await character.move(item_task_master):
            print("Failed to move to task master")
            return
        if not await character.trade_with_task_master(item, nb_resources_for_the_trip):
            print("Failed to complete task")
            return

    if await character.complete_task():
        print(f"✅ {character.surname} completed the item task")
    else:
        print(f"❌ {character.surname} failed to complete the item task")


async def __monster_task() -> None:
    pass
