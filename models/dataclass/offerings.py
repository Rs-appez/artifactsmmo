from dataclasses import dataclass

from models import Encyclopedia
from models.dataclass import Item, Monster, Resource
from models.enums import JobType


class OfferingType:
    CRAFT = "craft"
    MONSTER = "monster"
    RESOURCE = "resource"


@dataclass(frozen=True)
class Offering:
    id: str
    category: JobType
    type: OfferingType
    item: Item
    item_quantity: int
    target: Item | Resource | Monster
    xp_multiplier: float
    drop_multiplier: float

    @classmethod
    async def from_dict(cls, data):
        job = data["category"]
        if job == "combat":
            job = JobType.FIGHTING

        target_code = data["favor"]["target"]
        match data["favor"]["type"]:
            case OfferingType.CRAFT:
                target = await Encyclopedia.get_item_by_code(target_code)
            case OfferingType.MONSTER:
                target = await Encyclopedia.get_monster_by_code(target_code)
            case OfferingType.RESOURCE:
                target = await Encyclopedia.get_resource_by_code(target_code)
            case _:
                raise ValueError(f"Unknown favor type: {data['favor']['type']}")

        return cls(
            id=data["id"],
            category=JobType(job),
            type=data["type"],
            item=await Encyclopedia.get_item_by_code(data["requirement"]["code"]),
            item_quantity=int(data["requirement"]["item_quantity"]),
            target=target,
            xp_multiplier=float(data["favor"]["xp_multiplier"]),
            drop_multiplier=float(data["favor"]["drop_multiplier"]),
        )
