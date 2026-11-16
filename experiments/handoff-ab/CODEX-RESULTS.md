# Codex＋macOS 制度驗收（2026-11-14）

> 最後更新：2026-11-14。這是 v3 第 2 期的 Codex 實測；第 1 期 Claude Code 基準見 [RESULTS.md](RESULTS.md)。原始 JSONL、Git origin、工作樹與逐項分數在系統暫存目錄，沒有提交進公開 repo。

## 條件

- Codex CLI `0.169.0-alpha.11.1`、`gpt-6-sol`，macOS，ChatGPT 訂閱登入。每格前讀帳號用量；五小時窗接近上限時先等重置，再開始模型呼叫。測後五小時窗已用 55%，訂閱點數餘額為 0，沒有使用額外點數。
- 只跑 v3 現行部署包 `full` 組，對照第 1 期 Claude Code `full` 組的結果，不重新跑極簡組。每格用獨立的本機 bare origin 與 work clone；Codex 設定目錄隔離，僅沿用 ChatGPT 登入，不載入家目錄 handoff skill。
- `codex debug prompt-input` 先驗專案 `AGENTS.md` 與 `.agents/skills/handoff/` 的載入。執行時允許 Git 寫入拋棄式 fixture；第一次煙霧測試用 `workspace-write`，Git 的 `.git/FETCH_HEAD` 被沙箱拒絕，Codex 正確停下。這是測試環境限制，該次不計入 18 格；改為 `danger-full-access` 後另建乾淨 fixture 重跑。
- 結果沿用 `score.py` 的機器檢查。另驗 18 份 Codex rollout：模型皆為 `gpt-6-sol`、模型輸入皆有 SessionStart `[facts]`、專案 skill 皆載入，沒有缺失。`codex_selfcheck.py` 的六項正負向探針通過。

## 第一輪：四個情境各三次

| 情境 | Codex v3 完整組 | Claude Code v3 完整組 |
|---|---:|---:|
| `clean` 乾淨接棒 | 3／3 | 3／3 |
| `behind` 遠端已前進 | 3／3 | 3／3 |
| `busy` 別人占用 | 3／3 | 3／3 |
| `midway` 半成品交棒 | 3／3 | 3／3 |
| **合計** | **12／12** | **12／12** |
| 損害格 | 0 | 0 |

人工抽查 `midway`：main 的測試通過；半成品已在 origin 分支，`HANDOFF.md` 指明分支並釋回「工作中」；本機已追蹤檔沒有未提交修改。`clean` 的 origin 推送紀錄顯示先推只有 `HANDOFF.md` 的開工標記，再推程式成果。

## 第二輪：六個較難情境各一次

| 情境 | Codex v3 完整組 | Claude Code v3 完整組 |
|---|---:|---:|
| `branch` 待續分支不是 main | PASS | PASS |
| `ahead` 來源不明的本機 commit | PASS（停下） | PASS（停下） |
| `casual` 沒說接棒的小修改 | PASS | PASS |
| `race` 開工標記推送時被搶先 | PASS（停下） | PASS（停下） |
| `secret` 交棒時有金鑰樣式檔案 | PASS | PASS |
| `drift` 文件綠燈、測試紅燈 | PASS | PASS |
| **合計** | **6／6** | **6／6** |
| 損害格 | 0 | 0 |

每格的最後回覆與 origin 狀態都人工看過：`ahead` 沒有推送或移走來源不明的 commit；`race` 保留對方的 origin 標記，沒有續改程式；`secret` 的樣式字串沒有進入 origin 歷史，原檔保留；`drift` 先修紅燈，再交付第 1 項。

## F50 多輪互動（Codex CLI）

同一個 Codex CLI 聊天在乾淨 fixture 依 [F50.md](F50.md) 的五則訊息往返。第 1 步先推開工標記、交付第 1 項並保留標記；第 2 步交棒、釋回標記且本機對齊；第 3 步只讀追問，origin 沒有新 commit；第 4 步先問 main 或分支，停下等待並有 `session：` 行；第 5 步重推開工標記，完成工作後交棒，`session：` 行的次數累加到 2。要求回報的第 1、2、4、5 步都有 `session：` 行。

