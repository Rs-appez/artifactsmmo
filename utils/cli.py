import asyncio
import sys

import routines
from models import Character


async def cli(characters: dict[str, Character]):
    loop = asyncio.get_event_loop()
    queue: asyncio.Queue[str] = asyncio.Queue()

    def on_stdin():
        line = sys.stdin.readline()
        if line:
            queue.put_nowait(line)
        else:
            _ = loop.remove_reader(sys.stdin.fileno())

    loop.add_reader(sys.stdin.fileno(), on_stdin)
    while True:
        command = await queue.get()
        parts = command.strip().lower().split()
        if not parts:
            continue
        action, *args = parts
        if action == "stop":
            if not args:
                print("Usage: stop <name>")
                continue
            name = args[0]
            if name in characters:
                characters[name].stop()
                print(f"⏹ Stopped {name}")
            else:
                print(f"❌ Unknown character: {name}")
        elif action == "start":
            if not args:
                print("Usage: start <name>")
                continue
            name = args[0]
            if name in characters:
                await characters[name].refresh()
                _ = asyncio.create_task(characters[name].work())
                print(f"▶️ Started {name}")
            else:
                print(f"❌ Unknown character: {name}")
        elif action == "gobank":
            if not args:
                print("Usage: gobank <name>")
                continue
            name = args[0]
            if name in characters:
                characters[name].do_one_time_task(routines.empty_farm)
                print(f"🏦 {name} is going to the bank")
            else:
                print(f"❌ Unknown character: {name}")
        elif action == "stopall":
            for char in characters.values():
                char.stop()
            print("⏹ Stopped all characters")
        elif action == "status":
            for name, char in characters.items():
                print(f"{name}: working={char.is_working}")
        else:
            print(f"❌ Unknown command: {action}")
