from typing import TYPE_CHECKING, Protocol

from config import HEADERS
from models.dataclass import Item

from ..decorators import need_bank, refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


class BankMixin(Protocol):
    async def deposit_all_in_bank(self: "Character", comeback: bool = True):
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
    async def deposit_gold_in_bank(
        self: "Character", quantity: int, comeback: bool = True
    ) -> tuple[bool, dict | None]:
        if quantity > self.gold:
            print(f"❌ Cannot deposit {quantity} gold, only {self.gold} available")
            return False, None
        if quantity <= 0:
            print(f"❌ Cannot deposit non-positive quantity of gold: {quantity}")
            return False, None
        try:
            response = await self.client.post(
                f"{self.url}/action/bank/deposit/gold",
                headers=HEADERS,
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
    async def deposit_item_in_bank(
        self: "Character", items: dict[Item, int], comeback: bool = True
    ) -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                f"{self.url}/action/bank/deposit/item",
                headers=HEADERS,
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
    async def withdraw_item_from_bank(
        self: "Character", items: list[tuple[str, int]], comeback: bool = False
    ) -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                f"{self.url}/action/bank/withdraw/item",
                headers=HEADERS,
                json=[{"code": item, "quantity": quantity} for item, quantity in items],
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            print(
                f"📤 {self.surname} Withdrew {', '.join([f'{item[1]}x {item[0]}' for item in items])} from bank"
            )
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None

    @need_bank
    @request_action
    @refresh_after
    async def withdraw_gold_from_bank(
        self: "Character", quantity: int, comeback: bool = False
    ) -> tuple[bool, dict | None]:
        if quantity <= 0:
            print(f"❌ Cannot withdraw non-positive quantity of gold: {quantity}")
            return False, None
        try:
            response = await self.client.post(
                f"{self.url}/action/bank/withdraw/gold",
                headers=HEADERS,
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
