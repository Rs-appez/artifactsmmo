from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models.character.decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class ApiMixin:
    _client: httpx.AsyncClient | None = None

    def __init_api_mixin__(self: "Character"):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=HEADERS,
            base_url=f"{ARTIFACTSMMO_URL}/my/{self.name}/action",
        )

    @property
    def client(self):
        if self._client is None:
            raise Exception(
                "Client is not initialized. Call __init_api_mixin__() first."
            )
        return self._client

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