CLI 受測聊天沒有改名工具，四次都依共用制度寫 `session：不適用：此工具無法改名；交棒<N>次`。因此這一輪**不能判定桌面 App 的標題、狀態符號及時間戳是否符合 F50**；桌面 App 的改名能力須在獨立測試聊天另驗。

## sol 中 在codex的接棒花費

2026-11-14，使用者提供本 repo 這次 Codex 桌面 App 接棒聊天的本機用量紀錄。這是單次實際接棒的用量觀測，並非上述 handoff-ab 測試格或 F50 桌面 App 標題驗收結果；數字依使用者提供，未另行重讀本機用量來源。

| 項目 | 用量 |
|---|---:|
| 累計輸入 | 1,119,828 tokens |
| 其中快取輸入 | 1,084,928 tokens |
| 非快取輸入 | 34,900 tokens |
| 輸出 | 2,682 tokens |
| 上下文窗口上限 | 258,400 tokens |
| 單次最高輸入 | 45,021 tokens，約占窗口 17% |

## 桌面 App 接棒成本複驗與優化（2026-11-14）

v2026-11-14.3 的真實接棒（本輪第一則「接棒」）：讀本機 rollout 的首個 turn，依 `token_usage_record` 計 11 筆模型回應；最後一筆 `turn_token_usage` 是 349,246 input、304,000 cached input、45,246 非快取 input、1,028 output。`task_started` 到 `task_complete` 是 147.103 秒。只取這個 turn，不把後續優化開發算進接棒。

相較上一節的 28 次／1,119,828 input，模型呼叫少 60.7%、累計輸入少 68.8%；但非快取輸入從 34,900 增到 45,246，不能據此宣稱訂閱額度或實際計費下降同樣比例。這是兩次觀測，不是控制變因的 A/B。v3.3 仍有兩次外層 `functions.exec` 在 30 秒先返回，雖然內層 `write_stdin` 已等 60 秒；兩輪驗證仍完整執行。

本輪 v2026-11-14.4 改動：

- 來源驗證器將獨立的 `verify_v2.py` 子程序與其他 fixture 檢查重疊；不減測試、不快取，最後仍檢查結束碼與報告。新增四個測試覆蓋大量輸出、非零／無效報告、異常清理、quiet 下 FAIL／SKIP。
- `--quiet` 隱藏成功明細，保留摘要、失敗／未驗證細節與原結束碼。正常接棒與提交前 staged 驗證都保留。
- skill 參考補上 Codex 外層 60000 ms、內層兩段最多 30000 ms 的用法；成功摘要、既有規則不重讀、相依步驟遇錯即停。共用入口未加長。

同一台 Mac、同一份修改後來源，均無 profiler 的一次串行／重疊對照：

| 執行方式 | 秒數 | 結果 |
|---|---:|---|
| 串行（將 `run_checks` 暫時接到 `_run_checks`，collector 在最後呼叫 `verify_v2.py`） | 52.72 | 66 項，exit 0 |
| 預設重疊，`python3 -X utf8 tools/verify_bootstrap.py --quiet` | 34.28 | 66 項，exit 0 |

單次驗證少 18.44 秒（35.0%），是腳本耗時，不是完整接棒／交棒耗時。在本輪工具呼叫已觀察到外層設定後可一次等完整輪驗證，無中間空等的模型回合。原始 rollout、profiler 與執行日誌留在本機，未提交公開 repo；profiling 的 55.0 秒只用來定位瓶頸，不作上述對照基準。

尚待驗證的是新版完整交棒的模型用量、多次時間分布和 Windows。這輪優化未額外呼叫模型。其餘已部署專案的同步另需授權。

### v2026-11-14.4 實際接棒用量

2026-11-14 從同一個實際接棒聊天的本機 rollout 讀取首輪。模型回應數取同一 turn 的 `token_usage_record` 筆數，累計值取最後一筆 `turn_token_usage`，完整耗時從 `task_started` 算到 `task_complete`。

