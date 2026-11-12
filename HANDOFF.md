# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-12 21:03（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（F14 程序入口、Claude Code 探針、v2 併進 main、發布 beta epoch 3）

## 任務目標

依[需求決策書](project-bootstrap-requirements-decision.md)決策版本 2 與[實現規劃](project-bootstrap-implementation-plan.md)續作 v2；2026-11-12 使用者指示把 v2 併進 main（決策書 Q30，快轉），之後在 main 上做；同步各專案仍要另行授權。逐 ID 狀態唯一權威是 [v2 現況索引](experiments/v2/status.json)，索引不可讀就停止判定。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：無，在 `main` 上做（2026-11-12 `main` 快轉到 `codex/project-bootstrap_v2`，那條分支保留不刪）。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111221｜改交棒判定｜工作中｜交棒0次`，2026-11-12 21:19 (+08) 開工
- **骨架版本**：`2026-11-12.4`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；`gh` 已登入且有 `workflow` 權限。PATH 上沒有 `claude`／`codex`；桌面 App 內附的 Claude Code 2.1.321 已用 `claude auth login` 登入（Pro，到 2026-12-12），拿掉宿主 session 的變數就能單獨跑；ChatGPT.app 內附 Codex CLI `0.167.0-alpha.3.2`。Windows／Linux 未驗。

## 已完成

P0、P1、F22 與 P2 五片見 [v2 說明](experiments/v2/README.md)。2026-11-12（使用者指示逐項推進，之後依建議）：
- F14：`surfaces.py` 讓開場檢查、push 提醒、程序入口（`compare_procedure`：AGENTS.md、skill description 與六個檔）在每個 surface 照自己的接線比對；開場檢查另要求非 Antigravity 的 stderr 為空。
- 部署包三處修正，`VERSION` 都不動：3.11 push 提醒只看 `command`（Q27 (a)）、3.16 指標 description 補齊觸發詞（`v2026-11-12.2`）、3.10 全域 handoff skill 與專案不同時印 🟡（Q28 (a)，`v2026-11-12.3`）。
- Claude Code 2.1.321 啟動自測三次（`claude -p`）：開場 hook 進 context、push 提醒 exit 2 真的擋下、`AGENTS.md` 經 import 進 context、skill 由模型用 Skill 工具載入但家目錄同名 skill 蓋掉專案那份。矩陣對應格改為 `tested`。
- Q29 (a)：Antigravity 凍結，不測、不追、不移除。Q30：`main` 快轉到 v2。
- 發布 `channel/beta/3-ad6948d1…`（`main @ cf58954`）：本機重建 digest 相同、報告檔對得上、乾淨環境安裝放行、沿金鑰鏈從 epoch 2 升級。

## 未完成／下一步

1. 各專案還沒同步到 v2／epoch 3（含上面三處修正）；P2 退出條件也還差真實專案遷移與另外 20 個專案的私人清單；`鍵鼠同部署_mac` 與 upstream 沒對齊。使用者 2026-11-12 回答先不要同步，要等授權。
2. Codex：等使用者額度在 2026-11-14（週六）重置後再處理啟動自測與 F14 實測；每次模型呼叫仍要授權。
3. F14 只到「讀得到的文字與 hook 輸出相同」；部署包沒接 SessionEnd，模型是否照程序做沒有等價案例。Claude Code 原生讀 `AGENTS.md`（沒有 `CLAUDE.md`）沒測。
4. channel tag 沒有伺服器端保護（Q23）；每次發布要先刪舊的 `release-request/<channel>` 觸發 tag（見 ARCHITECT）。
5. F22 剩 Windows／Linux 與 Codex 沒量；P3／P4、Windows hook 同步、R01–R09 複審、F28 探針維持暫緩（2026-11-12 使用者再確認）。

## 地雷與注意事項

- 改這個 repo 的地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」（含發布與 `workflow` 權限），碰到對應的檔才讀。
- 跨工具表改 `src/kit/capabilities.json`，不改 `kit.md`；格子文字不能有 `|`。改矩陣會改變包的 digest。決策書已決題要逐一寫「未選 (x)」理由，否則 `test_trail_repo` 擋；HANDOFF 懸置的每一條都要在決策書登記成待決。
- Claude Code 會用 `~/.claude/skills/handoff/` 蓋掉專案那份；改了 skill 目錄要一起覆蓋這台的全域副本。
- `*_repo.py` 測試要 import `tools/`，不能進 mutation 群組，反證要手動做。
- 部署 hook 的註解別寫直譯器名稱，跨平台防呆會當成依賴。

## 服務查證與期望快照

- 2026-11-12 21:03 `verify_bootstrap.py --staged`：exit 0；`uv run --locked pytest` 652 通過（3.15）。mutation 只跑 surfaces 一組 41 個，全 killed，全量沒重跑。B4：本 repo 沒有 `check_docs.py`（已宣告例外）。B5：Codex hook 接線未改，不適用。模型呼叫：本 session Claude Code 探針兩次（各經授權）。

## 懸置事項（AI 勿自行處理）

- 無。
