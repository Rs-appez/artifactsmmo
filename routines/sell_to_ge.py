from config import MAX_ITEM_PER_ORDER
from typing import TYPE_CHECKING

from models.dataclass import Item
from models.dataclass.bank import Bank
from utils.find_nearest import find_nearest_grand_exchange

if TYPE_CHECKING:
    from models.character import Character


async def sell_item_to_ge(
    character: "Character", item: Item, quantity: int, price: int
):

    try:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")
        if price <= 0:
            raise ValueError("Price must be greater than 0.")

        ge_map = await find_nearest_grand_exchange(character)

        async with Bank.reserve_items(
            {item: quantity}, inventory=character.inventory
        ) as bank_token:
            per_trip = min(character.inventory_max_items, quantity)
            nb_trips = (quantity + per_trip - 1) // per_trip

            remain = quantity
            for _ in range(nb_trips):
                in_inventory = character.inventory.get(item, 0)
                trip_quantity = min(remain, per_trip)
                nb_to_withdraw = trip_quantity - in_inventory

                async with Bank.get_reserved_items_partial(
                    bank_token, {item: nb_to_withdraw}
                ) as partial_bank_token:
                    if character.need_deposit(partial_bank_token):
                        await character.deposit_all_in_bank(
                            items_to_ignore={item}, with_gold=False
                        )

                    await character.withdraw_item_from_bank(partial_bank_token)

                    await character.move(ge_map)

                    nb_to_sell = trip_quantity
                    while nb_to_sell > 0:
                        sell_quantity = min(nb_to_sell, MAX_ITEM_PER_ORDER)
                        await character.sell_item_to_ge(item, sell_quantity, price)
                        nb_to_sell -= sell_quantity

                    remain -= trip_quantity

    except Exception as e:
        print(f"❌ Failed to sell {quantity}x {item.name} to GE: {e}")
