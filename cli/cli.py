import asyncio
import inspect

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter, FuzzyCompleter
from prompt_toolkit.patch_stdout import patch_stdout

from models import Encyclopedia, GameManager
import routines
from . import cli_action

dict_single = {
    "stop": cli_action.stop,
    "resume": cli_action.resume,
    "gobank": cli_action.go_bank,
    "gotask": cli_action.complete_task,
    "exchange_coin": cli_action.exchange_task_coin,
}

dict_actions = {
    "craft": cli_action.craft,
    "gotask": cli_action.complete_task,
    "goroutine": cli_action.asign_routine,
    "gomission": cli_action.asign_mission,
}

dict_all = {
    "stopall": cli_action.stop_all,
    "status": cli_action.status,
}

dict_special = {
    "reserved_bank": cli_action.reserved_bank,
    "refresh_events": cli_action.refresh_events,
}


async def cli(game_manager: GameManager):
    characters = game_manager.characters
    character_names = {name: None for name in characters.keys()}

    routine_names = [
        name
        for name, obj in inspect.getmembers(routines)
        if inspect.isfunction(obj) and not name.startswith("_")
    ]
    # Initial completer without items
    completer_dict = {
        **{cmd: character_names for cmd in dict_single},
        **{"craft": {name: {} for name in characters.keys()}},
        **{
            "gotask": {
                name: {task: None for task in ["items", "monsters"]}
                for name in characters.keys()
            }
        },
        **{
            "goMission": {
                name: {routine: {} for routine in routine_names}
                for name in characters.keys()
            }
        },
        **{
            "goRoutine": {
                name: {routine: {} for routine in routine_names}
                for name in characters.keys()
            }
        },
        **{cmd: None for cmd in dict_all},
        **{cmd: None for cmd in dict_special},
    }

    completer = FuzzyCompleter(NestedCompleter.from_nested_dict(completer_dict))
    session: PromptSession = PromptSession("> ", completer=completer)

    # Load items in background
    async def load_items():
        updated_actions = {
            "craft": {
                name: {
                    item_code: None
                    for item_code in await Encyclopedia.get_all_items_names()
                }
                for name in characters.keys()
            },
            "goRoutine": {
                name: {
                    routine: (
                        {
                            monster: None
                            for monster in await Encyclopedia.get_all_items_names()
                        }
                        if routine == "gather"
                        else {
                            monster: None
                            for monster in await Encyclopedia.get_all_monsters_names()
                        }
                        if routine == "mob_farm"
                        else {}
                    )
                    for routine in routine_names
                }
                for name in characters.keys()
            },
            "goMission": {
                name: {
                    routine: (
                        {
                            monster: None
                            for monster in await Encyclopedia.get_all_items_names()
                        }
                        if routine == "gather"
                        else {
                            monster: None
                            for monster in await Encyclopedia.get_all_monsters_names()
                        }
                        if routine == "mob_farm"
                        else {}
                    )
                    for routine in routine_names
                }
                for name in characters.keys()
            },
        }
        completer_dict.update(updated_actions)
        session.completer = FuzzyCompleter(
            NestedCompleter.from_nested_dict(completer_dict)
        )

    _ = asyncio.create_task(load_items())

    with patch_stdout():
        try:
            while True:
                try:
                    command = await session.prompt_async()
                except EOFError, KeyboardInterrupt:
                    raise asyncio.CancelledError()

                parts = command.strip().lower().split()
                if not parts:
                    continue
                action, *args = parts

                if action in dict_special:
                    cmd = dict_special[action](game_manager)
                    if asyncio.iscoroutine(cmd):
                        await cmd
                    continue

                if action in dict_all:
                    cmd = dict_all[action](list(characters.values()))
                    if asyncio.iscoroutine(cmd):
                        await cmd
                    continue
                if len(args) < 1:
                    print(f"Usage: {action}")
                    continue

                name, *rests = args
                if not name:
                    print("Usage: action <name>")
                    continue

                character = characters.get(name)
                if not character:
                    print(f"❌ Unknown character: {name}")
                    continue

                if len(rests) > 0:
                    result = dict_actions.get(
                        action,
                        lambda char, *args: print(f"❌ Unknown command: {action}"),
                    )(character, *rests)

                    if asyncio.iscoroutine(result):
                        await result

                else:
                    result = dict_single.get(
                        action, lambda char: print(f"❌ Unknown command: {action}")
                    )(character)
                    if asyncio.iscoroutine(result):
                        await result
        except Exception as e:
            print(f"❌ {e}")
