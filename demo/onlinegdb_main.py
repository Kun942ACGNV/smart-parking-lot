# -*- coding: utf-8 -*-
# =====================================================================
#  智慧停車場 —— OnlineGDB 展示版（單檔、純標準函式庫、文字選單）
#  使用方式：貼到 OnlineGDB（語言選 Python 3），按 Run，依選單輸入數字
#
#  資料結構對照
#    車位狀態      二維陣列  slots[floor][index]
#    最近空位      最小堆積  heapq
#    入口排隊      佇列      collections.deque
#    車牌→票券     雜湊表    dict / set
#    車牌前綴搜尋  字典樹    Trie
#    場內導航      圖        Dijkstra（堆積版）
#    營收查詢      有序串列  bisect
# =====================================================================
import heapq
import bisect
import math
import time
from collections import deque

FLOORS = 2
PER_FLOOR = 4
RATE_PER_HOUR = 30


# ---------------------------------------------------------------- 圖與導航
def build_lot_graph(floors, per_floor):
    g = {}

    def add(u, v, w):
        g.setdefault(u, []).append((v, w))
        g.setdefault(v, []).append((u, w))

    add("入口", "路口F0", 5)
    for i in range(per_floor):
        add("路口F0", "F0-%d" % i, 2 + 2 * i)
    prev = "路口F0"
    for f in range(1, floors):
        add(prev, "路口F%d" % f, 10)          # 坡道
        for i in range(per_floor):
            add("路口F%d" % f, "F%d-%d" % (f, i), 2 + 2 * i)
        prev = "路口F%d" % f
    return g


def dijkstra(graph, start):
    dist = {start: 0}
    prev = {}
    pq = [(0, start)]
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


def shortest_path(graph, start, goal):
    dist, prev = dijkstra(graph, start)
    path = [goal]
    cur = goal
    while cur != start:
        cur = prev[cur]
        path.append(cur)
    return path[::-1], dist[goal]


# ---------------------------------------------------------------- Trie
class TrieNode(object):
    def __init__(self):
        self.children = {}
        self.is_end = False


