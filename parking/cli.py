from __future__ import annotations

import argparse
import os
import time
from typing import Optional

from .lot import ParkingLot
from .storage import load_state, save_state

MENU = """
================ 智慧停車場 ================
 1 車輛到達（加入入口佇列）
 2 入場處理（自動分配最近車位 + 導航）
 3 車輛出場（計費）
 4 以車牌查詢車位
 5 車牌前綴搜尋
 6 場內車位圖與狀態
 7 營收報表
 8 快進時間（展示計費）
 9 載入示範資料
 0 離開
============================================"""

DEMO_PLATES = ["ABC-123", "ABC-456", "ABD-555", "XYZ-789", "KUN-001"]


class Session:
    def __init__(self, lot: ParkingLot):
        self.lot = lot
        self.offset = 0.0                 # 展示用：快進的秒數

    def now(self) -> float:
        return time.time() + self.offset


def _read(prompt: str) -> Optional[str]:
    try:
        return input(prompt).strip()
    except EOFError:
        return None


def _duration(seconds: float) -> str:
    m = int(seconds // 60)
    return "%d 小時 %d 分" % (m // 60, m % 60)


def show_status(s: Session) -> None:
    lot = s.lot
    print("\n----- 車位圖（[ 空 ] 空位） -----")
    for f in range(lot.floors):
        cells = ["[%s]" % (sl.plate if sl.plate else "  空  ") for sl in lot.mgr.slots[f]]
        print("F%d  %s" % (f, " ".join(cells)))
    st = lot.status()
    print("總車位 %d｜使用中 %d｜空位 %d｜排隊中 %d" % (
        st["total"], st["occupied"], st["free"], st["waiting"]))
    if lot.entry_queue:
        print("排隊順序：" + " → ".join(lot.entry_queue))


def do_arrive(s: Session) -> None:
    plate = _read("輸入車牌：")
    if not plate:
        print("未輸入車牌")
        return
    plate = plate.upper()
    try:
        s.lot.arrive(plate)
    except ValueError as e:
        print("× %s" % e)
        return
    print("✓ %s 已加入入口佇列（目前排隊 %d 輛）" % (plate, len(s.lot.entry_queue)))


def do_process(s: Session) -> None:
    lot = s.lot
    if not lot.entry_queue:
        print("入口沒有等候的車輛")
        return
    for t in lot.process_all(s.now()):
        path, d = lot.route_to(t.plate)
        print("✓ %s 入場 → 車位 %s（行車距離 %g）" % (t.plate, t.slot.name, d))
        print("   路線：" + " → ".join(path))
    if lot.entry_queue:
        print("⚠ 車位已滿，仍有 %d 輛在排隊" % len(lot.entry_queue))


def do_exit(s: Session) -> None:
    plate = _read("輸入出場車牌：")
    if not plate:
        return
    plate = plate.upper()
    if plate not in s.lot.active:
        print("× 場內找不到 %s" % plate)
        return
    r = s.lot.exit(plate, s.now())
    print("✓ %s 出場｜停車 %s｜計費 %d 小時｜應收 %d 元" % (
        plate, _duration(r.seconds), r.hours, r.fee))
    t = s.lot.process_entry(s.now())
    if t:
        print("   排隊車輛 %s 自動進入釋出的車位 %s" % (t.plate, t.slot.name))


def do_find(s: Session) -> None:
    plate = _read("輸入完整車牌：")
    if not plate:
        return
    plate = plate.upper()
    if plate not in s.lot.active:
        print("× 場內找不到 %s" % plate)
        return
    path, d = s.lot.route_to(plate)
    print("✓ %s 在車位 %s" % (plate, s.lot.find(plate)))
    print("   入口到車位：" + " → ".join(path) + "（距離 %g）" % d)


def do_search(s: Session) -> None:
    prefix = _read("輸入車牌前綴：")
    if not prefix:
        return
    results = s.lot.search(prefix.upper())
    if not results:
        print("找不到符合的車牌")
    for plate, slot in results:
        print("  %s → %s" % (plate, slot))


def do_report(s: Session) -> None:
    lot = s.lot
    if not lot.history:
        print("尚無出場紀錄")
        return
    print("累計出場 %d 輛，營收 %d 元" % (len(lot.history), sum(h[2] for h in lot.history)))
    text = _read("查詢最近幾小時的營收？（直接 Enter 跳過）：")
    if not text:
        return
    try:
        hours = float(text)
    except ValueError:
        print("請輸入數字")
        return
    t2 = s.now()
    revenue, count = lot.revenue_between(t2 - hours * 3600, t2)
    print("最近 %g 小時：%d 輛，營收 %d 元" % (hours, count, revenue))


def do_skip_time(s: Session) -> None:
    text = _read("快進幾小時？（展示計費用）：")
    try:
        hours = float(text)
    except (TypeError, ValueError):
        print("請輸入數字")
        return
    s.offset += hours * 3600
    print("✓ 系統時間已快進 %g 小時" % hours)


def do_demo(s: Session) -> None:
    for p in DEMO_PLATES:
        try:
            s.lot.arrive(p)
        except ValueError:
            pass
    do_process(s)


ACTIONS = {"1": do_arrive, "2": do_process, "3": do_exit, "4": do_find,
           "5": do_search, "6": show_status, "7": do_report,
           "8": do_skip_time, "9": do_demo}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="parking", description="智慧停車場 CLI")
    parser.add_argument("--floors", type=int, default=2, help="樓層數（預設 2）")
    parser.add_argument("--per-floor", type=int, default=4, help="每層車位數（預設 4）")
    parser.add_argument("--state", help="狀態檔（JSON）；存在則載入，離開時自動存檔")
    args = parser.parse_args(argv)

    if args.state and os.path.exists(args.state):
        lot = load_state(args.state)
        print("已載入狀態檔：%s" % args.state)
    else:
        lot = ParkingLot(args.floors, args.per_floor)
    session = Session(lot)

    while True:
        print(MENU)
        choice = _read("請選擇功能：")
        if choice is None or choice == "0":
            break
        action = ACTIONS.get(choice)
        if action:
            action(session)
        else:
            print("無效的選項")

    if args.state:
        save_state(lot, args.state)
        print("已儲存狀態到 %s" % args.state)
    print("系統結束，再見！")
    return 0
