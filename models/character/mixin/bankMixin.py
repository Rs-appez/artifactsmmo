from typing import TYPE_CHECKING
import uuid

from models.dataclass import Item
from models.dataclass.bank import Bank, lock_bank

from ..decorators import need_bank

if TYPE_CHECKING:
    from models.character import Character


class BankMixin:
    async def deposit_all_in_bank(
        self: "Character",
        with_gold: bool = True,
        comeback: bool = False,
        items_to_ignore: set[Item] | None = None,
    ):
        if with_gold and self.gold > 0:
            if not await self.deposit_gold_in_bank(self.gold, comeback=comeback):
                print("❌ Failed to deposit gold in bank")
                return

        if self.inventory:
            if not await self.deposit_item_in_bank(
                comeback=comeback,
                items={
                    item: quantity
                    for item, quantity in self.inventory.items()
                    if not items_to_ignore or item not in items_to_ignore
                },
            ):
                print("❌ Failed to deposit items in bank")
                return

    @need_bank
    @lock_bank
    async def deposit_gold_in_bank(self: "Character", quantity: int) -> bool:
        if quantity > self.gold:
            print(f"❌ Cannot deposit {quantity} gold, only {self.gold} available")
            return False
        if quantity <= 0:
            print(f"❌ Cannot deposit non-positive quantity of gold: {quantity}")
            return False
        try:
            await self.post_api("/bank/deposit/gold", json={"quantity": quantity})

            print(f"󱉏  {self.surname} Deposited {quantity} gold in bank")
            return True
        except Exception as e:
            print(f"❌ {self.surname} deposit gold : {e}")
            return False

    @need_bank
    @lock_bank
    async def deposit_item_in_bank(
        self: "Character", items: dict[Item, int], comeback: bool = False
    ) -> bool:
        try:
            await self.post_api(
                "/bank/deposit/item",
                json=[
                    {"code": item.code, "quantity": int(quantity)}
                    for item, quantity in items.items()
                ],
            )
            print(
                f"📥 {self.surname} Deposited {', '.join([f'{quantity}x {item.name}' for item, quantity in items.items()])} in bank"
            )
            return True
        except Exception as e:
            print(f"❌ {self.surname} deposit item : {e}")
            return False

    @need_bank
    @lock_bank
    async def withdraw_item_from_bank(
        self: "Character",
        bank_token: uuid.UUID,
        comeback: bool = False,
    ) -> bool:
        try:
            items = Bank._get_reserved_items(bank_token)  # pyright: ignore[reportPrivateUsage]
            await self.post_api(
                "/bank/withdraw/item",
                json=[
                    {"code": item.code, "quantity": quantity}
                    for item, quantity in items.items()
                ],
            )
            print(
                f"📤 {self.surname} Withdrew {', '.join([f'{item[1]}x {item[0].code}' for item in items.items()])} from bank"
            )
            return True
        except Exception as e:
            print(f"❌ {self.surname} withdraw item : {e}")
            return False
        finally:
            Bank._unreserve_items(bank_token)  # pyright: ignore[reportPrivateUsage]

    @need_bank
    @lock_bank
    async def withdraw_gold_from_bank(
        self: "Character", quantity: int, comeback: bool = False
    ) -> bool:
        if quantity <= 0:
            print(f"❌ Cannot withdraw non-positive quantity of gold: {quantity}")
            return False
        try:
            await self.post_api("/bank/withdraw/gold", json={"quantity": quantity})

            print(f"💰 {self.surname} Withdrew {quantity} gold from bank")
            return True
        except Exception as e:
            print(f"❌ {self.surname} withdraw gold : {e}")
            return False
