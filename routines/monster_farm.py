import asyncio
from itertools import count
from models import Character, Encyclopedia
from models.dataclass import Monster
from models.dataclass.bank import get_food
from utils.find_nearest import find_nearest_lootable
from routines import empty_farm


async def mob_farm(character: Character, mob: Monster | str, nb: int | str = -1):
    try:
        if isinstance(mob, str):
            mob = await Encyclopedia.get_monster_by_code(mob)

        if isinstance(nb, str):
            try:
                nb = int(nb)
            except ValueError:
                print(f"❌ Invalid number of iterations : {nb}")
                return

        await character.weaponize()
        iterations = range(nb) if nb > 0 else count()
        for _ in iterations:
            if character.is_inventory_full:
                _ = await character.deposit_all_in_bank()
            while not character.will_win_against(mob):
                await __regenerate_hp(character)
            mob_position = await find_nearest_lootable(character, {mob})
            _ = await character.move(mob_position)
            _ = await character.fight()

    except Exception as e:
        print(f"❌ {character.surname} {e}")


async def boss_farm(
    character: Character,
    teammate: list[Character],
    boss: str | Monster,
    leader: bool = False,
):
    # V1 missing a lot of check
    try:
        if isinstance(boss, str):
            boss = await Encyclopedia.get_monster_by_code(boss)

        await character.weaponize()
        mob_position = await find_nearest_lootable(character, {boss})
        if character.is_inventory_full:
            for mate in teammate:
                mate.do_one_time_task(empty_farm)

        if character.hp < 200:
            _ = await __regenerate_hp(character)
        _ = await character.move(mob_position)
        await character.set_ready_to_fight()
        if leader:
            while any(not mate.is_ready_to_fight_boss for mate in teammate):
                await asyncio.sleep(0.2)
            _ = await character.fight(teammate)
        else:
            await character.waiting_for_fight

    except Exception as e:
        print(f"❌ {character.surname} {e}")
    finally:
        character._ready_to_fight_boss = False  # pyright: ignore[reportPrivateUsage]


async def __regenerate_hp(character: Character):
    try:
        if not character.has_food:
            print(f"󰜎 {character.surname} will search for food in bank")
            qty = character.inventory_max_items // 2
            async with get_food(character, qty) as food_token:
                _ = await character.deposit_all_in_bank()
                if not await character.withdraw_item_from_bank(food_token):
                    print(f"❌ {character.surname} couldn't withdraw food from bank")
                    return
        await character.regenerate_hp()
    except Exception:
        _ = await character.rest()
        print(f"󰻝  {character.surname} rests to recover hp before fighting")
