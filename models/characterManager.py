import httpx

import routines
from config import ARTIFACTSMMO_URL, HEADERS
from models import Character, CharacterData


class CharacterManager:
    default_tasks = {
        "bob": routines.yellow_slime_farm,
        "alice": routines.spruce_farm,
        "john": routines.iron_farm,
        "jane": routines.shrimp_farm,
        "charlie": routines.sunflower_farm,
    }

    def __init__(self):
        self.characters: dict[str, Character] = {}
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
