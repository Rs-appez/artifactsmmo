from exceptions import DontHaveLevelException
from models import Character
from models.dataclass.bank import Bank


async def empty_farm(character: Character):
    _ = await character.deposit_all_in_bank(comeback=False)


async def generate_missing_items(character: Character, items: dict):
    from routines import craft, gather, buy_from_npc

    async with Bank.reserve_items(
        items, False, inventory=character.inventory
    ) as bank_token:
        need_to_generate = await Bank.get_missing_promise(bank_token)
        for missing_item, missing_quantity in need_to_generate.items():
            if missing_item.is_dropable_resource:
                # TODO : implement mob farming when auto stuff implemented
                raise Exception("Not implemented yet")
                print(
                    f"󰢟 Not enough {missing_item.name} in bank for the task, need to farm {missing_quantity}x {missing_item.name}"
                )
                await mob_farm(character, missing_item, missing_quantity)

            elif missing_item.is_npc_resource:
                print(
                    f"󰢟 Not enough {missing_item.name} in bank for the task, need to buy {missing_quantity}x {missing_item.name} from npc"
                )
                await buy_from_npc(character, missing_item, missing_quantity)

            elif not character.can_genenerate(missing_item):
                raise DontHaveLevelException(
                    f"󰢟 Cannot generate {missing_item.name}, current job level {character.get_job_level(missing_item.job)}"
                )

            elif missing_item.is_craftable:
                print(
                    f"󰢟 Not enough {missing_item.name} in bank for the task, need to craft {missing_quantity}x {missing_item.name}"
                )
                await craft(character, missing_item, missing_quantity)

            elif missing_item.is_gatherable_resource:
                print(
                    f"󰢟 Not enough {missing_item.name} in bank for the task, need to gather {missing_quantity}x {missing_item.name}"
                )
                await gather(character, missing_item, missing_quantity)

            else:
                raise Exception(f"Don't know how to generate {missing_item.name}")
