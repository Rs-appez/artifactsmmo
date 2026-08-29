from httpx import AsyncClient

from config import ARTIFACTSMMO_URL, HEADERS
from models import CharacterManager, LocationRegistry, Encyclopedia
from models.dataclass import Event, Map


class EventHandler:
    current_events: list[tuple[Event, Map]] = []

    def __init__(self, CharacterManager: CharacterManager):
        self.character_manager = CharacterManager

    async def refresh_current_events(self) -> None:
        for event in self.current_events:
            LocationRegistry.remove_event_location(event[1], event[0])

        self.current_events = await self.__get_current_events()
        if not self.current_events:
            return

        for event, map_location in self.current_events:
            LocationRegistry.add_event_location(map_location, event)

    async def __get_current_events(self) -> list[tuple[Event, Map]]:
        from models import Encyclopedia

        try:
            async with AsyncClient() as client:
                response = await client.get(
                    f"{ARTIFACTSMMO_URL}/events/active", headers=HEADERS
                )
                _ = response.raise_for_status()
                events_data = response.json()
                return [
                    (
                        await Encyclopedia.get_event_by_code(event["code"]),
                        await LocationRegistry.get_map_by_id(event["map"]["map_id"]),
                    )
                    for event in events_data["data"]
                ]
        except Exception as e:
            print(f"Error fetching current events: {e}")
            return []

    async def add_event(self, event: Event, map: Map) -> None:
        self.current_events.append((event, map))
        LocationRegistry.add_event_location(map, event)
        self.character_manager.new_event_occurred(event)

    async def remove_event(self, event: Event, map: Map) -> None:
        self.current_events = [
            (e, m) for e, m in self.current_events if not (e == event and m == map)
        ]
        LocationRegistry.remove_event_location(map, event)

    async def start_raid(self, raid_boss_code: str) -> None:
        boss = await Encyclopedia.get_monster_by_code(raid_boss_code)
        self.character_manager.start_raid(boss)
