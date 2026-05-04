from models import Character


async def ash_farm(character: Character):
    if character.is_inventory_full:
        _ = await character.deposit_all_in_bank()
    _ = await character.move((6, 1))
    _ = await character.gather()
