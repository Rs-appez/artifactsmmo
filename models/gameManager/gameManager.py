import asyncio
from collections.abc import Coroutine, Sequence

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models import Character, Encyclopedia, LocationRegistry
from .mixins import JobMixin


class GameManager(JobMixin):
    def __init__(self):
        self.characters: dict[str, Character] = {}

        _ = asyncio.ensure_future(
            asyncio.gather(
                Encyclopedia.initialize(),
                LocationRegistry.initialize(),
            )
        )

    async def __load_characters(self):
        with httpx.Client() as client:
            response = client.get(f"{ARTIFACTSMMO_URL}/my/characters", headers=HEADERS)
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch characters: {response.status_code} - {response.text}"
                )

            characters_data = response.json()["data"]
            for char_data in characters_data:
                character = await Character.from_dict(char_data)
                self.characters[character.surname] = character

    async def start(self) -> Sequence[Coroutine]:

        await self.__load_characters()
        tasks = [char.start() for char in self.characters.values()]
        return tasks
