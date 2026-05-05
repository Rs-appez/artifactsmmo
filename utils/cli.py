import asyncio
import sys

from models import Character
from .cli_action import stop, start, stop_all, go_bank

dict_routines = {
    "stop": stop,
    "start": start,
    "gobank": go_bank,
}

dict_routines_all = {
    "stopall": stop_all,
}


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

        if action in dict_routines_all:
            dict_routines_all[action](characters.values())
            continue
        if len(args) < 1:
            print(f"Usage: {action} <name>")
            continue

        name, *rests = args
        if not name:
            print("Usage: stop <name>")
            continue

        character = characters.get(name)
        if not character:
            print(f"❌ Unknown character: {name}")
            continue

        result = dict_routines.get(
            action, lambda char: print(f"❌ Unknown command: {action}")
        )(character)
        if asyncio.iscoroutine(result):
            await result
