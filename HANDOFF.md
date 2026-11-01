# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-01 12:05（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（`README.md` 的跨工具表加守門人；加的當下就抓到一處已經發生的分岔）

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

- 2026-11-01（**刻意不跳版**：`SKILL.md` 與所有範本零改動，`sync_project.py` 不必跑）：
  **`README.md` 的跨工具表有守門人了**（上一棒「未完成」的第 4 項）。`verify_bootstrap.py` 新增
  「README 跨工具表一致性」——比對同名列的**判定符號**、孤兒版本號、指回部署包的指標，附四種分岔
  的負向測試。**加的當下就抓到一處已經發生的分岔**：「自動載入程序檔」×「Codex CLI」部署包
  2026-10-30 實測後改成 ✅，README 還停在 ⬜「靠 `AGENTS.md` 指路」，一個多月沒人發現；連帶修掉
  README 兩句過期散文，並把腳本裡 `FRESHNESS_PAGES` 那份網址副本補成跟部署包一致。
  為什麼不給 README 自己一個「查證日期」：部署包「這張表的保鮮期」那一節。驗證：exit 0，27 項全 `ok`。
- 2026-10-31（部署包當天第九次修改，**刻意不跳版**，範本內容沒動所以 `sync_project.py` 零改動）：
  **Codex hook 那兩個未知實測完畢**（`0.164.0`／Windows），而其中一個**問錯了問題**——`statusMessage` 是 Codex
  正式支援的鍵（「Optional UI message」），不是 Claude 專屬；`PreToolUse` 沒 matcher 就是每次都觸發、不分工具名
  （`Bash`×2 ＋ `apply_patch`×1 全中）。**沒人問的第三件最重要：信任綁 `hooks.json` 的絕對路徑、不綁內容**
  （記在 `~/.codex/config.toml` 的 `[hooks.state.'<絕對路徑>:<事件>:<組>:<序>']`，值是 `trusted_hash`；
  逐位元組相同的接線換資料夾就不信任），而且**只有互動模式會主動問**，`codex exec` 永遠靜默跳過。
  順手修掉保鮮期清單兩個已搬家的網址（Codex 文件搬到 `learn.chatgpt.com`，skills 那頁連路徑名都換了）。
  方法論補兩條：**「叫 agent 把注入背出來」在 Codex 上不成立**（它拒絕複述，會給假陰性）；
  **佈置與測量要分兩步**——這次把建設定檔跟跑受測物寫在同一個指令裡，指令被權限層拒絕、設定檔沒生成，
  前三次「沒觸發」全部無效。

## 未完成／下一步

1. 🔴 **六個專案的 Codex 接線從來沒有真的跑過**，要各開一次互動式 `codex` 選 `Trust all and continue`
   （信任綁 `hooks.json` 絕對路徑，審一個不會全通）。`Grist_test`／`NAA_TR`／`NAS_MAINT`／`摘要skill設計`／
   `第三批56箱後檢查`／`解決網路速度問題`。這是使用者要按的，AI 代不了。
2. `statusMessage` 在**互動 TUI** 顯不顯示仍未量（`codex exec` 已確認不顯示）。測法：在探針資料夾開一次
   互動 session，看開場有沒有 `PROBE-STATUSMSG-SENTINEL`。⚠️ 探針放在那個 session 的
   暫存區，**下一棒拿不到**，要重建（兩個檔：一支把 stdin 存檔＋append 一行 log 的 `.sh`，一份掛
   `SessionStart`＋`PreToolUse` 的 `.codex/hooks.json`，然後互動式開一次過第二道閘）。
   它在 `~/.codex/config.toml` 留下的 `[projects…codex-hook-probe]` 與兩筆 `[hooks.state…]` 指向一個
   會消失的暫存路徑，**是可以清掉的垃圾**——但那是使用者的設定檔，要他自己動手或明確授權。
3. （可選）`AGENTS.md` 補一段「開工第一件事」；`SessionStart` 的 `sessionTitle` 自動寫 session 名稱；
   `.codex/hooks.json` 接線本 repo 的 `repo-git-check.sh`（**不要**複製第二份腳本）。

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

目前：exit 0，**27 項全 `ok`**，骨架 **21 檔**（上一輪是 26 項，差額就是新增的
「README 跨工具表一致性」）。`VERSION` 仍是 2026-10-31（`SKILL.md` 沒動）。
跨工具表保鮮期的查證日期仍是 2026-10-30：這一輪**沒有重讀任何官方頁面**（只把腳本裡那份網址副本
補成跟部署包一致），所以**刻意沒有把時鐘歸零**——歸零會把「沒查」謊報成「查過」。

## 懸置事項（AI 勿自行處理）

- 第 1、2、3 項要不要做。
