from models.character import Character
from models.dataclass import NPC, Item
from models.dataclass.bank import Bank
from utils.find_best import find_best_npc
from utils.find_nearest import find_nearest_npc


async def __get_currency_item(
    character: "Character", currency: "Item", quantity: int
) -> bool:
    if currency in character.inventory:
        if character.inventory[currency] >= quantity:
            return True

        quantity -= character.inventory[currency]
    async with Bank.reserve_items({currency: quantity}) as bank_token:
        if character.inventory_free_slots < quantity:
            await character.deposit_all_in_bank(items_to_ignore={currency})
        if not await character.withdraw_item_from_bank(bank_token):
            print(
                f"❌ {character.surname} does not have enough {currency.name} to buy items"
            )
            return False

    return True


async def buy_to_npc(character: "Character", item: "Item", quantity: int):
    npcs = NPC.get_npcs_by_item_to_buy(item)
    if not npcs:
        print(f"❌ No NPC found buying {item.name}")
        return

    npc = find_best_npc(npcs, item)
    npc_location = await find_nearest_npc(character, npc)
    price, currency = npc.buy_items[item]
    total_price = price * quantity
    if currency:
        if not await __get_currency_item(character, currency, total_price):
            print(
                f"❌ {character.surname} does not have enough {currency.name} to buy {quantity}x {item.name} from {npc.name}"
            )
            return

    elif character.gold < total_price:
        if not await character.withdraw_gold_from_bank(total_price - character.gold):
            print(
                f"❌ {character.surname} does not have enough gold to buy {quantity}x {item.name} from {npc.name}"
            )
            return

    if not await character.move(npc_location):
        print(
            f"❌ {character.surname} failed to move to {npc.name} to buy {quantity}x {item.name}"
        )
        return
