from dataclasses import dataclass
from .enums import Layer
from datetime import datetime, timezone


@dataclass
class CharacterData:
    def __init__(
        self,
        name: str,
        location: tuple[int, int],
        layer: Layer,
        map: int,
        cooldown: datetime,
        hp: int,
        max_hp: int,
        xp: int,
        max_xp: int,
        level: int,
        gold: int,
        inventory: dict[str, int],
        inventory_max_items: int,
    ):
        self.name = name
        self.surname = name[4:]
        self.location = location
        self.layer = layer
        self.map = map
        self.cooldown = cooldown
        self.hp = hp
        self.max_hp = max_hp
        self.xp = xp
        self.max_xp = max_xp
        self.level = level
        self.gold = gold
        self.inventory = inventory
        self.inventory_max_items = inventory_max_items

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterData":
        return cls(
            name=data["name"],
            location=(data["x"], data["y"]),
            layer=Layer(data["layer"]),
            map=data["map"],
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
        )
        # cooldown=datetime.fromisoformat(
        #     data["cooldown_expiration"].replace("Z", "+00:00")
        # ),
