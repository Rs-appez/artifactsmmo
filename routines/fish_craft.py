from models import Character, Item
from .craft import craft


async def craft_fish(character: Character, item: Item, quantity: int):
    if item.job != "fishing":
        raise ValueError("Item must be a fishing item.")
    _ = await craft(character, (1, 1), item, quantity)
