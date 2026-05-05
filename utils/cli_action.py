import asyncio

from models import Character
import routines


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


def stop_all(characters: list[Character]):
    for char in characters:
        char.stop()
    print("⏹ Stopped all characters")


def status(characters: list[Character]):
    for char in characters:
        print(
            f"{char.surname}: working={char.is_working} - task={char.work_on} - interrupted={char.is_interrupted} - position={char.location}"
        )
