from __future__ import annotations

import math
import time
from collections import deque
from typing import Deque, Dict, List, Optional, Set, Tuple

from .graph import build_lot_graph, shortest_path, slot_distances
from .models import Receipt, Ticket
from .report import revenue_between
from .slots import SlotManager
from .trie import PlateTrie


class ParkingLot:
    def __init__(self, floors: int = 2, per_floor: int = 4, rate_per_hour: int = 30):
        self.floors = floors
        self.per_floor = per_floor
        self.rate_per_hour = rate_per_hour
        self.graph = build_lot_graph(floors, per_floor)
        self.mgr = SlotManager(floors, per_floor, slot_distances(self.graph))
        self.active: Dict[str, Ticket] = {}            # 車牌 -> 票券
        self.entry_queue: Deque[str] = deque()         # 入口佇列
        self.queued: Set[str] = set()
        self.history: List[Tuple[float, str, int]] = []
        self.trie = PlateTrie()

    # ---- 入口 ----
    def arrive(self, plate: str) -> None:
        if not plate:
            raise ValueError("車牌不可為空")
        if plate in self.active or plate in self.queued:
            raise ValueError("%s 已在場內或排隊中" % plate)
        self.entry_queue.append(plate)
        self.queued.add(plate)

    def process_entry(self, now: Optional[float] = None) -> Optional[Ticket]:
        now = time.time() if now is None else now
        if not self.entry_queue:
            return None
        slot = self.mgr.allocate()
        if slot is None:
            return None                                # 滿場，繼續排隊
        plate = self.entry_queue.popleft()
        self.queued.discard(plate)
        slot.plate = plate
        ticket = Ticket(plate, slot, now)
        self.active[plate] = ticket
        self.trie.insert(plate)
        return ticket

    def process_all(self, now: Optional[float] = None) -> List[Ticket]:
        tickets = []
        while True:
            t = self.process_entry(now)
            if t is None:
                return tickets
            tickets.append(t)

    # ---- 出口 ----
    def exit(self, plate: str, now: Optional[float] = None) -> Receipt:
        now = time.time() if now is None else now
        ticket = self.active.pop(plate)                # 不在場內會拋出 KeyError
        seconds = now - ticket.enter_time
        hours = max(1, int(math.ceil(seconds / 3600.0)))
        fee = hours * self.rate_per_hour
        self.mgr.release(ticket.slot)
        self.trie.delete(plate)
        self.history.append((now, plate, fee))
        return Receipt(plate, seconds, hours, fee)

    # ---- 查詢 ----
    def find(self, plate: str) -> Optional[str]:
        t = self.active.get(plate)
        return t.slot.name if t else None

    def search(self, prefix: str) -> List[Tuple[str, str]]:
        return [(p, self.active[p].slot.name) for p in self.trie.search_prefix(prefix)]

    def route_to(self, plate: str) -> Tuple[List[str], float]:
        return shortest_path(self.graph, "入口", self.active[plate].slot.name)

    def revenue_between(self, t1: float, t2: float) -> Tuple[int, int]:
        return revenue_between(self.history, t1, t2)

    def status(self) -> Dict[str, int]:
        return {"total": self.mgr.total(),
                "occupied": len(self.active),
                "free": self.mgr.free_count(),
                "waiting": len(self.entry_queue)}
