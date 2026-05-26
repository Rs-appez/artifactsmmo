from dataclasses import dataclass
from typing import override

from models import Encyclopedia, LocationRegistry
from models.dataclass import NPC, Map, Monster, Resource


@dataclass(frozen=True)
class Event:
    name: str
    code: str
    content: Monster | Resource | NPC | None
    maps: list[Map]

    @override
    def __hash__(self):
        return hash(self.code)

    @classmethod
    async def from_dict(cls, data):
        content = None
        match data["content"]["type"]:
            case "monster":
                content = await Encyclopedia.get_monster_by_code(
                    data["content"]["code"]
                )
            case "resource":
                content = await Encyclopedia.get_resource_by_code(
                    data["content"]["code"]
                )
            case "npc":
                pass
                # TODO: NPC data is not yet available in the encyclopedia, so this will be implemented later.
                # content = await Encyclopedia.get_npc_by_code(data["content"]["code"])
            case _:
                pass

        return cls(
            name=data["name"],
            code=data["code"],
            content=content,
            maps=[
                await LocationRegistry.get_map_by_id(map_code)
                for map_code in data["maps"]["map_id"]
            ],
        )
