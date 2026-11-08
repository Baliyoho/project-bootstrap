# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-08 21:40（+08）
- **交棒者**：Codex ／ `baliyohodeMini`（F46 文件設定同組情境）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-03`
- 本機能力：macOS 27.2、Python 3.15.2、bash 3.2。Windows／Linux 本輪未驗。現行部署包及程序未切換。

## 已完成

- P0 合成原型保留管道分權、POSIX 工作樹套用、限期票據與簽核、受管單 worker 生命週期、前提切換及 outbox。三個原始繞過反例仍重現；嚴格模式未就緒。細節見 [v2 原型說明](experiments/v2/README.md) 與索引。
- Mac 程序群組探針證明 `setsid` 後代能在 leader 退出後持鎖；Endpoint Security 後代 API 本機缺 entitlement。Virtualization framework 回 `isSupported=true`，尚未建立 guest 或驗 VM stop。
- F46 部分：三項已宣告來源例外逐項印出；來源與產物交接快照 11 種、文件 20 種正反例成對驗。本輪再補 9 種文件設定情境：非 Markdown 已知佔位符、專案自訂過期字串、死連結與各自豁免。來源端同一檢查入口也掃本 repo 受管非 Markdown 檔；負向情境會擋殘留欄位。來源 `--staged` 與產物完整／部分 stage 成對驗，另拒空候選及未追蹤檔。
- F46 本機 bare origin 雙 checkout 接力已成對驗：占用、陳舊接手、釋出、A2.5 到 A5 SHA 變更、開工、任務 push 與交棒；改讀本機快照的負向變異會重現錯誤放行。只驗 Git 與 hook 訊號，不證明模型遵循。
- 這輪只改來源驗證器、v2 索引與本 repo 結構說明；現行 22 檔部署包、skill／hook 副本及 `VERSION` 均未改，無同步債；未呼叫額外模型或真實服務。

## 未完成／下一步

1. **P0 未退出。** Mac 單 worker 禁 fork／spawn 已有合成證據，多程序任意後代仍無退場保障。VM 候選須先做合成 guest，驗 `setsid` 持鎖後代在強制 stop、host 被殺及重啟恢復後的退場證據、共享資料與網路隔離、entitlement 與成本；做不到就維持阻擋。Windows Job Object 尚無 Windows 實測。禁止用舊 PID 或時間推定退場。
2. F46 本機 Git 接力、20 種文件與 9 種文件設定情境已成對驗；仍須核對來源三項例外的替代保障、其他設定組合、跨工具／OS 接手與模型實際遵循。來源沒有專案自訂過期字串設定；本輪是合成設定能力對照，不是任意專案設定驗收。額外模型探針須先得授權。
3. 接可信真人核准、簽署金鑰發行／撤銷與額度來源；票據遺失沒有重新驗身分路徑。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。額外模型探針須另得授權且只用訂閱額度。
4. 鎖定完整 runtime／import 與候選版本、LICENSE、digest，驗 Windows／Mac 架構門檻後再做 P1。F22 常態必讀超過 12,000 字元；完整接棒時間與 token 未量，現行 A4 不省。
5. Windows hook 同步、Mac Codex 真實注入及 R01–R09 邊界獨立複審仍待做；逐 ID 狀態看索引。

## 地雷與注意事項

- 僅合成暫存 fixture。Mac profile 禁 fork／spawn／signal；程序群組可被 `setsid` 脫離，VM 的 `isSupported=true` 不是退場證據。監護被殺、父程序凍結且租期尚未到、整機暫停與任意後代不在回收保證內。
- materializer 只支援 broker 獨占的 POSIX 普通檔案。未知 phase、外部衝突或失效 epoch 保持 pending；不自動覆蓋、清掉或換 request ID。搬機、還原 DB、斷電及多 writer 尚未驗收。
- 票據庫權限須配合 OS 隔離；簽章測試使用一次性金鑰。原檔、票據與合成 Git object 不進本 repo。舊實驗庫若缺新指紋／前提／回收證據，不能自動收編。
- 現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。額外模型、真實部署、遠端保護與合入 main 仍依原授權邊界。

## 服務查證與期望快照

- 2026-11-08 `python3 -X utf8 tools/verify_bootstrap.py` exit 0，58 項全過，含 123 個 v2 測試及 F46 的 20＋9 種文件同組情境；B7 須對最終 staged 快照再驗。
- 本輪未另跑 `tools/verify_v2.py --require-ready`；嚴格模式依三個反例保持未就緒。跨工具／OS 與模型實際遵循未驗。
- 本 repo 無 verify_state.py／check_docs.py，依 AGENTS 使用替代入口；接線未改，信任重審不適用。無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 無新增待決。交棒為上下文管理；既有 v2 實作授權仍有效，P0 未驗收退出。
