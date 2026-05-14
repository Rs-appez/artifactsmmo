from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from models.dataclass import Map
from models.enums import Layer
from utils.find_nearest import find_nearest_transition

from ..decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class MoveMixin(Protocol):
    _location: Map | None = None

    @property
    def location(self: "Character") -> Map:
        if self._location is None:
            raise Exception("Location is not set for this character")
        return self._location

    @request_action
    @refresh_after
    async def move(self: "Character", destination: Map) -> tuple[bool, dict | None]:
        if destination == self.location:
            return True, None

        if destination.layer != self.location.layer:
            await self._change_layer(destination)
            await self.available
        try:
            response = await self.client.post(
                "/move",
                json={"map_id": destination.map_id},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                if data["error"]["code"] == 490:
                    return True, None
                raise Exception(data["error"]["message"])

            arrived = data["data"]["destination"]
            character_data = data["data"]["character"]

            print(
                f"🏃 {self.surname} Moved to ({arrived['x']}, {arrived['y']}) on {arrived['name']}"
            )
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None

    @request_action
    @refresh_after
    async def transition(self: "Character") -> tuple[bool, dict | None]:
        try:
            response = await self.client.post(
                "/transition",
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            destination = data["data"]["destination"]
            character_data = data["data"]["character"]

            print(
                f"󰓡 {self.surname} Transitioned to ({destination['x']}, {destination['y']}) on {destination['name']} layer : {destination['layer']}"
            )
            return True, character_data
        except Exception as e:
            print(f"❌ {e}")
            return False, None

    async def _change_layer(self: "Character", destination: Map) -> None:
        if destination.layer == self.location.layer:
            return

        # if self.location.layer is not Layer.OVERWORLD:
        #     transition_map = await find_nearest_transition(
        #         destination, destination.layer
        #     )
        # else:
        transition_map = await find_nearest_transition(self.location, destination.layer)

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
