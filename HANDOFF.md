# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-01 13:10（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（做完上一棒第 4 項那三件小事，順手補兩個守門人）

## 這份檔案在這個 repo 的角色（跟其他專案不一樣，先讀這段）

**它只有一個任務：當跨機器「工作中」標記的載體。** 這個 repo 是制度的來源，刻意沒有 handoff
skill 也沒有知識庫（見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」）。所以：
**不要把這裡當狀態日誌或知識庫**（跨 session 的事實看 `git log` 與各檔的 `source:` 標記）；
**它是範本 3.3 的*實例*、不是副本**，改它不必動 `VERSION`；**每輪只維護「待續分支」與
「工作中」兩欄**（A5 寫、B6 改回「無（已交棒）」）。

## 任務目標

維護 AI 協作專案管理骨架的權威版 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。
  ⚠️ **2026-11-01 這台的 `codex` 升到 `0.166.0`**（使用者授權，為繞過 TUI 開場的更新提示）。
  之前的 Codex 實測記在 `0.164.0`，部署包兩個版本號都保留著，別混成同一筆。

## 已完成

- 2026-11-01（部署包當天**第三次**修改，**刻意不跳版**：`SKILL.md` 一個字沒動、`VERSION` 仍
  `2026-10-31`；但**動到範本 3.10**，所以 `git-freshness.sh` 的 `source:` 標記跳到
  `v2026-11-01`，不加序號——當天前兩次只改敘述）：**上一棒第 4 項那三件小事全做完**（完整
  理由在部署包開頭那一條，這裡不重複）：①3.10 與本 repo 那支 `repo-git-check.sh` 各多印一行
  **開工改名提示**（`㊣　$(date +%y%m%d%H)｜<主題>｜工作中`）——**只印、不改名**；②本 repo 補
  `.codex/hooks.json`，掛自己那支 hook（**不是 3.17 的副本**）；③`AGENTS.md` 補「開工第一件
  事」；④兩個守門人：`sync_project.py` **拒絕把本 repo 當目標**、`verify_bootstrap.py` 27→**29
  項**。驗證：exit 0、29 項全 `ok`；三項新檢查各做過**負向測試**，測完已復原。

## 未完成／下一步

1. 🔴 **6 個專案要跑 `python -X utf8 tools/sync_project.py <路徑> --write`**（只差
   `git-freshness.sh` 一個檔）：`Grist_test`／`NAA_TR`／`NAS_MAINT`／`摘要skill設計`／
   `第三批56箱後檢查`／`解決網路速度問題`。⚠️ **落後偵測不會替你講**——3.10 改了而 `VERSION`
   沒跳（跳版會讓每個專案永遠印「骨架落後」且同步修不掉，鐵律 1），所以這是**有意識選的
   代價**，形狀跟 2026-09-13 那次「matcher 補了沒發下去」一樣。`--all` 另外掃到 `序號卡`
   （已完結，**不要碰**，它差 5 個檔是正常的）。同步只改檔案不 commit，各專案自己走 B 收尾。
2. 🔴 **Codex 接線從來沒真的跑過，現在是 7 個地方**：上面六個專案 ＋ **本 repo 自己**（這輪新
   加的 `.codex/hooks.json`）。各開一次互動式 `codex` 選 `Trust all and continue`（信任綁
   `hooks.json` 絕對路徑，審一個不會全通）。使用者要按的。⚠️ 按完要**在同一個 session 裡送出
   一句話**才驗得到（互動 TUI 開場不跑 `SessionStart`）；不要去畫面上找 `[git-check]`（那是
   developer context，不顯示給人）。
3. **未解：同一支 hook 在互動 TUI 退出碼 1，六分鐘前在 `codex exec` 下卻成功。** 兩個很有說服
   力的理由都被量掉了（`bash` 解析到 WSL：同一條啟動鏈獨立跑是 exit 0；殼層偵測不同：兩次
   rollout 都寫 `<shell>powershell</shell>`，**包括成功那次**）。要重開：讓探針印出 hook 自己
   看到的 `PATH` 與 cwd 再比對。⚠️ 量它**必然要花模型呼叫**，花之前要問使用者。
4. **Codex 這一面還沒有 `bash` 解析的解法**（Antigravity 靠 3.19 的 shim 解掉了）。它至今沒在
   真實部署裡失敗過，因為第 2 項還沒跑——**先別動手**，等有真的失敗案例再決定要不要補 shim。
5. （已結案，別掃回來）`SessionStart` **自動改** session 名稱做不到——改名的能力在 agent 手上，
   hook 只能把時間戳算好印出來，而那這輪已經做了。

（「階段二 pre-push hook」2026-10-30 決定不裝、「IDE `1.107.0` 為什麼沒觸發」2026-10-31 決定不追，
理由分別在 [ARCHITECT.md](ARCHITECT.md) 與部署包。掃到別再重提。）

## 地雷與注意事項

- 🔴 **會呼叫模型的步驟先問再跑。** 前提是只用訂閱額度；`codex exec`、在 TUI 送出一句話、
  `agy -p` 都會呼叫模型。講「花多少」之前先驗是哪一邊的帳（`codex login status`、`auth.json`
  的 `auth_mode` 與 `OPENAI_API_KEY` 是否為空）。2026-11-01 查證：ChatGPT 登入、走訂閱。
- 🔴 **改了會同步的檔（兩支 `.sh`、`check_docs.py`、三份接線）就要自己跑 `sync_project.py`。**
  落後偵測只認 `SKILL.md` 的 `source:` 標記，其餘的檔改了完全沒有信號——已知的洞，不是漏。
- 🔴 **新增檢查要附負向測試**：永遠回 `ok` 的檢查跟沒有這項在畫面上一模一樣。
- 🔴 **沒有量過的因果就標成未解，不要補一個合理的理由。**
- **single writer**：同一時間只有一台機器＋一個工具改 `main`。鐵律見 [AGENTS.md](AGENTS.md)。
- 本檔、`repo-git-check.sh` 與兩份接線都不是部署包的一部分，**不要**同步（腳本現在會拒絕）。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`（這個 repo 沒有 `verify_state.py`——那是骨架的檔，
不部署到自己身上）。目前：exit 0，**29 項全 `ok`**，骨架 **21 檔**，`VERSION` 仍 2026-10-31。
跨工具表保鮮期的查證日期仍是 2026-10-30：這輪**沒重讀任何官方頁面**，只在本機實測，所以
**刻意沒把時鐘歸零**——歸零會把「沒查」謊報成「查過」。

## 懸置事項（AI 勿自行處理）

- 第 1、2、3、4 項要不要做（第 1 項會寫進另外六個專案的資料夾，第 2 項要使用者親手按，
  第 3 項會花模型呼叫）。
