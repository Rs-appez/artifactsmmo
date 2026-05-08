import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import override

import httpx

from config import ARTIFACTSMMO_URL, HEADERS, TIMEZONE
from models.enums import Layer

from .decorators import refresh_after
from .mixin import (
    BankMixin,
    CraftMixin,
    FightMixin,
    GatherMixin,
    MoveMixin,
    TaskMixin,
    WorkMixin,
)


@dataclass
class Character(
    BankMixin, WorkMixin, MoveMixin, FightMixin, GatherMixin, CraftMixin, TaskMixin
):
    _name: str
    _surname: str
    _location: tuple[int, int]
    _layer: Layer
    _map: int
    _cooldown: datetime
    _hp: int
    _max_hp: int
    _xp: int
    _max_xp: int
    _level: int
    _gold: int
    _inventory: dict[str, int]
    _inventory_max_items: int
    _jobs: dict[str, int]

    def __post_init__(self):
        self.__url = f"{ARTIFACTSMMO_URL}/my/{self.name}"
        self.__client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

        self.__init_work_mixin__()

    @property
    def name(self):
        return self._name

    @property
    def surname(self):
        return self._surname

    @property
    def url(self):
        return self.__url

    @property
    def client(self):
        return self.__client

    @property
    def location(self) -> tuple[int, int]:
        return self._location

    @property
    def layer(self) -> Layer:
        return self._layer

    @property
    def map(self) -> int:
        return self._map

    @property
    def cooldown(self) -> float:
        return (self._cooldown - datetime.now(TIMEZONE)).total_seconds()

    @property
    async def available(self):
        while True:
            remaining = self.cooldown
            if remaining <= 0:
                break
            await asyncio.sleep(min(3.0, self.cooldown))

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def xp(self) -> int:
        return self._xp

    @property
    def max_xp(self) -> int:
        return self._max_xp

    @property
    def level(self) -> int:
        return self._level

    @property
    def gold(self) -> int:
        return self._gold

    @property
    def inventory(self) -> dict[str, int]:
        return self._inventory.copy()

    @property
    def inventory_max_items(self) -> int:
        return self._inventory_max_items

    @property
    def is_inventory_full(self) -> bool:
        return (
            sum(self._inventory.values()) >= self._inventory_max_items - 5
            or len(self._inventory) >= 17
        )

    def get_job_level(self, job_name: str) -> int:
        return self._jobs.get(job_name, 0)

    def has_job(self: "Character", job_name: str, level=1) -> bool:
        return self._jobs.get(job_name, 0) >= level

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

    @override
    def __str__(self):
        return f"{self.surname:8}: position={self.location} - working={self.is_working} - task={self.work_on}"

    def update_from_dict(self, data: dict) -> None:
        for key, value in self._parse_dict(data).items():
            setattr(self, key, value)

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        return cls(**cls._parse_dict(data))

    @staticmethod
    def _parse_dict(data: dict) -> dict:
        return dict(
            _name=data["name"],
            _surname=data["name"][3:],
            _location=(data["x"], data["y"]),
            _layer=Layer(data["layer"]),
            _map=data["map_id"],
            _cooldown=datetime.fromisoformat(
                data["cooldown_expiration"].replace("Z", "+00:00")
            ),
            _hp=data["hp"],
            _max_hp=data["max_hp"],
            _xp=data["xp"],
            _max_xp=data["max_xp"],
            _level=data["level"],
            _gold=data["gold"],
            _inventory={
                item["code"]: item["quantity"]
                for item in data["inventory"]
                if item["code"]
            },
            _inventory_max_items=data["inventory_max_items"],
            _jobs=Character.__get_jobs(data),
        )

    @classmethod
    def __get_jobs(cls, data: dict) -> dict[str, int]:
        jobs = {}
        jobs["mining"] = data.get("mining_level", 0)
        jobs["woodcutting"] = data.get("woodcutting_level", 0)
        jobs["fishing"] = data.get("fishing_level", 0)
        jobs["weaponcrafting"] = data.get("weaponcrafting_level", 0)
        jobs["gearcrafting"] = data.get("gearcrafting_level", 0)
        jobs["jewelrycrafting"] = data.get("jewelrycrafting_level", 0)
        jobs["cooking"] = data.get("cooking_level", 0)
        jobs["alchemy"] = data.get("alchemy_level", 0)
        return jobs
