# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-09 10:27（+08）
- **交棒者**：Codex ／ `baliyohodeMini`（固定受管工具進無共享 guest）

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
- Mac VM 舊共享 scratch 反例與退場探針仍通過：VM stop、host runner SIGKILL、控制管道 EOF、兩 VM 鎖不協調、父程序 SIGKILL 後 fail closed。固定 Alpine 3.24.4 aarch64 netboot digest 與雙向 virtio console 保留；正式工作樹不掛進 VM。
- 固定合成 `vm_managed_worker.sh` 隨 initramfs 進入**無共享目錄** guest；一次載入 epoch／factor，後續由 guest 格式化受限 `note` 寫入請求，parent 先保存原始 bytes 再用獨立 principal 送 broker。真 VM 兩個 epoch 的寫入 `10`／`21` 及事件關聯通過；pending 後舊 guest 寫入被拒、未完成操作失效，舊 VM stop 後才載入新上下文與 application ACK。新路徑沒有 host worker，也沒有把票據／管理 RPC 交進 guest。離線負向測試補錯 context ACK 與 base。
- F46 既有本機同組情境維持：來源例外逐項可見，交接快照 11 種、文件 20 種、文件設定 9 種正反例；本機 bare origin 雙 checkout 接力覆蓋占用、開工 SHA 變更、任務 push 與釋出。只驗 Git／hook 訊號，不證明模型遵循。
- 本輪只改 v2 隔離原型、索引、原型說明及結構摘要；現行 22 檔部署包、skill／hook 副本及 `VERSION` 未改，無同步債；未呼叫額外模型或真實服務。

## 未完成／下一步

1. **P0 未退出。** 無共享路徑只涵蓋固定 shell 工具與 `note` 寫入，parent 提供合成輸入並握有票據／channel；不是通用工具或模型。下一步將這條路徑的 VM 身分、啟停與退場證據持久化，供重啟核對；再驗管道與 VM 生存期綁定、已寫效果冪等／回滾及跨 epoch 原子歸因。舊 `managed_vm_switch` 仍借 host worker 並掛可寫 scratch；兩 VM 的 virtiofs `flock` 不協調 writer。
2. 父程序死於 VM 退場證據持久化前時，現設計安全地阻擋，但無可信自動解除路徑。設計可重啟核對的 VM 身分與退場證據，驗 host／hypervisor 故障、長操作及成本；禁止用舊 PID、時間或 guest 自報日誌推定。舊單鍵 VM 實驗庫不自動遷移；Windows Job Object 尚無 Windows 實測。
3. F46 仍須核對來源三項例外的替代保障、其他設定組合、跨工具／OS 接手與模型實際遵循。來源沒有專案自訂過期字串設定；合成設定對照不是任意專案驗收。額外模型探針須先得授權。
4. 接可信真人核准、簽署金鑰發行／撤銷與額度來源；票據遺失沒有重新驗身分路徑。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。額外模型探針須另得授權且只用訂閱額度。
5. 鎖定完整 runtime／import、候選版本、LICENSE、digest，驗 Windows／Mac 架構門檻後再做 P1。F22 常態必讀超過 12,000 字元；完整接棒時間與 token 未量，現行 A4 不省。Windows hook 同步、Mac Codex 真實注入及 R01–R09 邊界獨立複審仍待做。

## 地雷與注意事項

- 僅合成暫存 fixture。guest principal 是 parent 發的管道授權標籤，非防同 UID host 偽造的 VM 身分證明；不能把舊 host worker 路徑與無共享 guest 工具路徑拼成完整覆寫歸因。新 guest 工具是固定 shell 腳本，VM 退場證據尚未持久化。guest `/dev/hvc1` 須在已開啟 fd 上設 `raw -echo`。其餘反例的 VM stop 回呼與 1 秒 heartbeat 穩定不是 host OS／hypervisor 崩潰證據。監護被殺、整機暫停、父程序凍結且租期尚未到仍未驗。
- VM 退場資料庫列若未標 `retired`，resume 會 fail closed；不要人工改列或拿程序不在當退場證據。materializer 只支援 broker 獨占的 POSIX 普通檔案；未知 phase、外部衝突或失效 epoch 保持 pending，不自動覆蓋或換 request ID。搬機、還原 DB、斷電及多 writer 尚未驗。
- 票據庫權限須配合 OS 隔離；簽章測試使用一次性金鑰。原檔、票據與合成 Git object 不進本 repo。舊實驗庫若缺新指紋／前提／回收證據，不能自動收編。
- 現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。額外模型、真實部署、遠端保護與合入 main 仍依原授權邊界。

## 服務查證與期望快照

- 2026-11-09 `python3 -X utf8 tools/verify_bootstrap.py` exit 0，全部檢查通過，含 139 個 v2 契約／索引測試；提交候選另用 `--staged` 驗。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-09 `python3 -X utf8 experiments/v2/vm_probe.py` exit 0：舊兩 epoch／VM 退場與鎖反例保留；無共享 guest 固定工具完成兩 epoch 原始請求、舊請求拒絕及新寫入。固定映像 digest 由探針列出；runner SHA-256 `2e7d8f1be9a08c2ee1608c743a02724461c47cc4d2355dc29b728d94beed7a54`，guest init `3beb1059f912c0dbdabac1791c09b78393c34fb72454937db987aa5cd6d508ec`；未測真實工具或 host OS 崩潰。
- 2026-11-09 `python3 -X utf8 tools/verify_v2.py` exit 0，139 測試通過、三個預期反例仍重現、`strict_ready=False`；定向 VM 離線 12 測試 exit 0。未另跑 `--require-ready`（預期 exit 2）。接線未改，信任重審不適用；無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 無新增待決。交棒為上下文管理；既有 v2 實作授權仍有效，P0 未驗收退出。
