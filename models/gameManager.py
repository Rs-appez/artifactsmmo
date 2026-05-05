import asyncio
from collections.abc import Sequence
from typing import Coroutine
import httpx

import routines
from config import ARTIFACTSMMO_URL, HEADERS
from models import Character, CharacterData, Item


class GameManager:
    default_tasks = {
        "bob": routines.copper_farm,
        "alice": routines.spruce_farm,
        "john": routines.iron_farm,
        "jane": routines.shrimp_farm,
        "charlie": routines.yellow_slime_farm,
    }

    jobs = {
        "fishing": "jane",
    }

    def __init__(self):
        self.characters: dict[str, Character] = {}
        self.items: dict[str, Item] = {}
        self.__items_loaded = False

        self.__load_characters()
        self.__assign_default_tasks()

    @property
    async def items_loaded(self) -> bool:
        while not self.__items_loaded:
            _ = await asyncio.sleep(1)
        return self.__items_loaded

    def __load_characters(self):
        with httpx.Client() as client:
            response = client.get(f"{ARTIFACTSMMO_URL}/my/characters", headers=HEADERS)
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch characters: {response.status_code} - {response.text}"
                )

            characters_data = response.json()["data"]
            for char_data in characters_data:
                character = Character(CharacterData.from_dict(char_data))
                self.characters[character.surname] = character

    async def __load_items(self):
        page = 1
        max_pages = 2
        while page <= max_pages:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{ARTIFACTSMMO_URL}/items?page={page}", headers=HEADERS
                )
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch items: {response.status_code} - {response.text}"
                    )

                items_data = response.json()
                if not items_data:
                    break  # No more items to fetch

                for item_data in items_data["data"]:
                    item = Item.from_dict(item_data)
                    self.items[item.code] = item

                page += 1
                max_pages = items_data["pages"]

        self.__items_loaded = True

    def __assign_default_tasks(self):
        for char_name, character in self.characters.items():
            if char_name in self.default_tasks:
                character.assign_routine(self.default_tasks[char_name])
            else:
                print(
                    f"No default task found for {char_name}, skipping task assignment."
                )

    def start(self) -> Sequence[Coroutine]:

        tasks = [char.work() for char in self.characters.values()]
        tasks.append(self.__load_items())
        return tasks

    async def get_item_by_code(self, code: str) -> Item:
        await self.items_loaded

        item = self.items.get(code)
        if not item:
            raise ValueError(f"Item with code '{code}' not found.")

        return item
