import httpx

from config import ARTIFACTSMMO_URL, HEADERS, SANDBOX
import os

CHARACTERS = {
    "alice": "women2",
    "bob": "goblin",
    "charlie": "men1",
    "dave": "men3",
    "eve": "women3",
}
SUFFIX = "_t" if SANDBOX else ""


async def initialize_characters():
    for name, skin in CHARACTERS.items():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ARTIFACTSMMO_URL}/characters/create",
                headers=HEADERS,
                json={"name": f"rs_{name}{SUFFIX}", "skin": skin},
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to create character {name}: {response.status_code} - {response.text}"
                )
            print(f"Character {name} created successfully.")

    __restet_saves()


def __restet_saves():
    save_folder = "saves"
    for character_name in CHARACTERS.keys():
        save_file_path = f"{save_folder}/rs_{character_name}{SUFFIX}.json"
        with open(save_file_path, "w") as f:
            _ = f.write("{}")
