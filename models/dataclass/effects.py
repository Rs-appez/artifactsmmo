from dataclasses import dataclass


@dataclass(frozen=True)
class Effect:
    code: str
    value: int
    description: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            code=data["code"],
            value=data["value"],
            description=data["description"],
        )
