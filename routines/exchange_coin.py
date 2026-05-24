from models import Character, Encyclopedia
from models.dataclass.bank import get_max_items
from utils.find_nearest import find_nearest_tasks_master


async def exchange_task_coin(character: Character) -> None:

    task_coin = await Encyclopedia.get_item_by_code("tasks_coin")
    task_master_pos = await find_nearest_tasks_master(character)

    try:
        while True:
            async with get_max_items(character, task_coin, 2, 6) as (
                token,
                token_quantity,
            ):
                if token_quantity < 6:
                    print("No more task coin in bank")
                    break
                await character.deposit_all_in_bank(with_gold=False)
                if not await character.withdraw_item_from_bank(token):
                    print("Failed to withdraw task coin from bank")
                    return
                if not await character.move(task_master_pos):
                    print("Failed to move to task master")
                while await character.exchange_task_coin():
                    pass
        print(f"🪙 {character.surname} has finished exchanging task coin")
    except Exception as e:
        print(f"❌ {character.surname} failed to exchange task coin : {e}")
