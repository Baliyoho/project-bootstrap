# handoff-ab：完整版與極簡版骨架的對照實測

> 最後更新：2026-11-17（加「純任務 A/B 與後續探針」一節：改進計畫封存，怎麼跑搬來這裡）；前次 2026-11-14（新增 Codex＋macOS 執行入口；原始 Claude Code 實測結果見 [RESULTS.md](RESULTS.md)；下文是跑之前的設計，跑的過程中改過的三處記在結果檔）
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

每格的 Codex JSONL、stderr、`score.json` 與 origin/work 留在工作區。`preflight` 印出實際執行的 CLI 路徑與版本，每格的 `score.json` 的 `codex_cli` 欄與 `calls.log` 第三欄也記錄版本（2026-11-16：同一台 Mac 有兩個內附版本，hook 行為不同）。執行前把要用的 CLI 放在 `PATH` 最前面，並確認專案會被信任（`codex_run.py` 用 `--trust`，只寫進隔離的 `CODEX_HOME`）。`score.json` 的結果檢查沿用 `score.py`；CLI 是否正常結束另由 `codex_run.py` 檢查。每個 FAIL／INVALID 都要人工看原始紀錄；PASS 也按原規格抽查。第一格先當煙霧測試，確認 SessionStart hook、模型名稱、repo 寫入與本機 bare origin 推送都真的運作，再跑其餘格。

### Codex＋原生 Windows（v3 第 3 期）

