from collections import defaultdict
from dataclasses import dataclass
from typing import override

from models.dataclass import Item
from models.enums import JobType


@dataclass(frozen=True)
class Resource:
    _drop_item = defaultdict(set)

    name: str
    code: str
    level: int
    skill: JobType
    drops: dict[Item, dict[str, int]]

    @classmethod
    async def from_dict(cls, data):
        from models import Encyclopedia

        drops = {}
        for drop_data in data.get("drops", []):
            item = await Encyclopedia.get_item_by_code(drop_data["code"])
            drops[item] = {
                "rate": drop_data["rate"],
                "min_quantity": drop_data["min_quantity"],
                "max_quantity": drop_data["max_quantity"],
            }

        resource = cls(
            name=data["name"],
            code=data["code"],
            level=data["level"],
            skill=JobType(data["skill"]),
            drops=drops,
        )
        for item in drops:
            cls._drop_item[item].add(resource)

        return resource

    @override
    def __hash__(self):
        return hash(self.code)

    @staticmethod
    def from_drop_item(item: Item) -> set["Resource"]:
        return Resource._drop_item[item]
