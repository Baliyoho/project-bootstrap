# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-09 08:56（+08）
- **交棒者**：Codex ／ `baliyohodeMini`（兩個 epoch 的 VM 合成操作與退場紀錄）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`baliyohodeMini` ／ `Codex CLI` ／ `㊣　26110909｜移入VM工具｜工作中｜交棒0次`，2026-11-09 09:06 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2；ad hoc virtualization entitlement 可啟 VM。Windows／Linux 本輪未驗。現行部署包及程序未切換。

## 已完成

- v2 P0 原型保留管道分權、POSIX 工作樹套用、限期票據與簽核、受管單 worker、前提切換與 outbox。三個原始繞過反例仍重現，嚴格模式未就緒；細節及逐 ID 狀態見 [v2 原型說明](experiments/v2/README.md) 與索引。
- Mac VM 仍用固定 Alpine aarch64 netboot digest、無網路 guest、父程序控制管道、`setsid` 後代 heartbeat。兩個相繼 epoch 各起一台 guest 執行固定整數乘法；parent 核對具名結果，經既有 outbox／broker 套用到合成工作樹。舊 epoch 未送出的請求在切換後被拒，正式工作樹不掛進 VM。host 讀取 guest 結果拒絕 symlink／hardlink 並限制長度；有離線負向測試。
- VM 紀錄改為 actor＋epoch 複合鍵；連續 VM 探針抓到啟動時 actor-only UPDATE 將舊 `retired` 倒退為 `running`，已改為 actor＋epoch 且只允許 `unconfirmed→running`。實跑確認兩筆退場證據都保留；退場失敗仍阻擋切換。父程序 SIGKILL 後 guest 因控制 EOF 停止，但無持久退場證據時新父程序拒絕恢復。
- F46 既有本機同組情境維持：來源例外逐項可見，交接快照 11 種、文件 20 種、文件設定 9 種正反例；本機 bare origin 雙 checkout 接力覆蓋占用、開工 SHA 變更、任務 push 與釋出。只驗 Git／hook 訊號，不證明模型遵循。
- 本輪只改 v2 隔離原型、索引、原型說明與本 repo 結構說明；現行 22 檔部署包、skill／hook 副本及 `VERSION` 未改，無同步債；未呼叫額外模型或真實服務。

## 未完成／下一步

1. **P0 未退出。** VM 目前只做固定合成算術；每個 epoch 仍有獨立 host worker 載入上下文並提供 channel，broker 事件不能獨立歸因 guest。下一步需把真實受管工具與可信能力管道移入 guest，讓 guest 無正式工作樹寫入權；驗完整效果隔離、已寫效果的冪等／回滾及跨 epoch 原子歸因。共享 scratch 可由 guest 直接改；兩 VM 的 virtiofs `flock` 不協調 writer。
2. 父程序死於 VM 退場證據持久化前時，當前設計安全地阻擋，但無可信自動解除路徑。設計可重啟核對的 VM 身分與退場證據，驗 host／hypervisor 故障、長操作及成本；禁止用舊 PID、時間或 guest 自報日誌推定。舊單鍵 VM 實驗庫不自動遷移；Windows Job Object 尚無 Windows 實測。
3. F46 仍須核對來源三項例外的替代保障、其他設定組合、跨工具／OS 接手與模型實際遵循。來源沒有專案自訂過期字串設定；合成設定對照不是任意專案驗收。額外模型探針須先得授權。
4. 接可信真人核准、簽署金鑰發行／撤銷與額度來源；票據遺失沒有重新驗身分路徑。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。額外模型探針須另得授權且只用訂閱額度。
5. 鎖定完整 runtime／import、候選版本、LICENSE、digest，驗 Windows／Mac 架構門檻後再做 P1。F22 常態必讀超過 12,000 字元；完整接棒時間與 token 未量，現行 A4 不省。Windows hook 同步、Mac Codex 真實注入及 R01–R09 邊界獨立複審仍待做。

## 地雷與注意事項

- 僅合成暫存 fixture。Mac profile 禁 fork／spawn／signal；程序群組可被 `setsid` 脫離。VM 探針只涵蓋固定 guest；共享目錄已寫效果不回滾，無外部網路／真實 surface。結果檔和 guest 日誌不能防同 UID host 偽造；broker 現用 host worker principal。VM stop 回呼與 1 秒 heartbeat 穩定不是 host OS／hypervisor 崩潰證據。監護被殺、整機暫停、父程序凍結且租期尚未到仍未驗。
- VM 退場資料庫列若未標 `retired`，resume 會 fail closed；不要人工改列或拿程序不在當退場證據。materializer 只支援 broker 獨占的 POSIX 普通檔案；未知 phase、外部衝突或失效 epoch 保持 pending，不自動覆蓋或換 request ID。搬機、還原 DB、斷電及多 writer 尚未驗。
- 票據庫權限須配合 OS 隔離；簽章測試使用一次性金鑰。原檔、票據與合成 Git object 不進本 repo。舊實驗庫若缺新指紋／前提／回收證據，不能自動收編。
- 現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。額外模型、真實部署、遠端保護與合入 main 仍依原授權邊界。

## 服務查證與期望快照

- 2026-11-09 `python3 -X utf8 tools/verify_bootstrap.py --staged` exit 0，58 項全過，含 131 個 v2 契約／索引測試；驗的是待提交集合，工作樹無未暫存與未追蹤檔。
- 2026-11-09 08:52 (+08) `python3 -X utf8 experiments/v2/vm_probe.py` exit 0：stop、host runner SIGKILL、重啟、兩 VM 鎖反例、控制 EOF、兩個 epoch 的 guest 算術／broker 寫入／退場證據、舊請求拒絕及父程序 SIGKILL 後阻擋恢復均通過。固定映像及 runner SHA-256 由探針列出；未測真實工具或 host OS 崩潰。
- 2026-11-09 `python3 -X utf8 tools/verify_v2.py` exit 0，131 測試通過、三個預期反例仍重現、`strict_ready=False`；定向 16 測試亦 exit 0。未另跑 `--require-ready`（預期 exit 2）。
- 本 repo 無 verify_state.py／check_docs.py，依 AGENTS 使用替代入口；接線未改，信任重審不適用。無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 無新增待決。交棒為上下文管理；既有 v2 實作授權仍有效，P0 未驗收退出。
