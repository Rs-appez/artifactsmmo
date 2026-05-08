import routines
from models import Character
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
async def start(character: Character):
    await character.resume()
    print(f"▶️ Started {character.surname}")


@_check_freshness
async def go_bank(character: Character):
    character.do_one_time_task(routines.empty_farm)
    print(f"🏦 {character.surname} is going to the bank")


@_check_freshness
async def craft(character: Character, item: Item, quantity: int = 1):
    character.do_one_time_task(
        lambda character: routines.craft(character, item, quantity)
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
