from dataclasses import dataclass
from typing import TYPE_CHECKING

from exceptions import NotEnoughInBankException, TimeoutButSuccessException
from models import LocationRegistry
from models.dataclass import Item, Map
from models.dataclass.bank import Bank
from models.enums import Layer, ZoneType
from routines import craft
from utils.find_nearest import find_nearest_transition

if TYPE_CHECKING:
    from models.character import Character

TRANSITION_MAPS = {
    ZoneType.SANDWHISPER: {ZoneType.DEFAULT: 1093, ZoneType.SANDWHISPER: 1336},
}


@dataclass
class MoveMixin:
    _location: Map

    _default_return_potion: Item

    @property
    def location(self: "Character") -> Map:
        return self._location

    async def move(self: "Character", destination: Map) -> bool:
        if destination == self.location:
            return True

        await self._handle_travel(destination)

        if destination.layer != self.location.layer:
            await self._change_layer(destination)

        if destination == self.location:
            return True

        try:
            await self.post_api("/move", json_data={"map_id": destination.map_id})

            arrived = self.location

            print(
                f"🏃 {self.surname} Moved to ({arrived.x}, {arrived.y}) on {arrived.name} (layer : {arrived.layer.value})"
            )
            return True
        except TimeoutButSuccessException:
            print(
                f"🏃 {self.surname} Moved to ({destination.x}, {destination.y}) on {destination.name} (layer : {destination.layer.value}) (timeout but success)"
            )
            return True
        except Exception as e:
            print(f"❌ {self.surname} move : {e}")
            return False

    async def transition(self: "Character") -> bool:
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

        if not await self.transition():
            print(
                f"❌ {self.surname} Failed to transition to layer {destination.layer} from {transition_map.name}"
            )
            return

    async def _handle_travel(self: "Character", destination: Map) -> None:
        char_zone = self.location.zone
        if char_zone != destination.zone:
            match destination.zone:
                case ZoneType.DEFAULT:
                    await self._return_to_default_location()
                case ZoneType.SANDWHISPER:
                    await self.__handle_sandwhisper_travel()

    async def __get_pre_travel_items(
        self: "Character", gold_to_travel: int, return_potion: Item | None = None
    ) -> None:

        if return_potion is None:
            return_potion = self._default_return_potion

        if not self.has_in_inventory({return_potion: 1}):
            retry = True
            while retry:
                retry = False
                try:
                    async with Bank.reserve_items({return_potion: 1}) as bank_token:
                        if (
                            self.inventory_free_space < 1
                            or self.inventory_free_slots < 1
                        ):
                            await self.deposit_all_in_bank(with_gold=False)
                        await self.withdraw_item_from_bank(bank_token)
                except NotEnoughInBankException:
                    retry = True
                    await craft(self, return_potion, 100)
                except Exception as e:
                    raise e

        if self.gold < gold_to_travel:
            if not await self.withdraw_gold_from_bank(gold_to_travel):
                raise Exception(f"Failed to withdraw {gold_to_travel} gold from bank")

    async def __handle_sandwhisper_travel(self: "Character") -> None:
        await self.__get_pre_travel_items(1000)
        boat = await LocationRegistry.get_map_by_id(
            TRANSITION_MAPS[ZoneType.SANDWHISPER][self.location.zone]
        )
        await self.move(boat)
        await self.transition()

    async def _return_to_default_location(self: "Character") -> None:
        if self.has_in_inventory({self._default_return_potion: 1}):
            await self.use_item(self._default_return_potion)

        else:
            match self.location.zone:
                case ZoneType.SANDWHISPER:
                    boat = await LocationRegistry.get_map_by_id(
                        TRANSITION_MAPS[ZoneType.SANDWHISPER][self.location.zone]
                    )
                    await self.move(boat)
                    await self.transition()
