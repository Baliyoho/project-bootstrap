# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-11 17:06（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（P2 第 4 片：能力矩陣）

## 任務目標

依[需求決策書](project-bootstrap-requirements-decision.md)決策版本 2 與[實現規劃](project-bootstrap-implementation-plan.md)續作 v2；已授權分支實作，未授權切換現行程序或合併 main。逐 ID 狀態唯一權威是 [v2 現況索引](experiments/v2/status.json)，索引不可讀就停止判定。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111117｜做遷移器｜工作中｜交棒0次`，2026-11-11 17:11 (+08) 開工
- **骨架版本**：`2026-11-10.2`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；`gh` 已登入且有 `workflow` 權限。Windows／Linux 未驗。

## 已完成

P0、P1 與 F22 見 [v2 說明](experiments/v2/README.md)。2026-11-11 P2（使用者逐片指示，決策書 Q20–Q24）：第 1 片包格式與歸屬、第 2 片專案指標與寫入檢查、第 3 片簽章發布與 Git tag channel（已發 `channel/beta/1-ed31ffed…`）、第 4 片能力矩陣（Q24：`src/kit/capabilities.json` 是唯一的家，部署包兩張跨工具表由它生成、逐位元組不變；`capabilities.py` 逐 surface／版本報缺口，必要能力只認本次自測，目前沒有 surface 是 strict ready）。細節在 v2 說明 P2 各節。

## 未完成／下一步

1. P2 剩第 5 片同步器轉遷移器（客製保留、20 目標報告），等使用者指示。`beta` epoch 1 沒有報告檔，下一次發布才有。
2. 第 4 片缺口：真實工具上的自測、版本偵測、矩陣進正式包、F14 共用 CLI 契約與等價案例。
3. channel tag 沒有伺服器端保護（Q23）；安全靠簽章，假 tag 只會讓寫入停下。
4. F22 剩 Windows／Linux 與 Codex 沒量；P0 Mac 已知缺口清單在 v2 說明；金鑰撤銷、跨機通知與外部效果冪等沒做。
5. 動作提醒 hook：`bash -c "git push"` 會漏報。Windows hook 同步、R01–R09 複審、Codex 真實注入、F28 探針先不做（2026-11-10 裁定）。

## 地雷與注意事項

- 改這個 repo 的地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」（含發布與 `workflow` 權限），碰到對應的檔才讀。
- 跨工具表改 `src/kit/capabilities.json`，不改 `kit.md`；決策書已決題要逐一寫「未選 (x)」理由，否則 `test_trail_repo` 擋。
- 提交指令用 `&&` 綁住 verify 的結束碼；互動殼層是 zsh，變數不會自動拆成多個參數。

## 服務查證與期望快照

- 2026-11-11 17:05 `verify_bootstrap.py --staged`：exit 0；`uv run --locked pytest` 570 通過（3.15）。新 `capabilities` mutation 群組 33 個全 killed，全量沒重跑。B5：Codex hook 接線未改，不適用。無額外模型呼叫。

## 懸置事項（AI 勿自行處理）

- 無。
