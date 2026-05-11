from typing import TYPE_CHECKING, Protocol
import uuid

from config import HEADERS
from models.dataclass import Item
from models.dataclass.bank import Bank, lock_bank

from ..decorators import need_bank, refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


class BankMixin(Protocol):
    async def deposit_all_in_bank(self: "Character", comeback: bool = False):
        if self.gold > 0:
            if not await self.deposit_gold_in_bank(self.gold, comeback=comeback):
                print("❌ Failed to deposit gold in bank")
                return

        if self.inventory:
            if not await self.deposit_item_in_bank(
                comeback=comeback,
                items=self.inventory,
            ):
                print("❌ Failed to deposit items in bank")
                return

    @need_bank
    @request_action
    @refresh_after
    @lock_bank
    async def deposit_gold_in_bank(
        self: "Character", quantity: int, comeback: bool = False
    ) -> tuple[bool, dict | None]:
        if quantity > self.gold:
            print(f"❌ Cannot deposit {quantity} gold, only {self.gold} available")
            return False, None
        if quantity <= 0:
            print(f"❌ Cannot deposit non-positive quantity of gold: {quantity}")
            return False, None
        try:
            response = await self.client.post(
                "bank/deposit/gold",
                json={"quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            print(f"󱉏  {self.surname} Deposited {quantity} gold in bank")
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None

    @need_bank
    @request_action
    @refresh_after
    @lock_bank
    async def deposit_item_in_bank(
        self: "Character", items: dict[Item, int], comeback: bool = False
    ) -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/bank/deposit/item",
                json=[
                    {"code": item.code, "quantity": int(quantity)}
                    for item, quantity in items.items()
                ],
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            print(
                f"📥 {self.surname} Deposited {', '.join([f'{quantity}x {item.name}' for item, quantity in items.items()])} in bank"
            )
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None

    @need_bank
    @request_action
    @refresh_after
    @lock_bank
    async def withdraw_item_from_bank(
        self: "Character",
        bank_token: uuid.UUID,
        comeback: bool = False,
    ) -> tuple[bool, dict | None]:
        try:
            items = Bank.get_reserved_items(bank_token)
            response = await self.client.post(
                "/bank/withdraw/item",
                json=[
                    {"code": item.code, "quantity": quantity}
                    for item, quantity in items
                ],
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            print(
                f"📤 {self.surname} Withdrew {', '.join([f'{item[1]}x {item[0].code}' for item in items])} from bank"
            )
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None
        finally:
            await Bank.unreserve_items(bank_token)

    @need_bank
    @request_action
    @refresh_after
    @lock_bank
    async def withdraw_gold_from_bank(
        self: "Character", quantity: int, comeback: bool = False
    ) -> tuple[bool, dict | None]:
        if quantity <= 0:
            print(f"❌ Cannot withdraw non-positive quantity of gold: {quantity}")
            return False, None
        try:
            response = await self.client.post(
                "/bank/withdraw/gold",
                json={"quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            print(f"💰 {self.surname} Withdrew {quantity} gold from bank")
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None
