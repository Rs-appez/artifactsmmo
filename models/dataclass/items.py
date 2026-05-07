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
        craft_data = data.get("craft")
        if craft_data is None:
            craft_data: dict = {
                "skill": "",
                "level": 0,
                "items": [],
                "quantity": 0,
            }
        return cls(
            name=data["name"],
            code=data["code"],
            level=data["level"],
            type=data["type"],
            subtype=data["subtype"],
            description=data["description"],
            conditions=data.get("conditions", []),
            effects=data.get("effects", []),
            job=craft_data.get("skill", ""),
            craft_level=craft_data.get("level", 0),
            craft_ingredients=craft_data.get("items", []),
            craft_quantity=craft_data.get("quantity", 0),
            tradeable=data["tradeable"] == "true",
        )
