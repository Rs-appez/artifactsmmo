import routines
from models import Character
from models.dataclass import Item


def check_freshness(function):
    async def wrapper(character: Character, *args, **kwargs):
        if not character.is_working and not await character.refresh():
            print(f"❌ Failed to refresh {character.surname}")
            return
        return await function(character, *args, **kwargs)

    return wrapper


def stop(character: Character):
    character.stop()
    print(f"⏹ Stopped {character.surname}")


@check_freshness
async def start(character: Character):
    await character.resume()
    print(f"▶️ Started {character.surname}")


@check_freshness
def go_bank(character: Character):
    character.do_one_time_task(routines.empty_farm)
    print(f"🏦 {character.surname} is going to the bank")


@check_freshness
def craft(character: Character, item: Item, quantity: int = 1):
    character.do_one_time_task(
        lambda character: routines.craft(character, item, quantity)
    )
    print(f"⚒️ {character.surname} will craft {quantity}x {item.name}")


def stop_all(characters: list[Character]):
    for char in characters:
        char.stop()
    print("⏹ Stopped all characters")


@check_freshness
def status(characters: list[Character]):
    for char in characters:
        print(char)
