from locations import workshop_locations, bank_locations


def __manhattan_distance(pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def find_nearest_workshop(
    job: str, location: tuple[int, int]
) -> tuple[int, int] | None:
    if job not in workshop_locations:
        raise ValueError(f"No workshops found for job {job}")
    return min(
        workshop_locations[job],
        key=lambda pos: __manhattan_distance(pos, location),
    )


def find_nearest_bank(location: tuple[int, int]) -> tuple[int, int]:
    return min(
        bank_locations,
        key=lambda pos: __manhattan_distance(pos, location),
    )
