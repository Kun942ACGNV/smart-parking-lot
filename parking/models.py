from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


def slot_name(floor: int, index: int) -> str:
    return "F%d-%d" % (floor, index)


@dataclass
class Slot:
    floor: int
    index: int
    distance: float                    # 離入口的行車距離，作為堆積排序鍵
    kind: str = "normal"               # normal / ev / disabled
    plate: Optional[str] = None

    @property
    def name(self) -> str:
        return slot_name(self.floor, self.index)


@dataclass
class Ticket:
    plate: str
    slot: Slot
    enter_time: float                  # 秒


@dataclass
class Receipt:
    plate: str
    seconds: float                     # 實際停車秒數
    hours: int                         # 計費小時數
    fee: int
