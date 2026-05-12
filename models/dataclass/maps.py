from dataclasses import dataclass
from typing import override

from models.enums import Layer


@dataclass(frozen=True)
class Map:
    map_id: int
    name: str
    skin: str
    x: int
    y: int
    layer: Layer
    access_type: str
    conditions: list[dict[str, str | int]]
    _transitions_map: int | None

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        transition_map = None
        transition_data = data.get("transitions", None)
        if transition_data:
            transition_map = transition_data.get("map_id")

        return cls(
            map_id=data["map_id"],
            name=data["name"],
            skin=data["skin"],
            x=data["x"],
            y=data["y"],
            layer=Layer(data["layer"]),
            access_type=data["access"]["type"],
            conditions=data["access"].get("conditions", []),
            _transitions_map=transition_map,
        )

    @override
    def __hash__(self) -> int:
        return hash(self.map_id)

    @property
    def has_transition(self) -> bool:
        return self._transitions_map is not None

    @property
    async def get_transition_map(self) -> "Map | None":
        from models import LocationRegistry

        if self._transitions_map is None:
            return None

        return await LocationRegistry.get_map_by_id(self._transitions_map)
