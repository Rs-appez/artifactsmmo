from dataclasses import dataclass
from typing import override

from models.dataclass import Effect


@dataclass(frozen=True)
class Item:
    name: str
    code: str
    level: int
    type: str
    subtype: str
    description: str
    conditions: list[dict[str, str | int]]
    effects: dict[Effect, int]
    job: str
    craft_level: int
    craft_ingredients: list[dict[str, str | int]]
    craft_quantity: int
    tradeable: bool

    @classmethod
    def from_dict(cls, data):
        from models import Encyclopedia

        craft_data = data.get("craft")
        if craft_data is None:
            craft_data: dict = {
                "skill": "",
                "level": 0,
                "items": [],
                "quantity": 0,
            }
        effects = {}
        effects_data = data.get("effects", [])
        for effect_data in effects_data:
            effect = Encyclopedia.effects.get(effect_data["code"])
            if effect is None:
                raise ValueError(
                    f"Effect with code '{effect_data['code']}' not found for item '{data['name']}'"
                )
            effects[effect] = effect_data["value"]

        return cls(
            name=data["name"],
            code=data["code"],
            level=data["level"],
            type=data["type"],
            subtype=data["subtype"],
            description=data["description"],
            conditions=data.get("conditions", []),
            effects=effects,
            job=craft_data.get("skill", ""),
            craft_level=craft_data.get("level", 0),
            craft_ingredients=craft_data.get("items", []),
            craft_quantity=craft_data.get("quantity", 0),
            tradeable=data["tradeable"] == "true",
        )

    @override
    def __hash__(self):
        return hash(self.code)
