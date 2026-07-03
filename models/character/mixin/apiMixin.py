import asyncio
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
    def client(self) -> httpx.AsyncClient:
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
        attempt = 0
        while attempt < 3:
            try:
                response = await self.client.post(endpoint, json=json, timeout=2.0)
                data = response.json()

                if "error" in data:
                    match data["error"]["code"]:
                        case 499:
                            await self.refresh()
                            raise httpx.RequestError(
                                "Cooldown desynchronization detected. Refreshing character data..."
                            )
                        case _:
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

                break
            except httpx.RequestError as e:
                print(f"Attempt {attempt} failed: {e}. Retrying...")
                await asyncio.sleep(2**attempt)
                attempt += 1
        else:
            raise Exception("Failed to post API after 3 attempts.")

        return character_data
