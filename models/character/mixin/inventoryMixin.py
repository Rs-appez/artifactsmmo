from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from models.dataclass import Item

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class InventoryMixin(Protocol):
    _gold: int = 0
    _inventory: dict[Item, int] = {}
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
    def is_inventory_full(self) -> bool:
        return (
            sum(self._inventory.values()) >= self._inventory_max_items - 5
            or len(self._inventory) >= 17
        )

    def has_in_inventory(self: "Character", items: dict[Item, int]) -> bool:
        for item, quantity in items.items():
            if self._inventory.get(item, 0) < quantity:
                return False
        return True
