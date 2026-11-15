# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-15 21:34（+08）
- **交棒者**：Codex 桌面 App／Mac（macOS 複驗完成，下一棒驗 Windows）

## 任務目標

使用者下一輪在 Windows 接棒，驗證原生 Codex CLI 與部署骨架的交接流程。以需求 v3 的 F15 核對同情境關鍵結果。這輪焦點是 Codex，Claude Code 測試已結束。桌面 App 的 F50 五步互動按先前決定先擱置。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Codex` ／ `㊣　11.15.21｜驗Windows交接｜工作中｜交棒0次`，2026-11-15 22:06 (+08) 開工
- **骨架版本**：`2026-11-15.2`
- 占用者修正在 `5e48218`，複驗結果在 `9da20b4`，都已推至 `main`。

## 已完成

- macOS CLI 原計畫 37 回合。31 格通過，原版占用者探針 6 格曾誤釋回其他 session 的標記。正常接棒與交棒、異常情境、最長 610 秒等待及同聊天接棒再交棒的結果已落地。 [macOS 測試結果](experiments/handoff-ab/PHASE2-RESULTS.md#codex-cli-純任務與後續探針2026-11-15)
- 新版在交棒開始與釋回推送前核對 origin。本機兩份全域 skill 已同步。macOS 重跑占用者 6 格，A、B 各三格均正確停下，無修改或推送。 [占用者複驗](experiments/handoff-ab/PHASE2-RESULTS.md#codex-占用者核對複驗2026-11-15)

## 未完成／下一步

1. 在 Windows 從 origin 接棒。若舊工作區有未推提交或來源不明的改動，先依 AGENTS 的異常流程停下核對。確認原生 Codex CLI、PowerShell、Git for Windows／Git Bash、Python 及訂閱登入。
2. 先在原生 Windows 執行 `tools/verify_bootstrap.py`，記錄 Windows 專屬的啟動與結束碼檢查，並用拋棄式測試倉庫確認 Codex 實際收到 SessionStart 的 `[facts]`、PreToolUse 有執行。
3. 依 F15 用隔離倉庫跑同一組情境，每個情境先一次。對照 clean、behind、busy、midway、branch、ahead、casual、race、secret、drift 的關鍵結果，另驗新版占用者探針能保留另一個 session 的標記。比較時記清楚兩端部署版本。 [F15 需求決策](project-bootstrap-requirements-decision-v3.md) [情境表](experiments/handoff-ab/SCENARIOS.md)

## 地雷與注意事項

- `experiments/handoff-ab/common.py` 直接匯入 POSIX 專用的 `pwd`，原生 Windows 不能直接跑既有 runner。重用情境、提示及評分，先讓原生環境能跑離線 fixture，再呼叫模型。Windows 上的 WSL 結果不可代替原生 PowerShell、cmd 與 Git Bash 啟動鏈。
- 確認 hook 信任與實際執行後才判讀結果。模型測試每格前重查訂閱用量。上一輪測後五小時窗 20%、七天窗 80%，開跑要重新讀取。
- 原始串流、rollout 與隔離倉庫留在 repo 外。公開 repo 提交聚合結果。

## 服務查證與期望快照

- `9da20b4` 提交前 `python3 -X utf8 tools/verify_bootstrap.py --staged --quiet` 在 Mac 通過 66 項，exit 0。交棒快照使用同一入口驗證。
- 未執行原生 Windows 驗收。現有 macOS 66 項包含共用檢查，不能證明 Windows 專屬的執行路徑已通過驗收。

## 懸置事項（AI 勿自行處理）

- 無。
