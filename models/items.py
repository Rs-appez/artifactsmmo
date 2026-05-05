from dataclasses import dataclass


@dataclass
class Item:
    name: str
    code: str
    level: int
    type: str
    subtype: str
    description: str
    conditions: list[dict[str, str | int]]
    effects: list[dict[str, str | int]]
    job: str
    craft_level: int
    craft_ingredients: list[dict[str, str | int]]
    craft_quantity: int
    tradeable: bool

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            code=data["code"],
            level=data["level"],
            type=data["type"],
            subtype=data["subtype"],
            description=data["description"],
            conditions=data.get("conditions", []),
            effects=data.get("effects", []),
            job=data["craft"]["skill"],
            craft_level=data["craft"]["level"],
            craft_ingredients=data["craft"]["items"],
            craft_quantity=data["craft"]["quantity"],
            tradeable=data["tradeable"] == "true",
        )
