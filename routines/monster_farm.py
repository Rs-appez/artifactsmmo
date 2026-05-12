from models import Character, Encyclopedia
from models.dataclass import Monster
from models.dataclass.bank import Bank
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
            await __regenerate_hp(character)
        _ = await character.move(mob_position)
        _ = await character.fight()

    except Exception as e:
        print(f"❌ {character.surname} {e}")
        if character.work_on == "mob_farm":
            character.stop()
        else:
            raise e


async def __regenerate_hp(character: Character):
    try:
        if not character.has_food:
            print(f"󰜎 {character.surname} will search for food in bank")
            qty = character.inventory_max_items // 2
            food_token = await Bank.get_food(character, qty)
            _ = await character.deposit_all_in_bank()
            if not character.withdraw_item_from_bank(food_token):
                print(f"❌ {character.surname} couldn't withdraw food from bank")
                return
        await character.regenerate_hp()
    except Exception as e:
        print(f"❌ {character.surname} {e}")
        _ = await character.rest()
        print(f"󰻝  {character.surname} rests to recover hp before fighting")
