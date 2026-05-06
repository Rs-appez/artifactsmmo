import asyncio
from datetime import datetime

import httpx

from config import ARTIFACTSMMO_URL, HEADERS, TIMEZONE
from models.enums import Layer

from .character_data import CharacterData
from .decorators import refresh_after
from .mixin import (
    BankMixin,
    CraftMixin,
    FightMixin,
    GatherMixin,
    MoveMixin,
    WorkMixin,
)


class Character(
    BankMixin,
    WorkMixin,
    MoveMixin,
    FightMixin,
    GatherMixin,
    CraftMixin,
):
    def __init__(self, data: CharacterData):
        self.__name = data.name
        self.__surname = data.surname
        self.__url = f"{ARTIFACTSMMO_URL}/my/{self.name}"
        self.__client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

        self.__current_location = data.location
        self.__current_layer = data.layer
        self.__current_map_id = data.map

        self.__cooldown = data.cooldown

        self.__hp = data.hp
        self.__max_hp = data.max_hp
        self.__level = data.level
        self.__xp = data.xp
        self.__max_xp = data.max_xp
        self.__gold = data.gold
        self.__inventory = data.inventory
        self.__inventory_max_items = data.inventory_max_items

        self.__jobs = data.jobs

    @property
    def name(self):
        return self.__name

    @property
    def surname(self):
        return self.__surname

    @property
    def url(self):
        return self.__url

    @property
    def client(self):
        return self.__client

    @property
    def location(self) -> tuple[int, int]:
        return self.__current_location

    @property
    def layer(self) -> Layer:
        return self.__current_layer

    @property
    def map(self) -> int:
        return self.__current_map_id

    @property
    def cooldown(self) -> float:
        return (self.__cooldown - datetime.now(TIMEZONE)).total_seconds()

    @property
    async def available(self):
        while True:
            remaining = self.cooldown
            if remaining <= 0:
                break
            await asyncio.sleep(min(3.0, self.cooldown))

    @property
    def hp(self) -> int:
        return self.__hp

    @property
    def max_hp(self) -> int:
        return self.__max_hp

    @property
    def xp(self) -> int:
        return self.__xp

    @property
    def max_xp(self) -> int:
        return self.__max_xp

    @property
    def level(self) -> int:
        return self.__level

    @property
    def gold(self) -> int:
        return self.__gold

    @property
    def inventory(self) -> dict[str, int]:
        return self.__inventory.copy()

    @property
    def inventory_max_items(self) -> int:
        return self.__inventory_max_items

    @property
    def is_inventory_full(self) -> bool:
        return (
            sum(self.__inventory.values()) >= self.__inventory_max_items - 5
            or len(self.__inventory) >= 17
        )

    def get_job_level(self, job_name: str) -> int:
        return self.__jobs.get(job_name, 0)

    def has_job(self: "Character", job_name: str, level=1) -> bool:
        return self.__jobs.get(job_name, 0) >= level

    @refresh_after
    async def refresh(self) -> tuple[bool, dict | None]:
        try:
            response = await self.__client.get(
                f"{ARTIFACTSMMO_URL}/characters/{self.name}", headers=HEADERS
            )
            data = response.json()
            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])
            character_data = data["data"]
            return True, character_data

        except Exception as e:
            print(f"❌ {e}")
            return False, None

    def refresh_data(self, data: CharacterData):
        self.__current_location = data.location
        self.__current_layer = data.layer
        self.__current_map_id = data.map
        self.__cooldown = data.cooldown
        self.__hp = data.hp
        self.__max_hp = data.max_hp
        self.__xp = data.xp
        self.__max_xp = data.max_xp
        self.__level = data.level
        self.__gold = data.gold
        self.__inventory = data.inventory
        self.__inventory_max_items = data.inventory_max_items
        self.__jobs = data.jobs
