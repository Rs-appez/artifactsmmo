from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from models.character.decorators import request_action, refresh_after
from models.dataclass import Item

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class InventoryMixin(Protocol):
    _gold: int = 0
    _inventory: dict[Item, int] = field(default_factory=dict)
    _inventory_max_items: int = 0

    @property
    def gold(self) -> int:
        return self._gold

    @property
    def inventory(self) -> dict[Item, int]:
        return self._inventory.copy()

    @property
    def inventory_max_items(self) -> int:
        return self._inventory_max_items

    @property
    def inventory_used_slots(self) -> int:
        return sum(self._inventory.values())

    @property
    def inventory_free_slots(self) -> int:
        return self._inventory_max_items - self.inventory_used_slots

    @property
    def is_inventory_full(self) -> bool:
        return (
            sum(self._inventory.values()) >= self._inventory_max_items - 5
            or len(self._inventory) >= 17
        )

    @property
    def has_food(self) -> bool:
        for item, quantity in self._inventory.items():
            if item.is_food and quantity > 0:
                return True
        return False

    @property
    def get_food(self: "Character") -> dict[Item, int]:
        food_items = {}
        for item, quantity in self._inventory.items():
            if item.is_food and quantity > 0 and item.can_be_used_by(self):
                food_items[item] = quantity
        return food_items

    def has_in_inventory(self: "Character", items: dict[Item, int]) -> bool:
        for item, quantity in items.items():
            if self._inventory.get(item, 0) < quantity:
                return False
        return True

    @request_action
    @refresh_after
    async def use_item(
        self: "Character", item: Item, quantity: int = 1
    ) -> tuple[bool, dict | None]:
        try:
            if item.type != "consumable":
                raise Exception(f"{item.name} is not a consumable item")
            if quantity <= 0:
                raise Exception(
                    f"Cannot use non-positive quantity of {item.name}: {quantity}"
                )
            if self._inventory.get(item, 0) < quantity:
                raise Exception(
                    f"Not enough {item.name} in inventory to use (have: {self._inventory.get(item, 0)}, need: {quantity})"
                )
            response = await self.client.post(
                "/use",
                json={
                    "code": item.code,
                    "quantity": quantity,
                },
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]

            return True, character_data
        except Exception as e:
            print(f"❌ {self.surname} use_item : {e}")
            return False, None
