#!.venv/bin/python
import asyncio
import signal
import sys

from cli import cli
from config import LOCAL
from models import GameManager


async def main():
    manager = GameManager()

    loop = asyncio.get_event_loop()

    character_tasks = await manager.start()
    tasks = asyncio.gather(
        *character_tasks, cli(manager) if LOCAL else asyncio.sleep(0)
    )

    def shutdown():
        print("Shutting down gracefully...")
        _ = tasks.cancel()

    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    try:
        await tasks
    except asyncio.CancelledError:
        for character in manager.characters.values():
            character.save_routine()
        print("All character routines saved...")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        print("Program terminated.")
        sys.exit(0)
