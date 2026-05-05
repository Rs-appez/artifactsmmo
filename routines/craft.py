from models import Character, Item


async def craft(
    character: Character, workshop_location: tuple[int, int], item: Item, quantity: int
):
    ingredients = [
        (str(ingredient["code"]), int(ingredient["quantity"]) * quantity)
        for ingredient in item.craft_ingredients
    ]
    nb_ingredients = sum(nb[1] for nb in ingredients)
    if character.inventory_max_items < nb_ingredients:
        raise ValueError("Not enough inventory space to craft the item.")

    _ = await character.deposit_all_in_bank(comeback=False)
    _ = await character.withdraw_item_from_bank(ingredients)
    if await character.move(workshop_location):
        _ = await character.craft(item, quantity)
