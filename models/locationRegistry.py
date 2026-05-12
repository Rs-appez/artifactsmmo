import asyncio

import httpx
from config import ARTIFACTSMMO_URL, HEADERS
from models.dataclass import Monster, Map, Resource
from models.encyclopedia import Encyclopedia
from collections import defaultdict

from models.enums import JobType, TaskType


class LocationRegistry:
    __maps_loaded = False
    __drop_locations: defaultdict[Resource | Monster, set[Map]] = defaultdict(set)
    __bank_locations: set[Map] = set()
    __workshop_locations: dict[JobType, set[Map]] = defaultdict(set)
    __grand_exchange_locations: set[Map] = set()
    __tasks_masters_locations: dict[TaskType, set[Map]] = defaultdict(set)
    # __npc_locations: set[Map] = set()
    __maps: dict[int, Map] = {}

    @classmethod
    async def initialize(cls):
        await cls.__load_locations()

    @classmethod
    async def wait_location(cls) -> None:
        while not cls.__maps_loaded:
            _ = await asyncio.sleep(1)

    @staticmethod
    async def get_locations(entity: Resource | Monster) -> set[tuple[int, int]]:
        await LocationRegistry.wait_location()
        maps = LocationRegistry.__drop_locations.get(entity)
        return {(map.x, map.y) for map in maps} if maps else set()

    @staticmethod
    async def get_map_by_id(map_id: int) -> Map:
        await LocationRegistry.wait_location()
        return LocationRegistry.__maps[map_id]

    @staticmethod
    async def get_bank_locations() -> set[tuple[int, int]]:
        await LocationRegistry.wait_location()
        return {(map.x, map.y) for map in LocationRegistry.__bank_locations}

    @staticmethod
    async def get_workshop_locations(job: JobType) -> set[tuple[int, int]]:
        await LocationRegistry.wait_location()
        maps = LocationRegistry.__workshop_locations.get(job, set())
        return {(map.x, map.y) for map in maps}

    @staticmethod
    async def get_grand_exchange_locations() -> set[tuple[int, int]]:
        await LocationRegistry.wait_location()
        return {(map.x, map.y) for map in LocationRegistry.__grand_exchange_locations}

    @classmethod
    async def __load_locations(cls):
        if cls.__maps_loaded:
            print("Maps already loaded.")
            return

        async with httpx.AsyncClient() as client:
            page = 1
            max_pages = 2
            while page <= max_pages:
                response = await client.get(
                    f"{ARTIFACTSMMO_URL}/maps",
                    headers=HEADERS,
                    params={"size": 500, "page": page},
                )
                data = response.json()
                if "error" in data:
                    print("data : ", data)
                    raise Exception(data["error"]["message"])
                locations_data = data["data"]

                for location in locations_data:
                    map = Map.from_dict(location)
                    cls.__maps[map.map_id] = map

                    if interaction := location.get("interactions"):
                        if content := interaction.get("content"):
                            match content["type"]:
                                case "resource":
                                    resource = await Encyclopedia.get_resource_by_code(
                                        content["code"]
                                    )
                                    cls.__drop_locations[resource].add(map)
                                case "monster":
                                    resource = await Encyclopedia.get_monster_by_code(
                                        content["code"]
                                    )
                                    cls.__drop_locations[resource].add(map)
                                case "bank":
                                    cls.__bank_locations.add(map)
                                case "workshop":
                                    job_type = JobType(content["code"])
                                    cls.__workshop_locations[job_type].add(map)
                                case "grand_exchange":
                                    cls.__grand_exchange_locations.add(map)
                                case "tasks_master":
                                    task_type = TaskType(content["code"])
                                    cls.__tasks_masters_locations[task_type].add(map)
                                case "npc":
                                    pass  # For now, we won't store NPC locations
                                case _:
                                    raise Exception(
                                        f"Unknown interaction type: {interaction['content']['type']}"
                                    )
                page += 1
                max_pages = data["pages"]

            cls.__maps_loaded = True
            print(f"Loaded {len(cls.__maps)} maps.")