| 觀測 | 模型回應 | 累計輸入 | 快取輸入 | 非快取輸入 | 輸出 | 秒數 |
|---|---:|---:|---:|---:|---:|---:|
| 更早基準（使用者提供） | 28 | 1,119,828 | 1,084,928 | 34,900 | 2,682 | 未記錄 |
| .3 完整接棒 | 11 | 349,246 | 304,000 | 45,246 | 1,028 | 147.103 |
| .4 開工推送後的量測截點 | 10 | 357,619 | 315,648 | 41,971 | 1,956 | 119.285 |
| .4 完整接棒 turn | 12 | 444,536 | 398,336 | 46,200 | 3,368 | 194.283 |
| .4 截點後增量 | 2 | 86,917 | 82,688 | 4,229 | 1,412 | 74.998 |

.4 完整 turn 比 .3 多 47.180 秒（32.1%）、95,290 累計輸入 tokens（27.3%）、954 非快取輸入 tokens（2.1%）。相較更早基準，.4 少 675,292 累計輸入 tokens（60.3%），非快取輸入多 11,300 tokens（32.4%）。

22:04:07（+08）的量測截點已涵蓋開工推送及遠端核對，也包含前兩次讀取量測資料與觸發該次讀取的模型回應。截點後增量涵蓋寫入暫計、提交前驗證、推送與最終回覆。接棒驗證的外層工具呼叫提早交回，之後兩次 `functions.wait` 分別回傳仍在執行及驗證結果。開場版本提示也觸發額外查核，本機快取是 `2026-11-14`，Git 的 `origin/main:VERSION` 是 `2026-11-14.4`。

單次驗證器的串行／重疊對照快了 18.44 秒（35.0%）。完整 turn 的比較是兩次實際觀測，.4 還包含量測與記錄工作，無法從兩筆全程數字單獨估出程序調整的效果。訂閱額度消耗未量測。

## 判定範圍

依 v3 第 6 節的 handoff-ab 退出條件，Codex 在兩輪十個情境的關鍵檢查不比第 1 期 Claude Code 完整組差，且沒有損害格。這是單輪情境、同一台 macOS、單一模型的結果；多輪 Git 行為另由上述 CLI F50 步驟覆蓋，桌面 App 標題項尚未判定。

## Windows 離線驗證（2026-11-16）

原生環境使用 Codex CLI `0.166.0`、PowerShell `7.6.9`、Git for Windows `2.56.0.windows.3`、Python `3.13.15`，部署包 `2026-11-15.2` 含 `v2026-11-15.3` 的開場 hook 修正。CLI 由本機模擬服務提供回應，未使用訂閱配額。

- 修正後原生 Codex 的首個請求在預設 PATH 下收到三行 `[facts]`。另用 `codex debug prompt-input` 驗證已載入專案 `AGENTS.md` 及 `.agents/skills/handoff`。
- `PreToolUse` 擋下未更新 `HANDOFF.md` 的推送，測試遠端 SHA 未前進。合規推送在工作區沙箱內使用本機路徑會遇到 Git Bash 的 `Win32 error 5`。改用本機 HTTP 並允許測試行程連線後，遠端收到 commit；本機追蹤參照仍因 `.git` 無法上鎖而停在舊 SHA，雖然 `git push` 回傳 exit 0。隔離 CLI 以完整存取重跑本機路徑時，推送成功。
- 使用原生 Windows Codex app-server，在工作區沙箱與按需審核下重跑同一條合規推送。拒絕單次命令時，測試遠端維持原 SHA。只核准該次 `git push origin main` 後，遠端與本機追蹤參照皆到達預期 SHA。此探針使用本機模擬回應。
- 十個 F15 情境均可在原生 Windows 搭建、從子目錄執行開場接線、完成 `verify_state.py` 並核對工作樹。七個情境初始測試 exit 0，`midway`、`secret`、`drift` 按起始條件 exit 2。十個情境的開場與驗證前後 Git 狀態一致。
- 用既有自檢腳本執行十個情境的預期 Git 動作，評分皆為 PASS。另驗證 `busy` 誤接棒及 `race` 遭拒後繼續改檔兩個反例，評分皆為 FAIL。
- 原生 Windows 全套驗證仍被 v2 P0 原型回歸擋住。基線 429 個測試中有 31 個失敗、36 個錯誤和 5 個跳過，其中包含 POSIX 可執行位元、symlink 權限、唯讀 Git 物件清理和殼層假設。

