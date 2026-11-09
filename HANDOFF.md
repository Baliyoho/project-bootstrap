# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-09 22:25（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `baliyohodeMini`（無共享 guest 的 run 帳本與 channel 綁定）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-03`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2；ad hoc virtualization entitlement 可啟 VM。Windows／Linux 本輪未驗。現行部署包及程序未切換。

## 已完成

- v2 P0 原型保留管道分權、POSIX 工作樹套用、限期票據與簽核、受管單 worker、前提切換與 outbox。三個原始繞過反例仍重現，嚴格模式未就緒；逐 ID 狀態見 [v2 現況索引](experiments/v2/status.json)。
- Mac VM 舊共享 scratch 反例與退場探針仍通過（VM stop、host SIGKILL、控制管道 EOF、兩 VM 鎖不協調、受管 fixture 父程序 SIGKILL 後 fail closed）。固定 Alpine 3.24.4 aarch64 netboot digest；正式工作樹不掛進 VM。
- 無共享 guest 的固定 `vm_managed_worker.sh` 路徑：兩 epoch 寫入 `10`／`21`、pending 舊請求拒絕、事件歸因通過（前輪成果）。
- **本輪新增 `guest_runs.py` 持久 run 帳本**（同一私有 SQLite）：開機前記 `starting` 列（parent 自訂 run id、probe id、runner 二進位／kernel／initramfs／init／工具 SHA-256）；host 確認無共享開機後 `running`；退場只收 host 停機標記＋同 probe id＋runner 結束碼 0。有未退場列就拒絕新 guest、ACK、寫入與重啟；重開資料庫只讀帳本，不看 PID／時間／guest 日誌。
- **channel 綁定**：每台 run 綁一個 capability（只存雜湊），`require_live`／ACK 須出示同一個；退場同交易 `Lab.resume` 輪換 capability，舊 guest 的 channel 由 broker 以 `unknown-session` 拒絕（真 VM 驗：退場後舊 journal 再送寫入被拒、檔案不變）。
- **host／guest 日誌分離**：原本 runner stderr（`HOST_*`）與 guest console 合寫同一檔，guest 印出 `HOST_STOPPED state=0` 就能混進停機判讀。已改成 stderr 寫 `<log>.host`，所有探針的 host 啟動／停機判讀只讀該檔且整行比對。
- 真 VM `guest_broker` 改經帳本跑完兩 epoch 並重開資料庫核對；新增 `guest_parent_sigkill`：guest 運行中 SIGKILL 父程序，VM 因控制 EOF 停止，重開帳本仍 `running` 並阻擋重啟。
- 新增 `test_guest_runs.py` 8 測試＋`test_vm_probe.py` 2 案例；在 scratch 副本逐一移除 11 個守門條件，測試全部失敗（CAUGHT）。
- 本輪只改 v2 隔離原型、索引、原型說明及 ARCHITECT 結構摘要；現行 22 檔部署包、skill／hook 副本及 `VERSION` 未改，無同步債；未呼叫額外模型或真實服務。

## 未完成／下一步

1. **P0 未退出。** 父程序在退場前崩潰時帳本正確阻擋，但**沒有可信的解除路徑**：需設計「真人核准＋host 端獨立證據」的人工退場（不能用 PID／時間／guest 日誌），並驗 host／hypervisor 故障、長操作及成本。這牽涉可信真人核准來源（見第 3 項），動手前宜先和使用者確認方向。
2. 已寫效果冪等／回滾與跨 epoch 原子歸因仍未驗。舊 `managed_vm_switch` 仍借 host worker 並掛可寫 scratch；兩 VM 的 virtiofs `flock` 不協調 writer。無共享路徑只涵蓋固定 shell 工具與 `note` 寫入，不是通用工具或模型。
3. 接可信真人核准、簽署金鑰發行／撤銷與額度來源；票據遺失沒有重新驗身分路徑。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。
4. F46 仍須核對來源三項例外的替代保障、其他設定組合、跨工具／OS 接手與模型實際遵循。額外模型探針須先得授權且只用訂閱額度。
5. 鎖定完整 runtime／import、候選版本、LICENSE、digest，驗 Windows／Mac 架構門檻後再做 P1。F22 常態必讀超過 12,000 字元；完整接棒時間與 token 未量，現行 A4 不省。Windows hook 同步、Mac Codex 真實注入及 R01–R09 邊界獨立複審仍待做。

## 地雷與注意事項

- 帳本的「身分」是 parent 選定檔案的 digest，**不是** guest 實際執行內容或 VM 身分的證明；`.host` 日誌與資料庫仍可被同 UID host 程序改寫。guest principal 是 parent 發的管道授權標籤。
- `GuestRunLedger.retire` 會輪換該 actor 的 capability：同一 actor 的其他 channel（例如 host worker）也一起失效，parent 須重新 `connect`。舊 `managed_fixture` 路徑沒有用這個帳本，兩條路徑的證據不能拼成完整保障。
- 帳本列若未 `retired`，重啟一律 `vm-retirement-unconfirmed`；不要人工改列或拿程序不在當退場證據。guest `/dev/hvc1` 須在已開啟 fd 上設 `raw -echo`。
- 僅合成暫存 fixture；原檔、票據與合成 Git object 不進本 repo。現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 2026-11-09 `python3 -X utf8 tools/verify_bootstrap.py` exit 0，全部檢查通過，含 148 個 v2 契約／索引測試；提交候選另用 `--staged` 驗。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-09 `python3 -X utf8 experiments/v2/vm_probe.py` exit 0：舊反例保留；`guest_broker`（兩 epoch、退場後舊 channel 拒絕、重開核對身分）與 `guest_parent_sigkill` 通過。runner SHA-256 `2e7d8f1be9a08c2ee1608c743a02724461c47cc4d2355dc29b728d94beed7a54`、guest init `3beb1059f912c0dbdabac1791c09b78393c34fb72454937db987aa5cd6d508ec`、工具 `ff9c8ccc0dc791e72d8d071f10b299b07d3b244a7f9e7a809d2d5ccd3384df67`；未測真實工具或 host OS 崩潰。
- 2026-11-09 `python3 -X utf8 tools/verify_v2.py` exit 0，148 測試、三個預期反例重現、`strict_ready=False`。接線未改，信任重審不適用；無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 崩潰後人工解除要以什麼作為可信真人核准來源，待使用者決定（下一步 1／3）。既有 v2 實作授權仍有效，P0 未驗收退出。交棒為上下文管理。
