import uuid
from models import Character, Encyclopedia
from models.dataclass import Item
from models.dataclass.bank import Bank
from utils.find_nearest import find_nearest_workshop
from math import ceil


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
    character: Character,
    workshop_location: tuple[int, int],
    bank_token: uuid.UUID,
    item: Item,
    quantity: int,
):
    _ = await character.deposit_all_in_bank(comeback=False)
    if not await character.withdraw_item_from_bank(bank_token):
        print(
            f"❌ {character.surname} failed to withdraw ingredients from bank for crafting {item.name}"
        )
        return
    if not await character.move(workshop_location):
        print(
            f"❌ {character.surname} failed to move to workshop for crafting {item.name}"
        )
        return
    if not await character.craft(item, quantity):
        print(f"❌ {character.surname} failed to craft {quantity}x {item.name}")
        return


async def craft(character: Character, item: Item, quantity: int):
    if not character.has_job(item.job, item.craft_level):
        print(
            f"❌ {character.surname} does not have the required {item.job} level to craft {item.name}",
            f" (needed: {item.craft_level} - current: {character.get_job_level(item.job)})",
        )
        return

    nearest_workshop = await find_nearest_workshop(character, item.job)

    ingredients = {
        await Encyclopedia.get_item_by_code(str(ingredient["code"])): int(
            ingredient["quantity"]
        )
        for ingredient in item.craft_ingredients
    }
    reserved_ingredients = {
        ingredient: qty * quantity for ingredient, qty in ingredients.items()
    }
    tokens: list[uuid.UUID] = []
    try:
        bank_token = await Bank.reserve_items(reserved_ingredients)
        tokens.append(bank_token)
    except Exception as e:
        print(
            f"❌ {character.surname} failed to reserve ingredients in bank for crafting {item.name} : {e}"
        )
        return

    try:
        (
            nb_trips,
            (nb_craft_per_trip, ingredients_for_trip),
            (
                nb_craft_last_trip,
                ingredients_for_last_trip,
            ),
        ) = await __get_trips_info(ingredients, quantity, character.inventory_max_items)
        print(
            f"⚒️ {character.surname} needs to make {nb_trips} trips to craft {quantity}x {item.name}"
        )

        for _ in range(nb_trips - 1):
            trip_token = Bank.get_reserved_items_partial(
                bank_token, ingredients_for_trip
            )
            tokens.append(trip_token)
            await __make_trip(
                character,
                nearest_workshop,
                trip_token,
                item,
                nb_craft_per_trip,
            )
        last_trip_token = Bank.get_reserved_items_partial(
            bank_token, ingredients_for_last_trip
        )
        tokens.append(last_trip_token)
        await __make_trip(
            character,
            nearest_workshop,
            last_trip_token,
            item,
            nb_craft_last_trip,
        )

        _ = await character.deposit_all_in_bank(comeback=False)

        print(f"⚒️ {character.surname} finished crafting {quantity}x {item.name}")
    except Exception as e:
        print(f"❌ {e}")
        return
    finally:
        for token in tokens:
            await Bank.unreserve_items(token)
