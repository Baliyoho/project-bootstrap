# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-31 09:20（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（實測 Antigravity 接線不成立，移除那兩節）

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
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26103109｜修Antigravity斷言｜工作中`，2026-10-31 09:20 (+08) 開工
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。

## 已完成

- 2026-10-31（**刻意不跳版**，`SKILL.md` 一個字沒動）：**Antigravity 的 hook 接線實測不成立，已從部署包
  移除**（舊 3.18 轉接層 ＋ 舊 3.19 `.agents/hooks.json`，舊 3.20「其他 skills 慣例」遞補回 3.18）。
  同日稍早才加上它們，當天就被自己寫的驗收條件判掉——那一項本來就寫著「不是可選的驗收，是這兩個
  檔能不能留下來的條件」。**結論：Antigravity IDE `1.107.0` 不讀專案層的 `.agents/hooks.json`。**
  `verify_bootstrap.py` 移除「Antigravity 轉接層」六情境、`sync_project.py` 的 `WHOLE`／`WIRING` 各少
  一份、`ARCHITECT.md`／`AGENTS.md`／`README.md` 跟著改 → **exit 0，25 項全 ok**（18 檔）。
  完整證據與挖到的真實契約寫在部署包「跨工具與跨平台」的 Antigravity 那一節，**不要只看結論**：
  那一節同時記了「怎麼測才測得準」，前兩次測不準是因為拿「畫面上看不看得到訊息」當偵測器，
  那會把「沒跑」跟「跑了但輸出被丟掉」混在一起。第三次讓 hook 自己寫檔才分得開。
- 2026-10-31：順手修掉 `README.md` 跨工具表裡兩個過期斷言（Codex 桌面 App 寫「沒有 hooks」，
  是 2026-08-06 的實測；Antigravity 欄沒有依據）。那張表 2026-10-30 重查時只改了部署包、
  `ARCHITECT.md` 與協定檔，**README 自己那一份漏掉了**——同一個事實有第四個家。
- 2026-10-31（**跳版 `2026-10-31`**）：「工作中」標記加工具欄（`` `機器` ／ `工具` ／ `session 名` ``），
  四處一起改＋五個專案與兩份全域副本都已同步。**`序號卡`、`解決網路速度問題` 刻意沒同步**
  （前者已完結、後者仍有別人未提交的兩個檔），會在開場自己報「骨架落後」，是自癒的。
- 2026-10-30／31：三平台能力與環境變數重查、補跨機器「工作中」標記、**決定不裝**
  `pre-push-handoff.sh`。理由全在部署包的版本註與 [ARCHITECT.md](ARCHITECT.md)，這裡不複述。

## 未完成／下一步

1. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個工具都
   觸發、`statusMessage` 會不會被忽略。卡在互動式的 `/hooks` 信任（非互動只能用
   `--dangerously-bypass-hook-trust`，刻意沒用）。**量 hook 環境卡在同一道信任**（本 repo 也沒有 trust
   條目，`.codex/` 整層本來就被跳過）。這道牆沒拆掉之前，hook 端的工具偵測就只有推論、沒有測量。
2. （可選）`AGENTS.md` 補一段「開工第一件事」——可攜層目前沒有一句叫 agent 先 `git fetch`、先看
   origin 的「工作中」。**這一項的份量因為 Antigravity 那輪變重了**：那個工具現在只剩可攜層，
   沒有任何 hook 會替它開場，所以可攜層寫不寫得夠清楚，就是它唯一的防線。
3. （可選）`SessionStart` 的 `sessionTitle` 自動寫 session 名稱（只固定得住開場那一半，狀態轉換仍靠模型）；
   `.codex/hooks.json` 接線本 repo 的 `repo-git-check.sh`（**不要**複製第二份腳本）。
4. （刻意不做，掃到別再提）**Antigravity 的機器層 hook**（`~/.gemini/antigravity-ide/hooks.json`）沒測過，
   也不打算測：那是跟著機器走的路徑，不可能隨專案部署，不屬於骨架要解的問題。要重開
   「接回 Antigravity hook」這個決定，門檻是比 2026-10-31 那次探針更強的證據。

（「階段二 pre-push hook」2026-10-30 決定不裝，理由在 [ARCHITECT.md](ARCHITECT.md)，掃到別再重提。）

## 地雷與注意事項

- **single writer**：同一時間只有一台機器＋一個工具改 `main`。標記只告訴你「有東西在那台機器上」，別台未提交的變更仍然只在那台的磁碟上。
- 改制度改 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）。
- **只有 `SKILL.md` 真的改了才跳 `VERSION`**（鐵律 1）：這輪沒動它，所以沒跳。
- **文件裡的能力斷言要連同查證日期一起看**。2026-10-31 這輪又抓到一次過期（README 那張表），
  這已經是第三次同一種錯。`verify_bootstrap.py` 的「跨工具表保鮮期」只守部署包那一張，
  **README 自己那一份目前沒有守門人**。
- 本檔與 `.claude/hooks/repo-git-check.sh` 都不是部署包的一部分，**不要**用 `sync_project.py` 同步。
- 公開 repo：全部 Git 歷史人人看得到，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。

## 服務查證與期望快照

這個 repo 沒有 `tools/verify_state.py`——它是骨架的檔，不部署到自己身上。驗證指令是：

`python -X utf8 tools/verify_bootstrap.py`

目前：exit 0，**25 項全 `ok`**，骨架 18 檔（上一輪是 26 項／20 檔，差額就是移除的那兩個檔與
「Antigravity 轉接層」那一項）。`VERSION` 仍是 2026-10-31。

## 懸置事項（AI 勿自行處理）

- 第 1、2、3 項要不要做（要花時間實測或設計；第 1 項還卡在互動式信任）。
