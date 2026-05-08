import asyncio

from fuzzywuzzy import process  # pyright: ignore[reportMissingTypeStubs]
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter, FuzzyCompleter
from prompt_toolkit.patch_stdout import patch_stdout

from models import Encyclopedia, GameManager
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


async def fuzzy_find_item(item_code: str, threshold: int = 80):
    """Fuzzy search for item by code. Returns best match or raises Exception."""
    if item_code in Encyclopedia.items:
        return await Encyclopedia.get_item_by_code(item_code)

    matches = process.extract(item_code, Encyclopedia.items.keys(), limit=1)
    if matches and matches[0][1] >= threshold:
        return await Encyclopedia.get_item_by_code(matches[0][0])

    raise Exception(f"Item '{item_code}' not found (no close matches)")


async def cli(game_manager: GameManager):
    characters = game_manager.characters
    character_names = {name: None for name in characters.keys()}

    # Initial completer without items
    completer_dict = {
        **{cmd: character_names for cmd in dict_routines},
        **{cmd: {name: {} for name in characters.keys()} for cmd in dict_actions},
        **{cmd: None for cmd in dict_routines_all},
    }

    completer = FuzzyCompleter(NestedCompleter.from_nested_dict(completer_dict))
    session: PromptSession = PromptSession("> ", completer=completer)

    # Load items in background
    async def load_items():
        await Encyclopedia.wait_item()
        updated_actions = {
            cmd: {
                name: {item_code: None for item_code in Encyclopedia.items}
                for name in characters.keys()
            }
            for cmd in dict_actions
        }
        completer_dict.update(updated_actions)
        session.completer = FuzzyCompleter(
            NestedCompleter.from_nested_dict(completer_dict)
        )

    _ = asyncio.create_task(load_items())

    with patch_stdout():
        while True:
            try:
                command = await session.prompt_async()
            except EOFError, KeyboardInterrupt:
                raise asyncio.CancelledError()

            parts = command.strip().lower().split()
            if not parts:
                continue
            action, *args = parts

            if action in dict_routines_all:
                cmd = dict_routines_all[action](list(characters.values()))
                if asyncio.iscoroutine(cmd):
                    await cmd
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
                    itemObject = await fuzzy_find_item(item)
                except Exception as e:
                    print(f"❌ {e}")
                    continue

                result = dict_actions.get(
                    action, lambda char, it, qty: print(f"❌ Unknown command: {action}")
                )(character, itemObject, quantity)

                if asyncio.iscoroutine(result):
                    await result

            else:
                result = dict_routines.get(
                    action, lambda char: print(f"❌ Unknown command: {action}")
                )(character)
                if asyncio.iscoroutine(result):
                    await result
