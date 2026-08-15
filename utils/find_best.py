from typing import TYPE_CHECKING

from models import Encyclopedia, LocationRegistry
from models.dataclass import NPC, Item, Monster

if TYPE_CHECKING:
    from models.character import Character


def find_best_npc(npcs: set[NPC], item: Item) -> NPC:

    for npc in npcs:
        # TODO : determine the best NPC based on price, distance, etc. For now, there is no case where there are multiple NPCs buying the same item, so we just take the first one.
        return npc

    raise ValueError(f"No NPC found buying {item.name}")


async def find_best_monster(character: Character, item: Item) -> Monster:

    monsters = sorted(
        [
            m
            for m in await Encyclopedia.get_monsters_by_drop(item)
            if await LocationRegistry.get_locations(m)
        ],
        key=lambda m: m.drop_rate(item),
        reverse=True,
    )

    if not monsters:
        raise ValueError(
            f"No monster found dropping {item.name} that {character.surname} can defeat"
        )

    return monsters[0]
