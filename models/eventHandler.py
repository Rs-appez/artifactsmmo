from models.dataclass import Map, Event
from models import LocationRegistry
from httpx import AsyncClient
from config import ARTIFACTSMMO_URL, HEADERS


class EventHandler:
    current_events: list[tuple[Event, Map]] = []

    async def refresh_current_events(self) -> None:
        for event in self.current_events:
            LocationRegistry.remove_event_location(event[1], event[0])

        self.current_events = await self.__get_current_events()
        if not self.current_events:
            print("No active events found.")
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
