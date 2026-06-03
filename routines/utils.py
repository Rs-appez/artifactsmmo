from models import Character
from models.dataclass.bank import Bank


async def empty_farm(character: Character):
    _ = await character.deposit_all_in_bank(comeback=False)


async def generate_missing_items(character: Character, items: dict):
    from routines import craft, gather

    async with Bank.reserve_items(
        items, False, inventory=character.inventory
    ) as bank_token:
        need_to_generate = await Bank.get_missing_promise(bank_token)
        for missing_item, missing_quantity in need_to_generate.items():
            if missing_item.is_craftable:
                print(
                    f"󰢟 Not enough {missing_item.name} in bank for the task, need to craft {missing_quantity}x {missing_item.name}"
                )
                await craft(character, missing_item, missing_quantity)
            else:
                print(
                    f"󰢟 Not enough {missing_item.name} in bank for the task, need to gather {missing_quantity}x {missing_item.name}"
                )
                await gather(character, missing_item, missing_quantity)
