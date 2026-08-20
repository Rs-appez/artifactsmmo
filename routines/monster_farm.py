import asyncio
from itertools import count
from typing import TYPE_CHECKING

from exceptions import ImpossibleCombatException, NeedToRefreshStuffException
from models import Encyclopedia
from models.dataclass import Item, Monster
from routines import empty_farm
from utils.find_best import find_best_monster
from utils.find_nearest import find_nearest_lootable

if TYPE_CHECKING:
    from models.character import Character


async def mob_farm(
    character: Character,
    mob: Monster | str,
    nb: int | str = -1,
    force: bool | str = False,
):
    try:
        if isinstance(mob, str):
            mob = await Encyclopedia.get_monster_by_code(mob)

        if isinstance(nb, str):
            try:
                nb = int(nb)
            except ValueError:
                print(f"❌ Invalid number of iterations : {nb}")
                return

        if isinstance(force, str):
            force = force.lower() in ("true", "force", "f")

        await character.weaponize(mob)

        iterations = range(nb) if nb > 0 else count()
        for _ in iterations:
            await _fight(character, mob, force)

    except ImpossibleCombatException as e:
        raise e
    except Exception as e:
        print(f"❌ {character.surname} failed to combat : {e}")


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

        # await character.weaponize(boss)
        mob_position = await find_nearest_lootable(character, {boss})
        if character.is_inventory_full:
            for mate in teammate:
                mate.do_one_time_task(empty_farm)

        if character.hp < character.max_hp:
            _ = await __regenerate_hp(character, full=True)
        await character.move(mob_position)
        await character.set_ready_to_fight()
        if leader:
            while any(not mate.is_ready_to_fight_boss for mate in teammate):
                await asyncio.sleep(0.1)
            _ = await character.fight(teammate)
            for mate in teammate or []:
                if mate != character:
                    await mate.refresh()
                mate.is_ready_to_fight_boss = False
        else:
            await character.waiting_for_fight

    except Exception as e:
        print(f"❌ {character.surname} failed to combat boss : {e}")
    finally:
        character.is_ready_to_fight_boss = False


async def drop_on_mob_farm(character: Character, item: Item | str, nb: int | str = -1):
    if isinstance(item, str):
        get_item = await Encyclopedia.get_item_by_code(item)
        if not get_item:
            print(f"❌ {character.surname} Invalid item code : {item}")
            return
        else:
            item = get_item
    if isinstance(nb, str):
        try:
            nb = int(nb)
        except ValueError:
            print(f"❌ {character.surname} Invalid number of iterations : {nb}")
            return
    if not isinstance(item, Item):
        print(f"❌ {character.surname} Invalid item : {item}")
        return

    monster = await find_best_monster(character, item)
    await character.weaponize(monster)
    current_drop = 0
    while nb == -1 or nb > current_drop:
        fight_result = (await _fight(character, monster))["characters"]
        for char in fight_result:
            if char["character_name"] == character.name:
                for drops in char["drops"]:
                    if drops["code"] == item.code:
                        current_drop += drops["quantity"]
                        print(
                            f" {character.surname} found {item.name} on {monster.name} ({current_drop}/{nb if nb != -1 else '∞'})"
                        )
                        break
                break


async def _fight(character: Character, mob: Monster, force: bool = False) -> dict:

    mob_position = await find_nearest_lootable(character, {mob})
    has_moved = False

    if character.is_inventory_full:
        deposit_gold = True if character.gold > 10000 else False
        food = {item for item in character.inventory if item.is_food}
        await character.deposit_all_in_bank(
            with_gold=deposit_gold, items_to_ignore=food
        )
        has_moved = True

    if not character.will_win_against(mob, max_hp=False):
        if not character.will_win_against(mob, max_hp=True) and not force:
            raise ImpossibleCombatException(
                f"❌ {character.surname} will lose against {mob.name} even with full hp"
            )
        need_full_regeneration = not __can_win_with_eco_food(character, mob)
        has_moved = (
            await __regenerate_hp(character, full=need_full_regeneration) or has_moved
        )

    async with character.plan_move(mob_position) as plan:
        await plan.prepare()
        if has_moved:
            await character.weaponize(mob)
        await plan.execute_move()

    fight_result = await character.fight()

    return fight_result[1]


async def __regenerate_hp(character: Character, full: bool = False):
    # tmp return if has_moved -> to remove when bank will be cached
    has_moved = False
    try:
        if not character.has_food:
            has_moved = True
            await character.get_food_from_bank()

        await character.regenerate_hp(full=full)

        return has_moved
    except Exception:
        _ = await character.rest()
        print(f"󰻝  {character.surname} rests to recover hp before fighting")
        return False


def __can_win_with_eco_food(character: Character, mob: Monster) -> bool:
    food_regen = character.how_much_hp_can_regenerate()
    return character.will_win_against(mob, custom_hp=character.hp + food_regen)
