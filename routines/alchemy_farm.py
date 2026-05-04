from models import Character


async def sunflower_farm(character: Character):
    _ = await character.move((2, 2))
    if character.is_inventory_full:
        _ = await character.deposit_all_in_bank()
    _ = await character.gather()
