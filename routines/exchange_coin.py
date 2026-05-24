from models import Character, Encyclopedia
from models.dataclass.bank import get_max_items
from utils.find_nearest import find_nearest_tasks_master


async def exchange_task_coin(character: Character) -> None:

    task_coin = await Encyclopedia.get_item_by_code("task_coin")
    task_master_pos = await find_nearest_tasks_master(character)

    while True:
        async with get_max_items(character, task_coin) as (token, token_quantity):
            if token_quantity < 6:
                print("No more task coin in bank")
                break
            if not await character.deposit_all_in_bank(with_gold=False):
                print("Failed to deposit task coin in bank")
                return
            if not await character.withdraw_item_from_bank(token):
                print("Failed to withdraw task coin from bank")
                return
            if not await character.move(task_master_pos):
                print("Failed to move to task master")
            while await character.exchange_task_coin():
                pass
            return
