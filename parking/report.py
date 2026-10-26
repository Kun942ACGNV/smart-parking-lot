from __future__ import annotations

import bisect
from typing import List, Tuple

History = List[Tuple[float, str, int]]       # (出場時間, 車牌, 費用)


def revenue_between(history: History, t1: float, t2: float) -> Tuple[int, int]:
    """回傳 (營收, 出場輛數)。history 須依時間遞增。"""
    times = [h[0] for h in history]
    lo = bisect.bisect_left(times, t1)
    hi = bisect.bisect_right(times, t2)
    return sum(h[2] for h in history[lo:hi]), hi - lo
