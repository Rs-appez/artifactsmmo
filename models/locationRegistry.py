import asyncio
from collections import defaultdict

import httpx

from config import ARTIFACTSMMO_URL, HEADERS
from models.dataclass import NPC, Event, Map, Monster, Resource
from models.encyclopedia import Encyclopedia
from models.enums import JobType, Layer, TaskType


class LocationRegistry:
    __maps_loaded = False
    __drop_locations: defaultdict[Resource | Monster, set[Map]] = defaultdict(set)
    __bank_locations: set[Map] = set()
    __workshop_locations: dict[JobType, set[Map]] = defaultdict(set)
    __grand_exchange_locations: set[Map] = set()
    __tasks_masters_locations: dict[TaskType, set[Map]] = defaultdict(set)
    __transition_locations: dict[Layer, set[int]] = defaultdict(set)
    __npc_locations: defaultdict[NPC, set[Map]] = defaultdict(set)
    __maps: dict[int, Map] = {}

    @classmethod
    async def initialize(cls):
        await cls.__load_locations()

    @classmethod
    async def wait_location(cls) -> None:
        while not cls.__maps_loaded:
            _ = await asyncio.sleep(1)

    @staticmethod
    async def get_locations(entity: Resource | Monster) -> set[Map]:
        await LocationRegistry.wait_location()
        return LocationRegistry.__drop_locations.get(entity, set())

    @staticmethod
    async def get_map_by_id(map_id: int) -> Map:
        await LocationRegistry.wait_location()
        return LocationRegistry.__maps[map_id]

    @staticmethod
    async def get_bank_locations() -> set[Map]:
        await LocationRegistry.wait_location()
        return LocationRegistry.__bank_locations.difference(
            {await LocationRegistry.get_map_by_id(1234)}
        )

    @staticmethod
    async def get_npc_locations(npc: NPC) -> set[Map]:
        await LocationRegistry.wait_location()
        return LocationRegistry.__npc_locations.get(npc, set())

    @staticmethod
    async def get_workshop_locations(job: JobType) -> set[Map]:
        await LocationRegistry.wait_location()
        return LocationRegistry.__workshop_locations.get(job, set())

    @staticmethod
    async def get_grand_exchange_locations() -> set[Map]:
        await LocationRegistry.wait_location()
        return LocationRegistry.__grand_exchange_locations

    @staticmethod
    async def get_tasks_master_locations(task_type: TaskType | None = None) -> set[Map]:
        await LocationRegistry.wait_location()
        if task_type is None:
            return set.union(*LocationRegistry.__tasks_masters_locations.values())
        return LocationRegistry.__tasks_masters_locations.get(task_type, set())

    @staticmethod
    async def get_transition_locations(layer: Layer) -> set[Map]:
        await LocationRegistry.wait_location()
        maps_id = LocationRegistry.__transition_locations.get(layer, set())
        return {LocationRegistry.__maps[map_id] for map_id in maps_id}

    @staticmethod
    def add_event_location(map: Map, event: Event) -> None:
        if event.content is None:
            return

        match event.content:
            case Monster() | Resource():
                LocationRegistry.__drop_locations[event.content].add(map)
            case NPC():
                LocationRegistry.__npc_locations[event.content].add(map)

    @staticmethod
    def remove_event_location(map: Map, event: Event) -> None:
        if event.content is None:
            return

        match event.content:
            case Monster() | Resource():
                LocationRegistry.__drop_locations[event.content].discard(map)
            case NPC():
                LocationRegistry.__npc_locations[event.content].discard(map)

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
                    params={"size": 500, "page": page, "hide_blocked_maps": True},
                    timeout=30,
                )
                data = response.json()
                if "error" in data:
                    print("data : ", data)
                    raise Exception(data["error"]["message"])
                locations_data = data["data"]

                for location in locations_data:
                    map = await Map.from_dict(location)
                    cls.__maps[map.map_id] = map

                    if interaction := location.get("interactions"):
                        if transition := interaction.get("transition"):
                            layer = Layer(transition["layer"])
                            cls.__transition_locations[layer].add(map.map_id)

                        if content := interaction.get("content"):
                            match content["type"]:
                                case "resource":
                                    resource = await Encyclopedia.get_resource_by_code(
                                        content["code"]
                                    )
                                    cls.__drop_locations[resource].add(map)
                                case "monster":
                                    if content["code"]:
                                        resource = (
                                            await Encyclopedia.get_monster_by_code(
                                                content["code"]
                                            )
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
                                    npc = await Encyclopedia.get_npc_by_code(
                                        content["code"]
                                    )
                                    cls.__npc_locations[npc].add(map)
                                case "raid":
                                    pass
                                case _:
                                    raise Exception(
                                        f"Unknown interaction type: {interaction['content']['type']}"
                                    )
                page += 1
                max_pages = data["pages"]

            cls.__maps_loaded = True
            print(f"Loaded {len(cls.__maps)} maps.")
