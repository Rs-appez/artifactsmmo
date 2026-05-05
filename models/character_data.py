from dataclasses import dataclass
from .enums import Layer
from datetime import datetime, timezone


@dataclass
class CharacterData:
    name: str
    surname: str
    location: tuple[int, int]
    layer: Layer
    map: int
    cooldown: datetime
    hp: int
    max_hp: int
    xp: int
    max_xp: int
    level: int
    gold: int
    inventory: dict[str, int]
    inventory_max_items: int
    jobs: dict[str, int]

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterData":
        jobs = cls.__get_jobs(data)

        return cls(
            name=data["name"],
            surname=data["name"][3:],
            location=(data["x"], data["y"]),
            layer=Layer(data["layer"]),
            map=data["map_id"],
            cooldown=datetime.strptime(
                data["cooldown_expiration"], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=timezone.utc),
            hp=data["hp"],
            max_hp=data["max_hp"],
            xp=data["xp"],
            max_xp=data["max_xp"],
            level=data["level"],
            gold=data["gold"],
            inventory={item["code"]: item["quantity"] for item in data["inventory"]},
            inventory_max_items=data["inventory_max_items"],
            jobs=jobs,
        )
        # cooldown=datetime.fromisoformat(
        #     data["cooldown_expiration"].replace("Z", "+00:00")
        # ),

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
