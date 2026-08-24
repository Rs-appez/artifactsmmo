import uuid
from typing import TYPE_CHECKING

from exceptions import TimeoutButSuccessException
from models.dataclass import Item
from models.dataclass.bank import Bank, get_food, lock_bank

from ..decorators import need_bank

if TYPE_CHECKING:
    from models.character import Character


class BankMixin:
    @need_bank
    async def deposit_all_in_bank(
        self: "Character",
        with_gold: bool = True,
        comeback: bool = False,
        items_to_ignore: set[Item] | dict[Item, int] | None = None,
    ):
        if with_gold and self.gold > 0:
            if not await self.deposit_gold_in_bank(self.gold, comeback=comeback):
                print("❌ Failed to deposit gold in bank")
                return

        if self.inventory:
            if isinstance(items_to_ignore, set):
                items_to_ignore = {
                    item: self.inventory.get(item, 0) for item in items_to_ignore
                }
            if items_to_ignore is None:
                items_to_ignore = {}

            if not await self.deposit_item_in_bank(
                comeback=comeback,
                items={
                    item: quantity_to_deposit
                    for item, quantity in self.inventory.items()
                    if (
                        quantity_to_deposit := quantity - (items_to_ignore.get(item, 0))
                    )
                    > 0
                },
            ):
                print("❌ Failed to deposit items in bank")
                return

    @need_bank
    @lock_bank
    async def deposit_gold_in_bank(
        self: "Character", quantity: int, comeback: bool = False
    ) -> bool:
        success = False
        if quantity > self.gold:
            print(f"❌ Cannot deposit {quantity} gold, only {self.gold} available")
            return success
        if quantity <= 0:
            print(f"❌ Cannot deposit non-positive quantity of gold: {quantity}")
            return success
        try:
            await self.post_api("/bank/deposit/gold", json_data={"quantity": quantity})
            success = True
        except TimeoutButSuccessException:
            print(f"⚠️ {self.surname} deposit gold : Timeout but success")
            success = True
        except Exception as e:
            print(f"❌ {self.surname} deposit gold : {e}")

        finally:
            if success:
                await Bank._deposit_gold(quantity)
                print(f"󱉏  {self.surname} Deposited {quantity} gold in bank")
        return success

    @need_bank
    @lock_bank
    async def deposit_item_in_bank(
        self: "Character", items: dict[Item, int], comeback: bool = False
    ) -> bool:
        success = False
        try:
            await self.post_api(
                "/bank/deposit/item",
                json_data=[
                    {"code": item.code, "quantity": int(quantity)}
                    for item, quantity in items.items()
                ],
            )
            success = True
        except TimeoutButSuccessException:
            print(f"⚠️ {self.surname} deposit item : Timeout but success")
            success = True
        except Exception as e:
            print(f"❌ {self.surname} deposit item : {e}")

        finally:
            if success:
                await Bank._deposit_items(items)
                print(
                    f"📥 {self.surname} Deposited {', '.join([f'{quantity}x {item.name}' for item, quantity in items.items()])} in bank"
                )

        return success

    @need_bank
    @lock_bank
    async def withdraw_item_from_bank(
        self: "Character",
        bank_token: uuid.UUID,
        comeback: bool = False,
    ) -> bool:
        success = False
        try:
            items = Bank.get_token_info(bank_token)
            await self.post_api(
                "/bank/withdraw/item",
                json_data=[
                    {"code": item.code, "quantity": quantity}
                    for item, quantity in items.items()
                ],
            )
            success = True
        except TimeoutButSuccessException:
            print(f"⚠️ {self.surname} withdraw item : Timeout but success")
            success = True
        except Exception as e:
            print(f"❌ {self.surname} withdraw item : {e}")
        finally:
            if success:
                print(
                    f"📤 {self.surname} Withdrew {', '.join([f'{item[1]}x {item[0].code}' for item in items.items()])} from bank"
                )
                await Bank._withdraw_items(items)
            Bank._unreserve_items(bank_token)
        return success

    @need_bank
    @lock_bank
    async def withdraw_gold_from_bank(
        self: "Character", quantity: int, comeback: bool = False
    ) -> bool:
        success = False
        if quantity <= 0:
            print(f"❌ Cannot withdraw non-positive quantity of gold: {quantity}")
            return success
        try:
            await self.post_api("/bank/withdraw/gold", json_data={"quantity": quantity})
            success = True
        except TimeoutButSuccessException:
            print(f"⚠️ {self.surname} withdraw gold : Timeout but success")
            success = True
        except Exception as e:
            print(f"❌ {self.surname} withdraw gold : {e}")

        finally:
            if success:
                await Bank._withdraw_gold(quantity)
                print(f"💰 {self.surname} Withdrew {quantity} gold from bank")

        return success

    async def get_food_from_bank(self: "Character"):
        print(f"󰜎 {self.surname} will search for food in bank")
        qty = int(self.inventory_max_items * 0.8)
        async with get_food(self, qty) as food_token:
            await self.deposit_all_in_bank(with_gold=False)
            if not await self.withdraw_item_from_bank(food_token):
                raise Exception("Failed to withdraw food from bank")
