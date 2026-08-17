from dataclasses import dataclass
from typing import override

from models.dataclass import Item
from models.enums import Layer, ZoneType


# maps that are in a closed zone but are the entry point to the zone
ENTRY_ZONE_IDS = {
    718  # Enchanted Forest
}


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
    zone: ZoneType
    transition_cost: tuple[Item | None, int] | None

    @property
    def coordinates(self) -> tuple[int, int, Layer]:
        return (self.x, self.y, self.layer)

    @classmethod
    async def from_dict(cls, data: dict) -> "Map":
        from models import Encyclopedia

        transition_map = None
        transition_cost = None
        transition_data = data.get("interactions", {}).get("transition", None)
        if transition_data:
            transition_map = transition_data.get("map_id")
            if conditions := transition_data.get("conditions"):
                condition = conditions[0]

                trans_currency_code = condition.get("code")
                trans_currency = (
                    await Encyclopedia.get_item_by_code(trans_currency_code)
                    if trans_currency_code != "gold"
                    else None
                )
                transition_cost = (trans_currency, condition.get("value"))

        zone = (
            ZoneType.from_map_name(data["name"])
            if data["map_id"] not in ENTRY_ZONE_IDS
            else ZoneType.DEFAULT
        )

        return cls(
            map_id=data["map_id"],
            name=data["name"],
            skin=data["skin"],
            x=data["x"],
            y=data["y"],
            layer=Layer(data["layer"]),
            access_type=data["access"]["type"],
            conditions=data["access"].get("conditions", []),
            zone=zone,
            _transitions_map=transition_map,
            transition_cost=transition_cost,
        )

    @override
    def __hash__(self) -> int:
        return hash(self.map_id)

    @override
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    @property
    def has_transition(self) -> bool:
        return self._transitions_map is not None

    @property
    async def get_transition_map(self) -> "Map | None":
        from models import LocationRegistry

        if self._transitions_map is None:
            return None

        return await LocationRegistry.get_map_by_id(self._transitions_map)
