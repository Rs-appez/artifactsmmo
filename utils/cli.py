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
