from models import Character, Encyclopedia
from models.dataclass import Monster
from utils.find_nearest import find_nearest_mob


async def mob_farm(character: Character, mob: Monster | str):
    try:
        if isinstance(mob, str):
            mob = await Encyclopedia.get_monster_by_code(mob)

        await character.weaponize()
        mob_position = find_nearest_mob(character.location, mob)
        if character.is_inventory_full:
            _ = await character.deposit_all_in_bank()
        if not character.will_win_against(mob):
            _ = await character.rest()
            print(
                f"󰻝  {character.surname} rests to recover hp before fighting {mob.name}"
            )
        _ = await character.move(mob_position)
        _ = await character.fight()

    except Exception as e:
        print(f"❌ {character.surname} {e}")
        if character.work_on == "mob_farm":
            character.stop()
        else:
            raise e
