from models.dataclass.bank import Bank
from models.enums import TaskType
import routines
from models import Character, Encyclopedia
from models.dataclass import Item


def _check_freshness(function):
    async def wrapper(*args, **kwargs):
        character = args[0]
        if isinstance(character, Character):
            if not character.is_working and not await character.refresh():
                print(f"❌ Failed to refresh {character.surname}")
                return

        elif isinstance(character, list) and all(
            isinstance(char, Character) for char in character
        ):
            for char in character:
                if not char.is_working and not await char.refresh():
                    print(f"❌ Failed to refresh {char.surname}")
                    return
        return await function(*args, **kwargs)

    return wrapper


def stop(character: Character):
    character.stop()
    print(f"⏹ Stopped {character.surname}")


@_check_freshness
async def resume(character: Character):
    await character.resume()
    print(f"▶️ Started {character.surname}")


@_check_freshness
async def go_bank(character: Character):
    character.do_one_time_task(routines.empty_farm)
    print(f"🏦 {character.surname} is going to the bank")


@_check_freshness
async def craft(character: Character, item_code: str, quantity: str = "1"):
    item = await Encyclopedia.get_item_by_code(item_code)
    character.do_one_time_task(
        lambda character: routines.craft(character, item, int(quantity))
    )
    print(f"⚒️ {character.surname} will craft {quantity}x {item.name}")


def stop_all(characters: list[Character]):
    for char in characters:
        char.stop()
    print("⏹ Stopped all characters")


@_check_freshness
async def status(characters: list[Character]):
    for char in characters:
        print(char)


@_check_freshness
async def complete_task(character: Character, task_type_str: str = "items"):
    task_type = TaskType(task_type_str)
    character.do_one_time_task(lambda char: routines.complete_task(char, task_type))
    print(f"  {character.surname} will complete a task")


@_check_freshness
async def asign_routine(character: Character, routine_name: str, *args):
    routine_func = getattr(routines, routine_name, None)
    if not routine_func:
        print(f"❌ Unknown routine: {routine_name}")
        return
    character.assign_routine(routine_func, *args)
    print(f"🚀 {character.surname} started working on routine {routine_name}")


def reserved_bank(_):
    reserved = Bank.check_reservations()
    for reservation in reserved.values():
        print(
            f"🔒reserved {', '.join([f'{qty}x {item.name}' for item, qty in reservation.items()])}"
        )
