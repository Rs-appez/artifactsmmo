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
        print(
            f"❌ {character.surname} does not have enough inventory space to craft {quantity}x {item.name}"
        )
        return

    _ = await character.deposit_all_in_bank(comeback=False)
    if await character.withdraw_item_from_bank(ingredients):
        if await character.move(workshop_location):
            _ = await character.craft(item, quantity)

    print(f"⚒️ {character.surname} finished crafting {quantity}x {item.name}")
