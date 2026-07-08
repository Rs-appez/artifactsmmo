import asyncio
from collections.abc import Coroutine, Sequence

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models import Character, CharacterManager, Encyclopedia, LocationRegistry
from models.event import EventHandler, EventListener
from routines.monster_farm import boss_farm
from utils.initialize import initialize_characters


class GameManager:
    characters: dict[str, Character] = {}
    character_manager = CharacterManager(characters)
    event_handler = EventHandler(character_manager)
    event_listener = EventListener(event_handler)

    def __init__(self):
        _ = asyncio.ensure_future(
            asyncio.gather(
                Encyclopedia.initialize(),
                LocationRegistry.initialize(),
                self.event_listener.connect(),
                self.event_handler.refresh_current_events(),
            )
        )

    async def __load_characters(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ARTIFACTSMMO_URL}/my/characters", headers=HEADERS
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch characters: {response.status_code} - {response.text}"
                )

            characters_data = response.json()["data"]
            self.characters.clear()
            for char_data in characters_data:
                character = await Character.from_dict(char_data)
                self.characters[character.surname] = character

    async def start(self) -> Sequence[Coroutine]:

        await self.__load_characters()
        # tmp test boss fight
        # await self.__asign_boss()
        tasks = [char.start() for char in self.characters.values()]
        return tasks

    async def create_characters(self):
        try:
            await self.__load_characters()
            if self.characters:
                raise Exception("Characters already exist. No need to create new ones.")
            await initialize_characters()
        except Exception as e:
            print(f"Error loading characters: {e}")

    def save_characters(self):
        for character in self.characters.values():
            character.save()

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
