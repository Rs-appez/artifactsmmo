import uuid
from math import ceil
from typing import TYPE_CHECKING

from exceptions import NotEnoughInBankException
from models import Encyclopedia
from models.dataclass import Item, Map
from models.dataclass.bank import Bank
from routines import generate_missing_items
from utils.find_nearest import find_nearest_workshop

if TYPE_CHECKING:
    from models.character import Character


async def craft(
    character: "Character",
    item: Item,
    quantity: int,
    recycling_after: bool = False,
    recycling_pay_boost: bool = False,
):
    if not character.has_job(item.job, item.craft_level):
        print(
            f"❌ {character.surname} does not have the required {item.job} level to craft {item.name}",
            f" (needed: {item.craft_level} - current: {character.get_job_level(item.job)})",
        )
        return

    if not recycling_after:
        recycling_pay_boost = False

    nearest_workshop = await find_nearest_workshop(character, item.job)

    ingredients = {
        item_in_ing: int(ingredient["quantity"])
        for ingredient in item.craft_ingredients
        if (item_in_ing := await Encyclopedia.get_item_by_code(str(ingredient["code"])))
    }
    reserved_ingredients = {
        ingredient: qty * quantity for ingredient, qty in ingredients.items()
    }

    retry = True
    while retry:
        retry = False
        try:
            async with Bank.reserve_items(
                reserved_ingredients,
                inventory=character.inventory,
            ) as bank_token:
                if character.will_gain_xp_with(item):
                    wisdom = await Encyclopedia.get_effect_by_code("wisdom")
                    await character.maximaze_stats(wisdom)

                (
                    nb_trips,
                    (nb_craft_per_trip, ingredients_for_trip),
                    (
                        nb_craft_last_trip,
                        ingredients_for_last_trip,
                    ),
                ) = await __get_trips_info(
                    ingredients, quantity, character.inventory_max_items
                )
                print(
                    f"⚒️ {character.surname} needs to make {nb_trips} trips to craft {quantity}x {item.name}"
                )

                for _ in range(nb_trips - 1):
                    ingredients_to_withdraw = __get_withdraw_quantity_per_trip(
                        character, ingredients_for_trip
                    )
                    async with Bank.get_reserved_items_partial(
                        bank_token, ingredients_to_withdraw
                    ) as trip_token:
                        await __make_trip(
                            character,
                            nearest_workshop,
                            trip_token,
                            ingredients_for_trip,
                            item,
                            nb_craft_per_trip,
                            recycling_after,
                            recycling_pay_boost=recycling_pay_boost,
                        )
                ingredients_to_withdraw = __get_withdraw_quantity_per_trip(
                    character, ingredients_for_last_trip
                )
                async with Bank.get_reserved_items_partial(
                    bank_token, ingredients_to_withdraw
                ) as last_trip_token:
                    await __make_trip(
                        character,
                        nearest_workshop,
                        last_trip_token,
                        ingredients_for_last_trip,
                        item,
                        nb_craft_last_trip,
                        recycling_after,
                        recycling_pay_boost=recycling_pay_boost,
                    )

            print(f"⚒️ {character.surname} finished crafting {quantity}x {item.name}")
        except NotEnoughInBankException:
            await generate_missing_items(character, reserved_ingredients)
            retry = True

        except Exception as e:
            print(f"❌ {character.surname} failed to craft : {e}")
            return


async def __get_trips_info(
    ingredients: dict[Item, int],
    quantity: int,
    inventory_max_items: int,
) -> tuple[int, tuple[int, dict[Item, int]], tuple[int, dict[Item, int]]]:
    """
    Calculate the number of trips needed to craft the desired quantity of items, based on the ingredients required and the character's inventory capacity.
    Args:
        craft_ingredients (list[dict[str, str | int]]): A list of dictionaries representing the ingredients required for crafting, where each dictionary contains the "code" and "quantity" of the ingredient.
        quantity (int): The total quantity of the item to be crafted.
        inventory_max_items (int): The maximum number of items that the character can carry in their inventory.
    Returns:
        tuple[int, tuple[int, list[tuple[str, int]]], tuple[int, list[tuple[str, int]]]]: A tuple containing:
            - The total number of trips needed to craft the desired quantity of items.
            - A tuple with the number of items to craft per trip and a list of tuples representing the ingredients needed for each trip.
            - A tuple with the number of items to craft on the last trip and a list of tuples representing the ingredients needed for the last trip.
    Raises:
        Exception: If the number of ingredients required exceeds the character's inventory capacity, an exception is raised indicating that crafting is not possible.
    """

    nb_ingredients = sum(nb for nb in ingredients.values())
    nb_craft_per_trip = inventory_max_items // nb_ingredients
    if nb_craft_per_trip == 0:
        raise Exception(
            f"Cannot craft item, not enough inventory space for ingredients (needed: {nb_ingredients}, max: {inventory_max_items})"
        )
    nb_trips = ceil(quantity / nb_craft_per_trip)
    nb_craft_last_trip = quantity - (nb_trips - 1) * nb_craft_per_trip

    ingredients_per_trip = {
        item: nb_craft_per_trip * qty for item, qty in ingredients.items()
    }
    ingredients_last_trip = {
        item: nb_craft_last_trip * qty for item, qty in ingredients.items()
    }

    return (
        nb_trips,
        (nb_craft_per_trip, ingredients_per_trip),
        (nb_craft_last_trip, ingredients_last_trip),
    )


async def __make_trip(
    character: "Character",
    workshop_location: Map,
    bank_token: uuid.UUID,
    ingredients: dict[Item, int],
    item: Item,
    quantity: int,
    recycling_after: bool,
    recycling_pay_boost: bool,
):
    if character.need_deposit(bank_token):
        await character.deposit_all_in_bank(
            items_to_ignore=ingredients, with_gold=False
        )
    token_info = Bank.get_token_info(bank_token)
    if token_info and not await character.withdraw_item_from_bank(bank_token):
        print(
            f"❌ {character.surname} failed to withdraw ingredients from bank for crafting {item.name}"
        )
        return
    if recycling_pay_boost:
        enhanced_price = item.enhanced_recycling_price * quantity
        if character.gold < enhanced_price:
            await character.withdraw_gold_from_bank(enhanced_price - character.gold)

    await character.move(workshop_location)

    if not await character.craft(item, quantity):
        print(f"❌ {character.surname} failed to craft {quantity}x {item.name}")
        return

    if recycling_after and not await character.decraft(
        item, quantity, pay_boost=recycling_pay_boost
    ):
        print(f"❌ {character.surname} failed to decraft {quantity}x {item.name}")
        return


def __get_withdraw_quantity_per_trip(
    character: Character, ingredients: dict[Item, int]
) -> dict[Item, int]:

    ingredients_to_withdraw = {}
    for ingredient, quantity in ingredients.items():
        in_inventory = character.inventory.get(ingredient, 0)
        if in_inventory < quantity:
            ingredients_to_withdraw[ingredient] = quantity - in_inventory

    return ingredients_to_withdraw
