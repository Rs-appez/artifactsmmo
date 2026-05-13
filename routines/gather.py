from models import Character, Encyclopedia
from models.dataclass import Item, Resource
from utils.find_nearest import find_nearest_lootable


async def gather(character: Character, item: Item | str) -> None:
    if isinstance(item, str):
        item = await Encyclopedia.get_item_by_code(item)
    await character.toolize(item.job)
    if character.is_inventory_full:
        _ = await character.deposit_all_in_bank()
    resources = Resource.from_drop_item(item)
    resource_position = await find_nearest_lootable(character, resources)
    _ = await character.move(resource_position)
    _ = await character.gather()
