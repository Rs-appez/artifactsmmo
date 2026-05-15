from dataclasses import dataclass


@dataclass(frozen=True)
class NPC:
    name: str
    code: str
    type: str
