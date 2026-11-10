from typing import TYPE_CHECKING

from models import Encyclopedia
from models.dataclass import Item
from models.enums import JobType
from routines import craft, gather

if TYPE_CHECKING:
    from models.character import Character


async def make_food(
    character: Character, food: Item | str | None = None, nb: int | str = -1
):
    try:
        smart_food = False
        if not food:
            food = await _find_best_food_to_make(character)
            smart_food = True
        if isinstance(food, str):
            food = await Encyclopedia.get_item_by_code(food)
        if not food.is_food:
            raise ValueError(f"❌ {food.name} is not a food item.")

        if isinstance(nb, str):
            try:
                nb = int(nb)
            except ValueError:
                print(f"❌ {character.surname} Invalid number of iterations : {nb}")
                return

        print(f"🍳 {character.surname} is making {food.name}...")

        counter = 0
        while counter < nb or nb == -1:
            counter += 1
            food = await _find_best_food_to_make(character) if smart_food else food
            ingredient = await _get_ingredient_for_food(food)
            if ingredient.is_gatherable_resource:
                await _gather_and_make_food(character, food, ingredient)
            elif ingredient.is_dropable_resource:
                raise NotImplementedError(
                    f"❌ {ingredient.name} is a dropable resource. This feature is not implemented yet."
                )
            else:
                raise ValueError(
                    f"❌ {ingredient.name} is neither a gatherable nor a dropable resource."
                )
    except Exception as e:
        print(f"❌ {character.surname} failed to make food : {e}")


async def _gather_and_make_food(character: Character, food: Item, ingredient: Item):

    while not character.is_inventory_full:
        await gather(character, ingredient, 1)

    nb_ingredient_in_inventory = character.inventory.get(ingredient, 0)
    if nb_ingredient_in_inventory > 0:
        await craft(character, food, nb_ingredient_in_inventory)

    await character.deposit_all_in_bank()


async def _get_ingredient_for_food(food: Item) -> Item:
    if len(food.craft_ingredients) != 1:
        raise ValueError(
            f"❌ {food.name} has more than one ingredient. This feature only supports food items with a single ingredient."
        )
    ingredient_code = str(food.craft_ingredients[0]["code"])
    return await Encyclopedia.get_item_by_code(ingredient_code)


async def _find_best_food_to_make(character: Character) -> Item:
    fishing_level = character.get_job_level(JobType.FISHING)
    cooking_level = character.get_job_level(JobType.COOKING)
    target_level = min(fishing_level, cooking_level)

    return max(
        [
            food
            for food in await Encyclopedia.get_all_food()
            if food.craft_level <= target_level
            and len(food.craft_ingredients) == 1
            and (
                await Encyclopedia.get_item_by_code(
                    str(food.craft_ingredients[0]["code"])
                )
            ).job
            == JobType.FISHING
        ],
        key=lambda food: food.craft_level,
    )
