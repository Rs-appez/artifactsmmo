from models import Character


async def gudgeon_farm(character: Character):
    if character.is_inventory_full:
        _ = await character.deposit_all_in_bank()
    _ = await character.move((4, 2))
    _ = await character.gather()