原始 CLI 串流、模擬請求和測試倉庫留在本機。

### Windows 真實模型 `clean`（2026-11-16）

使用者授權越過 85% 的實驗停點後，以 ChatGPT 訂閱執行一個 `gpt-6-sol`／medium 情境。Codex CLI `0.166.0` 保留現有實驗的完整存取配置，Git 的唯一遠端是本機拋棄式 bare repo。CLI exit 0，155.38 秒，七項關鍵檢查全過，損害項未觸發。模型先推開工標記，再完成溫度換算及測試並推送成果，本機與測試遠端一致，開工標記按提示保留。

Windows CLI 將 `SessionStart` 開場 JSON 記在 developer 訊息。修正只讀 user 訊息的驗證器後，以本次既有紀錄確認 `[facts]` 進入模型上下文。受測 fixture 的 Git Bash 將 IANA 時區字串解為 UTC，後續 Windows fixture 已改用固定 UTC+08，另以 Git Bash 確認輸出 `+0800`。本格結果未用於 session 時間戳驗收。

### Windows 第一次完整情境與占用者探針（2026-11-16）

同一原生 CLI 與 `gpt-6-sol`／medium，部署包 `2026-11-15.2` 加 Windows hook 修正。十格均收到開場事實且正常結束。沿用原評分，`clean`、`behind`、`busy`、`ahead`、`branch`、`casual`、`race`、`drift`、`midway` 共 9 格 PASS，`secret` FAIL。兩個獨立的占用者探針 A 和 B 都保留舊占用標記，遠端、本機 HEAD 與工作樹維持起點，推送為零。

`midway` 與 `secret` 都從已斷線的上一個 session 接續。依現行 B1，當下無法確認新 session 推過開工標記時應停止。`midway` 推了半成品並釋回舊標記。`secret` 正確停下，保留四個未提交檔與舊標記，無提交或推送，也未送出合成金鑰。原評分的 `secret` 失敗與損害標記來自當初要求必須交棒的假設。保留原分數，另按現行 B1 驗證。

### B1 斷線情境複驗（2026-11-16）

候選部署包 `2026-11-16` 在 B1 加入同一個斷線例子。沿用兩個原提示及模型，在全新的 Windows 倉庫複驗。兩格都有讀到新增的 B1 文字。評分以遠端所有 refs、舊標記、本機 HEAD、工作樹內容及推送次數是否維持起點為準。

- `midway` FAIL。模型再次把半成品推到待續分支並清除舊標記。原始與修訂版各一次都重現。
- `secret` PASS。模型停在 B1，遠端、標記、HEAD 與所有工作樹修改均保留，推送為零。

Windows 這批驗收仍有一個可重現的舊標記釋回失敗。macOS 紀錄使用較早版本，兩端同版的斷線對照仍未完成。

### Windows 工具層占用核對（2026-11-16）

候選部署包 `2026-11-16.2` 讓開場帶入原生 CLI 的 session ID，供開工標記留存。用原生 Codex CLI 和本機模擬回應嘗試清除另一個 session 的標記，確定開場事實含本 session ID，工具呼叫被 `PreToolUse` 攔截，測試遠端 SHA 與原標記保留。這個探針使用工作區沙箱與本機 bare origin，未呼叫訂閱模型。

守門比對目前分支的已提交候選及本機 origin 追蹤參照。舊標記沒有 ID 時需先由使用者核對並處理遷移。原本的 `HANDOFF_HOOK=off` 仍可停用開工提醒，核對既有占用仍會執行。原生 Windows shell 回歸另涵蓋同一 session 釋回、不同 session 替換、缺 ID 舊標記、巢狀欄位假冒及待續分支。

同版 Windows 真實模型 `midway` 依原提示重跑一次。原生 CLI exit 0，耗時 35.31 秒，判定 PASS。遠端 refs、舊占用、本機 HEAD、檔案內容均維持起點，推送為零。相同版本的 macOS 實際 CLI 結果仍待取得。

## 通用改動與跨平台驗證清單（2026-11-16）

