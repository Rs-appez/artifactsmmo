from models import Character


async def chicken_farm(character: Character):
    if character.is_inventory_full:
        _ = await character.deposit_all_in_bank()
    _ = await character.move((0, 1))
    if character.hp < 40:
        _ = await character.rest()
    if not await character.fight():
        _ = await character.move((0, 1))
