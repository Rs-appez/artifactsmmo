from dataclasses import dataclass

from typing import TYPE_CHECKING, override


if TYPE_CHECKING:
    from models.dataclass import Effect, Item


@dataclass(frozen=True)
class Monster:
    name: str
    code: str
    level: int
    type: str
    hp: int
    attack_fire: int
    attack_water: int
    attack_earth: int
    attack_air: int
    res_fire: int
    res_water: int
    res_earth: int
    res_air: int
    critical_strike: int
    initiative: int
    effects: list[tuple[Effect, int]]
    min_gold: int
    max_gold: int
    drops: list[dict[Item, dict[str, str | int]]]

    @classmethod
    async def from_dict(cls, data):
        from models import Encyclopedia

        return cls(
            name=data["name"],
            code=data["code"],
            level=data["level"],
            type=data["type"],
            hp=data["hp"],
            attack_fire=data["attack_fire"],
            attack_water=data["attack_water"],
            attack_earth=data["attack_earth"],
            attack_air=data["attack_air"],
            res_fire=data["res_fire"],
            res_water=data["res_water"],
            res_earth=data["res_earth"],
            res_air=data["res_air"],
            critical_strike=data["critical_strike"],
            initiative=data["initiative"],
            effects=[
                (
                    await Encyclopedia.get_effect_by_code(effect_data["code"]),
                    effect_data["value"],
                )
                for effect_data in data.get("effects", [])
            ],
            min_gold=data["min_gold"],
            max_gold=data["max_gold"],
            drops=[
                {
                    await Encyclopedia.get_item_by_code(drop_data["code"]): {
                        "rate": drop_data["rate"],
                        "min_quantity": drop_data["min_quantity"],
                        "max_quantity": drop_data["max_quantity"],
                    }
                }
                for drop_data in data.get("drops", [])
            ],
        )

    @override
    def __hash__(self):
        return hash(self.code)

    @property
    def average_gold(self) -> float:
        return (self.min_gold + self.max_gold) / 2

    def drop_rate(self, item: "Item") -> float:
        for drop in self.drops:
            if item in drop:
                return 1 / int(drop[item]["rate"])
        return 0.0
