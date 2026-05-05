#!.venv/bin/python
from models import Character, GameManager
from utils.cli import cli
import routines
import asyncio


async def main():
    default_tasks = {
        "bob": routines.yellow_slime_farm,
        "alice": routines.spruce_farm,
        "john": routines.iron_farm,
        "jane": routines.shrimp_farm,
        "charlie": routines.sunflower_farm,
    }
    manager = GameManager()
    characters = manager.characters

    for char_name, character in characters.items():
        if char_name in default_tasks:
            character.assign_routine(default_tasks[char_name])
        else:
            print(f"No default task found for {char_name}, skipping task assignment.")

    _ = await asyncio.gather(
        *[char.work() for char in characters.values()],
        cli(characters),
    )


if __name__ == "__main__":
    asyncio.run(main())
