from models import Character, Encyclopedia
from models.dataclass import Monster
from utils.find_nearest import find_nearest_mob
from collections import defaultdict


threshold_dict = defaultdict(int)


async def mob_farm(character: Character, mob: Monster | str):
    try:
        if isinstance(mob, str):
            mob = await Encyclopedia.get_monster_by_code(mob)

        mob_position = find_nearest_mob(character.location, mob)
        if character.is_inventory_full:
            _ = await character.deposit_all_in_bank()
        _ = await character.move(mob_position)
        mob_threshold = threshold_dict[mob]
        if mob_threshold == 0 or character.hp < mob_threshold:
            _ = await character.rest()
        _ = await character.fight()
        threshold_dict[mob] = max(threshold_dict[mob], character.last_damage_taken)
    except Exception as e:
        print(f"❌ {character.surname} {e}")
