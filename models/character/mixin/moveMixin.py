from dataclasses import dataclass
from typing import TYPE_CHECKING

from exceptions import (
    NeedToRefreshStuffException,
    NotEnoughInBankException,
    TimeoutButSuccessException,
)
from models import Encyclopedia, LocationRegistry
from models.dataclass import Item, Map
from models.dataclass.bank import Bank
from models.enums import Layer, ZoneType
from routines import craft
from utils.find_nearest import find_nearest_transition
from utils.pathfinding import get_route

if TYPE_CHECKING:
    from models.character import Character

TRANSITION_MAPS = {
    ZoneType.SANDWHISPER: {ZoneType.DEFAULT: 1093, ZoneType.SANDWHISPER: 1336},
    ZoneType.ENCHANTED_FOREST: {
        ZoneType.DEFAULT: 718,
        ZoneType.ENCHANTED_FOREST: 667,
    },
}


@dataclass
class MoveMixin:
    _location: Map

    _default_return_potion: Item

    @property
    def location(self: "Character") -> Map:
        return self._location

    async def move(self: "Character", destination: Map) -> None:
        if destination == self.location:
            return

        path = await get_route(self.location, destination)
        for i, map in enumerate(path):
            await self._move(map)
            if i + 1 < len(path) and map.has_transition:
                await self._transition()

    async def _move(self: "Character", destination: Map) -> None:
        if destination == self.location:
            return

        try:
            await self.post_api("/move", json_data={"map_id": destination.map_id})

            arrived = self.location

            print(
                f"🏃 {self.surname} Moved to ({arrived.x}, {arrived.y}) on {arrived.name} (layer : {arrived.layer.value})"
            )
        except TimeoutButSuccessException:
            print(
                f"🏃 {self.surname} Moved to ({destination.x}, {destination.y}) on {destination.name} (layer : {destination.layer.value}) (timeout but success)"
            )
        except NeedToRefreshStuffException as e:
            raise e

    async def _transition(self: "Character") -> bool:
        try:
            await self.post_api("/transition")
            destination = self.location

            print(
                f"󰓡 {self.surname} Transitioned to ({destination.x}, {destination.y}) on {destination.name} (layer : {destination.layer.value})"
            )
            return True
        except TimeoutButSuccessException:
            destination = self.location
            print(
                f"󰓡 {self.surname} Transitioned to ({destination.x}, {destination.y}) on {destination.name} (layer : {destination.layer.value}) (timeout but success)"
            )
            return True
        except Exception as e:
            print(f"❌ {self.surname} transition : {e}")
            return False

    async def _change_layer(self: "Character", destination: Map) -> None:
        if destination.layer == self.location.layer:
            return

        if self.location.layer is Layer.OVERWORLD:
            transition_map = await find_nearest_transition(
                destination, destination.layer, self.location.layer
            )
        else:
            transition_map = await find_nearest_transition(
                self.location, destination.layer, self.location.layer
            )

        if not await self.move(transition_map):
            print(
                f"❌ {self.surname} Failed to move to transition map {transition_map.name} to change layer"
            )
            return

        if not await self._transition():
            print(
                f"❌ {self.surname} Failed to transition to layer {destination.layer} from {transition_map.name}"
            )
            return

    async def _handle_travel(self: "Character", destination: Map) -> bool:
        char_zone = self.location.zone
        if char_zone != destination.zone:
            match destination.zone:
                case ZoneType.DEFAULT:
                    await self._return_to_default_location()
                case ZoneType.SANDWHISPER:
                    await self.__handle_sandwhisper_travel()
                case ZoneType.ENCHANTED_FOREST:
                    await self.__handle_enchanted_forest_travel()
            return True
        return False

    async def __get_pre_travel_items(
        self: "Character", gold_to_travel: int, return_potion: Item | None = None
    ) -> None:

        if return_potion and not self.has_in_inventory({return_potion: 1}):
            try:
                async with Bank.reserve_items({return_potion: 1}) as bank_token:
                    if self.inventory_free_space < 1 or self.inventory_free_slots < 1:
                        await self.deposit_all_in_bank(with_gold=False)
                    await self.withdraw_item_from_bank(bank_token)
            except NotEnoughInBankException:
                await craft(self, return_potion, 100)
                raise NeedToRefreshStuffException(
                    f"Crafted {return_potion.name}, please retry the travel"
                )
            except Exception as e:
                raise e

        if self.gold < gold_to_travel:
            if not await self.withdraw_gold_from_bank(gold_to_travel):
                raise Exception(f"Failed to withdraw {gold_to_travel} gold from bank")

    async def __handle_sandwhisper_travel(self: "Character") -> None:
        boat = await LocationRegistry.get_map_by_id(
            TRANSITION_MAPS[ZoneType.SANDWHISPER][self.location.zone]
        )
        price = boat.transition_cost
        if price:
            if price[0] is None:
                gold_to_travel = price[1]
                await self.__get_pre_travel_items(
                    gold_to_travel, self._default_return_potion
                )

        await self.move(boat)
        await self._transition()

    async def _return_to_default_location(self: "Character") -> None:

        match self.location.zone:
            case ZoneType.SANDWHISPER:
                if self.has_in_inventory({self._default_return_potion: 1}):
                    await self.use_item(self._default_return_potion)
                else:
                    transition = await LocationRegistry.get_map_by_id(
                        TRANSITION_MAPS[ZoneType.SANDWHISPER][self.location.zone]
                    )
                    await self.move(transition)
                    await self._transition()
            case ZoneType.ENCHANTED_FOREST:
                transition = await LocationRegistry.get_map_by_id(
                    TRANSITION_MAPS[ZoneType.ENCHANTED_FOREST][self.location.zone]
                )
                await self.move(transition)
                await self._transition()

    async def __handle_enchanted_forest_travel(self: "Character") -> None:
        tp_potion = await Encyclopedia.get_item_by_code("enchanted_potion")
        if self.has_in_inventory({tp_potion: 1}):
            await self.use_item(tp_potion)

        else:
            try:
                async with Bank.reserve_items({tp_potion: 1}) as bank_token:
                    if self.inventory_free_space < 1 or self.inventory_free_slots < 1:
                        await self.deposit_all_in_bank(with_gold=False)
                    await self.withdraw_item_from_bank(bank_token)
                await self.use_item(tp_potion)
            except NotEnoughInBankException:
                enchanted_mush = await Encyclopedia.get_item_by_code(
                    "enchanted_mushroom"
                )

                try:
                    async with Bank.reserve_items(
                        {enchanted_mush: 1}, inventory=self.inventory
                    ) as bank_token:
                        await craft(self, tp_potion, 1, token=bank_token)
                        raise NeedToRefreshStuffException(
                            f"Crafted {tp_potion.name} from {enchanted_mush.name}, please retry the travel"
                        )
                except NotEnoughInBankException:
                    boat = await LocationRegistry.get_map_by_id(
                        TRANSITION_MAPS[ZoneType.ENCHANTED_FOREST][self.location.zone]
                    )
                    price = boat.transition_cost
                    if price:
                        if price[0] is None:
                            gold_to_travel = price[1]
                            await self.__get_pre_travel_items(gold_to_travel)
                    await self.move(boat)
                    await self._transition()
