from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from models.dataclass import Item
from models.dataclass.bank import Bank

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class InventoryMixin:
    _gold: int = 0
    _inventory: dict[Item, int] = field(default_factory=dict)
    _inventory_max_items: int = 0
    _inventory_max_slots: int = 20

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
    def inventory_free_space(self) -> int:
        return self._inventory_max_items - self.inventory_used_slots

    @property
    def inventory_free_slots(self) -> int:
        return self._inventory_max_slots - len(self._inventory)

    @property
    def is_inventory_full(self) -> bool:
        return (
            sum(self._inventory.values()) >= self._inventory_max_items - 5
            or len(self._inventory) >= self._inventory_max_slots - 3
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

    def need_deposit(self, token: UUID) -> bool:
        """
        Check if the character needs to deposit items in the bank before withdrawing reserved items.
        Returns True if the character needs to deposit items, False otherwise.
        """
        nb_items_to_withdraw = sum(Bank.get_token_info(token).values())
        nb_slots_to_withdraw = len(Bank.get_token_info(token))

        if (
            self.inventory_free_space < nb_items_to_withdraw
            or self.inventory_free_slots < nb_slots_to_withdraw
        ):
            return True

        return False

    async def use_item(self: "Character", item: Item, quantity: int = 1) -> bool:
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

            await self.post_api(
                "/use",
                json_data={
                    "code": item.code,
                    "quantity": quantity,
                },
            )
            return True
        except Exception as e:
            print(f"❌ {self.surname} use_item : {e}")
            return False
