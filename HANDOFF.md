# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-15 20:04（+08）
- **交棒者**：Codex 桌面 App／Mac（完成 Codex macOS 交接驗證）

## 任務目標

驗證現行交接流程在 macOS 的正確性與執行成本。使用者已結束 Claude Code 測試，並指示 Windows 實機驗收暫緩。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-14.4`
- 測試報告已推到 `main`（`b0aab00`）。本輪只提交報告與交接快照，部署、版本調整與 hook 信任重審不適用。
- 本機 Mac，使用 `python3`。Codex CLI 可用，已用 ChatGPT 訂閱登入。

## 已完成

- Codex macOS 共 37 個受測回合。純任務 12 格、現行版本情境 10 格、長驗證 5 格、同一聊天接棒再交棒 4 格皆通過。610 秒驗證只啟動一次。
- 占用者核對 6 格均釋回另一個 session 的標記。影響限於隔離測試倉庫。
- 執行提示組的接棒三對皆較慢，交棒快慢互見。正式 repo 的前後觀測使用相同模型及指令，歷史回合含量測與暫計提交，效益未經受控比較。
- 逐格結果、格式差異和用量見 [PHASE2-RESULTS.md](experiments/handoff-ab/PHASE2-RESULTS.md#codex-cli-純任務與後續探針2026-11-15)。

## 未完成／下一步

1. 本輪 macOS CLI 測試計畫已完成。若使用者要處理占用者核對或 session 名稱欄位，先讀測試報告的對應結果，依使用者決定從 `src/kit/` 改源頭、重生部署包並依拓撲同步。
2. Windows 實機驗收暫緩。桌面 App 的 F50 五步互動仍未驗，先前決定不另開測試聊天。CLI 既有 F50 結果見 [CODEX-RESULTS.md](experiments/handoff-ab/CODEX-RESULTS.md#f50-多輪互動codex-cli)。

## 地雷與注意事項

- Codex 測後五小時窗 86%、七天窗 77%，37 個回合皆於 85% 門檻前啟動。後續如獲授權執行模型測試，每格前重查訂閱用量。
- 原始串流、rollout 與隔離倉庫只留本機暫存。公開 repo 只有聚合報告。
- 若續作會碰 Windows 舊 session，先核對 Git 與 origin 上的占用者，再決定如何處理既有未推成果。

## 服務查證與期望快照

- 報告提交前 `python3 -X utf8 tools/verify_bootstrap.py --staged --quiet` 66 項通過，exit 0。交棒快照同樣以這個入口驗證。
- 實驗離線單元測試 16 項通過，`codex_selfcheck.py` 與 `selfcheck.py` 通過。本 repo 的文件與服務驗證使用上述專案入口。

## 懸置事項（AI 勿自行處理）

- 無。
