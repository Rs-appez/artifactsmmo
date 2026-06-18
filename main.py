#!.venv/bin/python
import asyncio
import signal
import sys

from config import LOCAL
from models import GameManager


async def main():
    manager = GameManager()

    loop = asyncio.get_event_loop()

    character_tasks = await manager.start()
    tasks = list(character_tasks)

    if LOCAL:
        from cli import cli

        tasks.append(cli(manager))

    gathered = asyncio.gather(*tasks)

    def shutdown():
        print("Shutting down gracefully...")
        _ = gathered.cancel()

    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    try:
        await gathered
    except asyncio.CancelledError:
        manager.save_characters()
        print("All character routines saved...")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        print("Program terminated.")
        sys.exit(0)
