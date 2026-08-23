from dataclasses import dataclass

from httpx import AsyncClient

from config import ARTIFACTSMMO_URL, HEADERS
from models import Encyclopedia
from models.dataclass import Item
from models.enums import OrderType


@dataclass(frozen=True)
class Order:
    id: str
    item: Item
    price: int
    quantity: int
    order_type: OrderType
    owner: str

    async def from_dict(data: dict) -> "Order":
        return Order(
            id=data["id"],
            item=await Encyclopedia.get_item_by_code(data["code"]),
            price=int(data["price"]),
            quantity=int(data["quantity"]),
            order_type=OrderType(data["type"]),
            owner=data["account"],
        )


class GrandExchange:
    __url = f"{ARTIFACTSMMO_URL}/grandexchange"

    @staticmethod
    async def get_buy_orders(item: Item) -> list[Order]:
        return await GrandExchange._fetch_orders(OrderType.BUY, item)

    @classmethod
    async def _fetch_orders(cls, order_type: OrderType, item: Item) -> list[Order]:
        parameters = {"code": item.code, "size": 100, "type": order_type.value}
        results = []
        try:
            page = 1
            max_page = 1
            async with AsyncClient() as client:
                while page <= max_page:
                    response = await client.get(
                        f"{cls.__url}/orders",
                        headers=HEADERS,
                        timeout=5.0,
                        params={**parameters, "page": page},
                    )
                    data = response.json()
                    max_page = data["max_page"]
                    page += 1

                    for order_data in data["data"]:
                        order = await Order.from_dict(order_data)
                        results.append(order)
        except Exception as e:
            print(f"❌ Error fetching orders: {e}")
            return results

        return results
