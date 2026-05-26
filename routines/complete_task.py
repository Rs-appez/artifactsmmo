from exceptions import NotEnoughInBankException
from models import Character
from models.dataclass import Item, Monster
from models.dataclass.bank import Bank
from models.enums import TaskType
from routines import gather, mob_farm
from utils.find_nearest import find_nearest_tasks_master


async def complete_task(character: Character, type: TaskType | str) -> None:

    if character.task is None:
        if isinstance(type, str):
            try:
                type = TaskType(type)
            except ValueError:
                print(f"❌ Invalid task type : {type}")
                return
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

        if character.is_inventory_full:
            if not await character.deposit_all_in_bank(with_gold=False, comeback=True):
                print("Failed to deposit items in bank")
                return

        if await character.complete_task():
            print(f"  {character.surname} completed the task")
        else:
            print(f"❌ {character.surname} failed to complete the task")

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
        task_resources = {item: character.task_resources_left}
        try:
            async with Bank.reserve_items(
                task_resources, inventory=character.inventory
            ) as bank_token:
                nb_resources_for_the_trip = min(
                    character.task_resources_left, character.inventory_max_items
                )
                trip_resources = {item: nb_resources_for_the_trip}
                async with Bank.get_reserved_items_partial(
                    bank_token, trip_resources
                ) as trip_token:
                    # TODO : optimize by not depositing/withdrawing if the items are already in inventory for the trip and avoid unhandled reservations
                    await character.deposit_all_in_bank(with_gold=False)
                    if not await character.withdraw_item_from_bank(trip_token):
                        raise Exception("Failed to withdraw item from bank")
                if not await character.move(task_master):
                    print("Failed to move to task master")
                    return
                if not await character.trade_with_task_master(
                    item, nb_resources_for_the_trip
                ):
                    print("Failed to complete task")
                    return
        except NotEnoughInBankException:
            async with Bank.reserve_items(
                task_resources, False, inventory=character.inventory
            ) as bank_token:
                need_to_generate = await Bank.get_missing_promise(bank_token)
                if item.is_craftable:
                    # TODO : craft the item if not enough in bank
                    raise Exception(
                        "Not enough item in bank and crafting not implemented yet"
                    )
                else:
                    await gather(character, item, need_to_generate)


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
        while character.task_resources_left > 0:
            await mob_farm(character, monster, character.task_resources_left)
    except Exception as e:
        print(f"❌ {character.surname} failed to complete the monster task : {e}")
        return
    task_master = await find_nearest_tasks_master(character, TaskType.MONSTER)
    if not await character.move(task_master):
        print("Failed to move to task master")
        return
