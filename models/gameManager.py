from collections.abc import Coroutine
import httpx

import routines
from config import ARTIFACTSMMO_URL, HEADERS
from models import Character, CharacterData, Item


class GameManager:
    default_tasks = {
        "bob": routines.yellow_slime_farm,
        "alice": routines.spruce_farm,
        "john": routines.iron_farm,
        "jane": routines.shrimp_farm,
        "charlie": routines.sunflower_farm,
    }

    jobs = {
        "fishing": "jane",
    }

    def __init__(self):
        self.characters: dict[str, Character] = {}
        self.items: dict[str, Item] = {}

        self.__load_items()
        print(f"Loaded {len(self.items)} items.")
        print(f"{self.items['raw_beef']}")
        self.__load_characters()

        self.__assign_default_tasks()

    def __load_characters(self):
        with httpx.Client() as client:
            response = client.get(f"{ARTIFACTSMMO_URL}/my/characters", headers=HEADERS)
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch characters: {response.status_code} - {response.text}"
                )

            characters_data = response.json()["data"]
            for char_data in characters_data:
                char_name = char_data["name"][3:]
                self.characters[char_name] = Character(
                    CharacterData.from_dict(char_data)
                )

    def __load_items(self):
        page = 1
        max_pages = 5  # Limit to prevent infinite loops
        while page <= max_pages:
            with httpx.Client() as client:
                response = client.get(
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

    def __assign_default_tasks(self):
        for char_name, character in self.characters.items():
            if char_name in self.default_tasks:
                character.assign_routine(self.default_tasks[char_name])
            else:
                print(
                    f"No default task found for {char_name}, skipping task assignment."
                )

    def start(self) -> list[Coroutine]:

        return [char.work() for char in self.characters.values()]
