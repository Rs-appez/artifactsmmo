import asyncio
from dataclasses import KW_ONLY, dataclass
from datetime import datetime
from re import I
from typing import override

import httpx

from config import ARTIFACTSMMO_URL, HEADERS, TIMEZONE
from models import Encyclopedia
from models.dataclass import Item, TaskQuest
from models.enums import Element, JobType, Layer
from utils.math_fight import calc_attack

from .decorators import refresh_after
from .mixin import (
    BankMixin,
    CraftMixin,
    FightMixin,
    GatherMixin,
    MoveMixin,
    TaskMixin,
    WorkMixin,
    StuffMixin,
    SaveMixin,
    InventoryMixin,
)


@dataclass
class Character(
    InventoryMixin,
    BankMixin,
    WorkMixin,
    MoveMixin,
    FightMixin,
    GatherMixin,
    CraftMixin,
    TaskMixin,
    StuffMixin,
    SaveMixin,
):
    _: KW_ONLY
    _name: str
    _surname: str
    _cooldown: datetime

    _location: tuple[int, int]
    _layer: Layer
    _map: int

    _hp: int
    _max_hp: int
    _initiative: int
    _resistance: dict[Element, int]
    _attack: dict[Element, int]
    _critical_strike: int

    _xp: int
    _max_xp: int
    _level: int

    _jobs: dict[JobType, int]

    _weapon: Item | None = None

    _task: TaskQuest | None = None

    def __post_init__(self):
        self.__client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=HEADERS,
            base_url=f"{ARTIFACTSMMO_URL}/my/{self.name}/action",
        )

        self.__init_work_mixin__()

    @property
    def name(self):
        return self._name

    @property
    def surname(self):
        return self._surname

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
    def resistance(self) -> dict[Element, int]:
        return self._resistance.copy()

    @property
    def attack(self) -> dict[Element, int]:
        return self._attack.copy()

    @property
    def critical_strike(self) -> int:
        return self._critical_strike

    @property
    def initiative(self) -> int:
        return self._initiative

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
    def weapon(self) -> Item | None:
        return self._weapon

    @property
    def task(self) -> TaskQuest | None:
        return self._task

    def get_job_level(self, job_name: str | JobType) -> int:
        job = JobType(job_name) if isinstance(job_name, str) else job_name
        return self._jobs.get(job, 0)

    def has_job(self: "Character", job_name: str | JobType, level=1) -> bool:
        job = JobType(job_name) if isinstance(job_name, str) else job_name
        return self._jobs.get(job, 0) >= level

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
        return f"{self.surname:8}: position={str(self.location):<9} - working={self.is_working} - task={self.work_on}"

    async def update_from_dict(self, data: dict) -> None:
        data_dict = await self._parse_dict(data)
        for key, value in data_dict.items():
            setattr(self, key, value)

    @classmethod
    async def from_dict(cls, data: dict) -> "Character":
        data_dict = await cls._parse_dict(data)
        return cls(**data_dict)

    @staticmethod
    async def _parse_dict(data: dict) -> dict:
        task_dict = {
            "task_type": data.get("task_type"),
            "task_total": data.get("task_total"),
            "task_progress": data.get("task_progress"),
            "task": data.get("task"),
        }
        resistance = {
            Element.AIR: data.get("res_air", 0),
            Element.EARTH: data.get("res_earth", 0),
            Element.FIRE: data.get("res_fire", 0),
            Element.WATER: data.get("res_water", 0),
        }
        dmg_boost = data.get("dmg", 0)

        attack = {
            Element.AIR: calc_attack(
                data.get("attack_air", 0), data.get("dmg_air", 0) + dmg_boost
            ),
            Element.EARTH: calc_attack(
                data.get("attack_earth", 0), data.get("dmg_earth", 0) + dmg_boost
            ),
            Element.FIRE: calc_attack(
                data.get("attack_fire", 0), data.get("dmg_fire", 0) + dmg_boost
            ),
            Element.WATER: calc_attack(
                data.get("attack_water", 0), data.get("dmg_water", 0) + dmg_boost
            ),
        }

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
                await Encyclopedia.get_item_by_code(item["code"]): item["quantity"]
                for item in data["inventory"]
                if item["code"]
            },
            _inventory_max_items=data["inventory_max_items"],
            _jobs=Character.__get_jobs(data),
            _task=await TaskQuest.from_dict(task_dict) if task_dict["task"] else None,
            _resistance=resistance,
            _attack=attack,
            _critical_strike=data.get("critical_strike", 0),
            _initiative=data.get("initiative", 0),
            _weapon=await Encyclopedia.get_item_by_code(data["weapon_slot"])
            if data.get("weapon_slot")
            else None,
        )

    @classmethod
    def __get_jobs(cls, data: dict) -> dict[str, int]:
        jobs = {}
        jobs[JobType.MINING] = data.get("mining_level", 0)
        jobs[JobType.WOODCUTTING] = data.get("woodcutting_level", 0)
        jobs[JobType.FISHING] = data.get("fishing_level", 0)
        jobs[JobType.WEAPONCRAFTING] = data.get("weaponcrafting_level", 0)
        jobs[JobType.GEARCRAFTING] = data.get("gearcrafting_level", 0)
        jobs[JobType.JEWELRYCRAFTING] = data.get("jewelrycrafting_level", 0)
        jobs[JobType.COOKING] = data.get("cooking_level", 0)
        jobs[JobType.ALCHEMY] = data.get("alchemy_level", 0)
        return jobs
