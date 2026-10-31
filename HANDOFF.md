# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-31 13:10（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（Antigravity CLI 的 hook 接線已附上並端到端實測）

## 這份檔案在這個 repo 的角色（跟其他專案不一樣，先讀這段）

**它只有一個任務：當跨機器「工作中」標記的載體。** 這個 repo 是制度的來源、刻意沒有 handoff
skill 也沒有知識庫（見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」），所以：

- **不要把這裡當狀態日誌或知識庫。** 鐵律「這裡不是知識庫」照舊；跨 session 的事實看 `git log`
  與各檔的 `source:` 版本標記。這一份要短，短到每輪交棒都願意維護它。
- **它是部署包範本 3.3 的*實例*，不是副本。** `sync_project.py` 的 `discover()` 靠 handoff skill
  認專案，掃不到這個 repo。所以它沒有同步義務，改它不必動 `VERSION`。
- **每輪一定要維護的只有「待續分支」與「工作中」兩欄**：開工由 skill 的 A5 寫，交棒由 B6 改回
  「無（已交棒）」。其餘段落沒變就不用動。

## 任務目標

維護 AI 協作專案管理骨架的權威版 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。

## 已完成

- 2026-10-31（**刻意不跳版**，`SKILL.md` 沒動；新增三檔的 `source:` 標記是 `v2026-10-31.2`）：
  **Antigravity CLI 的 hook 接線已附上，而且是端到端實測過的。** 新增三節範本：3.18
  `.claude/hooks/ag-wrap.sh`（轉接層，只做管線）、3.19 `.agents/ag-hook.cmd`（Windows shim，
  自己找 Git Bash）、3.20 `.agents/hooks.json`（只接 `SessionStart`）；舊 3.18「其他 skills 慣例」
  順延成 3.21。**骨架從 18 檔變 21 檔。**
  驗收方式不是看畫面，而是**讓 agent 自己把開場訊息背出來**：在重生出來的骨架上跑 `agy -p`，
  `[git-check]` 那一句原文被引用出來了（先用手寫版測通，再用 `extract()` 重生的**權威版**重跑一次）。
  `verify_bootstrap.py` 加「Antigravity 接線」情境、`sync_project.py` 的 `WHOLE` 多兩份並新增
  `AG_WIRING` → **exit 0，26 項全 ok**。
- 同日稍早：在 CLI `1.4.7` 上量完 hook 契約（六個事件全觸發、cwd 是 `.agents/`、相對路徑可用而
  絕對路徑才脆弱、`PreToolUse` 不明確允許就等於拒絕），並把前兩輪那些過度一般化的斷言縮回範圍。
- **`sync_project.py` 不會把這三個新檔「補裝」到既有專案**——`WHOLE` 碰到專案沒有的檔就 skip，
  那是刻意的設計。既有專案要接 Antigravity 就自己從部署包 3.18–3.20 補三個檔。

## 未完成／下一步

1. **IDE `1.107.0` 為什麼沒觸發，仍然沒有解釋。** CLI 能跑的同一種形狀、同樣的相對路徑，在 IDE
   上就是沒動。**不要替它編理由**（鐵律 3）。現在門檻比上一輪低很多：把骨架 3.18–3.20 這份
   **已經在 CLI 上端到端成立**的接線放進 IDE 的工作區再開一次 session 就知道了。
   Antigravity 2.0 也還沒測（沒有 headless，要人開 session 看）。
2. **五個既有專案要不要補 Antigravity 接線**（見上，`sync` 刻意不補裝）。
3. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個
   工具都觸發、`statusMessage` 會不會被忽略。卡在互動式 `/hooks` 信任。
4. （可選）`AGENTS.md` 補一段「開工第一件事」；`SessionStart` 的 `sessionTitle` 自動寫 session 名稱；
   `.codex/hooks.json` 接線本 repo 的 `repo-git-check.sh`（**不要**複製第二份腳本）。
5. **`README.md` 的跨工具表仍然沒有守門人**（保鮮期檢查只讀部署包那一張）。

（「階段二 pre-push hook」2026-10-30 決定不裝，理由在 [ARCHITECT.md](ARCHITECT.md)，掃到別再重提。）

## 地雷與注意事項

- 🔴 **`.agents/ag-hook.cmd` 有兩個不能「順手整理」掉的約束**，兩個都是踩到才知道的：
  **①全檔 ASCII**——中文 `rem` 註解被 OEM code page 誤讀後會**整段被當成指令執行**，stderr 噴
  `is not recognized`，而 stdout 的 JSON 看起來還是對的，所以不會有徵兆。**②不能有多行括號
  區塊或 label**——檔案是 LF 行末（`.gitattributes` 強制），`cmd.exe` 讀 LF-only 檔案時這兩種
  結構會出錯。`verify_bootstrap.py` 的「Antigravity 接線」兩項都擋。
- 🔴 **`PreToolUse` 不明確回 `{"allow_tool": true}` 就等於拒絕**（實測回 `{}` 時 `read_file` 與
  `run_command` 全被擋）。所以骨架**只接 `SessionStart`**；要接 `PreToolUse` 之前先想清楚失敗
  路徑怎麼保證回 allow——那比「hook 不跑」糟得多。
- 🔴 **`agy` 的 `command` 照空白切 token、不解析引號。** 所以相對路徑才是可靠的那一邊，鐵律 5
  跟 Antigravity **沒有**衝突；Windows 上它甚至是唯一寫得出來的形式。
- 🔴 **沒有量過的因果就標成未解，不要補一個合理的理由。** 2026-10-31 的推論「骨架自己的不變量
  害探針測不出東西」聽起來很有說服力，實測是反的。
- **測 hook 要讓它自己寫檔或讓 agent 把注入背出來，不要看畫面。** 「看不到訊息」把「沒跑」與
  「跑了但輸出被丟掉」混在一起，前兩次就是這樣測不準的。
- **寫外部工具能力時先確認講的是哪一個 surface**（Antigravity vs Antigravity IDE 是不同產品）。
- **single writer**：同一時間只有一台機器＋一個工具改 `main`。
- 改制度改 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）。
- **只有 `SKILL.md` 真的改了才跳 `VERSION`**（鐵律 1）：這輪沒動它，所以沒跳。
- 公開 repo：全部 Git 歷史人人看得到，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。
- 本檔與 `.claude/hooks/repo-git-check.sh` 都不是部署包的一部分，**不要**用 `sync_project.py` 同步。

## 服務查證與期望快照

這個 repo 沒有 `tools/verify_state.py`——它是骨架的檔，不部署到自己身上。驗證指令是：

`python -X utf8 tools/verify_bootstrap.py`

目前：exit 0，**26 項全 `ok`**，骨架 **21 檔**（上一輪是 25 項／18 檔，差額就是新增的三個範本與
「Antigravity 接線」那一項）。`VERSION` 仍是 2026-10-31。跨工具表保鮮期的查證日期仍是
2026-10-30——這幾輪沒有重讀那六頁官方文件，所以**刻意沒有把時鐘歸零**。

## 懸置事項（AI 勿自行處理）

- 第 1 項要不要追（IDE 那個未解問題；2.0 要人開 session 才測得到）。
- 第 2 項要不要做（既有專案補裝 Antigravity 接線）。
- 第 3、4、5 項要不要做。
