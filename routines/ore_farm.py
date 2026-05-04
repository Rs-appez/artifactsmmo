from models import Character


async def copper_farm(character: Character):
    _ = await character.move((2, 0))
    if character.is_inventory_full:
        _ = await character.deposit_all_in_bank()
    _ = await character.gather()