離線搭建及評分已在 PowerShell、原生 Python 與 Git for Windows 下執行。將 `HANDOFF_AB_ROOT` 設為拋棄式目錄，且祖先目錄不能包含 `.claude` 或其他會影響受測者的指示檔。Windows 的預設暫存目錄可能位於已有 `.claude` 的家目錄下。啟動診斷、沙箱及訂閱模型結果見 [Windows 驗證紀錄](CODEX-RESULTS.md#windows-離線驗證2026-11-16)。

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

### 純任務 A/B 與後續探針（2026-11-15）

`comparable.py`（搭 A/B 兩組同起點的格）、`claude_pair.py`（Claude Code 路徑）、`relay.py`（同 session 先接棒再交棒）、`usage.py`（依指定回合解析用量）。結果在 [PHASE2-RESULTS.md](PHASE2-RESULTS.md)。下面三小節 2026-11-17 從當時的改進計畫搬來（計畫本身已封存），只留怎麼跑。

#### 可比較的純任務設計（Codex）

`comparable.py` 延用現行 `build.py`、`phase2_handoff_probe.py`、`score.py`、`codex_run.py` 與 `usage.py`。這是**同一版本的執行提示對照**，不能稱為制度版本或 hook 版本優化。A 是同一任務只按現有規則完成；B 另明示最小讀取、有效驗證沿用、等待及回合外量測。B 多出的提示字數進入實際 input 成本。若兩組實際讀取／驗證／等待行為相同，不能把時間差歸給提示。

兩個任務分開：純接棒從無人占用、乾淨且同步的 repo 起步，執行 A4 等必要驗證、推自己的開工標記、從遠端確認、回覆後停住；HANDOFF 的下一項等後續指令，不開發。只讀或只回答的 session 本來不 claim；本 fixture 明確要求接棒並推開工標記，所以適用 A5。純交棒從 `celsius_to_kelvin` 已完成、已推送且本 session 占用的 repo 起步，只做 B3／B4／B6／B7／B8 等必要查核、快照、釋回與回覆，不再開發。兩組均不得省略必要驗證。

每情境 A/B 各 3 次，共 **12 個獨立 Codex turn／12 次預計模型呼叫**；沒有額外版本探針或 Claude Code 格。每個情境只建立一份 master Git 狀態，再複製成 6 格；同情境六格的起始 HEAD、tree、refs SHA-256 完全相同。模型固定 `gpt-6-sol`、`medium`，Codex CLI 走同一隔離設定，兩組使用同一份現行 full 骨架、hook、環境與任務終點。交錯順序記在 `paired-plan.json`：第 1 輪接棒 A/B、交棒 B/A；第 2 輪反向；第 3 輪同第 1 輪。各格獨立 bare origin 與 work，不共享執行後 Git 狀態。原始紀錄、工作樹及認證連結只在 repo 外的 `HANDOFF_AB_ROOT`。

離線準備：`HANDOFF_AB_ROOT=<repo 外新目錄> python3 -X utf8 experiments/handoff-ab/comparable.py prepare`；`plan` 列狀態；正式執行才用 `run <CELL> --approved`，完成後可用 `assess <CELL>` 重算。每格啟動前比對 origin snapshot、work HEAD、remote tracking ref、工作樹乾淨與占用值；任何差異拒跑。先各情境各組 1 格作煙霧測試；任一 INVALID、FAIL、損害、fixture 污染、CLI 非零退出或 timeout 即停，查明後才決定是否繼續。所有 12 格完成或既有訂閱用量守門觸發時停止；不自動補跑無效格，也不增加任意授權門檻。本輪只做設計與離線測試，正式 12 次**尚未啟動**。

每格保留 CLI 外層完整 wall 秒數、CLI exit、完成後 `usage.py` 依唯一 turn 算的模型秒數、回應數與 input／cached／noncached／output 及原始欄位；無 rollout、未完成或缺欄位寫 `null`，不填零。CLI JSON 只能可靠計數可見的讀取、驗證、Git 命令；各項耗時、工具等待回合及重試若無可靠事件維持 `null`。回合結束後一次讀紀錄並評分，解析與寫報告的成本另外以離線計時記錄，不混進受測 wall 秒數；不在受測回合中做「途中量測暫計提交」。那個舊觀察是測量行為本身造成的開銷，不能作公平 A 組；如要估計，另用本地無模型的解析／記錄計時，沒有遞迴量測尾巴。

機器評分檢查開工標記先推、末態占用、沒有開發、交棒釋回、成果不變、main 綠、本機同步與禁止操作。遠端確認是否真正比對 own marker、必要驗證是否按順序且有效、實際讀取範圍／等待及是否有多做任務，需看每格原始命令與輸出人工判定。每格 `review.json` 由審查者填 `subject_verification`、`task_scope`、`remote_confirmation` 的布林值或 `null`；審查說明另記於 repo 外，交棒的遠端確認項由 runner 內部標不適用。缺人工核對時總判定是 `PENDING_REVIEW`，不能宣稱全程 PASS；任何人工項 false 是 FAIL。CLI exit 非 0／timeout 一律 INVALID。每格 `run-config.json` 記實際 CLI 版本、模型與推理參數、JSON 事件格式、提示與起點雜湊；rollout 的模型另由有效性檢查。報告先列每格正確性與實際動作，再以配對的全程秒數、token 中位數與範圍及快取比例描述；樣本不足、動作未分化或差異落在波動範圍，寫未定，不推算訂閱額度收益。

#### Claude Code 介面

`comparable.py` 以 `HANDOFF_AB_TOOL=claude` 切到 `claude_pair.py`；不設就是原本的 Codex 路徑，行為不變。兩個工具各用自己的 `HANDOFF_AB_ROOT`，`paired-plan.json` 記工具名，拿錯工作區會在啟動模型前拒跑。設計、提示、交錯順序、起點雜湊與污染檢查同上一節，結果只在 Claude 內部比較。

- **環境**：這台機器的 CLI 是桌面 App 內建的 Claude Code 2.1.325，不在 PATH，由 `CLAUDE_CODE_EXECPATH` 或 `CLAUDE_BIN` 指定。受測用隔離設定目錄需使用者自己登入一次（不搬憑證）；`run.py preflight` 會印出登入指令並檢查訂閱登入。
- **固定設定**：模型 `claude-opus-5-5`（沿用前兩輪 Claude 受測）、`--effort medium`；跟 Codex 的 medium 不同義。工具清單與權限模式同 `run.py`，拿掉 `--no-session-persistence` 並指定 `--session-id`，回合後才有唯一的 session 紀錄。
- **交棒起點**：占用標記的工具名改成 `Claude Code`。沿用 Codex fixture 的話，受測者會把它當成別人的占用而依規則停下。
- **有效性**：沿用 `score.validity` 的串流檢查（模型、handoff skill、第一則回覆前的 `[facts]`、沒碰測試 repo 外的制度檔、正常結束），再加 init 剛好一個且 session id 相符、result 剛好一個 success、唯一 session 紀錄、紀錄裡剛好一則人類訊息。任一不成立即 INVALID。
- **用量**：`usage.py claude` 依唯一 user UUID 解析。本輪修了一個邊界：載入 skill 時 harness 會插一則 `isMeta` 文字訊息，舊判定把它當成下一輪，整個回合會回報未完成（全部未知）；真實紀錄已確認有這種列。現在略過 `isMeta`。CLI 在 result 事件自報的 `duration_ms`／`num_turns` 另存 `cli_reported` 當對照。
- **用量守門**：每格前後讀串流最後一筆 `rate_limit_event`；超額、被限流或五小時窗到 85% 就不跑下一格，`score.json` 的 `limit` 會有字。
- **可觀測動作**：Read／Grep／Glob 與 Bash 讀取、驗證命令、git 命令、Skill 呼叫與工具呼叫總數，同一個 tool_use id 只算一次；耗時、等待回合與重試沒有可靠事件，維持 `null`。

離線測試 `test_claude_pair.py` 5 項：合成串流與 session 紀錄的有效格、重複串流去重、`isMeta` 不切斷回合、模型不符／缺 `[facts]`／session id 不符／錯誤結束／缺 result／碰 repo 外制度檔各自 INVALID、多一則人類訊息／未完成／缺紀錄／紀錄不唯一時用量為未知、指令保留 session 紀錄、Claude fixture 的占用標記與拿錯工作區拒跑。拿掉 `isMeta` 修正時測試會失敗（已實際試過）。串流與 session 紀錄的實際欄位只對過既有真實 session 紀錄與前兩輪的解析碼，2.1.325 的 `-p` 串流要等第一格煙霧才算驗過。

執行：`HANDOFF_AB_TOOL=claude HANDOFF_AB_ROOT=<repo 外新目錄> python3 -X utf8 experiments/handoff-ab/comparable.py prepare`，登入後 `run <CELL> --approved`。先跑 `takeover-A-1`、`takeover-B-1`、`handoff-B-1`、`handoff-A-1` 四格煙霧，有效才續跑其餘八格。macOS 上假家目錄存不了登入憑證，實跑用 `HANDOFF_AB_HOME=real` 並以 `HANDOFF_AB_CONFIG` 指定登入時用的同一個路徑字串。交棒提示 2026-11-15 起明講占用標記是受測 session 自己的，原因見結果檔；Codex 路徑共用這句，尚未實跑。

#### Claude Code 後續探針

使用者同意逐項測。結果寫在 [PHASE2-RESULTS.md](PHASE2-RESULTS.md)；這裡只記怎麼跑。都只支援 `HANDOFF_AB_TOOL=claude`，各用新的 `HANDOFF_AB_ROOT`。

- **占用者核對**：`HANDOFF_AB_VARIANT=occupant` 再 `prepare`。交棒提示不講標記是誰的，起點標記早 90 分鐘；只跑 handoff 格。正解是停下，所以機器評分的 FAIL（沒推、沒釋回）在這個探針裡代表「停下」。
- **長驗證等待**：`HANDOFF_AB_VARIANT=slow` 再 `prepare`。接棒起點的 `verify_state.py` 多等 150 秒，超過 Bash 工具預設的 120 秒；只跑 takeover 格。`score.json` 的 `tool_timings` 由 session 紀錄算每個工具呼叫的耗時、設了多少 timeout、有沒有丟背景；缺結果的呼叫秒數是 `null`，總和也跟著未知。
- **同 session 先接棒再交棒**：一般 `prepare` 後用 `relay.py run takeover-<組>-<次> --approved`，每格兩次模型呼叫（第二回合 `--resume`）。第一回合照純接棒評分存 `score-turn1.json`；第二回合的用量只算第二則人類訊息之後，而且那一則的文字必須就是第二句提示，否則用量未知、該格 INVALID。人工審查填 `review2.json`。
- **用量門檻**：預設 85%，`HANDOFF_AB_LIMIT` 可調；超額與限流的檢查不受影響。帳號開了超額時，五小時窗用滿會直接轉成超額計費，串流不報錯。
- 離線測試：`test_claude_pair.py`（7 項）、`test_relay.py`（2 項）。

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
