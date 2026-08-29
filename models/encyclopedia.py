import asyncio
import json

from config import DATA_DIR
from models.dataclass import NPC, Effect, Event, Item, Monster, Resource, Raid
from models.enums import JobType


class Encyclopedia:
    _items: dict[str, Item] = {}
    __items_loaded = asyncio.Event()

    _effects: dict[str, Effect] = {}
    __effects_loaded = asyncio.Event()

    _monsters: dict[str, Monster] = {}
    __monsters_loaded = asyncio.Event()

    _resources: dict[str, Resource] = {}
    __resources_loaded = asyncio.Event()

    _events: dict[str, Event] = {}
    __events_loaded = asyncio.Event()

    __npcs: dict[str, NPC] = {}
    __npcs_loaded = asyncio.Event()

    _raids: dict[str, Raid] = {}
    __raids_loaded = asyncio.Event()

    @classmethod
    async def initialize(cls):
        _ = await asyncio.gather(
            cls.__load_items(),
            cls.__load_effects(),
            cls.__load_monsters(),
            cls.__load_resources(),
            cls.__load_npcs(),
            cls.__load_events(),
            cls.__load_raids(),
        )

    # ITEMS

    @staticmethod
    async def get_item_by_code(code: str) -> Item:
        await Encyclopedia.__items_loaded.wait()

        item = Encyclopedia._items.get(code)

        if not item:
            raise ValueError(f"Item with code '{code}' not found.")

        return item

    @staticmethod
    async def get_all_items_names() -> list[str]:
        await Encyclopedia.__items_loaded.wait()
        return list(Encyclopedia._items)

    @staticmethod
    async def get_all_food() -> set[Item]:
        await Encyclopedia.__items_loaded.wait()
        return {item for item in Encyclopedia._items.values() if item.is_food}

    @staticmethod
    async def get_all_items_by_job(job: JobType, level: int = -1) -> set[Item]:
        await Encyclopedia.__items_loaded.wait()
        return {
            item
            for item in Encyclopedia._items.values()
            if item.job == job and (item.level <= level or level == -1)
        }

    @classmethod
    async def __load_items(cls):
        if cls.__items_loaded.is_set():
            print("Items already loaded, skipping fetch.")
            return
        items_data = await cls.__read_json_file(DATA_DIR + "items_data.json")

        for item_data in items_data:
            item = await Item.from_dict(item_data)
            cls._items[item.code] = item

        cls.__items_loaded.set()
        print(f"Loaded {len(cls._items)} items.")

    # EFFECTS

    @staticmethod
    async def get_effect_by_code(code: str) -> Effect:
        await Encyclopedia.__effects_loaded.wait()

        effect = Encyclopedia._effects.get(code)
        if not effect:
            raise ValueError(f"Effect with code '{code}' not found.")

        return effect

    @classmethod
    async def __load_effects(cls):
        if cls.__effects_loaded.is_set():
            print("Effects already loaded, skipping fetch.")
            return

        effects_data = await cls.__read_json_file(DATA_DIR + "effects_data.json")

        for effect_data in effects_data:
            effect = Effect.from_dict(effect_data)
            cls._effects[effect.code] = effect

        cls.__effects_loaded.set()
        print(f"Loaded {len(cls._effects)} effects.")

    # MONSTERS

    @staticmethod
    async def get_monster_by_code(code: str) -> Monster:
        await Encyclopedia.__monsters_loaded.wait()

        monster = Encyclopedia._monsters.get(code)
        if not monster:
            raise ValueError(f"Monster with code '{code}' not found.")

        return monster

    @staticmethod
    async def get_all_monsters_names() -> list[str]:
        await Encyclopedia.__monsters_loaded.wait()
        return list(Encyclopedia._monsters)

    @staticmethod
    async def get_monsters_by_drop(item: Item) -> set[Monster]:
        await Encyclopedia.__monsters_loaded.wait()
        return {
            monster
            for monster in Encyclopedia._monsters.values()
            if any(item in drop for drop in monster.drops)
        }

    @classmethod
    async def __load_monsters(cls):
        if cls.__monsters_loaded.is_set():
            print("Monsters already loaded, skipping fetch.")
            return

        monsters_data = await cls.__read_json_file(DATA_DIR + "monsters_data.json")

        for monster_data in monsters_data:
            monster = await Monster.from_dict(monster_data)
            cls._monsters[monster.code] = monster

        cls.__monsters_loaded.set()
        print(f"Loaded {len(cls._monsters)} monsters.")

    # RESOURCES

    @staticmethod
    async def get_resource_by_code(code: str) -> Resource:
        await Encyclopedia.__resources_loaded.wait()

        resource = Encyclopedia._resources.get(code)
        if not resource:
            raise ValueError(f"Resource with code '{code}' not found.")

        return resource

    @staticmethod
    async def get_all_resources_by_job(job: JobType, level: int = -1) -> set[Resource]:
        await Encyclopedia.__resources_loaded.wait()
        return {
            resource
            for resource in Encyclopedia._resources.values()
            if resource.skill == job and (resource.level <= level or level == -1)
        }

    @classmethod
    async def __load_resources(cls):
        if cls.__resources_loaded.is_set():
            print("Resources already loaded, skipping fetch.")
            return

        resources_data = await cls.__read_json_file(DATA_DIR + "resources_data.json")

        for resource_data in resources_data:
            resource = await Resource.from_dict(resource_data)
            cls._resources[resource.code] = resource

        cls.__resources_loaded.set()
        print(f"Loaded {len(cls._resources)} resources.")

    # EVENTS

    @staticmethod
    async def get_event_by_code(code: str) -> Event:
        await Encyclopedia.__events_loaded.wait()

        event = Encyclopedia._events.get(code)
        if not event:
            raise ValueError(f"Event with code '{code}' not found.")

        return event

    @staticmethod
    async def get_all_events() -> set[Event]:
        await Encyclopedia.__events_loaded.wait()
        return set(Encyclopedia._events.values())

    @classmethod
    async def __load_events(cls):
        if cls.__events_loaded.is_set():
            print("Events already loaded, skipping fetch.")
            return
        events_data = await cls.__read_json_file(DATA_DIR + "events_data.json")
        for event_data in events_data:
            event = await Event.from_dict(event_data)
            cls._events[event.code] = event

        cls.__events_loaded.set()
        print(f"Loaded {len(cls._events)} events.")

    # NPCS

    @staticmethod
    async def get_npc_by_code(code: str) -> NPC:
        await Encyclopedia.__npcs_loaded.wait()

        npc = Encyclopedia.__npcs.get(code)
        if not npc:
            raise ValueError(f"NPC with code '{code}' not found.")

        return npc

    @classmethod
    async def __load_npcs(cls):
        if cls.__npcs_loaded.is_set():
            print("NPCs already loaded, skipping fetch.")
            return

        npcs_data = await cls.__read_json_file(DATA_DIR + "npcs_data.json")
        for npc_data in npcs_data:
            npc = await NPC.from_dict(npc_data)
            cls.__npcs[npc.code] = npc

        cls.__npcs_loaded.set()
        print(f"Loaded {len(cls.__npcs)} NPCs.")

    # RAID

    @staticmethod
    async def get_raid_by_code(code: str) -> Raid:
        await Encyclopedia.__raids_loaded.wait()

        raid = Encyclopedia._raids.get(code)
        if not raid:
            raise ValueError(f"Raid with code '{code}' not found.")

        return raid

    @classmethod
    async def __load_raids(cls):
        if cls.__raids_loaded.is_set():
            print("Raids already loaded, skipping fetch.")
            return

        raids_data = await cls.__read_json_file(DATA_DIR + "raids_data.json")
        for raid_data in raids_data:
            raid = await Raid.from_dict(raid_data)
            cls._raids[raid.code] = raid

        cls.__raids_loaded.set()
        print(f"Loaded {len(cls._raids)} Raids.")

    @staticmethod
    async def __read_json_file(filepath: str) -> dict:
        """Read JSON file asynchronously without blocking the event loop."""

        def _read():
            with open(filepath, "r") as f:
                return json.load(f)

        try:
            res = await asyncio.to_thread(_read)
        except Exception as e:
            print(f"❌ Failed to read JSON file {filepath}: {e}")
            print("Launch fecth first")
            raise e

        return res
