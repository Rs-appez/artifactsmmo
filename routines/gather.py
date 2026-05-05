from models import Character


async def gather(character: Character, resource_position: tuple[int, int]):
    if character.is_inventory_full:
        _ = await character.deposit_all_in_bank()
    _ = await character.move(resource_position)
    _ = await character.gather()
