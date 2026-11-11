# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-11 15:25（+08）中途安全點（C，未交棒）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（P2 正式包）

## 任務目標

依[需求決策書](project-bootstrap-requirements-decision.md)決策版本 2 與[實現規劃](project-bootstrap-implementation-plan.md)續作 v2；已授權分支實作，未授權部署或切換現行程序。逐 ID 狀態唯一權威是 [v2 現況索引](experiments/v2/status.json)，索引不可讀就停止判定。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111113｜啟動P2正式包｜工作中｜交棒0次`，2026-11-11 13:44 (+08) 開工
- **骨架版本**：`2026-11-10.2`
- 本機：macOS 27.2、Python 3.15.2、bash 3.2、uv 0.13.7；Windows／Linux 未驗。

## 已完成

P0 原型與 P1 四片（開發骨架、原型搬進 `src/`、部署包由 `src/kit` 生成、狀態卡／schema／連結檢查）都在本分支，逐模組見 [v2 說明](experiments/v2/README.md)，P1 退出條件對照在實現規劃第 7 節。決策書第 6 節 Q1–Q19 都已裁定。

2026-11-11 F22：常態必讀約 11,100 字元、Mac 接棒約 101 秒，細節在索引 F22。

2026-11-11 P2（使用者逐片指示，Q20／Q21）：包格式與歸屬、專案指標與每次寫入檢查、簽章發布與金鑰鏈與 Git tag channel、發布／安裝命令列與 `release.yml`，見 v2 說明 P2 各節。3b 的 E1 已做：GitHub `release` environment（擁有者核准）存 CI 私鑰，公鑰在 `src/kit/release-keys.txt`。部署包、skill 與 `VERSION` 沒動。

## 未完成／下一步

1. P2 3b 剩 E3 tag 保護規則、E4 首次發 `beta`、E5 驗收，每步都要使用者點頭；之後是第 4 片能力矩陣、第 5 片遷移器。風險：workflow 沒在 GitHub 跑過，macOS runner 可能過不了驗證。HANDOFF 字元餘量約 500。F22 剩 Windows／Linux 與 Codex 沒量。
2. P0 Mac 已知缺口（真斷電、真重開機、錨點只擋意外遺失、通用工具進無共享 guest）清單在 v2 說明，不在 P0 補。
3. 金鑰外洩後的撤銷與額度來源沒做；接真實工具前要補跨機通知／恢復、外部效果冪等與輸入裁剪。
4. 動作提醒 hook 試行中：`bash -c "git push"` 會漏報，沒有 python 時退回字串比對會誤報。
5. Swift runner 沒有離線測試；guest 腳本離線測試跑的不是 busybox ash；F14／F15 需另一個工具或 OS；F41 先不用雲端。
6. Windows hook 同步、R01–R09 獨立複審、Mac Codex 真實注入、F28 模型探針先不做（使用者 2026-11-10 裁定）。

## 地雷與注意事項

- 改這個 repo 的地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」，碰到對應的檔才讀。
- 提交指令用 `&&` 綁住 verify 的結束碼；互動殼層是 zsh，管線結束碼看 `${pipestatus[1]}`。

## 服務查證與期望快照

- 2026-11-11 15:25 `verify_bootstrap.py --staged`：exit 0；`uv run --locked pytest` 549 通過（3.15）。P2 新群組 mutation 只單跑（package 27、pointer＋channel 82、distribute 25 全 killed），全量沒重跑。
- 2026-11-11 P1 收尾：全量 756 killed、`vm_probe.py` exit 0、3.12.16 476 通過。Windows／Linux 未跑；無額外模型呼叫。

## 懸置事項（AI 勿自行處理）

- 無。
