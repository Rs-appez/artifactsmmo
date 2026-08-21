#!.venv/bin/python
import asyncio
import signal
import sys

from config import CLI
from models import GameManager


async def main(first_run=False):
    manager = GameManager()

    if first_run:
        await manager.create_characters()

    loop = asyncio.get_event_loop()

    character_tasks = await manager.start()
    tasks = list(character_tasks)

    if CLI:
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
    args = sys.argv[1:]
    try:
        if args and args[0] == "new":
            asyncio.run(main(first_run=True))
        else:
            asyncio.run(main())
    except asyncio.CancelledError:
        print("Program terminated.")
        sys.exit(0)
