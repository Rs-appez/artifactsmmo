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
        self._last_message_time = None
        self._message_timeout = 90

    async def connect(self):
        retries = 0
        while True:
            try:
                async with websockets.connect(ARTIFACTSMMO_WS_URL) as websocket:
                    await websocket.send(json.dumps(self.subscription_message))
                    print("Subscribed to websocket events.")
                    retries = 0
                    self._last_message_time = asyncio.get_event_loop().time()
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
        timeout_task = asyncio.create_task(self._check_timeout(websocket))

        try:
            while True:
                message = await websocket.recv()
                self._last_message_time = asyncio.get_event_loop().time()
                await self._handle_message(json.loads(message))

        finally:
            timeout_task.cancel()  # noqa: F821

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

            case SubscriptionsType.RAID_STARTED:
                pass
                # await self._event_handler.start_raid(data["raid"]["monster"])

            case _:
                pass

    async def _check_timeout(self, websocket: ClientConnection):
        while True:
            await asyncio.sleep(self._message_timeout)
            current_time = asyncio.get_event_loop().time()
            if (
                self._last_message_time is not None
                and (current_time - self._last_message_time) > self._message_timeout
            ):
                print("No messages received for a while, reconnecting...")
                await websocket.close()
                break
