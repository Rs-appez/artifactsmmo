import asyncio
from collections.abc import Coroutine, Sequence

import httpx

import routines
from config import ARTIFACTSMMO_URL, HEADERS
from models import Character, Encyclopedia
from .mixins import JobMixin


class GameManager(JobMixin):
    default_tasks = {
        "bob": (routines.shrimp_farm, []),
        "alice": (routines.mob_farm, ["chicken"]),
        "john": (routines.coal_farm, []),
        "jane": (routines.mob_farm, ["cow"]),
        "charlie": (routines.iron_farm, []),
    }

    def __init__(self):
        self.characters: dict[str, Character] = {}

        _ = asyncio.ensure_future(Encyclopedia.initialize())

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

    def __assign_default_tasks(self):
        for char_name, character in self.characters.items():
            if char_name in self.default_tasks:
                character.assign_routine(
                    self.default_tasks[char_name][0], *self.default_tasks[char_name][1]
                )
                print(
                    f"🚀 {character.surname} started working on routine {character.work_on}"
                )
            else:
                print(
                    f"No default task found for {char_name}, skipping task assignment."
                )

    async def start(self) -> Sequence[Coroutine]:

        await self.__load_characters()
        self.__assign_default_tasks()
        tasks = [char.start() for char in self.characters.values()]
        return tasks
