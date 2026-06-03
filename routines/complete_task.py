from itertools import count

from exceptions import NotEnoughInBankException, NotWorthableTaskException
from models import Character, Encyclopedia
from models.dataclass import Item, Monster
from models.dataclass.bank import Bank
from models.enums import TaskType
from routines import mob_farm, generate_missing_items
from utils.find_nearest import find_nearest_tasks_master


async def complete_task(
    character: Character, type: TaskType | str = TaskType.ITEM, nb: int | str = -1
) -> None:

    if isinstance(nb, str):
        try:
            nb = int(nb)
        except ValueError:
            print(f"❌ Invalid number of iterations : {nb}")
            return

    match type:
        case TaskType.MONSTER:
            task_master = await find_nearest_tasks_master(character, TaskType.MONSTER)
        case TaskType.ITEM:
            task_master = await find_nearest_tasks_master(character, TaskType.ITEM)
        case _:
            print(f"❌ Invalid task type : {type}")
            return

    iterations = range(nb) if nb > 0 else count()
    for _ in iterations:
        if character.task is None:
            if isinstance(type, str):
                try:
                    type = TaskType(type)
                except ValueError:
                    print(f"❌ Invalid task type : {type}")
                    return

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
                if not await character.deposit_all_in_bank(with_gold=False):
                    print("Failed to deposit items in bank")
                    return

            if not await character.move(task_master):
                print("Failed to move to task master to complete the task")
                return
            if await character.complete_task():
                print(f"  {character.surname} completed the task")
            else:
                print(f"❌ {character.surname} failed to complete the task")

        except NotWorthableTaskException as e:
            print(f"⚠️ {character.surname} skipped the task : {e}")
            continue
        except Exception as e:
            print(f"❌ {character.surname} failed to complete the task : {e}")
            return


async def __item_task(character: Character) -> None:
    if character.task is None:
        raise Exception("No task accepted")
    if isinstance(character.task.cible, Item):
        item: Item = character.task.cible
    else:
        raise Exception("Task cible is not an item")
    task_master = await find_nearest_tasks_master(character, TaskType.ITEM)
    if not __is_worth_it(item):
        _ = await __give_up_task(character, TaskType.ITEM)
        raise NotWorthableTaskException(
            f"Task for {item.name} is not worth it, skipping..."
        )

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
                    raise Exception("Failed to move to task master")
                if not await character.trade_with_task_master(
                    item, nb_resources_for_the_trip
                ):
                    raise Exception("Failed to trade with task master")
        except NotEnoughInBankException:
            await generate_missing_items(character, task_resources)


async def __monster_task(character: Character) -> None:
    if character.task is None:
        print("❌ No task accepted")
        return
    if isinstance(character.task.cible, Monster):
        monster: Monster = character.task.cible
    else:
        print("❌ Task cible is not a monster")
        return

    while character.task_resources_left > 0:
        await mob_farm(character, monster, character.task_resources_left)

    task_master = await find_nearest_tasks_master(character, TaskType.MONSTER)
    if not await character.move(task_master):
        print("Failed to move to task master")
        return


def __is_worth_it(item: Item) -> bool:
    # TODO : add more logic to determine if the task is worth it or not
    if item.level == 35 or item.level == 50:
        return False
    return True


async def __give_up_task(character: Character, task_type: TaskType) -> None:
    task_master = await find_nearest_tasks_master(character, task_type)

    if await Encyclopedia.get_item_by_code("tasks_coin") not in character.inventory:
        async with Bank.reserve_items(
            {await Encyclopedia.get_item_by_code("tasks_coin"): 1}
        ) as bank_token:
            if character.is_inventory_full:
                if not await character.deposit_all_in_bank(with_gold=False):
                    raise Exception("Failed to deposit items in bank")
            if not await character.withdraw_item_from_bank(bank_token):
                raise Exception("Failed to withdraw task coin from bank")
    if not await character.move(task_master):
        raise Exception("Failed to move to task master")
    if not await character.give_up_task():
        raise Exception("Failed to give up task")
