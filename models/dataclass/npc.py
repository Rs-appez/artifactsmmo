from dataclasses import dataclass
from typing import override

from models.dataclass import Item
from models.enums import NPCType


@dataclass(frozen=True)
class NPC:
    name: str
    code: str
    type: NPCType
    buy_items: dict[Item, tuple[int, None | Item]]
    sell_items: dict[Item, tuple[int, None | Item]]

    @classmethod
    async def from_dict(cls, data):
        from models import Encyclopedia

        buy_items = {}
        sell_items = {}

        for item_data in data["items"]:
            item = await Encyclopedia.get_item_by_code(item_data["item"]["code"])
            currency = (
                await Encyclopedia.get_item_by_code(item_data["currency"])
                if item_data["currency"] != "gold"
                else None
            )
            if item_data["buy_price"]:
                buy_items[item] = (item_data["buy_price"], currency)
            if item_data["sell_price"]:
                sell_items[item] = (item_data["sell_price"], currency)

        return cls(
            name=data["name"],
            code=data["code"],
            type=NPCType(data["type"]),
            buy_items=buy_items,
            sell_items=sell_items,
        )

    @override
    def __str__(self):
        return self.name

    @override
    def __hash__(self):
        return hash(self.code)
