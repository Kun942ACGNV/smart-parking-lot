from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

from .models import Slot, slot_name


class SlotManager:
    """二維陣列存車位、最小堆積取最近空位。"""

    def __init__(self, floors: int, per_floor: int,
                 distance_map: Optional[Dict[str, float]] = None):
        self.floors = floors
        self.per_floor = per_floor
        self.slots: List[List[Slot]] = [
            [Slot(f, i, distance_map[slot_name(f, i)] if distance_map else f * 100 + i)
             for i in range(per_floor)]
            for f in range(floors)
        ]
        self.free_heap: List[Tuple[float, int, int]] = []
        self.rebuild_heap()

    def rebuild_heap(self) -> None:
        self.free_heap = [(s.distance, s.floor, s.index)
                          for row in self.slots for s in row if s.plate is None]
        heapq.heapify(self.free_heap)

    def allocate(self) -> Optional[Slot]:
        if not self.free_heap:
            return None
        _, f, i = heapq.heappop(self.free_heap)
        return self.slots[f][i]

    def release(self, slot: Slot) -> None:
        slot.plate = None
        heapq.heappush(self.free_heap, (slot.distance, slot.floor, slot.index))

    def get_slot(self, name: str) -> Slot:
        floor, index = name[1:].split("-")
        return self.slots[int(floor)][int(index)]

    def free_count(self) -> int:
        return len(self.free_heap)

    def total(self) -> int:
        return self.floors * self.per_floor
