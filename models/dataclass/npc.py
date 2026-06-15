from dataclasses import dataclass
from typing import ClassVar, override

from models.dataclass import Item
from models.enums import NPCType


@dataclass(frozen=True)
class NPC:
    _items_to_buy_npc: ClassVar[dict[Item, set[NPC]]] = {}
    _items_to_sell_npc: ClassVar[dict[Item, set[NPC]]] = {}

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
            item = await Encyclopedia.get_item_by_code(item_data["code"])
            currency = (
                await Encyclopedia.get_item_by_code(item_data["currency"])
                if item_data["currency"] != "gold"
                else None
            )
            if item_data["buy_price"]:
                buy_items[item] = (item_data["buy_price"], currency)
            if item_data["sell_price"]:
                sell_items[item] = (item_data["sell_price"], currency)

        current_cls = cls(
            name=data["name"],
            code=data["code"],
            type=NPCType(data["type"]),
            buy_items=buy_items,
            sell_items=sell_items,
        )

        cls._items_to_buy_npc.update(
            {
                item: cls._items_to_buy_npc.get(item, set()).union({current_cls})
                for item in buy_items
            }
        )
        cls._items_to_sell_npc.update(
            {
                item: cls._items_to_sell_npc.get(item, set()).union({current_cls})
                for item in sell_items
            }
        )

        return current_cls

    @override
    def __str__(self):
        return self.name

    @override
    def __hash__(self):
        return hash(self.code)

    @staticmethod
    def get_npcs_by_item_to_buy(item: Item) -> set["NPC"]:
        return NPC._items_to_buy_npc.get(item, set())

    @staticmethod
    def get_npcs_by_item_to_sell(item: Item) -> set["NPC"]:
        return NPC._items_to_sell_npc.get(item, set())
