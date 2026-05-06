import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.patch_stdout import patch_stdout

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
    character_names = {name: None for name in characters.keys()}

    # Initial completer without items
    completer_dict = {
        **{cmd: character_names for cmd in dict_routines},
        **{cmd: {name: {} for name in characters.keys()} for cmd in dict_actions},
        **{cmd: None for cmd in dict_routines_all},
    }

    completer = NestedCompleter.from_nested_dict(completer_dict)
    session: PromptSession = PromptSession("> ", completer=completer)

    # Load items in background
    async def load_items():
        await GameManager.wait_item()
        updated_actions = {
            cmd: {
                name: {item_code: None for item_code in GameManager.items}
                for name in characters.keys()
            }
            for cmd in dict_actions
        }
        completer_dict.update(updated_actions)
        session.completer = NestedCompleter.from_nested_dict(completer_dict)

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
