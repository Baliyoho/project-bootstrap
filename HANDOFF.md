# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-31 03:05（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（「工作中」標記加工具欄，擋同機器跨工具誤接棒）

## 這份檔案在這個 repo 的角色（跟其他專案不一樣，先讀這段）

**它只有一個任務：當跨機器「工作中」標記的載體。** 這個 repo 是制度的來源、刻意沒有 handoff
skill 也沒有知識庫（見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」），所以：

- **不要把這裡當狀態日誌或知識庫。** 鐵律「這裡不是知識庫」照舊；跨 session 的事實看 `git log`
  與各檔的 `source:` 版本標記。這一份要短，短到每輪交棒都願意維護它——會腐化的文件就是從
  「順手多寫兩段」開始的。
- **它是部署包範本 3.3 的*實例*，不是副本。** `sync_project.py` 的 `discover()` 靠 handoff skill
  認專案，掃不到這個 repo；`PARTIAL` 也只會在缺欄位時補欄位。所以它沒有同步義務，改它不必
  動 `VERSION`，也不要拿 `sync_project.py` 同步它。
- **每輪一定要維護的只有「待續分支」與「工作中」兩欄**：開工由 skill 的 A5 寫上機器、工具與
  session，交棒由 B6 改回「無（已交棒）」。其餘段落沒變就不用動。

## 任務目標

維護 AI 協作專案管理骨架的權威版 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26103103｜Antigravity hook｜工作中`，2026-10-31 03:20 (+08) 開工
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。

## 已完成

- 2026-10-31（**跳版 `2026-10-31`**）：**「工作中」標記加工具欄**，格式 `` `機器` ／ `工具` ／ `session 名`（可選） ``。
  四處一起改：A5 寫標記填工具名；A2.5 的「指向這台機器」拆成同工具／別的工具／沒有工具欄三列
  （判準不再綁側欄，因為只有 Claude Code 有側欄）；兩支 hook 的同機器分支拆成同工具→🟡／不同
  工具→🔴；`check_docs.py` 第 6 項擋「標記在工作中卻沒有工具欄」。環境變數只拿來加嚴，兩家簽章
  同時在場（＝被繼承）就不猜，認不出來只印 🟡 並把「你自己是不是 X」丟回給模型答。新舊格式靠
  session 名裡的全形豎線分辨。`verify_bootstrap.py` 把兩支 hook 的期望值收斂成共用的 `busy_cases()`
  （八情境）並清掉工具簽章變數再測，另加工具欄負向測試 → **exit 0，25 項全 ok**。
- 2026-10-31：**五個專案已同步到 `2026-10-31`**：`Grist_test` `42c60cc`、`NAA_TR` `7791ed9`、
  `NAS_MAINT` `123c3fb`、`摘要skill設計` `796664f`、`第三批56箱後檢查` `7255bce`，各一個 commit 都已
  push，`check_docs.py` 全 exit 0。兩份全域副本（`~/.claude/`、`~/.codex/`）也已覆蓋。
  **`序號卡`、`解決網路速度問題` 刻意沒同步**（前者已完結、後者仍有別人未提交的兩個檔），
  會在下次開場自己報「骨架落後」，是自癒的。
- 2026-10-31：三平台環境變數實測、同機器跨工具的缺口、Antigravity 有 CLI 這個修正，都在部署包「工具身分」一節。
- 2026-10-30：三平台能力重查、補跨機器「工作中」標記、**決定不裝** `pre-push-handoff.sh`（理由在部署包版本註與 [ARCHITECT.md](ARCHITECT.md)）。

## 未完成／下一步

1. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個工具都
   觸發、`statusMessage` 會不會被忽略。卡在互動式的 `/hooks` 信任（非互動只能用
   `--dangerously-bypass-hook-trust`，刻意沒用）。**量 hook 環境卡在同一道信任**（本 repo 也沒有 trust
   條目，`.codex/` 整層本來就被跳過）。這道牆沒拆掉之前，hook 端的工具偵測就只有推論、沒有測量。
2. （可選，要實測）Antigravity `.agents/hooks.json`：設計已定——一支**只做管線**的 wrapper，讀 stdin 取
   `workspacePaths[0]`、`cd` 過去、跑同一支 `.sh`、stdout 包成 `injectSteps` 的 `ephemeralMessage`。
3. （可選）`SessionStart` 的 `sessionTitle` 自動寫 session 名稱（只固定得住開場那一半，狀態轉換仍靠模型）；
   `.codex/hooks.json` 接線本 repo 的 `repo-git-check.sh`（**不要**複製第二份腳本）；`AGENTS.md` 補一段
   「開工第一件事」——可攜層目前沒有一句叫 agent 先 `git fetch`、先看 origin 的「工作中」。

（「階段二 pre-push hook」2026-10-30 決定不裝，理由在 [ARCHITECT.md](ARCHITECT.md)，掃到別再重提。）

## 地雷與注意事項

- **single writer**：同一時間只有一台機器＋一個工具改 `main`。標記只告訴你「有東西在那台機器上」，別台未提交的變更仍然只在那台的磁碟上。
- 改制度改 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）。
- **只有 `SKILL.md` 真的改了才跳 `VERSION`**（鐵律 1）：這輪改了，所以跳；上一輪只改範本敘述，所以沒跳。
- 本檔與 `.claude/hooks/repo-git-check.sh` 都不是部署包的一部分，**不要**用 `sync_project.py` 同步。
- 公開 repo：全部 Git 歷史人人看得到，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。

## 服務查證與期望快照

這個 repo 沒有 `tools/verify_state.py`——它是骨架的檔，不部署到自己身上。驗證指令是：

`python -X utf8 tools/verify_bootstrap.py`

目前：exit 0，**25 項全 `ok`**（`VERSION` 2026-10-31）。新增的那一項是「工具欄（負向測試）」。

## 懸置事項（AI 勿自行處理）

- 上面「未完成」三項要不要做（都要花時間實測或設計，不是順手能完成的；第 1 項還卡在互動式信任）。
