# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-06 09:20（+08）
- **交棒者**：Claude Code ／ `vm`（雲端容器；盤點骨架在 Claude Code 雲端版上的可用性，只讀、未改制度）

## 任務目標

**使用者 2026-11-06 發現需求規劃漏了「可能跑在雲端」這個情境。** 本輪在 Claude Code 雲端版實測骨架各環節，結果列在下方「未完成」第 1 項。使用者決定**先不用雲端**；是否把雲端納入需求、怎麼排優先序尚未決定。D8 專案數仍是需求文件的既有阻擋點。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26110613｜補登F21待決｜工作中｜交棒0次`，2026-11-06 13:39 (+08) 開工
- **骨架版本**：`2026-11-03`
- 上一輪本機能力：Windows、Python 3.13、Git Bash、PowerShell。本輪是 Linux 雲端容器（Python 3.13、bash、git）。

## 已完成

- 雲端可用性盤點（2026-11-06，Claude Code 雲端版，容器 `CLAUDE_CODE_REMOTE=true`）。可用：開場 hook 會跑、fetch／比對 origin 正常、`curl` 讀得到上游 `VERSION`、Python 腳本可跑、`git push --dry-run` 到 main 成功（未實推前）、session 改名有工具（需先取 session ID）。
- 需求文件全文搜「雲端／cloud／remote／容器」零筆，證實需求未涵蓋此情境。
- 本輪除 `HANDOFF.md` 外未改任何檔案；未改 skill、hook、`VERSION`、需求文件，未同步其他專案，未呼叫額外模型。

## 未完成／下一步

1. **雲端情境要不要納入需求，待使用者決定**（使用者 2026-11-06：先不用雲端）。本輪實測到的缺口，供納入時當證據：
   - **機器名不能分辨雲端容器**：hostname 一律 `vm`，兩個雲端 session 互相會落進「同機器同工具」的 🟡，跨機防呆失效。
   - **session 名的 `YYMMDDHH` 用容器時區 UTC**，比 +08 慢 8 小時（hook 印 `26110601`，台灣當時 09 點）。
   - **全域 `~/.claude/skills/handoff/` 每次都不存在**：本 repo 只能讀部署包範本；「覆蓋全域副本」在雲端做不到。部署出去的專案自帶 skill，不受影響。
   - **容器會被回收**：A2.5 選項 1「回那台機器走完交棒」可能做不到；雲端自帶 Stop hook 會要求未提交／未推送變更先 commit+push，算部分補救。
   - **pre-push 防呆只攔 Bash／PowerShell**：雲端有 GitHub MCP 寫檔工具，可繞過。
   - **雲端預設規則**（預設分支先開新分支、使用者沒要求不 commit）與 A5 直接推標記到 main 相反；本 repo 靠 AGENTS.md 優先。
   - `sync_project.py --all` 在雲端掃不到其他專案；專案 `verify_state.py` 的服務項在雲端無憑證只會 SKIP。
   - Windows／Codex／Antigravity 接線在雲端用不到。
2. **D8 專案數**仍是需求文件第 6 節的阻擋點；四項資料（活躍專案數、更新頻率、例外比例、操作者人數）未蒐集，更新頻率須先定統計口徑。
3. 需求第 7 節第 1 步的**現況對照**未建立（照第 5 節逐 ID 移交，做三種輸入的紙上核對）。
4. [第二輪複審快照](project-bootstrap-reaudit-2026-11-03.md) R01–R09 未逐項核對：驗證器已有以 R01–R09 命名的情境，「全部未修」的舊說法不成立，但修正邊界要自己對一遍。
5. [效率計畫](project-bootstrap-efficiency-plan.md) P0／P1 未實作；第 14 章 S1 仍待採納。

## 地雷與注意事項

- 冷啟動先依 [AGENTS.md](AGENTS.md) 完成 A；改檔前重新取得自己的工作中標記。
- **雲端缺口是單次實測觀測**（2026-11-06、一個雲端環境），不是已決定的需求；`push` 只做了 dry-run 與本輪實推，未測權限受限的環境。
- 上一輪 HANDOFF 的交接時間寫 10:10（+08），但該輪 commit `8fff1dc` 時間是 09:02（+08），時間欄當時填錯；原因未查。
- F21 的「留痕（阻擋是目標，待使用者確認）」仍未決定，不要當成已定案。
- **第 4 節的強度是使用者的決定，不是量測結果**；不得從現行程式能力反推或下調。
- v3.3 與 v3.4 同日採納，日期分不出狀態，必須看版本。
- 用腳本改 `.md` 不要手寫 `\u` 轉義，patch 一律「命中數 ≠ 1 就 abort」。
- 定案需求不等於已實作，也不等於曾被驗收。

## 服務查證與期望快照

本輪在雲端容器執行 `python3 -X utf8 tools/verify_bootstrap.py`：exit 0、50 項全過、無 skip。上一輪 Windows 為 52 項；差的 2 項推測是只在 Windows 跑的 PowerShell 檢查（未逐項核對）。
本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用上述替代入口。同步與 hook 重審不適用（未改相關內容）。
未測其他 OS、Python 3.8、私人專案、外部服務或模型遵循。

## 懸置事項（AI 勿自行處理）

- 雲端情境是否納入需求與優先序；D8 專案數與四項資料口徑；F21 的阻擋升級。
- 原子 claim 另案，Antigravity IDE 不重開；額外模型探針須先授權且只用訂閱額度。
