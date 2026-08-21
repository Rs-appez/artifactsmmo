import routines
from models import Character, Encyclopedia, GameManager, LocationRegistry
from models.dataclass.bank import Bank
from models.enums import TaskType
from utils.xp_craft_calculator import nb_craft_needed_for_level_up


def _check_freshness(function):
    async def wrapper(*args, **kwargs):
        character = args[0]
        if isinstance(character, Character):
            if not character.is_working:
                try:
                    await character.refresh()
                except Exception as e:
                    print(f"❌ Failed to refresh {character.surname} : {e}")
                    return

        elif isinstance(character, list) and all(
            isinstance(char, Character) for char in character
        ):
            for char in character:
                if not char.is_working:
                    try:
                        await char.refresh()
                    except Exception as e:
                        print(f"❌ Failed to refresh {char.surname} : {e}")
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
    character.do_one_time_task(routines.complete_task, task_type, nb=1)
    print(f"  {character.surname} will complete a task")


@_check_freshness
async def asign_routine(character: Character, routine_name: str, *args):
    routine_func = getattr(routines, routine_name, None)
    if not routine_func:
        print(f"❌ Unknown routine: {routine_name}")
        return
    character.assign_routine(routine_func, *args)
    print(f"🚀 {character.surname} started working on routine {routine_name}")


@_check_freshness
async def asign_mission(character: Character, routine_name: str, *args):
    routine_func = getattr(routines, routine_name, None)
    if not routine_func:
        print(f"❌ Unknown routine: {routine_name}")
        return
    character.do_one_time_task(routine_func, *args)
    print(f"🚀 {character.surname} started working on {routine_name}")


async def exchange_task_coin(character: Character):
    character.do_one_time_task(routines.exchange_task_coin)
    print(f"🪙 {character.surname} will exchange task coins")


def reserved_bank(_):
    reserved = Bank.show_reservations()
    for reservation in reserved.values():
        print(
            f"🔒reserved {', '.join([f'{qty}x {item.name}' for item, qty in reservation.items()])}"
        )


@_check_freshness
async def nb_craft_needed_calculator(
    character: Character, item_code: str, target_level: str | None = None
):
    nb_craft_needed = await nb_craft_needed_for_level_up(
        character, item_code, int(target_level) if target_level else None
    )
    print(
        f"⚒️ {character.surname} needs {nb_craft_needed} crafts to reach level {target_level} with item {item_code}"
    )


async def refresh_events(gm: GameManager):

    await gm.event_handler.refresh_current_events()


@_check_freshness
async def bagize(character: Character):
    async def bagize_routine(character: Character):
        await character.bagize()

    character.do_one_time_task(bagize_routine)
    print(f"👜 {character.surname} will bagize")


@_check_freshness
async def move_to(character: Character, map_id: str):
    map = await LocationRegistry.get_map_by_id(int(map_id))

    async def move(character: Character, map):
        await character.move(map)

    character.do_one_time_task(move, map)


async def refresh_bank(_):
    await Bank.refresh_bank()
    print("🏦 Bank refreshed")