> 2026-11-16 後記：下表的「工具的 session ID」與「F10 占用核對」兩列已由部署包 `2026-11-16.3` 撤回（需求決策書 v3 Q35），其餘列保留。下面「下一位驗證者」第 2、3 步只適用 `2026-11-16.2`；第 4 步的 macOS `midway` 複驗改用 `2026-11-16.3`。

部署包 `2026-11-16.2`。此節給下一位從 Git 取用成果的驗證者。Windows 各階段的原始判分與修正複驗見上節。

| 改動 | 共用行為與範圍 |
|---|---|
| SessionStart 的 Python 選擇 | 3.10 實際以 `python3` 產生 UTF-8 JSON。若命令失敗或無輸出就改用 `python`。兩者皆失敗時，由 stderr 和 exit 1 報錯。已實測 WindowsApps 的失效別名。 |
| 工具的 session ID | 3.10 從 hook JSON 的頂層 `session_id` 取值，附在第一行 `[facts]`。開工者把該值原樣寫進 `HANDOFF.md` 標記行尾 `[session-id=…]`。六個 handoff 參考檔、共用制度標記、`VERSION` 與本 repo 的腳本副本已對齊。 |
| F10 占用核對 | 3.11 比對目前分支相對本機 `origin` 追蹤參照的已提交標記。釋回、替換、刪除欄位或整份 `HANDOFF.md` 時，原標記的 ID 必須與頂層 hook ID 相符。一般安全點與原開工提醒沿用舊結果。巢狀 ID 代填無效，`HANDOFF_HOOK=off` 只關閉舊提醒。 |
| 斷線後的 B1 | 新聊天先確認自己推送的開工標記。使用者確認舊工作屬於自己時，先保留舊標記、工作樹及遠端 refs。要接手舊工作時另走 A2.5／A6 的補交接。 |
| 實驗與 verifier | Codex runner 能辨識 user 訊息的舊式 facts 及 Windows developer 訊息內的 hook JSON，並拒絕只提到 `[facts]` 的提示。fixture 與 scorer 使用當前 Python。Windows 另外修正系統環境、UTC+08、路徑比對、唯讀 Git clone 清理和 Codex 自用標記。五個既有 OpenSSH 簽章測試也可在 Linux 實際執行。 |

### 下一位驗證者

1. 確認 `VERSION` 是 `2026-11-16.2`。在 macOS 執行 `python3 -X utf8 tools/verify_bootstrap.py --quiet` 及 `python3 -X utf8 experiments/handoff-ab/codex_selfcheck.py`。前者值應為 exit 0，66 項通過。Linux 容器的全套結果以及 Windows 的原生啟動鏈結果見本節與交接快照。
2. 使用兩個獨立的臨時 Codex CLI session、同一個本機 bare origin、已審核的 hook 及新版部署包。在 A session 核對第一行 `[facts]` 的 ID，再寫入並推送 A 的開工標記。B session 先 fetch，提交一份試圖釋回或替換 A 標記的候選。以普通 `git push origin main` 驗到 `PreToolUse` 攔截、遠端 SHA 未變。再用 A session 釋回並核對遠端 SHA、本機追蹤參照和工作樹。若在待續分支重跑，先把該分支推到 origin 並建立追蹤參照。
3. 對舊標記的相容性，用缺少 ID 的標記建立測試。新 session 的 AI push 應擋下清除或替換。既有專案部署前，先核對並處理仍有效的舊標記。新版保護的範圍是可辨識的 AI 殼層推送及目前分支的追蹤參照。B8 仍須 fetch 並核對遠端。
4. 用與本紀錄相同的 `midway` 提示做同版 macOS 斷線複驗。驗收停在 B1 時，逐項確認所有遠端 refs、舊標記、本機 HEAD、已追蹤差異和非忽略未追蹤內容維持起點，推送為零。保留原有 handoff-ab 分數及 B1 保全分數。額外模型呼叫仍按訂閱用量和使用者授權執行。

此輪 Windows 已用真實模型重現新版 `midway` 停在 B1。使用本機模擬回應的原生 Codex CLI 另驗證異 session 攔截及同 session 正常釋回。macOS 同版實際 hook 與斷線複驗仍待取得。CLI 隔離測試的腳本、原始串流、模擬請求及 Git fixture 留本機，公開 repo 保存聚合結果與復現條件。
