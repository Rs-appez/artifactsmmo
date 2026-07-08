import asyncio
import json

import websockets
from websockets import ClientConnection

from config import ARTIFACTSMMO_API_KEY, ARTIFACTSMMO_WS_URL
from models import Encyclopedia, LocationRegistry
from models.event import EventHandler

from .subscriptionsType import SubscriptionsType


class EventListener:
    subscription_message = {
        "token": ARTIFACTSMMO_API_KEY,
        "subscribe": [v.value for v in SubscriptionsType],
    }

    def __init__(self, event_handler: EventHandler):
        self._event_handler = event_handler

    async def connect(self):
        retries = 0
        while True:
            try:
                async with websockets.connect(ARTIFACTSMMO_WS_URL) as websocket:
                    await websocket.send(json.dumps(self.subscription_message))
                    print("Subscribed to websocket events.")
                    retries = 0
                    await self._listen(websocket)

            except asyncio.CancelledError:
                print("Closing websocket connection due to cancellation.")
                break

            except websockets.ConnectionClosed:
                print("Connection closed, attempting to reconnect...")
                await asyncio.sleep(pow(2, retries))
                retries = min(retries + 1, 5)
                continue

            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    async def _listen(self, websocket: ClientConnection):

        while True:
            message = await websocket.recv()
            await self._handle_message(json.loads(message))

    async def _handle_message(self, message: dict):
        event_type = message["type"]
        data = message["data"]

        match event_type:
            case SubscriptionsType.EVENT_SPAWN | SubscriptionsType.EVENT_REMOVED:
                event = await Encyclopedia.get_event_by_code(data["code"])
                map = await LocationRegistry.get_map_by_id(data["map"]["map_id"])
                if event_type == SubscriptionsType.EVENT_SPAWN:
                    await self._event_handler.add_event(event, map)
                else:
                    await self._event_handler.remove_event(event, map)

            case _:
                pass
