from models.dataclass import NPC, Item


def find_best_npc(npcs: set[NPC], item: Item) -> NPC:

    for npc in npcs:
        # TODO : determine the best NPC based on price, distance, etc. For now, there is no case where there are multiple NPCs buying the same item, so we just take the first one.
        return npc

    raise ValueError(f"No NPC found buying {item.name}")
