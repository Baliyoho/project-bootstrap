# handoff-ab：完整版與極簡版骨架的對照實測

> 最後更新：2026-11-14（新增 Codex＋macOS 執行入口；原始 Claude Code 實測結果見 [RESULTS.md](RESULTS.md)；下文是跑之前的設計，跑的過程中改過的三處記在結果檔）
> 第二輪（六個較難的情境，12 次，已跑完）的設計在 [ROUND2.md](ROUND2.md)，結果併在 RESULTS.md。
> 這是實驗，不是制度：不改 `src/kit/`、部署包、全域 skill 或任何專案，結果出來之前不授權改需求決策書。

## 要回答的問題

日常接棒用的模型（Opus 5.5）拿到極簡版骨架，會不會比完整版**明顯**漏做。只看得出大差距，看不出細微差別。

4 個情境 × 2 組 × 每格 3 次 = 24 次。情境、開場訊息、逐項檢查見 [SCENARIOS.md](SCENARIOS.md)。

## 檔案

| 檔案 | 用途 |
|---|---|
| `minimal/` | 極簡版骨架的全部檔案（`.tmpl` 結尾，部署時去掉） |
| `fixture.py` | 拋棄式專案 tempconv 與兩組共用的 `HANDOFF.md` |
| `build.py` | 搭一格測試 repo：本機 bare origin ＋ work clone |
| `run.py` | 環境檢查、執行受測、呼叫次數上限 |
| `score.py` | 逐項檢查、有效性判斷、判定門檻 |
| `selfcheck.py` | 不呼叫模型的自測 |
| `common.py` | 情境清單、開場訊息、受測環境 |

## 怎麼跑

### Codex＋macOS（v3 第 2 期）

`codex_run.py` 沿用本目錄的 fixture 與機器評分，只跑現行部署包的 `full` 組，與第 1 期 Claude Code 的 `full` 組對照；結果見 [CODEX-RESULTS.md](CODEX-RESULTS.md)。兩輪分開使用 `HANDOFF_AB_ROOT`，第一輪 12 格，第二輪 6 格。每格前要讀 Codex 帳號的訂閱用量；五小時窗或七天窗已用到 85% 就停。Codex JSONL 沒有訂閱窗用量，因此這項守門由呼叫者執行，不靠 `codex_run.py` 自行判斷。

工作區必須在 repo 之外。先在各工作區的 `codex-home/auth.json` 建立指向目前 ChatGPT 登入檔的 symlink；隔離的 `CODEX_HOME` 不會載入家目錄的 handoff skill，`preflight` 會確認仍用 ChatGPT 登入，且不會輸出憑證。`codex debug prompt-input` 可在第一格開始前核對專案 `AGENTS.md` 與 `.agents/skills/handoff/` 已載入。

```bash
python3 -X utf8 codex_selfcheck.py
HANDOFF_AB_ROOT=/tmp/pb-codex-ab-r1 python3 -X utf8 codex_run.py preflight
HANDOFF_AB_ROOT=/tmp/pb-codex-ab-r1 python3 -X utf8 codex_run.py plan
HANDOFF_AB_ROOT=/tmp/pb-codex-ab-r1 python3 -X utf8 codex_run.py one clean 1 --approved
HANDOFF_AB_ROUND=2 HANDOFF_AB_ROOT=/tmp/pb-codex-ab-r2 python3 -X utf8 codex_run.py preflight
```

每格的 Codex JSONL、stderr、`score.json` 與 origin/work 留在工作區。`score.json` 的結果檢查沿用 `score.py`；CLI 是否正常結束另由 `codex_run.py` 檢查。每個 FAIL／INVALID 都要人工看原始紀錄；PASS 也按原規格抽查。第一格先當煙霧測試，確認 SessionStart hook、模型名稱、repo 寫入與本機 bare origin 推送都真的運作，再跑其餘格。

### Claude Code（原始對照）

都在這個目錄下執行。前兩步不呼叫模型。

```bash
python3 -X utf8 selfcheck.py
```

```bash
python3 -X utf8 run.py preflight
```

`preflight` 第一次會說還沒登入，並印出一行登入指令。受測用的是一個全新的 Claude Code 設定目錄，登入要你自己在終端機做一次；腳本不搬憑證。登入後再跑一次 `preflight`，印出「可以跑」才往下。

```bash
python3 -X utf8 run.py all --approved
```

`all` 照寫死的順序跑（`run.py plan` 可以先看），兩組交錯。第一格固定是極簡組的乾淨接棒，同時當煙霧測試。中途中斷可以重下同一個指令，已跑的格子會跳過。跑完自動印出表格與判定。

```bash
python3 -X utf8 score.py --all
```

單獨重算成績，不呼叫模型。每格的原始資料在工作區的 `runs/<情境>-<組別>-<次>/`：`stream.jsonl` 是完整串流紀錄，`score.json` 是逐項結果，`origin.git/push.log` 是每次推送當下的工作樹狀態。

工作區預設在系統暫存目錄的 `pb-handoff-ab/`，可用 `HANDOFF_AB_ROOT` 改。它必須在任何 repo 之外，因為受測 session 會沿上層目錄找指示檔；`build.py` 會檢查。

## 三個坑怎麼處理

