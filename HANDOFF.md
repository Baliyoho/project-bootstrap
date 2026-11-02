# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 15:46（+08）
- **交棒者**：Claude Code ／ `DESKTOP-M8MRS05`（修 F05：接線從子目錄找不到腳本）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。依
[project-bootstrap-audit.md](project-bootstrap-audit.md) 分批修正；已修 **F01、F09、F02、F03、F05**
（五條 P1），其餘 11 條未實作。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26110215｜修F05接線定位｜工作中｜交棒1次`，2026-11-02 15:58 (+08) 開工
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
  **退回舊接線實跑過，確實 FAIL（exit 2）。**
- `python -X utf8 tools/verify_bootstrap.py`：exit 0、**39 項全過**、無 skip。

## 未完成／下一步

1. **這一輪的接線修正還沒發到任何專案。** `VERSION` 刻意不跳，所以各專案的落後偵測**不會替你講
   這件事**（鐵律 1）；要發就手動跑 `python -X utf8 tools/sync_project.py <專案路徑> --write`
   （`--all` 掃不到本 repo）。⚠️ **六個專案已經有上一輪 F01／F09 的未提交變更**，再同步一次會把
   兩輪混進同一個未提交 diff；2026-11-02 使用者尚未決定要不要現在發。
2. **六個專案的未提交變更仍待各自的 session 照 B 模式收尾**（2026-11-02 使用者明確決定不在骨架
   這個 session 代做）。四個在權威分支（`Grist_test`、`NAS_MAINT`、`第三批56箱後檢查`、
   `解決網路速度問題`）不更新 `HANDOFF.md` 會被 pre-push 擋（exit 2）；`解決網路速度問題` 另有兩個
   與本次無關的未提交檔，要**明確 stage**、不可 `git add -A`。
3. **本 repo 的 `.codex/hooks.json` 改過，Codex 那一面要重新審核 hook**（信任綁當前雜湊，而且只有
   互動模式會問）。Claude Code 這一面的端到端證據就是**下一個 session 開場那幾行 `[repo-check]`**
   ——沒印出來就是接線壞了，請立刻回報。
4. 其餘 11 條未實作。複核過的優先序：**F15／F14 → F08**；F06（push 防呆的漏判）與 F05 相鄰，但是 P2。

## 地雷與注意事項

- **不要為了讓各專案知道而跳 `VERSION`**：它是「`SKILL.md` 的版本」，跳了各專案會永遠印「骨架
  落後」而且同步修不掉（鐵律 1）。本輪沒動 `SKILL.md`，也沒有任何 `source:` 標記要跳。
- **不要「順手統一」Antigravity 的接線**：它的 `command` 不經 shell，`$( )` 不會展開，只會變成
  檔名的一部分（理由寫在 3.20）。
- Windows 這一側的驗收是 **PowerShell → cmd → Git Bash** 的實跑；**沒有**在真的 Codex session 裡
  重驗（那要互動模式並重新審核），所以 B5 的「驗收實際執行」對 Codex 只做到命令鏈這一層。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、39 項全過、重生骨架 22 檔，無 skip。
B4：本 repo 沒有 `check_docs.py`，由上述完整驗證涵蓋。

## 懸置事項（AI 勿自行處理）

- 要不要把這一輪的接線修正同步到六個專案（它們已有未提交變更）——等使用者決定。
- 新增模型探針仍須先取得授權且只用訂閱額度；本輪未呼叫任何模型探針。
- Antigravity IDE hook 未觸發原因維持未知、不再追查。
