from models import Character, Item
from .craft import craft


async def craft_cooking(character: Character, item: Item, quantity: int):
    if item.job != "cooking":
        print(f"❌ {item.name} is not a fishing item")
        return
    if not character.has_job("cooking", item.craft_level):
        print(
            f"❌ {character.surname} does not have the required cooking level to craft {item.name}"
        )
        return
    _ = await craft(character, (1, 1), item, quantity)
