import asyncio
from collections.abc import Coroutine, Sequence

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models import Character, Encyclopedia, LocationRegistry
from routines.monster_farm import boss_farm
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
        # tmp test boss fight
        await self.__asign_boss()
        tasks = [char.start() for char in self.characters.values()]
        return tasks

    async def __asign_boss(self):
        boss = await Encyclopedia.get_monster_by_code("king_slime")
        john = self.characters.get("john")
        jane = self.characters.get("jane")
        bob = self.characters.get("bob")

        team = [john, jane, bob]

        if jane:
            jane.assign_routine(boss_farm, team, boss)

        if bob:
            bob.assign_routine(boss_farm, team, boss, True)

        if john:
            john.assign_routine(boss_farm, team, boss)
