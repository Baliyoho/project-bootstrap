# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-09 22:55（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `baliyohodeMini`（無共享 guest 帳本＋M1／M3 閘門原型）

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
- Mac VM：舊共享 scratch 反例與退場探針保留；無共享 guest 的固定 `vm_managed_worker.sh` 兩 epoch 寫入與舊請求拒絕通過。
- **`guest_runs.py` 持久 run 帳本**：開機前記 parent 選定 digest 與 run id，退場只收 host 停機標記＋runner 結束碼 0；未退場就拒新 guest、ACK、寫入與重啟。每台 run 綁一個 channel，退場同交易輪換 capability，舊 channel 由 broker 拒絕。runner stderr 改寫 `<log>.host`，guest console 不能再偽造 `HOST_*` 標記。真 VM `guest_broker` 經帳本並重開核對；`guest_parent_sigkill` 證明父程序被殺後重開仍阻擋。
- **`gitclaim.py` M3 開工／收尾閘門（F4／F9／F10／F19／F25 原型證據）**：開工先 fetch，失敗不用舊 ref；dirty、ahead-only、分岔、落後、無／錯 upstream、detached、遠端標記缺／重複都拒絕；占用按機器／工具／session 分代碼。收尾只收綁定 HEAD tree 的檢查收據，遠端前進、push 被拒、離線、推送後被搶占都不給 `HandoffReceipt`。`batch.py` 對 20 個真 repo 彙總（F30），壞一個就 NOT OK。
- **`release.py` M1 整包 manifest 與逐次寫入確認（F18／F32／F33）**：元件 SHA-256 manifest；每次寫入前取綁定新 nonce 的 ssh-keygen 簽章聲明，無快取路徑。
- 本輪新增模組都在 scratch 副本做過 mutation：移除守門會讓測試失敗；唯一例外是 gitclaim 推送後的「標記已釋出」再查，它被推送前檢查蘊含，已註明。多餘的絕對路徑檢查已刪。
- 索引只補證據，以上 ID 結果仍是「未驗證／不通過」：都是本機合成原型，未接進現行 A／B 程序、hook 或任何工具。現行 22 檔部署包、skill／hook 副本及 `VERSION` 未改，無同步債；未呼叫額外模型或真實服務。

## 未完成／下一步

1. **P0 未退出。** 父程序在 guest 退場前崩潰時帳本正確阻擋，但**沒有可信的解除路徑**：需「真人核准＋host 端獨立證據」的人工退場，牽涉可信真人核准來源（第 3 項），動手前先和使用者確認方向。
2. 已寫效果冪等／回滾與跨 epoch 原子歸因未驗。舊 `managed_vm_switch` 仍借 host worker 並掛可寫 scratch；兩 VM 的 virtiofs `flock` 不協調。無共享路徑只涵蓋固定 shell 工具與 `note` 寫入。
3. 接可信真人核准、簽署金鑰發行／撤銷與額度來源；`release.py` 的可信端與金鑰仍是測試替身（無 CI 身分）。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。
4. 不需使用者決定、可續做的：把 `gitclaim`＋`release` 組成單一「受管寫入前檢查」並讓 `batch` 也帶 manifest 確認；F12（同工作樹兩 writer）、F23（純問答不升級 owner）、F1／F2／F5（HANDOFF 內容與證據一致性）目前仍無原型證據。
5. F46 仍須核對來源三項例外的替代保障與模型實際遵循（額外模型探針須先授權）。鎖定 runtime／候選版本／LICENSE／digest 後才做 P1。F22 常態必讀超過 12,000 字元；完整接棒時間與 token 未量，現行 A4 不省。Windows hook 同步、Mac Codex 真實注入及 R01–R09 邊界獨立複審仍待做。

## 地雷與注意事項

- 帳本「身分」是 parent 選定檔案的 digest，不是 VM 身分證明；`.host` 日誌與資料庫仍可被同 UID host 程序改寫。`GuestRunLedger.retire` 會輪換該 actor 所有 channel，parent 須重新 `connect`。舊 `managed_fixture` 路徑沒用帳本，兩條路徑證據不能拼成完整保障。
- `gitclaim` 是協調檢查不是原子 claim；判定到推送之間仍有時間窗。它只在 macOS 本機 Git 跑過。帳本列未 `retired` 時重啟一律阻擋；不要人工改列或拿程序不在當退場證據。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 2026-11-09 `python3 -X utf8 tools/verify_bootstrap.py` exit 0，全部檢查通過，含 173 個 v2 契約／索引測試；提交候選另用 `--staged` 驗。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-09 `python3 -X utf8 experiments/v2/vm_probe.py` exit 0（帳本與 channel 綁定版本）：舊反例保留，`guest_broker`、`guest_parent_sigkill` 通過。runner SHA-256 `2e7d8f1be9a08c2ee1608c743a02724461c47cc4d2355dc29b728d94beed7a54`、guest init `3beb1059f912c0dbdabac1791c09b78393c34fb72454937db987aa5cd6d508ec`、工具 `ff9c8ccc0dc791e72d8d071f10b299b07d3b244a7f9e7a809d2d5ccd3384df67`；之後的 gitclaim／release／batch 改動未碰 VM 程式。
- 2026-11-09 `python3 -X utf8 tools/verify_v2.py` exit 0，173 測試、三個預期反例重現、`strict_ready=False`。接線未改，信任重審不適用；無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 崩潰後人工解除要以什麼作為可信真人核准來源，待使用者決定（下一步 1／3）。第 4 項不需決定，可直接續做。既有 v2 實作授權仍有效，P0 未驗收退出。
