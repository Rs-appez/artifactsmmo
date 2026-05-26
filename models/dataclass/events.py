from dataclasses import dataclass
from typing import override

from models import Encyclopedia, LocationRegistry
from models.dataclass import Map, Monster, Resource


@dataclass(frozen=True)
class Event:
    name: str
    code: str
    content: Monster | Resource
    maps: list[Map]

    @override
    def __hash__(self):
        return hash(self.code)

    @classmethod
    async def from_dict(cls, data):

        return cls(
            name=data["name"],
            code=data["code"],
            content=await Encyclopedia.get_monster_by_code(data["content"]),
            maps=[
                await LocationRegistry.get_map_by_id(map_code)
                for map_code in data["maps"]["map_id"]
            ],
        )
