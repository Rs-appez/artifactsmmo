from itertools import count
from models import Character, Encyclopedia
from models.dataclass import Item, Resource
from utils.find_nearest import find_nearest_lootable


async def gather(character: Character, item: Item | str, nb: int | str = -1) -> None:
    try:
        if isinstance(item, str):
            item = await Encyclopedia.get_item_by_code(item)
        if isinstance(nb, str):
            try:
                nb = int(nb)
            except ValueError:
                print(f"❌ Invalid number of iterations : {nb}")
                return
        await character.toolize(item.job)

        if character.will_gain_xp_with(item):
            wisdom = await Encyclopedia.get_effect_by_code("wisdom")
            await character.maximaze_stats(wisdom)

        iterations = range(nb) if nb > 0 else count()
        for _ in iterations:
            if character.is_inventory_full:
                _ = await character.deposit_all_in_bank()
            resources = Resource.from_drop_item(item)
            resource_position = await find_nearest_lootable(character, set(resources))
            if not await character.move(resource_position):
                raise Exception(f"Failed to move to {resource_position.name}")
            if not await character.gather():
                raise Exception(f"Failed to gather {item.name}")
    except Exception as e:
        print(f"❌ {character.surname} {e}")
