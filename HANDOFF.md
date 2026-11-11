# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-11 17:26（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（P2 第 5 片：遷移器）

## 任務目標

依[需求決策書](project-bootstrap-requirements-decision.md)決策版本 2 與[實現規劃](project-bootstrap-implementation-plan.md)續作 v2；已授權分支實作，未授權切換現行程序或合併 main。逐 ID 狀態唯一權威是 [v2 現況索引](experiments/v2/status.json)，索引不可讀就停止判定。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-10.2`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；`gh` 已登入且有 `workflow` 權限。Windows／Linux 未驗。

## 已完成

P0、P1 與 F22 見 [v2 說明](experiments/v2/README.md)。2026-11-11 P2（使用者逐片指示，決策書 Q20–Q25）：第 1 片包格式與歸屬、第 2 片專案指標與寫入檢查、第 3 片簽章發布與 Git tag channel（已發 `channel/beta/1-ed31ffed…`）、第 4 片能力矩陣（Q24：`src/kit/capabilities.json` 生成兩張跨工具表）、第 5 片遷移器（Q25：`sync_project.py` 清單改由 `owners.json` 算出、行為不變；`tools/migrate_project.py` 預演只讀、寫入一次一個專案，只換發過的舊版，客製或行末不同就整個專案停下）。細節在 v2 說明 P2 各節。

## 未完成／下一步

1. P2 五片都做了，退出條件仍未全達成：真實專案沒有遷移（要逐專案授權）；真實只讀跑只找到本機一層目錄 4 個專案，20 個要使用者給私人清單（報告只留本機，repo 公開）。`beta` epoch 1 沒有報告檔，下一次發布才有。
2. 第 4 片缺口：真實工具上的自測、版本偵測、矩陣進正式包、F14 共用 CLI 契約與等價案例。
3. channel tag 沒有伺服器端保護（Q23）；安全靠簽章，假 tag 只會讓寫入停下。
4. F22 剩 Windows／Linux 與 Codex 沒量；P0 Mac 已知缺口清單在 v2 說明；金鑰撤銷、跨機通知與外部效果冪等沒做。
5. 動作提醒 hook：`bash -c "git push"` 會漏報。Windows hook 同步、R01–R09 複審、Codex 真實注入、F28 探針先不做（2026-11-10 裁定）。

## 地雷與注意事項

- 改這個 repo 的地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」（含發布與 `workflow` 權限），碰到對應的檔才讀。
- 跨工具表改 `src/kit/capabilities.json`，不改 `kit.md`；決策書已決題要逐一寫「未選 (x)」理由，否則 `test_trail_repo` 擋。
- 提交指令用 `&&` 綁住 verify 的結束碼；互動殼層是 zsh，變數不會自動拆成多個參數。

## 服務查證與期望快照

- 2026-11-11 `verify_bootstrap.py --staged`：exit 0；`uv run --locked pytest` 591 通過（3.15）。新 `migrate` mutation 群組 28 個全 killed，全量沒重跑。B5：Codex hook 接線未改，不適用。無額外模型呼叫。

## 懸置事項（AI 勿自行處理）

- 決策書 Q26：`.cmd` 行末。有專案用 `.gitattributes` 強制 CRLF，寫入檢查逐位元組比對會擋；選項與 AI 建議在決策書。
