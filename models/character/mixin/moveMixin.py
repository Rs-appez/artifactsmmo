from dataclasses import dataclass
from typing import TYPE_CHECKING

from models.dataclass import Map
from models.enums import Layer
from utils.find_nearest import find_nearest_transition

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class MoveMixin:
    _location: Map | None = None

    @property
    def location(self: "Character") -> Map:
        if self._location is None:
            raise Exception("Location is not set for this character")
        return self._location

    async def move(self: "Character", destination: Map) -> bool:
        if destination == self.location:
            return True

        if destination.layer != self.location.layer:
            await self._change_layer(destination)
            await self.available
            if destination == self.location:
                return True
        try:
            await self.post_api("/move", json={"map_id": destination.map_id})

            arrived = self.location

            print(
                f"🏃 {self.surname} Moved to ({arrived.x}, {arrived.y}) on {arrived.name} (layer : {arrived.layer.value})"
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
        except Exception as e:
            print(f"❌ {self.surname} transition : {e}")
            return False

    async def _change_layer(self: "Character", destination: Map) -> None:
        if destination.layer == self.location.layer:
            return

        if self.location.layer is Layer.OVERWORLD:
            transition_map = await find_nearest_transition(
                destination, destination.layer
            )
        else:
            transition_map = await find_nearest_transition(
                self.location, destination.layer
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
