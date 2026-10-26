from __future__ import annotations

import heapq
import math
from typing import Dict, List, Tuple

Graph = Dict[str, List[Tuple[str, float]]]


def build_lot_graph(floors: int, per_floor: int) -> Graph:
    g: Graph = {}

    def add(u: str, v: str, w: float) -> None:
        g.setdefault(u, []).append((v, w))
        g.setdefault(v, []).append((u, w))

    add("入口", "路口F0", 5)
    for i in range(per_floor):
        add("路口F0", "F0-%d" % i, 2 + 2 * i)
    prev = "路口F0"
    for f in range(1, floors):
        add(prev, "路口F%d" % f, 10)               # 坡道
        for i in range(per_floor):
            add("路口F%d" % f, "F%d-%d" % (f, i), 2 + 2 * i)
        prev = "路口F%d" % f
    return g


def dijkstra(graph: Graph, start: str):
    dist = {start: 0.0}
    prev: Dict[str, str] = {}
    pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, math.inf):
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    return dist, prev


def shortest_path(graph: Graph, start: str, goal: str):
    dist, prev = dijkstra(graph, start)
    if goal not in dist:
        raise ValueError("無法從 %s 到達 %s" % (start, goal))
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return path[::-1], dist[goal]


def slot_distances(graph: Graph, start: str = "入口") -> Dict[str, float]:
    dist, _ = dijkstra(graph, start)
    return {k: v for k, v in dist.items() if k.startswith("F") and "-" in k}
