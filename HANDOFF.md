# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-31 17:14（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（Antigravity 收尾：六個專案補完接線，只剩 2.0 要人測）

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
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26103112｜Antigravity接線｜工作中`，2026-10-31 20:12 (+08) 開工
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。

## 已完成

- 2026-10-31（部署包當天第七次修改，**刻意不跳版**，三個範本內容沒動所以 `source:` 標記不變）：
  **既有專案的 Antigravity 接線補完了**——`Grist_test`／`NAA_TR`／`NAS_MAINT`／`摘要skill設計`／
  `第三批56箱後檢查`／`解決網路速度問題` 各補 3.18／3.19／3.20 三個檔，各一個 commit 已 push；
  `序號卡`已完結所以不補。`sync_project.py` 沒有改（它刻意不做補裝，所以補裝是一次性動作，
  用 `extract()` 重生的權威版複製，腳本留在暫存區不進 repo）。**實測**：在 `Grist_test` 跑
  `agy -p`，`[git-check]` 開場原文被背出來，而且 CLI 已經是 `1.4.12`（上一輪量的是 `1.4.7`，
  換版沒壞）。順手堵掉一個陷阱：Windows 提交會讓 `ag-wrap.sh` 記成 `100644`，而 Unix handler
  是直接跑這支 `.sh`——六個專案都用 `git update-index --chmod=+x` 補成 `100755`，部署包 3.18
  補上那條紅字。
- 2026-10-31：**IDE `1.107.0` 那個未解問題決定不追**——使用者不再用這個 surface。界線見
  「未完成／下一步」末尾那段括號，判準同時寫進 [AGENTS.md](AGENTS.md) 的 Antigravity 那一條。
- 2026-10-31：**Antigravity CLI 的 hook 接線附進骨架並端到端實測過**（3.18 轉接層／3.19 Windows
  shim／3.20 只接 `SessionStart`；舊 3.18 順延成 3.21，骨架 18 檔→21 檔），同日稍早在 CLI `1.4.7`
  上量完 hook 契約。理由與約束在部署包的版本行與「跨工具與跨平台」那一節，這裡不重述。

## 未完成／下一步

1. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個
   工具都觸發、`statusMessage` 會不會被忽略。卡在互動式 `/hooks` 信任。
2. **Antigravity 2.0 仍未測**——它沒有 headless，`agy -p` 這一招用不上，要**你本人**開一次
   session 看開場有沒有 `[git-check]`。其餘三個 surface 都已收斂（CLI 實測通、IDE 決定不追）。
3. （可選）`AGENTS.md` 補一段「開工第一件事」；`SessionStart` 的 `sessionTitle` 自動寫 session 名稱；
   `.codex/hooks.json` 接線本 repo 的 `repo-git-check.sh`（**不要**複製第二份腳本）。
4. **`README.md` 的跨工具表仍然沒有守門人**（保鮮期檢查只讀部署包那一張）。

（「階段二 pre-push hook」2026-10-30 決定不裝，理由在 [ARCHITECT.md](ARCHITECT.md)，掃到別再重提。）

（「IDE `1.107.0` 為什麼沒觸發」2026-10-31 決定**不追**：使用者不再使用這個 surface，那個未解問題
沒有讀者了。**量到的事實照留**——部署包與 `README.md` 都還寫著它沒觸發、原因未解，刪掉會讓下一個
部署的人以為它能用；要收掉的是「去 IDE 重跑一次」這個下一步，不是那個結果。掃到別再重提。）

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

- 第 1、3、4 項要不要做。
- 第 2 項要你本人跑（Antigravity 2.0 沒有 headless，AI 這一端測不到）。
