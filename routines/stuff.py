from models import Character
from models.dataclass import Item
from models.dataclass.bank import Bank
from models.dataclass.bank.get_in_bank import _reserve_unequipped_items


async def stuff(character: Character, equipment: dict[Item, int]):
    async with Bank.locked():
        token = await _reserve_unequipped_items(character, equipment)

    if len(Bank.get_token_info(token)) != 0:
        await character.deposit_all_in_bank(items_to_ignore=equipment, with_gold=False)

        await character.withdraw_item_from_bank(token)
