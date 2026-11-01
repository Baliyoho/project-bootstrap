# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-01 12:42（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（量完 `statusMessage`，順手推翻同一節另一句沒人懷疑過的話）

## 這份檔案在這個 repo 的角色（跟其他專案不一樣，先讀這段）

**它只有一個任務：當跨機器「工作中」標記的載體。** 這個 repo 是制度的來源、刻意沒有 handoff
skill 也沒有知識庫（見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」），所以：

- **不要把這裡當狀態日誌或知識庫。** 跨 session 的事實看 `git log` 與各檔的 `source:` 標記。
- **它是部署包範本 3.3 的*實例*，不是副本**，`sync_project.py` 掃不到它，改它不必動 `VERSION`。
- **每輪一定要維護的只有「待續分支」與「工作中」兩欄**（A5 寫、B6 改回「無（已交棒）」）。

## 任務目標

維護 AI 協作專案管理骨架的權威版 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26110112｜補接線與開工提示｜工作中`，2026-11-01 12:52 (+08) 開工
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。
  ⚠️ **2026-11-01 這台的 `codex` 升到 `0.166.0`**（使用者授權，為繞過 TUI 開場的更新提示）。
  之前的 Codex 實測記在 `0.164.0`，部署包兩個版本號都保留著，別混成同一筆。

## 已完成

- 2026-11-01（部署包當天**第二次**修改，**刻意不跳版**：`SKILL.md` 與所有範本零改動，
  `sync_project.py` 不必跑）：**上一棒「未完成」第 2 項量完**。①**互動 TUI 會顯示
  `statusMessage`**（`0.166.0`），接在狀態行後面（`Working (1s • esc to interrupt) · <字串>`）
  ——配上「純文字 stdout 只進 agent 的 context」那條，它是互動模式下**使用者唯一看得到的那行
  字**。②**互動 TUI 開場不跑 `SessionStart`，跟著第一個 turn 才跑**；舊版 3.17 與第 5 節都寫
  「你按下同意的那個 session 不會跑，要再開一個才算」，那是推論、實測是反的，而且教人用**保證
  看不到**的方式驗收，兩處一起改掉。③**TUI 的 hook 失敗是吵的**（`• Hook failed` ＋
  `└ hook exited with code 1`），跟 `codex exec` 全程無聲相反。④留一個未解（見下第 2 項）。
  ⑤把「PATH 上的 `bash` 是 WSL 那支」從 Antigravity 那節延伸到 Codex 這一面，只加指標、
  不重寫事實。驗證：exit 0，27 項全 `ok`。

## 未完成／下一步

1. 🔴 **六個專案的 Codex 接線從來沒有真的跑過**，要各開一次互動式 `codex` 選
   `Trust all and continue`（信任綁 `hooks.json` 絕對路徑，審一個不會全通）。`Grist_test`／
   `NAA_TR`／`NAS_MAINT`／`摘要skill設計`／`第三批56箱後檢查`／`解決網路速度問題`。使用者要按的。
   ⚠️ **驗收方式這輪改了**：按完信任要**在同一個 session 裡送出一句話**才驗得到（開場不跑）；
   不要去畫面上找 `[git-check]`（那是 developer context，不顯示給人）。
2. **未解：同一支 hook 在互動 TUI 退出碼 1，六分鐘前在 `codex exec` 下卻成功。** 兩個很有說服
   力的理由都被量掉了（`bash` 解析到 WSL：同一條啟動鏈獨立跑是 exit 0；殼層偵測不同：兩次
   rollout 都寫 `<shell>powershell</shell>`，**包括成功那次**）。要重開：讓探針印出 hook 自己
   看到的 `PATH` 與 cwd 再比對。⚠️ 量它**必然要花模型呼叫**，花之前要問使用者。
3. **Codex 這一面還沒有 `bash` 解析的解法**（Antigravity 靠 3.19 的 shim 解掉了）。它至今沒在
   真實部署裡失敗過，因為第 1 項還沒跑——**先別動手**，等有真的失敗案例再決定要不要補 shim。
4. （可選）`AGENTS.md` 補「開工第一件事」；`SessionStart` 自動寫 session 名稱；本 repo 的
   `.codex/hooks.json` 接線 `repo-git-check.sh`（**不要**複製第二份腳本）。

（「階段二 pre-push hook」2026-10-30 決定不裝、「IDE `1.107.0` 為什麼沒觸發」2026-10-31 決定不追，
理由分別在 [ARCHITECT.md](ARCHITECT.md) 與部署包。掃到別再重提。）

## 地雷與注意事項

- 🔴 **會呼叫模型的步驟先問再跑。** 這套制度的前提是只用訂閱額度；`codex exec`、在 TUI 送出一句
  話、`agy -p` 都會呼叫模型。要講「花多少」之前先驗是哪一邊的帳（`codex login status`、
  `auth.json` 的 `auth_mode` 與 `OPENAI_API_KEY` 是否為空），不要用「OpenAI 額度」這種含混說法。
  2026-11-01 查證：本機是 ChatGPT 登入、`OPENAI_API_KEY` 為空，走訂閱、沒動到 API。
- 🔴 **測 hook 的探針要能分開「沒跑」與「跑了但看不到」**：讓 hook 自己寫 log ＋ 故意慢（這輪用
  `sleep 20`）。少了 log 分不出有沒有跑，少了那段延遲分不出「沒顯示」與「只閃一下」。
- 🔴 **沒有量過的因果就標成未解，不要補一個合理的理由。** 這輪連續推翻兩個聽起來很對的理由，
  早一步收手就會寫出錯的因果。
- **single writer**：同一時間只有一台機器＋一個工具改 `main`。
- 改制度改部署包，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）；只有 `SKILL.md` 真的改了才跳
  `VERSION`（鐵律 1，這輪沒跳）。公開 repo，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。
- 本檔與 `.claude/hooks/repo-git-check.sh` 不是部署包的一部分，**不要**用 `sync_project.py` 同步。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`（這個 repo 沒有 `verify_state.py`——那是骨架的檔，
不部署到自己身上）。目前：exit 0，**27 項全 `ok`**，骨架 **21 檔**，`VERSION` 仍 2026-10-31。
跨工具表保鮮期的查證日期仍是 2026-10-30：這輪**沒重讀任何官方頁面**，只在本機實測，所以
**刻意沒把時鐘歸零**——歸零會把「沒查」謊報成「查過」。

## 懸置事項（AI 勿自行處理）

- 第 1、2、3、4 項要不要做。
- （已結案）`~/.codex/config.toml` 的三個探針殘留 2026-11-01 經使用者授權清掉了：3 個
  `[projects…]` ＋ 4 個 `[hooks.state…]`，共 7 個表，備份在同目錄的 `config.toml.bak-*`。
  剩下一個空的 `[hooks.state]` 表頭是合法 TOML、無害，**也是誠實的**——六個專案的 hook
  到現在真的一個都沒被審核過（見「未完成」第 1 項）。
