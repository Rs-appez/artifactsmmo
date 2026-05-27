from itertools import count
from models import Character, Encyclopedia
from models.dataclass import Item, Resource
from utils.find_nearest import find_nearest_lootable


async def gather(character: Character, item: Item | str, nb: int = -1) -> None:
    if isinstance(item, str):
        item = await Encyclopedia.get_item_by_code(item)
    await character.toolize(item.job)

    iterations = range(nb) if nb > 0 else count()
    for _ in iterations:
        if character.is_inventory_full:
            _ = await character.deposit_all_in_bank()
        resources = Resource.from_drop_item(item)
        resource_position = await find_nearest_lootable(character, set(resources))
        if not await character.move(resource_position):
            print(f"❌ {character.surname} Failed to move to {resource_position.name}")
            return
        if not await character.gather():
            print(f"❌ {character.surname} Failed to gather {item.name}")
            return
