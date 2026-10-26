# 🅿️ 智慧停車場

以**資料結構為架構**的停車管理系統：進出場、自動分配最近車位、入口排隊、
計費、車牌搜尋、場內導航、營收報表與狀態存檔。純 Python 標準函式庫，無需安裝任何套件。

![CI](https://github.com/<你的帳號>/smart-parking-lot/actions/workflows/ci.yml/badge.svg)

## 資料結構對照

| 功能 | 資料結構 | 檔案 | 複雜度 |
|---|---|---|---|
| 車位狀態 | 二維陣列 | `parking/slots.py` | 存取 O(1) |
| 分配最近空位 | 最小堆積 | `parking/slots.py` | O(log n) |
| 入口排隊 | 佇列 `deque` | `parking/lot.py` | O(1) |
| 車牌 → 票券 | 雜湊表 `dict` / `set` | `parking/lot.py` | O(1) 平均 |
| 車牌前綴搜尋 | 字典樹 Trie | `parking/trie.py` | O(L + k) |
| 場內導航 | 圖 + Dijkstra | `parking/graph.py` | O((V+E) log V) |
| 營收區間查詢 | 有序串列 + `bisect` | `parking/report.py` | O(log n) 定位 |

## 專案結構

```
smart-parking-lot/
├─ parking/            # 核心套件
│  ├─ models.py        # Slot / Ticket / Receipt
│  ├─ slots.py         # 車位管理（陣列 + 堆積）
│  ├─ trie.py          # 車牌 Trie
│  ├─ graph.py         # 路網圖與 Dijkstra
│  ├─ report.py        # 營收查詢
│  ├─ lot.py           # ParkingLot 整合進出場與計費
│  ├─ storage.py       # JSON 存檔 / 讀檔
│  └─ cli.py           # 文字選單
├─ tests/              # 單元測試（unittest）
├─ notebooks/          # Colab 開發 notebook
├─ demo/               # OnlineGDB 單檔展示版
└─ .github/workflows/  # GitHub Actions 自動測試
```

## 快速開始（Windows / VS Code）

```powershell
# 1. 建立並啟用虛擬環境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. 執行（可選 --state 自動存檔）
python -m parking
python -m parking --state parking_state.json --floors 3 --per-floor 10

# 3. 執行測試
python -m unittest discover -s tests -v
```

> 終端機若中文顯示亂碼，請使用 Windows Terminal 或 VS Code 內建終端機，
> 或先執行 `chcp 65001`。

## 作為函式庫使用

```python
from parking import ParkingLot

lot = ParkingLot(floors=2, per_floor=4)
lot.arrive("ABC-123")
ticket = lot.process_entry()
print(ticket.slot.name, lot.route_to("ABC-123"))
print(lot.exit("ABC-123").fee)
```

## 開發流程

- `main` 分支保持可用；新功能在 `feature/<名稱>` 分支開發，再開 Pull Request 合併
- Commit 訊息格式：`feat:` 新功能、`fix:` 修正、`test:` 測試、`docs:` 文件、`refactor:` 重構
- 每次 push 會由 GitHub Actions 在 Python 3.9 / 3.11 / 3.12 執行全部測試

## 擴充構想

預約車位（到期時間堆積）、電動車 / 身障車位（各一個堆積）、月租車優先入場（優先佇列）、
Flask API 或 JavaScript 網頁版。
