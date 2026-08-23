from typing import TYPE_CHECKING

from models import Encyclopedia
from models.dataclass import Item
from routines import craft, gather

if TYPE_CHECKING:
    from models.character import Character


async def make_food(character: "Character", food: Item | str):
    try:
        if isinstance(food, str):
            food = await Encyclopedia.get_item_by_code(food)
        if not food.is_food:
            raise ValueError(f"❌ {food.name} is not a food item.")

        if len(food.craft_ingredients) != 1:
            raise ValueError(
                f"❌ {food.name} has more than one ingredient. This feature only supports food items with a single ingredient."
            )

        print(f"🍳 {character.surname} is making {food.name}...")
        ingredient_code = str(food.craft_ingredients[0]["code"])
        ingredient = await Encyclopedia.get_item_by_code(ingredient_code)

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


async def _gather_and_make_food(character: "Character", food: Item, ingredient: Item):

    while True:
        while not character.is_inventory_full:
            await gather(character, ingredient, 1)

        nb_ingredient_in_inventory = character.inventory.get(ingredient, 0)
        if nb_ingredient_in_inventory > 0:
            await craft(character, food, nb_ingredient_in_inventory)

        await character.deposit_all_in_bank()
