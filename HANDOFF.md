# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-12 20:05（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（P2 第 4 片缺口：版本偵測、安裝自測、矩陣進包；F14 兩支 hook 的跨 surface 等價；動作提醒 hook 補 `bash -c`）

## 任務目標

依[需求決策書](project-bootstrap-requirements-decision.md)決策版本 2 與[實現規劃](project-bootstrap-implementation-plan.md)續作 v2；已授權分支實作，未授權切換現行程序或合併 main。逐 ID 狀態唯一權威是 [v2 現況索引](experiments/v2/status.json)，索引不可讀就停止判定。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-10.2`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；`gh` 已登入且有 `workflow` 權限。PATH 上沒有 `claude`／`codex`／`agy`；Claude Code 2.1.321（桌面 App 內附）、Antigravity.app 2.31.0。Windows／Linux 未驗。

## 已完成

P0、P1、F22 與 P2 五片見 [v2 說明](experiments/v2/README.md)。2026-11-12（使用者指示「依未完成清單逐項推進」）：
- 包的 manifest 帶能力矩陣（隨簽章）；`selftest.py` 偵測版本（不猜）與只看檔案的安裝自測，含 `--os windows` 檢查 Windows handler；自測沒過讓能力變成沒有，通過不升級。
- F14：`surfaces.py` 以兩支 hook 的輸出為共用契約，每個 surface 照自己的接線與工作目錄跑；開場檢查七種狀態六個 surface 文字相同，push 提醒五種狀態 Claude Code／Codex 相同，Antigravity 明示不支援。
- 本 repo 的 `repo-action-rules.sh` 對 `bash -c`／`sh -lc`／`eval` 裡的指令再解析一層。

## 未完成／下一步

1. P2 退出條件未全達成：真實專案遷移（逐專案授權）、另外 20 個專案的私人清單、發布 `beta` epoch 2（第一個帶矩陣與報告檔的正式包，要在 GitHub 核准 release environment）。
2. 啟動自測（真的觸發 hook 並讀回、問工具有沒有讀到指示檔）要模型呼叫；Codex 專案信任不在檔案裡；`.cmd` 在 Windows 上真的跑沒驗。
3. push 提醒不等價（Q27）；F14 其他程序步驟沒有等價案例；`ag-wrap.sh` 會把 stderr 併進訊息，hook 若開始寫 stderr 就不等價，目前沒有案例守。
4. channel tag 沒有伺服器端保護（Q23）；安全靠簽章。
5. F22 剩 Windows／Linux 與 Codex 沒量；金鑰撤銷、跨機通知與外部效果冪等屬 P3／P4。Windows hook 同步、R01–R09 複審、Codex 真實注入、F28 探針先不做（2026-11-10 裁定）。

## 地雷與注意事項

- 改這個 repo 的地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」（含發布與 `workflow` 權限），碰到對應的檔才讀。
- 跨工具表改 `src/kit/capabilities.json`，不改 `kit.md`；格子文字不能有 `|`。改矩陣會改變包的 digest。決策書已決題要逐一寫「未選 (x)」理由，否則 `test_trail_repo` 擋。
- `*_repo.py` 測試要 import `tools/`，`mutants.py` 只複製 `src` 與 `tests`，所以它們不能進 mutation 群組，反證要手動做。
- 提交指令用 `&&` 綁住 verify 的結束碼；互動殼層是 zsh。

## 服務查證與期望快照

- 2026-11-12 20:00 `verify_bootstrap.py --staged`：exit 0；`uv run --locked pytest` 639 通過（3.15）。mutation 只跑 selftest 40、surfaces 27、capabilities 33、package 27 四組，全 killed，全量沒重跑。B4：本 repo 沒有 `check_docs.py`（已宣告例外）。B5：Codex hook 接線未改，不適用。無額外模型呼叫。

## 懸置事項（AI 勿自行處理）

- 決策書 Q27（待決）：push 提醒在非殼層工具上 Codex 擋、Claude Code 不擋，修法三選一；測試已釘住現況。
