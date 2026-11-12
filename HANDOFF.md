# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-12 19:41（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（使用者登入 CLI 後跑 Claude Code 啟動自測一次，通過；矩陣該格改為實測）

## 任務目標

依[需求決策書](project-bootstrap-requirements-decision.md)決策版本 2 與[實現規劃](project-bootstrap-implementation-plan.md)續作 v2；已授權分支實作，未授權切換現行程序或合併 main。逐 ID 狀態唯一權威是 [v2 現況索引](experiments/v2/status.json)，索引不可讀就停止判定。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-10.2`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；`gh` 已登入且有 `workflow` 權限。PATH 上沒有 `claude`／`codex`／`agy`；桌面 App 內附的 Claude Code 2.1.321 已用 `claude auth login` 登入（Pro，到 2026-12-12），拿掉宿主 session 的變數就能單獨跑；Antigravity.app 2.31.0。Windows／Linux 未驗。

## 已完成

P0、P1、F22 與 P2 五片見 [v2 說明](experiments/v2/README.md)。2026-11-12（使用者指示逐項推進，之後依建議）：
- P2 第 4 片缺口：包的 manifest 帶能力矩陣；`selftest.py` 偵測版本、做只看檔案的安裝自測（含 `--os windows`）。
- F14：`surfaces.py` 讓兩支 hook 在每個 surface 照自己的接線跑；開場檢查與 push 提醒都等價，Antigravity 不接 push 提醒時明示不支援。
- Q27 (a)：部署包 3.11 push 提醒只看 `command` 欄位，`source:` `v2026-11-12`，`VERSION` 不動。
- 發布 `channel/beta/2-b2878c41…`（`8bcdbb1`）：本機重建 digest 相同、報告檔對得上、乾淨環境安裝放行、沿金鑰鏈從 epoch 1 升級。
- 本 repo 的動作提醒 hook 會看進 `bash -c`／`eval`。
- Claude Code 2.1.321 啟動自測（一次 `claude -p`）：開場 hook 的輸出確實進到模型 context；矩陣 `claude-code/hooks` 改為 `tested`，包的 digest 會變，下次發布才帶出去。

## 未完成／下一步

1. P2 退出條件未全達成：真實專案遷移與另外 20 個專案的私人清單。2026-11-12 預演：從 v2 同步會帶出六檔版 skill，與 Q14 (b) 衝突，使用者選先不同步；`鍵鼠同部署_mac` 與 upstream 沒對齊。等 v2 上 main 時一起處理。
2. 啟動自測只做了 Claude Code 的 SessionStart；有沒有讀 `AGENTS.md`、push 提醒的 exit 2 是否真的擋下、Codex／Antigravity 都沒測，每次模型呼叫要另行授權。
3. F14 其他程序步驟沒有等價案例；`ag-wrap.sh` 會把 stderr 併進訊息，hook 若開始寫 stderr 就不等價。
4. channel tag 沒有伺服器端保護（Q23）；每次發布要先刪舊的 `release-request/<channel>` 觸發 tag（見 ARCHITECT）。
5. F22 剩 Windows／Linux 與 Codex 沒量；P3／P4、Windows hook 同步、R01–R09 複審、Codex 真實注入、F28 探針維持暫緩（2026-11-12 使用者再確認）。

## 地雷與注意事項

- 改這個 repo 的地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」（含發布與 `workflow` 權限），碰到對應的檔才讀。
- 跨工具表改 `src/kit/capabilities.json`，不改 `kit.md`；格子文字不能有 `|`。改矩陣會改變包的 digest。決策書已決題要逐一寫「未選 (x)」理由，否則 `test_trail_repo` 擋；HANDOFF 懸置的每一條都要在決策書登記成待決。
- `*_repo.py` 測試要 import `tools/`，不能進 mutation 群組，反證要手動做。
- 部署 hook 的註解別寫直譯器名稱，跨平台防呆會當成依賴。

## 服務查證與期望快照

- 2026-11-12 19:41 `verify_bootstrap.py --staged`：exit 0；`uv run --locked pytest` 639 通過（3.15）。mutation 只跑 selftest 40、surfaces 27、capabilities 33、package 27 四組，全 killed，全量沒重跑。B4：本 repo 沒有 `check_docs.py`（已宣告例外）。B5：Codex hook 接線未改，不適用。模型呼叫：Claude Code 探針一次（已授權）。

## 懸置事項（AI 勿自行處理）

- 無。
