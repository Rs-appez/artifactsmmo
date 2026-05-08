import asyncio

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models.dataclass import Effect, Item, Monster


class Encyclopedia:
    items: dict[str, Item] = {}
    __items_loaded = False

    effects: dict[str, Effect] = {}
    __effects_loaded = False

    monsters: dict[str, Monster] = {}
    __monsters_loaded = False

    @classmethod
    async def initialize(cls):
        _ = await asyncio.gather(
            cls.load_items(),
            # cls.load_effects(),
            # cls.load_monsters(),
        )

    # ITEMS

    @classmethod
    async def wait_item(cls) -> None:
        while not cls.__items_loaded:
            _ = await asyncio.sleep(1)

    @staticmethod
    async def get_item_by_code(code: str) -> Item:
        await Encyclopedia.wait_item()

        item = Encyclopedia.items.get(code)
        if not item:
            raise ValueError(f"Item with code '{code}' not found.")

        return item

    @classmethod
    async def load_items(cls):
        if cls.__items_loaded:
            print("Items already loaded, skipping fetch.")
            return
        page = 1
        max_pages = 2
        while page <= max_pages:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{ARTIFACTSMMO_URL}/items",
                    headers=HEADERS,
                    params={"size": 500, "page": page},
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
                    Encyclopedia.items[item.code] = item

                page += 1
                max_pages = items_data["pages"]

        Encyclopedia.__items_loaded = True

    # EFFECTS

    @classmethod
    async def wait_effect(cls) -> None:
        while not cls.__effects_loaded:
            _ = await asyncio.sleep(1)

    @staticmethod
    async def get_effect_by_code(code: str) -> Effect:
        await Encyclopedia.wait_effect()

        effect = Encyclopedia.effects.get(code)
        if not effect:
            raise ValueError(f"Effect with code '{code}' not found.")

        return effect

    # MONSTERS

    @classmethod
    async def wait_monster(cls) -> None:
        while not cls.__monsters_loaded:
            _ = await asyncio.sleep(1)
