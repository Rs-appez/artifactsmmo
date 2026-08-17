import heapq
from itertools import count

from models import LocationRegistry
from models.dataclass import Map

cache = {}


async def get_route(a: Map, b: Map):
    key = (a, b)
    if key not in cache:
        cache[key] = dijkstra(await LocationRegistry.get_map_graph(), a, b)
    return cache[key]


def dijkstra(graph: dict[Map, set[Map]], start: Map, goal: Map):
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
            nd = d + weight(u, v)
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, next(tie), v))

    if goal not in dist:
        return None, float("inf")
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return path[::-1], dist[goal]


def weight(u: Map, v: Map) -> int:
    if u.has_transition:
        return 1
    return 0
