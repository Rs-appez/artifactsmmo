#!.venv/bin/python
from models import Character
import routines
import asyncio


async def cli(characters: dict[str, Character]):
    loop = asyncio.get_event_loop()
    while True:
        command = await loop.run_in_executor(None, input, "> ")
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
                if characters[name].is_working:
                    print(f"❌ {name} is currently working, stop it first")
                    continue
                characters[name].refresh()
                _ = asyncio.create_task(
                    characters[name].deposit_all_in_bank(comeback=False)
                )
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


async def main():
    bob = Character("rs_bob")
    bob.assign_routine(routines.yellow_slime_farm)

    alice = Character("rs_alice")
    alice.assign_routine(routines.ash_farm)

    john = Character("rs_john")
    john.assign_routine(routines.copper_farm)

    jane = Character("rs_jane")
    jane.assign_routine(routines.gudgeon_farm)

    charlie = Character("rs_charlie")
    charlie.assign_routine(routines.sunflower_farm)

    characters = {
        "bob": bob,
        "alice": alice,
        "john": john,
        "jane": jane,
        "charlie": charlie,
    }
    _ = await asyncio.gather(
        bob.work(),
        alice.work(),
        john.work(),
        jane.work(),
        charlie.work(),
        cli(characters),
    )


if __name__ == "__main__":
    asyncio.run(main())
