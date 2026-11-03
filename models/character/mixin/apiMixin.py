import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from config import ARTIFACTSMMO_URL, HEADERS, MAX_RETRY_ATTEMPTS
from exceptions import TimeoutButSuccessException, TimeoutNotSuccessException
from models.character.decorators import refresh_after, request_action

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class ApiMixin:
    _client: httpx.AsyncClient | None = None

    def __init_api_mixin__(self: Character):
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
        self: Character,
        endpoint: str,
        json_data: dict | list[dict] | None = None,
        retreive_data: dict[str, dict] | None = None,
    ) -> dict:
        attempt = 0
        while attempt < MAX_RETRY_ATTEMPTS:
            try:
                response = await self.client.post(endpoint, json=json_data, timeout=5.0)
                data = response.json()

                if "error" in data:
                    if "code" in data["error"]:
                        match data["error"]["code"]:
                            case _:
                                raise Exception(data["error"]["message"])
                    raise TimeoutNotSuccessException(data["error"])

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

                if retreive_data:
                    for key, value in retreive_data.items():
                        if key in data:
                            value.update(data[key])

                break

            except (httpx.TimeoutException, TimeoutNotSuccessException) as e:
                print(f"Attempt {attempt} failed: Timeout occurred. Retrying...")
                await self.refresh()
                if self.cooldown > 0:
                    print("Request timeout but succeded")
                    raise TimeoutButSuccessException("Request timeout but succeded")
                attempt = await self._retry(attempt, e)

            except httpx.RequestError as e:
                await self.refresh()
                if self.cooldown > 0:
                    print("Request error but succeded")
                    raise TimeoutButSuccessException("Request timeout but succeded")
                attempt = await self._retry(attempt, e)
        else:
            raise Exception(f"Failed to post API after {MAX_RETRY_ATTEMPTS} attempts.")

        return character_data

    async def _retry(self, attempt: int, e: Exception) -> int:
        print(f"Attempt {attempt} failed: {e}. Retrying...")
        await asyncio.sleep(2**attempt)
        return attempt + 1
