import asyncio

from models import Character, Item
import routines
from utils import find_craft_routine


def stop(character: Character):
    character.stop()
    print(f"⏹ Stopped {character.surname}")


async def start(character: Character):
    await character.refresh()
    _ = asyncio.create_task(character.work())
    print(f"▶️ Started {character.surname}")


def go_bank(character: Character):
    character.do_one_time_task(routines.empty_farm)
    print(f"🏦 {character.surname} is going to the bank")


def craft(character: Character, item: Item, quantity: int = 1):
    if routine := find_craft_routine(item):
        character.do_one_time_task(lambda character: routine(character, item, quantity))
        print(f"⚒️ {character.surname} will craft {quantity}x {item.name}")

    else:
        print(f"❌ No crafting routine found for {item.name}")


def stop_all(characters: list[Character]):
    for char in characters:
        char.stop()
    print("⏹ Stopped all characters")


def status(characters: list[Character]):
    for char in characters:
        print(
            f"{char.surname}: working={char.is_working} - task={char.work_on} - interrupted={char.is_interrupted} - position={char.location}"
        )
