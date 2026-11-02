# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 17:35（+08）
- **交棒者**：Claude Code ／ `DESKTOP-M8MRS05`（產出查核處理進度報告，準備換模型接棒）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。依
[project-bootstrap-audit.md](project-bootstrap-audit.md) 分批修正；16 條裡**已修 9 條**
（F01–F05、F08、F09、F14、F15），其餘 **7 條未實作**（F06、F07、F10–F13、F16）。

🔴 **接手第一件事：走完 A 模式之後，先讀
[project-bootstrap-audit-progress.md](project-bootstrap-audit-progress.md)。** 它是為「換一個
模型接棒」寫的：16 條逐條的狀態、已修的那幾條守門人是哪一項與證據、未修的那幾條的複核、
建議作法、驗收門檻與建議順序，還有跨條目的共同規則與兩個會咬人的工具陷阱。本檔只放當下
狀態，**不要在這裡重建那些細節**。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-02`
- 本機能力：Windows、Python 3.13.15、Git Bash、PowerShell 7；本輪 fetch、開工標記與收尾 push 均成功。

## 已完成

- **本輪只新增文件，沒有動制度**：根目錄新增
  [project-bootstrap-audit-progress.md](project-bootstrap-audit-progress.md)（查核 16 條的處理
  進度），並掛上兩個入口——[AGENTS.md](AGENTS.md) 的「開工第一件事」加一行要求先讀它，
  [ARCHITECT.md](ARCHITECT.md) 的根目錄表登記這一檔。**不部署、不同步**，`sync_project.py`
  不碰它；`SKILL.md` 與任何帶 `source:` 標記的範本都沒動，所以 `VERSION` 與標記都不跳。
- **為什麼狀態不寫進查核報告**：那份報告是對 `main @ 313e7a5` 的凍結快照，它自己寫明
  「不代表問題已修正」。進度會變、快照不會變，所以進度有自己的家（每個事實只有一個家）。
- 前兩輪修完的 F14／F15（維護工具的 Python 下限、五處「已修正的主張又復活」）與
  F04／F08（`verify_state` 不再把失敗吞成 exit 0、`check_docs` 補交接快照檢查與連結誤報），
  守門人是第 40–43 項，**都拿修正前的內容實跑比對過**。細節在進度報告。
- `tools/verify_bootstrap.py`：exit 0、**43 項全過**、重生骨架 22 檔，無 skip。

## 未完成／下一步

1. **先讀上面那份進度報告**，再挑下一條。建議順序：**F06 → F07**（把查核第一批「修錯誤
   成功訊號」收完，跟已修的 F03／F04 同一種病），之後 **F11 → F10 → F12**（F11 的狀態表是
   另外兩條的前提；這三條會動 `SKILL.md`，所以**會跳 `VERSION`**、要同步各專案），
   最後 **F13 → F16**。
2. 🔴 **第 43 項上線後在三個專案抓到真的制度漂移**（不是誤報，各自在那個專案的 session 修；
   本輪刻意不代改——填「待續分支」要知道那個專案的實況）：`NAA_TR`、`NAS_MAINT` 的
   `HANDOFF.md` **沒有「待續分支」欄位**（A2 靠它判斷主幹在哪）；`解決網路速度問題` 有
   **兩個「## 已完成」**（累積成日誌）。其餘三個專案 `check_docs.py` exit 0。
3. **六個專案仍有未提交變更**，每個要在自己的 session 照 B 模式收尾（2026-11-02 使用者明確
   決定不在骨架這個 session 代做）。`解決網路速度問題` 另有兩個與本制度無關、使用者說過
   不用管的 `docs/ai-notes/` 檔，所以那個專案要**明確 stage**，不可 `git add -A`。
   ⚠️ 四個在權威分支的專案不更新 `HANDOFF.md` 會被 pre-push 防呆擋下（exit 2）。
4. **接線改過的專案，Codex 那一面要重新審核 hook**（信任綁當前雜湊，只有互動模式會問）。

## 地雷與注意事項

- 🔴 **`VERSION` 沒跳，所以各專案的落後偵測不會講「骨架落後」**，而前一輪真的改了
  `tools/check_docs.py` 這個同步對象——同步是手動做的。別以為沒提示就是沒落後（鐵律 1）。
- **不要用 `sync_project.py --all --write`**：它會掃到一個已完結、刻意不再維護的專案
  （2026-11-02 實測）。逐一指定路徑同步。
- **Python 下限是靜態擔保，不是實測**（這台機器只有 3.13）。別把「43 項全過」說成
  「在 3.8 上驗過」。
- **用腳本改檔時不要把 patch 從 heredoc 餵進 `python -`**，轉義會被多解一層；**寫測試要
  先驗儀器再測受測物**。兩條都在進度報告與 AGENTS.md 裡有常駐的家。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、43 項全過、重生骨架 22 檔，無 skip。
B4：本 repo 沒有 `check_docs.py`，由上述完整驗證涵蓋。

## 懸置事項（AI 勿自行處理）

- 新增模型探針仍須先取得授權且只用訂閱額度；本輪未呼叫任何模型探針。
- Antigravity IDE hook 未觸發原因維持未知、不再追查。
