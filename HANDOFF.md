# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 15:54（+08）
- **交棒者**：Claude Code ／ `DESKTOP-M8MRS05`（修 F05 接線定位，並把副本發到六個專案）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。依
[project-bootstrap-audit.md](project-bootstrap-audit.md) 分批修正；已修 **F01、F09、F02、F03、F05**
（五條 P1），其餘 11 條未實作。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-02`
- 本機能力：Windows、Python 3.13.15、Git Bash、PowerShell 7；本輪 fetch、開工標記與收尾 push 均成功。

## 已完成

- **F05（接線 cwd 定位）**：hook 的 `command` 以 **session 的 cwd** 執行，所以從子目錄開 session
  （`cd tools && claude`）時 `bash .claude/hooks/git-freshness.sh` 是 **exit 127**——在 `tools/` 下
  重現過，而 **SessionStart 失敗跟「檢查過了沒事」在畫面上一模一樣**。四份接線（部署包 3.9 兩條、
  3.17 兩條 Unix ＋兩條 Windows，以及本 repo 自己的 `.claude/settings.json`、`.codex/hooks.json`）
  改成 `$(git rev-parse --show-cdup)` 前綴；它回的是**相對**路徑，所以鐵律 5 原封不動。Windows
  那一欄多一次 `-replace '/','\'`：`cmd` 吃不下 `../.claude\hooks\...` 的混合斜線（從子目錄實測
  `'..' is not recognized`）。**Antigravity（3.20）刻意不跟**——`agy` 的 `command` 不經 shell、
  cwd 是 `.agents/`，基準不同。
- 守門人：驗證器新增第 39 項「接線 cwd 定位」——四份接線的文字檢查，加上在**含空白與中文**路徑的
  fixture repo 上，從 `.`／`tools`／`docs/ai-notes` 實跑接線 JSON 裡**原始的那一串命令**（開場檢查
  要 exit 0 並印 `[git-check]`；pre-push 要 exit 2——拿 exit 2 當「腳本真的跑到了」的證據，exit 0
  連「什麼都沒發生」都會過），外加 Windows 完整啟動鏈與兩個負向測試（舊形式、拿掉斜線正規化）。
  **退回舊接線實跑過，確實 FAIL（exit 2）。** `tools/verify_bootstrap.py`：exit 0、**39 項全過**、無 skip。
- **副本已發下**：六個專案（`Grist_test`、`NAA_TR`、`NAS_MAINT`、`摘要skill設計`、
  `第三批56箱後檢查`、`解決網路速度問題`）各 2 項、共 12 項全部 exit 0；每個專案的 diff 就是那兩份
  接線的命令各 3 行，專案自己的 `permissions` 與自有 hook 都在。驗收不只看檔案：六個專案都**從
  `tools/` 實跑接線裡原始的那一串命令**，exit 0 且印出 `[git-check]`（那正是 F05 修的情境），
  `check_docs.py` 六個都 exit 0；`Grist_test` 另外走完 **PowerShell → cmd → Git Bash** 的 Windows
  啟動鏈，也是從 `tools/` 起跑。`序號卡` 已完結，**刻意排除**（它現在落後 4 項）。

## 未完成／下一步

1. **六個專案都有未提交的變更，每個要在自己的 session 照 B 模式收尾。** 2026-11-02 使用者明確決定
   不在骨架這個 session 代做。五個專案各 4 個檔（上一輪的 `git-freshness.sh`、`check_docs.py`
   ＋本輪的兩份接線）；`解決網路速度問題` 有 8 個——多了上一輪補的兩份 `SKILL.md`，以及**兩個與
   這些都無關的 `docs/ai-notes/` 檔（使用者說過不用管）**，所以那個專案要**明確 stage**，
   不可 `git add -A`。⚠️ 四個在權威分支（`Grist_test`、`NAS_MAINT`、`第三批56箱後檢查`、
   `解決網路速度問題`）不更新 `HANDOFF.md` 就會被 pre-push 防呆擋下（exit 2）。
2. **接線改過的專案，Codex 那一面要重新審核 hook**（信任綁當前雜湊，而且只有互動模式會問）；
   本 repo 自己的 `.codex/hooks.json` 也改過。Claude Code 這一面的端到端證據是**下一個 session
   開場那幾行 `[repo-check]`／`[git-check]`**——沒印出來就是接線壞了，請立刻回報。
3. 其餘 11 條未實作。複核過的優先序：**F15／F14 → F08**；F06（push 防呆的漏判）與 F05 相鄰，但是 P2。

## 地雷與注意事項

- **不要為了讓各專案知道而跳 `VERSION`**：它是「`SKILL.md` 的版本」，跳了各專案會永遠印「骨架
  落後」而且同步修不掉（鐵律 1）。本輪沒動 `SKILL.md`，也沒有任何 `source:` 標記要跳——所以這次
  是**手動**同步，落後偵測不會替你講這件事。
- **不要「順手統一」Antigravity 的接線**：它的 `command` 不經 shell，`$( )` 不會展開，只會變成
  檔名的一部分（理由寫在 3.20）。
- 六個專案的 Windows 啟動鏈只在 `Grist_test` 上實跑過，另外五個驗的是 Unix 命令與檔案內容；
  也**沒有**在真的 Codex session 裡重驗（那要互動模式並重新審核）。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、39 項全過、重生骨架 22 檔，無 skip。
B4：本 repo 沒有 `check_docs.py`，由上述完整驗證涵蓋。

## 懸置事項（AI 勿自行處理）

- 新增模型探針仍須先取得授權且只用訂閱額度；本輪未呼叫任何模型探針。
- Antigravity IDE hook 未觸發原因維持未知、不再追查。
