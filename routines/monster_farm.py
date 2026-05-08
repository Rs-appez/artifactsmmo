from models import Character, Encyclopedia
from models.dataclass import Monster
from utils.find_nearest import find_nearest_mob


async def mob_farm(character: Character, mob: Monster | str, hp_threshold: int = 150):
    try:
        if isinstance(mob, str):
            mob = await Encyclopedia.get_monster_by_code(mob)

        mob_position = find_nearest_mob(character.location, mob)
        if character.is_inventory_full:
            _ = await character.deposit_all_in_bank()
        _ = await character.move(mob_position)
        if character.hp < hp_threshold:
            _ = await character.rest()
        _ = await character.fight()
    except Exception as e:
        print(f"❌ {character.surname} {e}")


#
# async def chicken_farm(character: Character):
#     await __mob_farm(character, (0, 1), 40)
#
#
# async def sheep_farm(character: Character):
#     await __mob_farm(character, (5, 12), 100)
#
#
# async def cow_farm(character: Character):
#     await __mob_farm(character, (0, 2), 250)
#
#
# async def yellow_slime_farm(character: Character):
#     await __mob_farm(character, (4, -1), 70)
#
#
# async def green_slime_farm(character: Character):
#     await __mob_farm(character, (3, -2), 85)
#
#
# async def blue_slime_farm(character: Character):
#     await __mob_farm(character, (2, -1), 110)
#
#
# async def red_slime_farm(character: Character):
#     await __mob_farm(character, (1, -1), 120)
#
#
# async def mushroom_farm(character: Character):
#     await __mob_farm(character, (5, 3), 100)
