from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from models.enums import Element

if TYPE_CHECKING:
    from models.dataclass import Effect, Item


@dataclass(frozen=True)
class Monster:
    name: str
    code: str
    level: int
    type: str
    hp: int
    attack: dict[Element, int]
    resistance: dict[Element, int]
    critical_strike: int
    initiative: int
    effects: dict[Effect, int]
    min_gold: int
    max_gold: int
    drops: list[dict[Item, dict[str, str | int]]]

    @classmethod
    async def from_dict(cls, data):
        from models import Encyclopedia

        damage = {
            Element.FIRE: data["attack_fire"],
            Element.WATER: data["attack_water"],
            Element.EARTH: data["attack_earth"],
            Element.AIR: data["attack_air"],
        }
        resistance = {
            Element.FIRE: data["res_fire"],
            Element.WATER: data["res_water"],
            Element.EARTH: data["res_earth"],
            Element.AIR: data["res_air"],
        }

        return cls(
            name=data["name"],
            code=data["code"],
            level=data["level"],
            type=data["type"],
            hp=data["hp"],
            attack=damage,
            resistance=resistance,
            critical_strike=data["critical_strike"],
            initiative=data["initiative"],
            effects={
                await Encyclopedia.get_effect_by_code(effect_data["code"]): effect_data[
                    "value"
                ]
                for effect_data in data.get("effects", [])
            },
            min_gold=data["min_gold"],
            max_gold=data["max_gold"],
            drops=[
                {
                    item: {
                        "rate": drop_data["rate"],
                        "min_quantity": drop_data["min_quantity"],
                        "max_quantity": drop_data["max_quantity"],
                    }
                }
                for drop_data in data.get("drops", [])
                if (item := await Encyclopedia.get_item_by_code(drop_data["code"]))
            ],
        )

    @override
    def __hash__(self):
        return hash(self.code)

    @override
    def __str__(self):
        return self.name

    @property
    def average_gold(self) -> float:
        return (self.min_gold + self.max_gold) / 2

    def drop_rate(self, item: "Item") -> float:
        for drop in self.drops:
            if item in drop:
                return 1 / int(drop[item]["rate"])
        return 0.0
