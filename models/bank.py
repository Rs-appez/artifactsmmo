from .enums import Layer

BANK_POS: dict[Layer, set[tuple[int, int]]] = {
    Layer.OVERWORLD: {(4, 1), (7, 13)},
}


def nearest_bank(layer: Layer, location: tuple[int, int]) -> tuple[int, int]:
    if layer not in BANK_POS:
        raise ValueError(f"No bank found for layer {layer}")
    return min(
        BANK_POS[layer],
        key=lambda pos: (pos[0] - location[0]) ** 2 + (pos[1] - location[1]) ** 2,
    )
