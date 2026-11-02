# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 17:15（+08）
- **交棒者**：Claude Code ／ `DESKTOP-M8MRS05`（修查核報告的 F04 與 F08）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。依
[project-bootstrap-audit.md](project-bootstrap-audit.md) 分批修正；16 條裡**已修 9 條**
（F01、F02、F03、F05、F09、F14、F15、F04、F08），其餘 **7 條未實作**（F06、F07、F10–F13、F16）。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26110216｜寫查核進度報告｜工作中｜交棒2次`，2026-11-02 17:25 (+08) 開工
- **骨架版本**：`2026-11-02`
- 本機能力：Windows、Python 3.13.15、Git Bash、PowerShell 7；本輪 fetch、開工標記與收尾 push 均成功。

## 已完成

- **F04（服務失敗仍回成功碼）**：舊 `verify_state.py` **每一種情況都 `return 0`**——放一個
  exit 7 的命令進去，畫面印 `boom=rc7`、結束碼仍是 0（修正前實跑確認）。改成每項只回
  PASS／FAIL／ERROR／SKIP／NOT_CONFIGURED，末尾印彙總：FAIL／ERROR→2；SKIP 獨立列出
  （缺配置不等於通過），`--strict`→3，真可選的寫進 `OPTIONAL`；`NOT_CONFIGURED` 仍回 0
  （刻意保留）。另補 HTTP 的 `expect`（200 配空錯誤頁照樣會過）與**輸出遮罩**（命令
  stdout／例外訊息不在我們控制下，而快照會被貼進 HANDOFF、對話與 issue）。
- **F08（文件檢查器保障範圍）**：①新增第 7 項「交接快照」——`HANDOFF.md` 必須存在、必要
  欄位與章節齊備、≤80 行。舊版第 6 項是「HANDOFF 有出現在輸入清單裡才驗」，整份刪掉就
  回報乾淨；而 80 行與章節是 B6 的規則，**在此之前只有骨架自己這個 repo 在驗**。
  ②連結檢查先塗白圍欄與行內程式碼，並解析 `title` 與角括號寫法（舊版把文件裡的程式碼
  範例報成死連結，而「這支腳本的 FAIL 可以無視」一旦學會，真死連結也跟著被無視）。
  ③對外名稱改成「文件與交接快照的機械檢查」，`--docs-only` 可只查文件。
- 守門人：新增第 **42** 項「verify_state 失敗訊號」（十情境全部實跑）與第 **43** 項
  「交接快照檢查」（刪檔／超行／缺章節／章節重複／欄位重複都要 exit 2，`--docs-only` 要
  真的關得掉，連結誤報 fixture 要 exit 0 而真死連結仍要 exit 2）。
  **拿 `HEAD` 舊範本實跑比對過**：舊 `verify_state` 兩個失敗情境都 exit 0、舊 `check_docs`
  超 80 行 exit 0 且誤報 fixture，新版反過來。`verify_bootstrap.py`：exit 0、**43 項全過**、無 skip。
- **副本已同步**：六個專案的 `tools/check_docs.py` 各更新一份（`序號卡` 已完結，刻意排除），
  專案設定區塊都保留。3.14／3.15 的 `source:` 標記跳到 `v2026-11-02.3`；`SKILL.md` 未動，
  `VERSION` 不跳。

## 未完成／下一步

1. 🔴 **新的第 7 項在三個專案上抓到真的缺陷**（都是制度漂移，不是檢查器壞掉；各自在那個
   專案的 session 修，本輪刻意不代改——改 `待續分支` 要知道那個專案的實況）：
   - `NAA_TR`、`NAS_MAINT`：`HANDOFF.md` **沒有「待續分支」欄位**（A2 靠它判斷主幹在哪）。
   - `解決網路速度問題`：有**兩個「## 已完成」**（累積成日誌，B6 禁止）。
   其餘三個（`Grist_test`、`摘要skill設計`、`第三批56箱後檢查`）`check_docs.py` exit 0。
2. **六個專案仍有未提交變更**，每個要在自己的 session 照 B 模式收尾（2026-11-02 使用者
   明確決定不在骨架這個 session 代做）。本輪每個專案又多一個 `tools/check_docs.py`；
   `解決網路速度問題` 另有兩個與本制度無關、使用者說過不用管的 `docs/ai-notes/` 檔，
   所以那個專案要**明確 stage**，不可 `git add -A`。⚠️ 四個在權威分支的專案不更新
   `HANDOFF.md` 會被 pre-push 防呆擋下（exit 2）。
3. **接線改過的專案，Codex 那一面要重新審核 hook**（信任綁當前雜湊，只有互動模式會問）。
   Claude Code 這一面的證據是開場那幾行 `[repo-check]`——本輪有印出來。
4. 其餘 7 條未實作。下一個優先是 **F06／F07**（把查核報告第一批「修錯誤成功訊號」收完：
   F06 是 push 防呆的漏判，F07 是有 SKIP 仍進入 ZIP 打包）。

## 地雷與注意事項

- 🔴 **`VERSION` 沒跳，所以各專案的落後偵測不會講「骨架落後」**，而這一輪真的改了 3.14
  這個同步對象——所以同步是手動做的。別以為沒有提示就是沒有落後（鐵律 1）。
- **第 7 項會讓制度漂移的專案 B4 失敗**，那是它的目的，不是誤報。但訊息要讀對：「缺章節」
  指的是 B6 模板那一節不在，「有 N 個」指的是往下疊成了日誌。
- **Python 下限仍是靜態擔保，不是實測**（這台機器只有 3.13）。別把「43 項全過」說成
  「在 3.8 上驗過」。
- 本輪踩到兩類已知坑：**測試自己壞掉而畫面上像受測物壞掉**（fixture 放錯目錄；拿「刪檔」
  驗 `--docs-only`，而刪檔本身會製造真的死連結），以及 heredoc 餵 `python -` 把 `\n`
  多解一層成真換行。**先驗儀器再測受測物**；兩條的常駐家都在 AGENTS.md。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、43 項全過、重生骨架 22 檔，無 skip。
B4：本 repo 沒有 `check_docs.py`，由上述完整驗證涵蓋。

## 懸置事項（AI 勿自行處理）

- 新增模型探針仍須先取得授權且只用訂閱額度；本輪未呼叫任何模型探針。
- Antigravity IDE hook 未觸發原因維持未知、不再追查。
