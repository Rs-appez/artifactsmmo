from dataclasses import dataclass
from typing import override


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
