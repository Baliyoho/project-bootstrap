# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-31 04:10（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（補上 Antigravity 的 hook 轉接層與接線）

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
- **工作中**：無（已交棒）
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。

## 已完成

- 2026-10-31（**刻意不跳版**，`SKILL.md` 一個字沒動）：**Antigravity 的 hook 接線補上了**，四個平面
  從此都有觸發層。新增兩節範本：3.18 `.claude/hooks/antigravity-wrap.sh`（只做管線的轉接層：取
  `workspacePaths[0]`、`cd`、跑**同一支** `git-freshness.sh`、把 stdout 包成
  `{"injectSteps":[{"ephemeralMessage":…}]}`）與 3.19 `.agents/hooks.json`（只接 `SessionStart`）；
  舊 3.18「其他 skills 慣例」順延成 3.20。轉接層裡**沒有任何判斷規則**，所以它不可能跟權威版分岔。
  失敗路徑刻意做成吵的（`[ag-wrap] ⚠️`），不安靜回空物件。`verify_bootstrap.py` 加「Antigravity
  轉接層」六情境、`sync_project.py` 的 `WHOLE`／`WIRING` 各多一份 → **exit 0，26 項全 ok**。
  **證據強度分兩層，別混在一起**：管線已測量（Windows ＋ Git for Windows 的 bash）；
  **「Antigravity 真的會觸發它、吃不吃這個設定檔形狀」還沒測量**——官方只寫了檔案位置、事件名與
  stdout 契約，沒有列設定檔欄位，而它沒有 headless 模式。
- 2026-10-31（**跳版 `2026-10-31`**）：「工作中」標記加工具欄（`` `機器` ／ `工具` ／ `session 名` ``），
  四處一起改＋五個專案與兩份全域副本都已同步。**`序號卡`、`解決網路速度問題` 刻意沒同步**
  （前者已完結、後者仍有別人未提交的兩個檔），會在開場自己報「骨架落後」，是自癒的。
- 2026-10-30／31：三平台能力與環境變數重查、補跨機器「工作中」標記、**決定不裝**
  `pre-push-handoff.sh`。理由全在部署包的版本註與 [ARCHITECT.md](ARCHITECT.md)，這裡不複述。

## 未完成／下一步

1. 🔴 **在 Antigravity 裡開一個 session 驗一次**（只有這台機器的人做得到，IDE 1.107.0 已安裝）：
   對話開頭要看到 `[git-check]`。**看不到就把 `.agents/hooks.json` 與 `.claude/hooks/antigravity-wrap.sh`
   從部署包刪掉**，順便把實測結果寫進部署包那一節——一個不會觸發的 hook 比沒有更糟，它看起來像
   有防護。驗之前這兩個檔只到「管線測過了」。
   不用開 IDE 也能先驗管線（第 5 節那一項）：
   `printf '{"workspacePaths":["<本專案絕對路徑>"]}' | bash .claude/hooks/antigravity-wrap.sh .claude/hooks/git-freshness.sh`
2. **既有專案要啟用 Antigravity 接線＝手動補兩個檔**。`sync_project.py` 刻意不做「補裝」，所以
   2026-10-31 的 `--all` 預演對五個已同步專案全是 `ok`、新檔全是 `skip`（確認過）。沒驗過的接線不該
   自動長出來，所以這是每個專案各自的決定，不是同步的事。
3. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個工具都
   觸發、`statusMessage` 會不會被忽略。卡在互動式的 `/hooks` 信任（非互動只能用
   `--dangerously-bypass-hook-trust`，刻意沒用）。**量 hook 環境卡在同一道信任**（本 repo 也沒有 trust
   條目，`.codex/` 整層本來就被跳過）。這道牆沒拆掉之前，hook 端的工具偵測就只有推論、沒有測量。
4. （可選）`SessionStart` 的 `sessionTitle` 自動寫 session 名稱（只固定得住開場那一半，狀態轉換仍靠模型）；
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

目前：exit 0，**26 項全 `ok`**（`VERSION` 仍是 2026-10-31——`SKILL.md` 沒動就不跳版，鐵律 1）。新增的那一項是「Antigravity 轉接層」。

## 懸置事項（AI 勿自行處理）

- 第 1 項（在 Antigravity 裡驗）要不要現在做——那一步只有坐在這台機器前面的人能做。
- 第 3、4 項要不要做（要花時間實測或設計；第 3 項還卡在互動式信任）。