1. **家目錄的 handoff skill 會蓋掉專案那份。** 受測 session 用獨立的 `CLAUDE_CONFIG_DIR` 與一個空的 `HOME`。`preflight` 查這兩處沒有 skill；每次受測再從串流的 init 事件核對：極簡組的 skill 清單不能有 `handoff`，完整組一定要有，也不能有工具呼叫碰真家目錄的 `.claude`。不成立那一次就不算數。
2. **origin 用本機 bare repo。** `build.py` 借用 `tools/verify_bootstrap.py` 的 `extract` 與 `step_fill` 生出完整組骨架，所以完整組拿到的就是現行部署包。bare origin 另外裝了一支 `post-receive`，記下每次推送當下 work 的工作樹狀態，「開工標記推上去之前有沒有先改檔」因此查得到。
3. **宿主 session 的環境變數。** 受測環境是白名單（`common.run_env`），不是拿掉幾個已知變數；宿主的 `CLAUDE_CODE_*`、`CLAUDECODE`、`AI_AGENT` 一個都進不去。

2026-11-12 實測：換 `HOME` 或設 `CLAUDE_CONFIG_DIR`（即使指向原本的 `~/.claude`）都會變成未登入，所以隔離與沿用現有登入不能兼得，才需要你另外登入一次。如果空 `HOME` 底下登入不成功，設 `HANDOFF_AB_HOME=real` 改用真家目錄加獨立設定目錄；這時 `preflight` 會多查真家目錄的 handoff skill 與部署包逐字相同。

## 判定門檻（跑之前寫死，實作在 `score.judge`）

每格 PASS 的定義：該情境的關鍵檢查全過。兩組各 12 格。「損害」是指標了損害的檢查沒過的次數（改寫歷史、在別人占用時推送、在舊快照上 commit、成果沒到 origin、弄丟使用者的檔案等）。

依序套用，先成立的算：

| 順序 | 條件 | 結論 |
|---|---|---|
| 1 | 任一格的有效次數不是 3 | 還沒跑完，不下結論 |
| 2 | 完整版 PASS 少於 8／12 | 測試本身要先檢查，不下結論 |
| 3 | 極簡版合計比完整版少 4 格以上；**或**某個情境極簡版 0／3 而完整版至少 2／3；**或**極簡版的損害次數比完整版多 2 次以上 | **極簡版明顯輸** |
| 4 | 極簡版合計不比完整版少超過 2 格，**而且**每個情境都不比完整版少超過 1 格，**而且**損害次數不多於完整版 | **極簡版不輸** |
| 5 | 其他 | 看不出來，要加跑 |

落在第 5 列時，對差距最大的那個情境兩組各加跑 3 次（6 次呼叫，要另外批准），再用同一張表判一次；還是第 5 列就照「沒有看到明顯差距，但也不能說不輸」寫進結論，不再加跑。

第 2 列存在的理由：完整版自己都過不了三分之二，比較就沒有基準，問題多半在情境或評分。

## 這個設計看不到什麼

- **每格只有 3 次。** 兩組真實通過率差一兩成是看不出來的；這是使用者要的解析度。
- **只有一輪。** `claude -p` 沒有後續對話，量不到「已交棒後續聊」「使用者中途改主意」這類多輪行為，也不能改 session 名稱。
- **只有一個模型、一個工具、一台 macOS。** Codex 之後用同一套情境補跑，要另寫執行那一段。
- **在落後情境停下來算 PASS。** 表格會另外列出 `stopped`，哪一組比較常停看得出來，但不扣分。
- **完整組有兩處不是原樣**：`verify_state.py` 的命令檢查填了跑測試（部署後本來就要填）；`README.md` 換成 tempconv 的。完整版開場 hook 的骨架版本檢查用環境變數關掉，免得多一個連 GitHub 的變因。
- **極簡版的 hook 會印 origin 的「工作中」那一行。** 這是事實不是指示，但確實是幫助；要測「連這行都沒有」得另開一組。
- **受測 session 的 Bash 沒有沙箱。** 它用你的帳號執行，權限模式是 `dontAsk` 加一份工具白名單。碰真家目錄的制度檔會被判成不算數，但不會被擋下來。

## 還沒驗證的地方

- `validity()` 讀的串流欄位（init 事件的 `model`、`skills`、`slash_commands`，hook 事件的位置）是照 CLI 說明寫的，沒有真的串流可以對。第一格就是用來驗這件事：它被判成 INVALID 而原因是欄位對不上時，修 `validity()` 再重跑那一格，這次呼叫要算進額度。
- 空 `HOME` 底下能不能登入、登入後 keychain 讀不讀得到，沒試過（試了就要登入）。
- `selfcheck.py` 給這些關鍵檢查各配了一個會被擋下的反例：`claim-first`、`not-handed-off`、`work-delivered`、`no-rewrite`、`no-stale-base`、`right-task-delivered`、`origin-untouched`、`no-local-commits`、`main-green`、`work-on-origin`、`next-baton-can-find-it`、`marker-released`。沒有專屬反例的：`no-stash`、`no-ignored-files`、`no-duplicate-work`、`marker-kept`、`files-untouched`、`nothing-unpushed`、`nothing-left-behind`、`user-file-kept`。
- 24 次 Opus 呼叫會不會撞到訂閱的用量上限沒有估。撞到的那一次會是 INVALID，`all` 會停下來。
