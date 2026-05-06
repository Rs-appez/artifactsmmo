import asyncio
import sys

from models import GameManager
from . import cli_action

dict_routines = {
    "stop": cli_action.stop,
    "start": cli_action.start,
    "gobank": cli_action.go_bank,
}

dict_actions = {
    "craft": cli_action.craft,
}

dict_routines_all = {
    "stopall": cli_action.stop_all,
    "status": cli_action.status,
}


async def cli(game_manager: GameManager):
    characters = game_manager.characters
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
            dict_routines_all[action](list(characters.values()))
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

        if len(rests) > 0:
            item, *quantity = rests
            if not quantity:
                quantity = 1
            else:
                quantity = int(quantity[0])

            try:
                itemObject = await GameManager.get_item_by_code(item)
            except Exception as e:
                print(f"❌ {e}")
                continue

            dict_actions.get(
                action, lambda char, it, qty: print(f"❌ Unknown command: {action}")
            )(character, itemObject, quantity)

        else:
            result = dict_routines.get(
                action, lambda char: print(f"❌ Unknown command: {action}")
            )(character)
            if asyncio.iscoroutine(result):
                await result
