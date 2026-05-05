from models import Character, Item


async def craft(
    character: Character, workshop_location: tuple[int, int], item: Item, quantity: int
):
    ingredients = [
        (str(ingredient["code"]), int(ingredient["quantity"]))
        for ingredient in item.craft_ingredients
    ]
    nb_ingredients = sum(nb[1] for nb in ingredients)
    nb_trips = max((nb_ingredients * quantity) // character.inventory_max_items, 1)
    nb_craft_per_trip = quantity // nb_trips

    ingredients_for_trip = [
        (code, nb_craft_per_trip * quantity) for code, quantity in ingredients
    ]

    print(
        f"⚒️ {character.surname} needs to make {nb_trips} trips to craft {quantity}x {item.name}"
    )

    for _ in range(nb_trips):
        _ = await character.deposit_all_in_bank(comeback=False)
        if await character.withdraw_item_from_bank(ingredients_for_trip):
            if await character.move(workshop_location):
                _ = await character.craft(item, nb_craft_per_trip)

    print(f"⚒️ {character.surname} finished crafting {quantity}x {item.name}")
