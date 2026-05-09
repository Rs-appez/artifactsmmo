#!.venv/bin/python
import asyncio
import signal
import sys

from models import Encyclopedia, GameManager
from cli import cli


async def main():
    manager = GameManager()

    loop = asyncio.get_event_loop()

    character_tasks = await manager.start()
    tasks = asyncio.gather(
        *character_tasks,
        cli(manager),
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
