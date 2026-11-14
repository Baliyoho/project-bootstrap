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

## 判定範圍

依 v3 第 6 節的 handoff-ab 退出條件，Codex 在兩輪十個情境的關鍵檢查不比第 1 期 Claude Code 完整組差，且沒有損害格。這是單輪情境、同一台 macOS、單一模型的結果；多輪 Git 行為另由上述 CLI F50 步驟覆蓋，桌面 App 標題項尚未判定。
