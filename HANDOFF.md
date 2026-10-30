# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-31 01:02（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（同機器跨工具的防呆缺口＋三平台環境變數實測）

## 這份檔案在這個 repo 的角色（跟其他專案不一樣，先讀這段）

**它只有一個任務：當跨機器「工作中」標記的載體。** 這個 repo 是制度的來源、刻意沒有 handoff
skill 也沒有知識庫（見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」），所以：

- **不要把這裡當狀態日誌或知識庫。** 鐵律「這裡不是知識庫」照舊；跨 session 的事實看 `git log`
  與各檔的 `source:` 版本標記。這一份要短，短到每輪交棒都願意維護它——會腐化的文件就是從
  「順手多寫兩段」開始的。
- **它是部署包範本 3.3 的*實例*，不是副本。** `sync_project.py` 的 `discover()` 靠 handoff skill
  認專案，掃不到這個 repo；`PARTIAL` 也只會在缺欄位時補欄位。所以它沒有同步義務，改它不必
  動 `VERSION`，也不要拿 `sync_project.py` 同步它。
- **每輪一定要維護的只有「待續分支」與「工作中」兩欄**：開工由 skill 的 A5 寫上機器與 session，
  交棒由 B6 改回「無（已交棒）」。其餘段落沒變就不用動。

## 任務目標

維護 AI 協作專案管理骨架的權威版 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。

## 已完成

- 2026-10-31（**刻意不跳版**）：查出**同機器跨工具沒有防呆**，三平台環境變數實測寫進部署包「工具身分」
  那一節（`AI_AGENT` 不是跨廠商慣例、跨工具啟動時變數會被繼承所以會說謊、Codex 的 **hook** 環境仍未量到）。
  連帶修正上一輪的錯誤斷言：**Antigravity 有 CLI**（`antigravity-ide`，本來就在 PATH），也有
  `chat --mode agent`，只是沒有 headless 列印模式。修法還沒動手，見下方第 1 項。
- 2026-10-31：**五個專案的骨架同步落地**（`VERSION` 2026-10-30.3）：`Grist_test` `d2f8bf2`、`NAA_TR`
  `5b0bc66`、`NAS_MAINT` `ad987a1`、`摘要skill設計` `bef4916`、`第三批56箱後檢查` `c87ae61`，各一個 commit
  都已 push，`check_docs.py` 全 exit 0。**`序號卡`、`解決網路速度問題` 刻意留在 `.2`**（前者已完結、後者
  有別人未提交的工作），會在下次開場自己報「骨架落後」，是自癒的。
- 2026-10-30：三平台能力重查、補跨機器「工作中」標記、**決定不裝** `pre-push-handoff.sh`（理由在部署包版本註與 [ARCHITECT.md](ARCHITECT.md)）。

## 未完成／下一步

1. 🔴 **同機器跨工具沒有防呆**（2026-10-31 查出，**設計已定、還沒動手**；洞與理由見部署包「工具身分」
   那一節）。四步修法：①「工作中」標記加工具欄（`` `機器` ／ `工具` ／ `session 名`（可選） ``）；②hook
   的同機器分支拆成「同工具→🟡／不同工具→🔴」；③A2.5 的「指向這台機器」拆成兩列，把「看側欄」換成
   不綁工具的判準；④`check_docs.py` 第 6 項檢查欄位有工具名，否則新格式會靜默退化回舊的。工具名由寫
   標記的那一棒自己填，不靠環境變數；變數只做交叉檢查，偵測不出來就退回只比機器名。
   ⚠️ 會動到 `SKILL.md`，所以要跳 `VERSION` 並**再同步一輪五個專案**。
2. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個工具都
   觸發、`statusMessage` 會不會被忽略。卡在互動式的 `/hooks` 信任（非互動只能用
   `--dangerously-bypass-hook-trust`，本輪刻意沒用）。**量 hook 環境卡在同一道信任**（本 repo 也沒有 trust 條目，`.codex/` 整層本來就被跳過）。
3. （可選，要實測）Antigravity `.agents/hooks.json`：設計已定——一支**只做管線**的 wrapper，讀 stdin 取
   `workspacePaths[0]`、`cd` 過去、跑同一支 `.sh`、stdout 包成 `injectSteps` 的 `ephemeralMessage`。
4. （可選）`SessionStart` 的 `sessionTitle` 自動寫 session 名稱（只固定得住開場那一半，狀態轉換仍靠模型）；
   `.codex/hooks.json` 接線本 repo 的 `repo-git-check.sh`（**不要**複製第二份腳本）；`AGENTS.md` 補一段
   「開工第一件事」——可攜層目前沒有一句叫 agent 先 `git fetch`、先看 origin 的「工作中」。

（「階段二 pre-push hook」2026-10-30 決定不裝，理由在 [ARCHITECT.md](ARCHITECT.md)，掃到別再重提。）

## 地雷與注意事項

- **single writer**：同一時間只有一台機器改 `main`。標記只告訴你「有東西在那台機器上」，別台未提交的變更仍然只在那台的磁碟上。
- 改制度改 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）。
- 本檔與 `.claude/hooks/repo-git-check.sh` 都不是部署包的一部分，**不要**用 `sync_project.py` 同步。
- 公開 repo：全部 Git 歷史人人看得到，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。

## 服務查證與期望快照

這個 repo 沒有 `tools/verify_state.py`——它是骨架的檔，不部署到自己身上。驗證指令是：

`python -X utf8 tools/verify_bootstrap.py`

目前：exit 0，**24 項全 `ok`**（`VERSION` 2026-10-30.3）。新增的那一項是「跨工具表保鮮期」。

## 懸置事項（AI 勿自行處理）

- 上面「未完成」第 1 項的修法**設計已定，等使用者點頭才動手**——它會跳 `VERSION` 並要再同步一輪五個專案。
- 第 2、3、4 項要不要做（都要花時間實測或設計，不是順手能完成的）。
