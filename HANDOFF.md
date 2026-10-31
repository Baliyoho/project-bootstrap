# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-31 10:05（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（在 Antigravity CLI `1.4.7` 實測 hook，結論反轉）

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

- 2026-10-31（**刻意不跳版**，`SKILL.md` 沒動）：**在 Antigravity CLI `1.4.7` 上把 hook 實測完，結論反轉。**
  `agy` 有 `--print` headless（IDE 沒有——那就是前兩次測不準的根因），所以這次量得到：
  **專案層 `.agents/hooks.json` 會被讀，`SessionStart`／`PreInvocation`／`PreToolUse`／`PostToolUse`／
  `PostInvocation`／`Stop` 六個事件全部觸發**；cwd 是 `hooks.json` 所在目錄（`.agents/`），與官方契約
  一致；`PreInvocation` 在 CLI 沒失效。三個意外見「地雷」。四處敘述同步改掉
  （`AGENTS.md`／`README.md`／`ARCHITECT.md`／部署包的 Antigravity 整節＋跨工具表＋CLI 表＋第 5 節
  驗收項＋`handover-protocol.md` 範本那句）→ **`verify_bootstrap.py` exit 0，25 項全 ok（18 檔）**。
- 2026-10-31 稍早（同日）：先把前一輪探針的結論縮回它實際覆蓋的範圍（Antigravity 是四個 surface，
  探針只覆蓋 IDE），並修掉「hook 是機器層設定」這個過度一般化——`applicationName` 跟著 surface 走。
- **決定沒變（骨架仍不附接線），但理由第二次換了**：從「這個入口不存在」→「探針只覆蓋 IDE」→
  現在是「**Windows 上缺一層 `.cmd` shim**」。

## 未完成／下一步

1. **接 Antigravity CLI 的 hook：寫那層 `.cmd` shim。** 實測已經證明接得上，缺的是 Windows 的管線。
   死結是：`cmd /c` 跑不了 `.sh`；PATH 上的 `bash` 是 WSL 的（本機還是壞的）；Git Bash 在
   `C:\Program Files\Git\bin\bash.exe`，**路徑含空白而 `command` 不吃空白也不吃引號**，寫不出來。
   出路：`.agents/` 放一支相對、不含空白的 `.cmd`（例如 `.\ag-hook.cmd`），由它自己找 Git Bash 並跑
   `..\.claude\hooks\<script>.sh`，同時把 stdout 包成各事件要的形狀。
   🔴 **動手前先解決三件事**（部署包那一節有完整敘述）：①shim 怎麼跨機器找到 Git Bash（寫死絕對
   路徑換機器就靜默失效，跨平台防呆會擋）；②macOS／Linux 走 `sh -c` 不需要 shim，接線會變成兩種
   形狀；③**第一版只接 `SessionStart`**——`PreToolUse` 接上後，shim 任何失敗都等於擋掉使用者全部
   的工具呼叫。
2. **IDE `1.107.0` 為什麼沒觸發，仍然沒有解釋**（CLI 能跑的同一種形狀、同樣的相對路徑，IDE 就是
   沒動）。刻意留成未解問題，**不要替它編理由**。要查就在 IDE 上重跑那份已在 CLI 上成立的設定。
   Antigravity 2.0 也還沒測（沒有 headless，要人開 session 看）。
3. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個工具
   都觸發、`statusMessage` 會不會被忽略。卡在互動式 `/hooks` 信任。
4. （可選）`AGENTS.md` 補一段「開工第一件事」；`SessionStart` 的 `sessionTitle` 自動寫 session 名稱；
   `.codex/hooks.json` 接線本 repo 的 `repo-git-check.sh`（**不要**複製第二份腳本）。
5. **`README.md` 的跨工具表仍然沒有守門人**（保鮮期檢查只讀部署包那一張）。

（「階段二 pre-push hook」2026-10-30 決定不裝，理由在 [ARCHITECT.md](ARCHITECT.md)，掃到別再重提。）

## 地雷與注意事項

- 🔴 **`PreToolUse` 不明確回 `{"allow_tool": true}` 就等於拒絕。** 實測回 `{}` 的那一輪，agy 把
  `read_file` 與 `run_command` 全擋掉並回報 `tool calls were blocked by a pre-tool hook`。
  **這比「hook 不跑」危險得多**：不跑只是沒有防護，擋掉是讓使用者的工具不能用。
- 🔴 **`command` 照空白切 token、不解析引號。** 絕對路徑實測四種組合，只有「不含空白＋不加引號」
  跑得起來。**所以相對路徑才是可靠的那一邊**——鐵律 5 跟 Antigravity **沒有**衝突。
- 🔴 **上一輪那個推論被推翻了，記住這個形狀**：當時推論「探針的 `command` 必然是相對的，而指南說
  要絕對，所以骨架自己的不變量害探針測不出東西」——聽起來很有說服力，實測是反的。
  **沒有量過的因果就標成未解，不要補一個合理的理由**（鐵律 3）。
- 🔴 **寫外部工具能力時先確認講的是哪一個 surface。** 同名不同產品（Antigravity vs Antigravity IDE）
  在斷言裡沒被區分，一次探針失敗就被記成一整層能力不存在。
- **測 hook 要讓它自己寫檔，不要看畫面。** 「看不到訊息」把「沒跑」與「跑了但輸出被丟掉」混在一起，
  前兩次就是這樣測不準的。有 headless 模式（`agy -p`）就用它。
- **single writer**：同一時間只有一台機器＋一個工具改 `main`。
- 改制度改 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）。
- **只有 `SKILL.md` 真的改了才跳 `VERSION`**（鐵律 1）：這輪沒動它，所以沒跳。
- 公開 repo：全部 Git 歷史人人看得到，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。
- 本檔與 `.claude/hooks/repo-git-check.sh` 都不是部署包的一部分，**不要**用 `sync_project.py` 同步。

## 服務查證與期望快照

這個 repo 沒有 `tools/verify_state.py`——它是骨架的檔，不部署到自己身上。驗證指令是：

`python -X utf8 tools/verify_bootstrap.py`

目前：exit 0，**25 項全 `ok`**，骨架 18 檔（這兩輪都只改敘述，沒有增刪範本）。`VERSION` 仍是
2026-10-31。跨工具表保鮮期的查證日期仍是 2026-10-30——這兩輪沒有重讀那六頁官方文件，只查了
Antigravity 的 surface 區分與 hook 契約，所以**刻意沒有把時鐘歸零**。

## 懸置事項（AI 勿自行處理）

- 第 1 項要不要做（要寫跨平台的 shim，而且會讓接線變成兩種形狀）。
- 第 2 項要不要追（IDE 那個未解問題；2.0 要人開 session 才測得到）。
- 第 3、4、5 項要不要做。
