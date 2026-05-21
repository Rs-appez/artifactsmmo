from models import Character
from models.dataclass import Bank
from utils.find_nearest import find_nearest_tasks_master


async def exchange_task_coin(character: Character) -> None:

    async with Bank.

    task_master_pos = find_nearest_tasks_master(character)
    if not await character.move(task_master_pos):
        print("Failed to move to task master")
        return
