from models import Character, Item
from utils.find_nearest import find_nerest_workshop
from math import ceil


def __get_trips_info(
    craft_ingredients: list[dict[str, str | int]],
    quantity: int,
    inventory_max_items: int,
) -> tuple[int, int, list[tuple[str, int]]]:

    ingredients = [
        (str(ingredient["code"]), int(ingredient["quantity"]))
        for ingredient in craft_ingredients
    ]
    nb_ingredients = sum(nb[1] for nb in ingredients)
    nb_trips = ceil((nb_ingredients * quantity) / inventory_max_items)
    nb_craft_per_trip = quantity // nb_trips

    ingredients_for_trip = [
        (code, nb_craft_per_trip * quantity) for code, quantity in ingredients
    ]
    return nb_trips, nb_craft_per_trip, ingredients_for_trip


async def craft(character: Character, item: Item, quantity: int):
    if not character.has_job(item.job, item.craft_level):
        print(
            f"❌ {character.surname} does not have the required {item.job} level to craft {item.name}",
            f" (needed: {item.craft_level} - current: {character.get_job_level(item.job)})",
        )
        return

    nearest_workshop = find_nerest_workshop(item.job, character.location)

    if nearest_workshop is None:
        print(f"❌ No workshop found for job {item.job}")
        return

    nb_trips, nb_craft_per_trip, ingredients_for_trip = __get_trips_info(
        item.craft_ingredients, quantity, character.inventory_max_items
    )
    print(
        f"⚒️ {character.surname} needs to make {nb_trips} trips to craft {quantity}x {item.name}"
    )

    for _ in range(nb_trips):
        _ = await character.deposit_all_in_bank(comeback=False)
        if await character.withdraw_item_from_bank(ingredients_for_trip):
            if await character.move(nearest_workshop):
                _ = await character.craft(item, nb_craft_per_trip)

    print(f"⚒️ {character.surname} finished crafting {quantity}x {item.name}")
