from exceptions import NotEnoughInBankException
from models import Character
from models.dataclass import Item, Monster
from models.dataclass.bank import Bank
from models.enums import TaskType
from routines import gather, mob_farm
from utils.find_nearest import find_nearest_tasks_master


async def complete_task(character: Character, type: TaskType) -> None:

    if character.task is None:
        match type:
            case TaskType.MONSTER:
                task_master = await find_nearest_tasks_master(
                    character, TaskType.MONSTER
                )
            case TaskType.ITEM:
                task_master = await find_nearest_tasks_master(character, TaskType.ITEM)

        if not await character.move(task_master):
            print("Failed to move to task master")
            return
        if not await character.accept_task():
            print("Failed to accept task")
            return

    if character.task is None:
        print("❌ No task accepted")
        return

    try:
        if isinstance(character.task.cible, Monster):
            await __monster_task(character)
        elif isinstance(character.task.cible, Item):
            await __item_task(character)
    except Exception as e:
        print(f"❌ {character.surname} failed to complete the task : {e}")
        return


async def __item_task(character: Character) -> None:
    if character.task is None:
        print("❌ No task accepted")
        return
    if isinstance(character.task.cible, Item):
        item: Item = character.task.cible
    else:
        print("❌ Task cible is not an item")
        return
    task_master = await find_nearest_tasks_master(character, TaskType.ITEM)
    while character.task_resources_left > 0:
        nb_resources_for_the_trip = min(
            character.task_resources_left, character.inventory_max_items
        )

        trip_resources = {item: nb_resources_for_the_trip}
        if not character.has_in_inventory(trip_resources):
            try:
                async with Bank.reserve_items(trip_resources) as bank_token:
                    await character.deposit_all_in_bank(comeback=False)
                    if not await character.withdraw_item_from_bank(bank_token):
                        raise Exception("Failed to withdraw item from bank")
            except NotEnoughInBankException:
                async with Bank.reserve_items(trip_resources, False) as bank_token:
                    if item.is_craftable:
                        # TODO : craft the item if not enough in bank
                        raise Exception(
                            "Not enough item in bank and crafting not implemented yet"
                        )
                    else:
                        resources = Bank.check_reserved_items(bank_token)
                        missing = abs(resources.get(item, 0))
                        await gather(character, item, missing)
                        continue
        if not await character.move(task_master):
            print("Failed to move to task master")
            return
        if not await character.trade_with_task_master(item, nb_resources_for_the_trip):
            print("Failed to complete task")
            return

    if await character.complete_task():
        print(f"  {character.surname} completed the item task")
    else:
        print(f"❌ {character.surname} failed to complete the item task")


async def __monster_task(character: Character) -> None:
    if character.task is None:
        print("❌ No task accepted")
        return
    if isinstance(character.task.cible, Monster):
        monster: Monster = character.task.cible
    else:
        print("❌ Task cible is not a monster")
        return

    try:
        await mob_farm(character, monster, character.task_resources_left)
    except Exception as e:
        print(f"❌ {character.surname} failed to complete the monster task : {e}")
        return
    task_master = await find_nearest_tasks_master(character, TaskType.MONSTER)
    if not await character.move(task_master):
        print("Failed to move to task master")
        return
    if await character.complete_task():
        print(f"  {character.surname} completed the monster task")
    else:
        print(f"❌ {character.surname} failed to complete the monster task")
