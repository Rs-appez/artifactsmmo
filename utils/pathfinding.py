import heapq
from functools import lru_cache
from itertools import count

from models import LocationRegistry
from models.dataclass import Map


@lru_cache(maxsize=128)
async def get_route(a: Map, b: Map) -> list[Map]:
    maps_key = []
    path, cost = _dijkstra(await LocationRegistry.get_map_graph(), a, b)

    for i, map in enumerate(path):
        if (
            (map_trans := await map.get_transition_map)
            and i + 1 < len(path)
            and map_trans == path[i + 1]
        ):
            maps_key.append(map)

    maps_key.append(path[-1])

    return maps_key


def _dijkstra(
    graph: dict[Map, set[Map]], start: Map, goal: Map
) -> tuple[list[Map], int]:
    dist = {start: 0}
    prev = {}
    tie = count()
    pq = [(0, next(tie), start)]

    while pq:
        d, _, u = heapq.heappop(pq)
        if u == goal:
            break
        if d > dist.get(u, float("inf")):
            continue
        for v in graph.get(u, ()):
            nd = d + __weight(u, v)
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, next(tie), v))

    if goal not in dist:
        raise ValueError(f"No path found from {start} to {goal}")
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return path[::-1], dist[goal]


def __weight(u: Map, v: Map) -> int:
    if u.has_transition:
        return 1
    return 0
