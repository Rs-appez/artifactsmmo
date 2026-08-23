from itertools import count
from typing import TYPE_CHECKING

from models import Encyclopedia
from models.dataclass import Item, Resource
from utils.find_nearest import find_nearest_lootable

if TYPE_CHECKING:
    from models.character import Character


async def gather(character: Character, item: Item | str, nb: int | str = -1) -> None:
    try:
        if isinstance(item, str):
            get_item = await Encyclopedia.get_item_by_code(item)
            if not get_item:
                print(f"❌ {character.surname} Invalid item code : {item}")
                return
            else:
                item = get_item
        if isinstance(nb, str):
            try:
                nb = int(nb)
            except ValueError:
                print(f"❌ {character.surname} Invalid number of iterations : {nb}")
                return
        if not isinstance(item, Item):
            print(f"❌ {character.surname} Invalid item : {item}")
            return

        await _get_ready_to_gather(character, item)

        iterations = range(nb) if nb > 0 else count()
        for _ in iterations:
            if character.is_inventory_full:
                await character.deposit_all_in_bank()
            resources = Resource.from_drop_item(item)
            resource_position = await find_nearest_lootable(character, set(resources))
            async with character.plan_move(resource_position) as plan:
                await plan.prepare()
                await _get_ready_to_gather(character, item)
                await plan.execute_move()
            if not await character.gather():
                raise Exception(f"Failed to gather {item.name}")

    except Exception as e:
        print(f"❌ {character.surname} failed to gather : {e}")


async def _get_ready_to_gather(character: Character, item: Item) -> None:
    await character.toolize(item.job)

    if character.will_gain_xp_with(item):
        wisdom = await Encyclopedia.get_effect_by_code("wisdom")
        await character.maximaze_stats(wisdom)
    elif item.job.has_drop:
        prospection = await Encyclopedia.get_effect_by_code("prospecting")
        await character.maximaze_stats(prospection)
