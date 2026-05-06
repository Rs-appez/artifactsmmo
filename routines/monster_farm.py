from models import Character


async def __mob_farm(character: Character, mob_position: tuple, hp_threshold: int):
    if character.is_inventory_full:
        _ = await character.deposit_all_in_bank()
    _ = await character.move(mob_position)
    if character.hp < hp_threshold:
        _ = await character.rest()
    _ = await character.fight()


async def chicken_farm(character: Character):
    await __mob_farm(character, (0, 1), 40)


async def sheep_farm(character: Character):
    await __mob_farm(character, (5, 12), 100)


async def yellow_slime_farm(character: Character):
    await __mob_farm(character, (4, -1), 70)


async def green_slime_farm(character: Character):
    await __mob_farm(character, (3, -2), 85)


async def blue_slime_farm(character: Character):
    await __mob_farm(character, (2, -1), 100)


async def red_slime_farm(character: Character):
    await __mob_farm(character, (1, -1), 105)


async def mushroom_farm(character: Character):
    await __mob_farm(character, (5, 3), 100)
