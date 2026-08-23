from exceptions import TimeoutButSuccessException
from dataclasses import dataclass
from typing import TYPE_CHECKING

from config import MAX_ITEM_PER_ORDER
from models.dataclass import Item

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class GrandExchangeMixin:
    async def sell_item_to_ge(
        self: "Character", item: Item, quantity: int, price: int
    ) -> None:
        """
        Sell an item on the Grand Exchange.

        :param item: The item to sell.
        :param quantity: The quantity of the item to sell.
        :param price: The price at which to sell the item.
        """
        if not 0 <= quantity <= MAX_ITEM_PER_ORDER:
            raise ValueError("Quantity must be between 0 and 100.")
        if price <= 0:
            raise ValueError("Price must be greater than 0.")

        endpoint = "/grandexchange/create_sell_order"
        json_data = {"code": item.code, "quantity": quantity, "price": price}
        try:
            await self.post_api(endpoint, json_data=json_data)
        except TimeoutButSuccessException:
            pass

        print(
            f"💰 {self.surname} created sell order for {quantity}x {item.name} at {price} coins each"
        )

    async def sell_item_to_ge_buy_order(
        self: "Character",
        order_id: int,
        quantity: int,
    ):
        """
        Sell an item to a buy order on the Grand Exchange.

        :param item: The item to sell.
        :param quantity: The quantity of the item to sell.
        :param price: The price at which to sell the item.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")

        endpoint = "/grandexchange/fill"
        try:
            await self.post_api(
                endpoint, json_data={"id": order_id, "quantity": quantity}
            )
        except TimeoutButSuccessException:
            pass

        print(f"💰 {self.surname} sold {quantity}x to buy order {order_id}")
