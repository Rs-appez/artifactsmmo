from dataclasses import dataclass
from typing import override
from typing import TYPE_CHECKING

from models.dataclass import Effect
from models.enums import EquipentType, JobType

if TYPE_CHECKING:
    from models.character.character import Character

NOT_TO_EAT_FOOD = {"apple", "coconut"}


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
    job: JobType
    craft_level: int
    craft_ingredients: list[dict[str, str | int]]
    craft_quantity: int
    tradeable: bool

    @classmethod
    async def from_dict(cls, data):
        from models import Encyclopedia

        craft_data = data.get("craft")
        if craft_data is None:
            craft_data: dict = {
                "skill": "no_job",
                "level": 0,
                "items": [],
                "quantity": 0,
            }
        effects = {}
        effects_data = data.get("effects", [])
        for effect_data in effects_data:
            effect = await Encyclopedia.get_effect_by_code(effect_data["code"])
            effects[effect] = effect_data["value"]

        # ugly temp (i hope)
        job = JobType(craft_data.get("skill", "no_job"))
        if job == JobType.NO_JOB and data["type"] == "resource":
            try:
                job = JobType(data["subtype"])
            except ValueError:
                job = JobType.NO_JOB

        return cls(
            name=data["name"],
            code=data["code"],
            level=data["level"],
            type=data["type"],
            subtype=data["subtype"],
            description=data["description"],
            conditions=data.get("conditions", []),
            effects=effects,
            job=job,
            craft_level=craft_data.get("level", 0),
            craft_ingredients=craft_data.get("items", []),
            craft_quantity=craft_data.get("quantity", 0),
            tradeable=data["tradeable"] == "true",
        )

    @property
    def is_weapon(self) -> bool:
        return self.type == "weapon" and self.subtype == ""

    @property
    def is_equipment(self) -> bool:
        return self.type in EquipentType

    @property
    def is_craftable(self) -> bool:
        return len(self.craft_ingredients) > 0

    @property
    def is_food(self) -> bool:
        return (
            self.type == "consumable"
            and self.subtype == "food"
            and self.code not in NOT_TO_EAT_FOOD
        )

    @property
    def heal(self) -> int:
        if self.is_food:
            for effect in self.effects:
                if effect.code == "heal":
                    return self.effects[effect]
        return 0

    @property
    def is_tool(self) -> bool:
        return self.type == "weapon" and self.subtype == "tool"

    def is_for_job(self, job: JobType) -> bool:
        if not self.is_tool:
            return False

        for effect in self.effects:
            if effect.code == job.value:
                return True

        return False

    def can_be_used_by(self, character: Character) -> bool:

        for condition in self.conditions:
            value = int(condition["value"])
            operator = str(condition["operator"])
            match condition["code"]:
                case "level":
                    return self.__check_conditions(
                        character.level,
                        value,
                        operator,
                    )
                case "hp":
                    return self.__check_conditions(
                        character.hp,
                        value,
                        operator,
                    )
                case str(job) if job.endswith("_level"):
                    return self.__check_conditions(
                        character.get_job_level(job[:-6]),
                        value,
                        operator,
                    )
                case _:
                    raise ValueError(
                        f"Unknown condition code {condition['code']} in item conditions"
                    )

        return True

    def __check_conditions(
        self, character_values: int, condition_values: int, operator: str
    ) -> bool:
        match operator:
            case "eq":
                return character_values == condition_values
            case "ne":
                return character_values != condition_values
            case "gt":
                return character_values > condition_values
            case "lt":
                return character_values < condition_values
            case _:
                raise ValueError(f"Unknown operator {operator} in item conditions")

    @override
    def __hash__(self):
        return hash(self.code)
