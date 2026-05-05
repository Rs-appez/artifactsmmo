#!.venv/bin/python
import asyncio
import signal
import sys

import routines
from models import GameManager
from utils.cli import cli


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

    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(
        *[char.work() for char in characters.values()],
        cli(characters),
    )

    def shutdown():
        print("Shutting down gracefully...")
        _ = tasks.cancel()

    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    try:
        await tasks
    except asyncio.CancelledError:
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        print("Program terminated.")
        sys.exit(0)
