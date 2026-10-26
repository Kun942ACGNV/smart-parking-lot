from __future__ import annotations

import json

from .lot import ParkingLot
from .models import Ticket


def save_state(lot: ParkingLot, path: str) -> None:
    data = {
        "floors": lot.floors,
        "per_floor": lot.per_floor,
        "rate_per_hour": lot.rate_per_hour,
        "active": {p: {"slot": t.slot.name, "enter_time": t.enter_time}
                   for p, t in lot.active.items()},
        "queue": list(lot.entry_queue),
        "history": lot.history,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_state(path: str) -> ParkingLot:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    lot = ParkingLot(data["floors"], data["per_floor"], data.get("rate_per_hour", 30))
    for plate, info in data["active"].items():
        slot = lot.mgr.get_slot(info["slot"])
        slot.plate = plate
        lot.active[plate] = Ticket(plate, slot, info["enter_time"])
        lot.trie.insert(plate)
    lot.mgr.rebuild_heap()
    for plate in data["queue"]:
        lot.entry_queue.append(plate)
        lot.queued.add(plate)
    lot.history = [tuple(h) for h in data["history"]]
    return lot
