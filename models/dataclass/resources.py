from dataclasses import dataclass
from models.enums import JobType
from models.dataclass import Item


@dataclass(frozen=True)
class Resource:
    name: str
    code: str
    level: int
    skill: JobType
    drops: dict[Item, dict[str, int]]

    @classmethod
    def from_dict(cls, data):
        from models import Encyclopedia

        drops = {}
        for drop_data in data.get("drops", []):
            item = Encyclopedia.get_item_by_code(drop_data["code"])
            drops[item] = {
                "rate": drop_data["rate"],
                "min_quantity": drop_data["min_quantity"],
                "max_quantity": drop_data["max_quantity"],
            }

        return cls(
            name=data["name"],
            code=data["code"],
            level=data["level"],
            skill=JobType(data["skill"]),
            drops=drops,
        )
