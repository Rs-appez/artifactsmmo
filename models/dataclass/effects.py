from dataclasses import dataclass
from typing import override

from models.enums import Element


@dataclass(frozen=True)
class Effect:
    name: str
    code: str
    description: str
    type: str
    subtype: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            code=data["code"],
            description=data["description"],
            type=data["type"],
            subtype=data["subtype"],
        )

    @override
    def __hash__(self):
        return hash(self.code)

    @property
    def has_element(self) -> bool:
        """Returns True if the effect has an associated element, False otherwise."""
        return self.get_element is not None

    @property
    def get_element(self) -> Element | None:
        """Returns the element associated with the effect, if any."""
        for element in Element:
            if self.code.endswith(element.value):
                return element

    @property
    def get_atk_element(self) -> Element | None:
        """Returns the element associated with the effect's attack, if any."""
        for element in Element:
            if self.code.startswith(f"atk_{element.value}"):
                return element

    @property
    def get_res_element(self) -> Element | None:
        """Returns the element associated with the effect's resistance, if any."""
        for element in Element:
            if self.code.startswith(f"res_{element.value}"):
                return element

    @property
    def get_dmg_element(self) -> Element | None:
        """Returns the element associated with the effect's damage, if any."""
        for element in Element:
            if self.code.startswith(f"dmg_{element.value}"):
                return element
