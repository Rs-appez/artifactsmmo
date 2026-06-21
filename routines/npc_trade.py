from collections.abc import AsyncGenerator

from models.character import Character
from models.dataclass import NPC, Item
from models.dataclass.bank import Bank
from utils.find_best import find_best_npc
from utils.find_nearest import find_nearest_npc


async def __go_buy_from_npc(
    character: "Character", npc: NPC, item: "Item", quantity: int
):
    npc_location = await find_nearest_npc(character, npc)
    if not await character.move(npc_location):
        print(
            f"❌ {character.surname} failed to move to {npc.name} to buy {quantity}x {item.name}"
        )
        return

    if not await character.buy_from_npc(item, quantity):
        print(
            f"❌ {character.surname} failed to buy {quantity}x {item.name} from {npc.name}"
        )
        return


async def __get_currency_item(
    character: "Character", currency: Item, price: int, total_price: int
) -> AsyncGenerator[int, None]:

    async with Bank.reserve_items(
        {currency: total_price}, inventory=character.inventory
    ) as bank_token:
        per_trip = (character.inventory_max_items // price) * price
        nb_trips = (total_price + per_trip - 1) // per_trip
        print(
            f"💰 Need to withdraw {total_price} {currency.name} from bank to buy items, will do it in {nb_trips} trip(s)"
        )
        remain = total_price
        for _ in range(nb_trips):
            price_to_withdraw = min(remain, per_trip)
            await character.deposit_all_in_bank(with_gold=False)

            async with Bank.get_reserved_items_partial(
                bank_token, {currency: price_to_withdraw}
            ) as partial_bank_token:
                if character.inventory_free_slots < price_to_withdraw:
                    await character.deposit_all_in_bank(items_to_ignore={currency})
                if not await character.withdraw_item_from_bank(partial_bank_token):
                    raise Exception(
                        f"❌ {character.surname} does not have enough {currency.name} to buy items"
                    )
            yield price_to_withdraw // price
            remain -= price_to_withdraw


async def buy_from_npc(character: "Character", item: "Item", quantity: int):
    npcs = NPC.get_npcs_by_item_to_buy(item)
    if not npcs:
        print(f"❌ No NPC found buying {item.name}")
        return

    npc = find_best_npc(npcs, item)
    price, currency = npc.buy_items[item]
    total_price = price * quantity
    if currency:
        async for trip_buy_quantity in __get_currency_item(
            character, currency, price, total_price
        ):
            _ = await __go_buy_from_npc(character, npc, item, trip_buy_quantity)

    elif character.gold < total_price:
        if not await character.withdraw_gold_from_bank(total_price - character.gold):
            print(
                f"❌ {character.surname} does not have enough gold to buy {quantity}x {item.name} from {npc.name}"
            )
            return
        _ = await __go_buy_from_npc(character, npc, item, quantity)
