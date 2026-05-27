import asyncio

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models.dataclass import Effect, Item, Monster, Resource
from models.enums import JobType


class Encyclopedia:
    _items: dict[str, Item] = {}
    __items_loaded = False

    _effects: dict[str, Effect] = {}
    __effects_loaded = False

    _monsters: dict[str, Monster] = {}
    __monsters_loaded = False

    _resources: dict[str, Resource] = {}
    __resources_loaded = False

    @classmethod
    async def initialize(cls):
        _ = await asyncio.gather(
            cls.__load_items(),
            cls.__load_effects(),
            cls.__load_monsters(),
            cls.__load_resources(),
        )

    # ITEMS

    @classmethod
    async def wait_item(cls) -> None:
        while not cls.__items_loaded:
            _ = await asyncio.sleep(1)

    @staticmethod
    async def get_item_by_code(code: str) -> Item:
        await Encyclopedia.wait_item()

        item = Encyclopedia._items.get(code)
        if not item:
            print(f"❌ Item with code '{code}' not found.")
            return Item(
                name="Missing Item",
                code="missing_item",
                level=0,
                type="",
                subtype="",
                description="",
                conditions=[],
                effects={},
                job=JobType.NO_JOB,
                craft_level=0,
                craft_ingredients=[],
                craft_quantity=0,
                tradeable=False,
            )

        return item

    @staticmethod
    async def get_all_items_names() -> list[str]:
        await Encyclopedia.wait_item()
        return list(Encyclopedia._items)

    @classmethod
    async def __load_items(cls):
        if cls.__items_loaded:
            print("Items already loaded, skipping fetch.")
            return
        async with httpx.AsyncClient() as client:
            page = 1
            max_pages = 2
            while page <= max_pages:
                response = await client.get(
                    f"{ARTIFACTSMMO_URL}/items",
                    headers=HEADERS,
                    params={"size": 500, "page": page},
                    timeout=30.0,
                )
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch items: {response.status_code} - {response.text}"
                    )

                items_data = response.json()
                if not items_data:
                    break  # No more items to fetch

                for item_data in items_data["data"]:
                    item = await Item.from_dict(item_data)
                    cls._items[item.code] = item

                page += 1
                max_pages = items_data["pages"]

        cls.__items_loaded = True
        print(f"Loaded {len(cls._items)} items.")

    # EFFECTS

    @classmethod
    async def wait_effect(cls) -> None:
        while not cls.__effects_loaded:
            _ = await asyncio.sleep(1)

    @staticmethod
    async def get_effect_by_code(code: str) -> Effect:
        await Encyclopedia.wait_effect()

        effect = Encyclopedia._effects.get(code)
        if not effect:
            raise ValueError(f"Effect with code '{code}' not found.")

        return effect

    @classmethod
    async def __load_effects(cls):
        if cls.__effects_loaded:
            print("Effects already loaded, skipping fetch.")
            return

        async with httpx.AsyncClient() as client:
            page = 1
            max_pages = 2
            while page <= max_pages:
                response = await client.get(
                    f"{ARTIFACTSMMO_URL}/effects",
                    headers=HEADERS,
                    params={"size": 100},
                    timeout=30.0,
                )
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch effects: {response.status_code} - {response.text}"
                    )

                effects_data = response.json()
                for effect_data in effects_data["data"]:
                    effect = Effect.from_dict(effect_data)
                    cls._effects[effect.code] = effect

                page += 1
                max_pages = effects_data["pages"]

        cls.__effects_loaded = True
        print(f"Loaded {len(cls._effects)} effects.")

    # MONSTERS

    @classmethod
    async def wait_monster(cls) -> None:
        while not cls.__monsters_loaded:
            _ = await asyncio.sleep(1)

    @staticmethod
    async def get_monster_by_code(code: str) -> Monster:
        await Encyclopedia.wait_monster()

        monster = Encyclopedia._monsters.get(code)
        if not monster:
            raise ValueError(f"Monster with code '{code}' not found.")

        return monster

    @staticmethod
    async def get_all_monsters_names() -> list[str]:
        await Encyclopedia.wait_monster()
        return list(Encyclopedia._monsters)

    @classmethod
    async def __load_monsters(cls):
        if cls.__monsters_loaded:
            print("Monsters already loaded, skipping fetch.")
            return

        async with httpx.AsyncClient() as client:
            page = 1
            max_pages = 2
            while page <= max_pages:
                response = await client.get(
                    f"{ARTIFACTSMMO_URL}/monsters",
                    headers=HEADERS,
                    params={"size": 100, "page": page},
                    timeout=30.0,
                )
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch monsters: {response.status_code} - {response.text}"
                    )

                monsters_data = response.json()
                for monster_data in monsters_data["data"]:
                    monster = await Monster.from_dict(monster_data)
                    cls._monsters[monster.code] = monster

                page += 1
                max_pages = monsters_data["pages"]

        cls.__monsters_loaded = True
        print(f"Loaded {len(cls._monsters)} monsters.")

    # RESOURCES

    @classmethod
    async def wait_resource(cls) -> None:
        while not cls.__resources_loaded:
            _ = await asyncio.sleep(1)

    @staticmethod
    async def get_resource_by_code(code: str) -> Resource:
        await Encyclopedia.wait_resource()

        resource = Encyclopedia._resources.get(code)
        if not resource:
            raise ValueError(f"Resource with code '{code}' not found.")

        return resource

    @classmethod
    async def __load_resources(cls):
        if cls.__resources_loaded:
            print("Resources already loaded, skipping fetch.")
            return

        async with httpx.AsyncClient() as client:
            page = 1
            max_pages = 2
            while page <= max_pages:
                response = await client.get(
                    f"{ARTIFACTSMMO_URL}/resources",
                    headers=HEADERS,
                    params={"size": 50, "page": page},
                    timeout=30.0,
                )
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch resources: {response.status_code} - {response.text}"
                    )

                resources_data = response.json()
                for resource_data in resources_data["data"]:
                    resource = await Resource.from_dict(resource_data)
                    cls._resources[resource.code] = resource

                page += 1
                max_pages = resources_data["pages"]

        cls.__resources_loaded = True
        print(f"Loaded {len(cls._resources)} resources.")
