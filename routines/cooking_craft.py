from models import Character, Item
from .craft import craft


async def craft_cooking(character: Character, item: Item, quantity: int):
    if item.job != "cooking":
        print(f"❌ {item.name} is not a fishing item")
        return
    _ = await craft(character, (1, 1), item, quantity)
