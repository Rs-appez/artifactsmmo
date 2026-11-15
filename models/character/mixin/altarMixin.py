from dataclasses import dataclass
from typing import TYPE_CHECKING

from models.dataclass import Offering

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class AltarMixin:
    async def accept_offering(self: Character, offering: Offering):
        endpoint = "/offering/accept"
        json_data = {"offering_id": offering.id}
        response = await self.post_api(endpoint, json_data=json_data)
        return response

    async def complete_offering(self: Character, offering: Offering):
        endpoint = "/offering"
        json_data = {"offering_id": offering.id}
        response = await self.post_api(endpoint, json_data=json_data)
        return response