class PlateTrie(object):
    def __init__(self):
        self.root = TrieNode()

    def insert(self, plate):
        node = self.root
        for ch in plate:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True

    def search_prefix(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        result = []

        def dfs(n, path):
            if n.is_end:
                result.append(prefix + path)
            for c in sorted(n.children):
                dfs(n.children[c], path + c)

        dfs(node, "")
        return result

    def delete(self, plate):
        def _del(node, i):
            if i == len(plate):
                if not node.is_end:
                    return False
                node.is_end = False
                return not node.children
            child = node.children.get(plate[i])
            if child is None:
                return False
            if _del(child, i + 1):
                del node.children[plate[i]]
                return (not node.children) and (not node.is_end)
            return False

        _del(self.root, 0)


# ---------------------------------------------------------------- 車位與票券
class Slot(object):
    def __init__(self, floor, index, distance):
        self.floor = floor
        self.index = index
        self.distance = distance
        self.plate = None

    @property
    def name(self):
        return "F%d-%d" % (self.floor, self.index)


class Ticket(object):
    def __init__(self, plate, slot, enter_time):
        self.plate = plate
        self.slot = slot
        self.enter_time = enter_time


class SlotManager(object):
    def __init__(self, floors, per_floor, distance_map):
        self.floors = floors
        self.per_floor = per_floor
        self.slots = [[Slot(f, i, distance_map["F%d-%d" % (f, i)])
                       for i in range(per_floor)] for f in range(floors)]
        self.free_heap = [(s.distance, s.floor, s.index)
                          for row in self.slots for s in row]
        heapq.heapify(self.free_heap)

    def allocate(self):
        if not self.free_heap:
            return None
        _, f, i = heapq.heappop(self.free_heap)
        return self.slots[f][i]

    def release(self, slot):
        slot.plate = None
        heapq.heappush(self.free_heap, (slot.distance, slot.floor, slot.index))

    def free_count(self):
        return len(self.free_heap)

    def total(self):
        return self.floors * self.per_floor


# ---------------------------------------------------------------- 停車場
class ParkingLot(object):
    def __init__(self, floors, per_floor):
        self.graph = build_lot_graph(floors, per_floor)
        dist, _ = dijkstra(self.graph, "入口")
        distance_map = dict((k, v) for k, v in dist.items()
                            if k.startswith("F") and "-" in k)
        self.mgr = SlotManager(floors, per_floor, distance_map)
        self.active = {}            # 車牌 -> Ticket
        self.entry_queue = deque()  # 入口排隊
        self.queued = set()
        self.history = []           # (出場時間, 車牌, 費用)
        self.trie = PlateTrie()
        self.offset = 0.0           # 展示用：快進時間（秒）

    def now(self):
        return time.time() + self.offset

    def arrive(self, plate):
        if plate in self.active or plate in self.queued:
            return False
        self.entry_queue.append(plate)
        self.queued.add(plate)
        return True

    def process_entry(self):
        if not self.entry_queue:
            return None
        slot = self.mgr.allocate()
        if slot is None:
            return None
        plate = self.entry_queue.popleft()
        self.queued.discard(plate)
        slot.plate = plate
        ticket = Ticket(plate, slot, self.now())
        self.active[plate] = ticket
        self.trie.insert(plate)
        return ticket

    def exit(self, plate):
        ticket = self.active.pop(plate)
        seconds = self.now() - ticket.enter_time
        hours = max(1, int(math.ceil(seconds / 3600.0)))
        fee = hours * RATE_PER_HOUR
        self.mgr.release(ticket.slot)
        self.trie.delete(plate)
        self.history.append((self.now(), plate, fee))
        return seconds, hours, fee


# ---------------------------------------------------------------- 介面輔助
def read(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return None


def fmt_duration(seconds):
    m = int(seconds // 60)
    return "%d 小時 %d 分" % (m // 60, m % 60)


def show_status(lot):
    print("\n----- 車位圖（[ ] 空位，[車牌] 占用） -----")
    for f in range(lot.mgr.floors):
        row = []
        for s in lot.mgr.slots[f]:
            row.append("[%s]" % (s.plate if s.plate else "  空  "))
        print("F%d  %s" % (f, " ".join(row)))
    print("總車位 %d｜使用中 %d｜空位 %d｜排隊中 %d" % (
        lot.mgr.total(), len(lot.active),
        lot.mgr.free_count(), len(lot.entry_queue)))
    if lot.entry_queue:
        print("排隊順序：" + " → ".join(lot.entry_queue))


def do_arrive(lot):
    plate = read("輸入車牌：")
    if not plate:
        print("未輸入車牌")
        return
    plate = plate.upper()
    if not lot.arrive(plate):
        print("× %s 已在場內或排隊中" % plate)
        return
    print("✓ %s 已加入入口佇列（目前排隊 %d 輛）" % (plate, len(lot.entry_queue)))


def do_process(lot):
    if not lot.entry_queue:
        print("入口沒有等候的車輛")
        return
    count = 0
    while True:
        t = lot.process_entry()
        if t is None:
            break
        count += 1
        path, d = shortest_path(lot.graph, "入口", t.slot.name)
        print("✓ %s 入場 → 車位 %s（行車距離 %d）" % (t.plate, t.slot.name, d))
        print("   路線：" + " → ".join(path))
    if lot.entry_queue:
        print("⚠ 車位已滿，仍有 %d 輛在排隊" % len(lot.entry_queue))


def do_exit(lot):
    plate = read("輸入出場車牌：")
    if not plate:
        return
    plate = plate.upper()
    if plate not in lot.active:
        print("× 場內找不到 %s" % plate)
        return
    seconds, hours, fee = lot.exit(plate)
    print("✓ %s 出場｜停車 %s｜計費 %d 小時｜應收 %d 元" % (
        plate, fmt_duration(seconds), hours, fee))
    t = lot.process_entry()
    if t:
        print("   排隊車輛 %s 自動進入釋出的車位 %s" % (t.plate, t.slot.name))


def do_find(lot):
    plate = read("輸入完整車牌：")
    if not plate:
        return
    plate = plate.upper()
    t = lot.active.get(plate)
    if t is None:
        print("× 場內找不到 %s" % plate)
        return
    path, d = shortest_path(lot.graph, "入口", t.slot.name)
    print("✓ %s 在車位 %s" % (plate, t.slot.name))
    print("   入口到車位：" + " → ".join(path) + "（距離 %d）" % d)


def do_search(lot):
    prefix = read("輸入車牌前綴：")
    if not prefix:
        return
    results = lot.trie.search_prefix(prefix.upper())
    if not results:
        print("找不到符合的車牌")
        return
    for p in results:
        print("  %s → %s" % (p, lot.active[p].slot.name))


def do_report(lot):
    if not lot.history:
        print("尚無出場紀錄")
        return
    total = sum(h[2] for h in lot.history)
    print("累計出場 %d 輛，營收 %d 元" % (len(lot.history), total))
    s = read("查詢最近幾小時的營收？（直接 Enter 跳過）：")
    if not s:
        return
    try:
        hrs = float(s)
    except ValueError:
        print("請輸入數字")
        return
    times = [h[0] for h in lot.history]
    t2 = lot.now()
    t1 = t2 - hrs * 3600
    lo = bisect.bisect_left(times, t1)
    hi = bisect.bisect_right(times, t2)
    part = lot.history[lo:hi]
    print("最近 %g 小時：%d 輛，營收 %d 元" % (hrs, len(part), sum(h[2] for h in part)))


def do_skip_time(lot):
    s = read("快進幾小時？（展示計費用）：")
    try:
        hrs = float(s)
    except (TypeError, ValueError):
        print("請輸入數字")
        return
    lot.offset += hrs * 3600
    print("✓ 系統時間已快進 %g 小時" % hrs)


def do_demo(lot):
    for p in ["ABC-123", "ABC-456", "ABD-555", "XYZ-789", "KUN-001"]:
        lot.arrive(p)
    do_process(lot)


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


def main():
    lot = ParkingLot(FLOORS, PER_FLOOR)
    actions = {"1": do_arrive, "2": do_process, "3": do_exit,
               "4": do_find, "5": do_search, "6": show_status,
               "7": do_report, "8": do_skip_time, "9": do_demo}
    while True:
        print(MENU)
        choice = read("請選擇功能：")
        if choice is None or choice == "0":
            print("系統結束，再見！")
            break
        action = actions.get(choice)
        if action:
            action(lot)
        else:
            print("無效的選項")


if __name__ == "__main__":
    main()
