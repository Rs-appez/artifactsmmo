import asyncio
import inspect

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import (
    Completer,
    Completion,
    FuzzyCompleter,
    NestedCompleter,
)
from prompt_toolkit.document import Document
from prompt_toolkit.patch_stdout import patch_stdout

import routines
from models import Encyclopedia, GameManager
from models.enums import JobType, TaskType

from . import cli_action

dict_single = {
    "stop": cli_action.stop,
    "resume": cli_action.resume,
    "gobank": cli_action.go_bank,
    "exchange_coin": cli_action.exchange_task_coin,
    "bagize": cli_action.bagize,
}

dict_actions = {
    "craft": cli_action.craft,
    "goroutine": cli_action.asign_routine,
    "gomission": cli_action.asign_mission,
    "nbcraft": cli_action.nb_craft_needed_calculator,
    "move": cli_action.move_to,
    "sell": cli_action.sell_to_ge,
}

dict_all = {
    "stopall": cli_action.stop_all,
    "ls": cli_action.status,
}

dict_special = {
    "reserved_bank": cli_action.reserved_bank,
    "refresh_bank": cli_action.refresh_bank,
    "refresh_events": cli_action.refresh_events,
}


async def cli(game_manager: GameManager):
    characters = game_manager.characters

    routine_names = [
        name
        for name, obj in inspect.getmembers(routines)
        if inspect.isfunction(obj) and not name.startswith("_")
    ]

    def per_character(value_factory):
        return {name: value_factory() for name in characters}

    def names_completion(names):
        return {name: None for name in names}

    def routine_completion(routine_args=None, overrides=None):
        routine_args = routine_args or {}
        overrides = overrides or {}
        return {
            routine: overrides.get(routine)
            or names_completion(routine_args.get(routine, []))
            for routine in routine_names
        }

    def build_completer_dict(items=None, routine_args=None):
        items = items or {}
        routine_args = routine_args or {}

        item_completer = NestedCompleter.from_nested_dict(
            names_completion(items.get("all", []))
        )
        xp_skill_completion = {
            skill: NumberThenCompleter(item_completer)
            for skill in routine_args.get("xp_skill", [])
        }
        routine_overrides = {"xp_skill": xp_skill_completion}
        item_commands = {
            "craft": "craft",
            "nbCraft": "craft",
            "sell": "all",
        }
        return {
            **{cmd: per_character(lambda: None) for cmd in dict_single},
            **{
                cmd: per_character(
                    lambda t=item_type: names_completion(items.get(t, []))
                )
                for cmd, item_type in item_commands.items()
            },
            "move": per_character(lambda: None),
            "goMission": per_character(
                lambda: routine_completion(routine_args, routine_overrides)
            ),
            "goRoutine": per_character(
                lambda: routine_completion(routine_args, routine_overrides)
            ),
            **{cmd: None for cmd in (*dict_all, *dict_special)},
        }

    def make_completer(completer_dict):
        return FuzzyCompleter(NestedCompleter.from_nested_dict(completer_dict))

    session: PromptSession = PromptSession(
        "> ", completer=make_completer(build_completer_dict())
    )

    # Load items in background
    async def load_items():
        items = {
            "all": await Encyclopedia.get_all_items_names(),
            "craft": await Encyclopedia.get_all_craftable_items_names(),
        }
        routine_args = {
            "gather": await Encyclopedia.get_all_gatherable_items_names(),
            "mob_farm": await Encyclopedia.get_all_monsters_names(),
            "make_food": await Encyclopedia.get_all_food_names(),
            "complete_task": [task_type.value for task_type in TaskType],
            "xp_skill": [skill.value for skill in JobType.character_job_types()],
        }
        session.completer = make_completer(build_completer_dict(items, routine_args))

    _ = asyncio.create_task(load_items())

    with patch_stdout():
        while True:
            try:
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
                print(f"❌ cli error : {e}")


class NumberThenCompleter(Completer):
    """Accepts any integer as the next token, then delegates to `inner`."""

    def __init__(self, inner: Completer, hints=(str(i * 5) for i in range(1, 1))):
        self.inner = inner
        self.hints = hints

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lstrip()
        first, sep, rest = text.partition(" ")
        if not sep:
            # Still typing the number: suggest a few common values
            for hint in self.hints:
                if hint.startswith(first):
                    yield Completion(hint, start_position=-len(first))
            return
        if first.isdigit():
            yield from self.inner.get_completions(Document(rest), complete_event)
