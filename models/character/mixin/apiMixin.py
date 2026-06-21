from typing import TYPE_CHECKING, Protocol

from models.character.decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


class ApiMixin(Protocol):
    @request_action
    @refresh_after
    async def post_api(
        self: "Character", endpoint: str, json: dict | list[dict] | None = None
    ) -> dict:
        response = await self.client.post(endpoint, json=json)
        data = response.json()

        if "error" in data:
            print("data : ", data)
            raise Exception(data["error"]["message"])

        data = data["data"]
        character_data = {}
        if "character" not in data:
            characters = data["characters"]
            for character in characters:
                if character["name"] == self.name:
                    character_data = character
                    break
        else:
            character_data = data["character"]

        return character_data
