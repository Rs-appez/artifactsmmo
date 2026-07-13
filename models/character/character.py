import asyncio
from dataclasses import KW_ONLY, dataclass
from datetime import datetime
from typing import override


from config import ARTIFACTSMMO_URL, TIMEZONE
from models import Encyclopedia, LocationRegistry
from models.dataclass import TaskQuest
from models.enums import Element, EquipentType, JobType
from utils.math_fight import calc_attack

from .decorators import refresh_after
from .mixin import (
    ApiMixin,
    BankMixin,
    CraftMixin,
    JobMixin,
    FightMixin,
    GatherMixin,
    MoveMixin,
    TaskMixin,
    WorkMixin,
    StuffMixin,
    SaveMixin,
    InventoryMixin,
    NpcMixin,
)


@dataclass
class Character(
    ApiMixin,
    MoveMixin,
    JobMixin,
    InventoryMixin,
    BankMixin,
    WorkMixin,
    FightMixin,
    GatherMixin,
    CraftMixin,
    TaskMixin,
    StuffMixin,
    SaveMixin,
    NpcMixin,
):
    _: KW_ONLY
    _name: str
    _surname: str
    _cooldown: datetime

    _xp: int
    _max_xp: int
    _level: int

    _wisdom: int
    _protecting: int

    def __post_init__(self):
        self.__init_api_mixin__()
        self.__init_work_mixin__()

    @property
    def name(self) -> str:

        return self._name

    @property
    def surname(self) -> str:
        return self._surname

    @property
    def cooldown(self) -> float:
        return (self._cooldown - datetime.now(TIMEZONE)).total_seconds()

    @property
    async def available(self) -> None:
        while True:
            remaining = self.cooldown
            if remaining <= 0:
                break
            await asyncio.sleep(min(1.0, self.cooldown))

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
    def wisdom(self) -> int:
        return self._wisdom

    @property
    def protecting(self) -> int:
        return self._protecting

    @refresh_after
    async def refresh(self) -> dict:
        response = await self.client.get(f"{ARTIFACTSMMO_URL}/characters/{self.name}")
        data = response.json()
        if "error" in data:
            print("data : ", data)
            raise Exception(data["error"]["message"])
        character_data = data["data"]
        return character_data

    @override
    def __str__(self):
        return f"{self.surname:8}: position={str(self.location):<9} - working={self.is_working} - task={self.work_on} - cooldown={self.cooldown:.2f}s"

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

        effects = {
            await Encyclopedia.get_effect_by_code(effect["code"]): effect["value"]
            for effect in data.get("effects", [])
        }

        equipments = {
            EquipentType.RUNE: await Encyclopedia.get_item_by_code(data["rune_slot"])
            if data.get("rune_slot")
            else None,
            EquipentType.SHIELD: await Encyclopedia.get_item_by_code(
                data["shield_slot"]
            )
            if data.get("shield_slot")
            else None,
            EquipentType.HELMET: await Encyclopedia.get_item_by_code(
                data["helmet_slot"]
            )
            if data.get("helmet_slot")
            else None,
            EquipentType.BODY_ARMOR: await Encyclopedia.get_item_by_code(
                data["body_armor_slot"]
            )
            if data.get("body_armor_slot")
            else None,
            EquipentType.LEG_ARMOR: await Encyclopedia.get_item_by_code(
                data["leg_armor_slot"]
            )
            if data.get("leg_armor_slot")
            else None,
            EquipentType.BOOTS: await Encyclopedia.get_item_by_code(data["boots_slot"])
            if data.get("boots_slot")
            else None,
            EquipentType.AMULET: await Encyclopedia.get_item_by_code(
                data["amulet_slot"]
            )
            if data.get("amulet_slot")
            else None,
        }

        return dict(
            _name=data["name"],
            _surname=data["name"][3:],
            _location=await LocationRegistry.get_map_by_id(data["map_id"]),
            _cooldown=datetime.fromisoformat(
                data["cooldown_expiration"].replace("Z", "+00:00")
            ),
            _hp=data["hp"],
            _max_hp=data["max_hp"],
            _xp=data["xp"],
            _max_xp=data["max_xp"],
            _level=data["level"],
            _wisdom=data["wisdom"],
            _protecting=data["protecting"],
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
            _effects=effects,
            _bag=await Encyclopedia.get_item_by_code(data["bag_slot"])
            if data.get("bag_slot")
            else None,
            _weapon=await Encyclopedia.get_item_by_code(data["weapon_slot"])
            if data.get("weapon_slot")
            else None,
            _equipped_items=equipments,
            _ring_1=await Encyclopedia.get_item_by_code(data["ring1_slot"])
            if data.get("ring1_slot")
            else None,
            _ring_2=await Encyclopedia.get_item_by_code(data["ring2_slot"])
            if data.get("ring2_slot")
            else None,
            _artifact_1=await Encyclopedia.get_item_by_code(data["artifact1_slot"])
            if data.get("artifact1_slot")
            else None,
            _artifact_2=await Encyclopedia.get_item_by_code(data["artifact2_slot"])
            if data.get("artifact2_slot")
            else None,
            _artifact_3=await Encyclopedia.get_item_by_code(data["artifact3_slot"])
            if data.get("artifact3_slot")
            else None,
        )

    @classmethod
    def __get_jobs(cls, data: dict) -> dict[JobType, dict[str, int]]:

        def get_job_level(job_type: JobType) -> dict[str, int]:
            return {
                "level": data.get(f"{job_type.value}_level", 0),
                "xp": data.get(f"{job_type.value}_xp", 0),
                "next_level_xp": data.get(f"{job_type.value}_max_xp", 0),
            }

        jobs = {}
        for job_type in JobType.character_job_types():
            jobs[job_type] = get_job_level(job_type)
        return jobs
