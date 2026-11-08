# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-08 14:43（+08）
- **交棒者**：Codex CLI ／ `baliyohodeMini`（檢驗程序群組候選）

## 任務目標

使用者已授權按 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 實作 v2。下一棒直接續作。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點、限制與行動。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立；本輪程序群組候選將以本次交棒 commit 發布）；main 尚未合入 v2。
- **工作中**：`baliyohodeMini` ／ `Codex CLI` ／ `㊣ 26110814｜驗後代退場｜工作中｜交棒0次`，2026-11-08 14:54 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：macOS、Python 3.15.2、bash 3.2、OpenSSH 套件回報 10.5p1。Windows／Linux 本輪未驗。現行部署包及程序未切換。

## 已完成

- [P0 原型](experiments/v2/README.md) 既有內容／效果交易、管道分權、合成工作樹套用、受管生命週期及 outbox 均保留。三個原始繞過反例仍重現。
- `a1d228b`：macOS 單 worker 接合 guardian、supervisor 與 outbox。舊工作作廢、舊請求原 bytes 重送被拒；確認回收及新前提摘要才啟用，只有新結果寫盤。未確認退場、錯摘要、離線收件者、遺失回應均有測試。
- `a3915d6`：guardian wait 後寫本次啟動專屬的私有回收紀錄。重啟明確核對原票據、計畫與檔案身分；四處真 SIGKILL 可恢復 pending 或已生效前提，作廢未完成計算並續送原請求。舊次紀錄不能解鎖新 worker。
- `912af66`：限期票據可由可信合成父程序續期；原定位符保留，舊票據失效，資源、principal 及 outbox 保留。撤銷、遺失、更新交易失敗有負向測試。父程序 SIGSTOP 後，存活 guardian 仍會在本機租期截止回收。
- `a6fc7a8`：合成動作以固定 Ed25519 公鑰驗簽，綁 audience、principal、前提、動作、資源、額度來源、次數與期限；Mac 隔離 worker 經 broker 消耗一次合成額度。錯簽、竄改、重播、收據遺失、舊前提及回滾有測試。
- `c660684`：啟動指紋涵蓋 guardian 腳本與 Python executable；變更後拒絕替換及恢復。v2 JSON 附四項本機執行檔／腳本 SHA-256。
- 本輪新增合成程序群組探針：一般後代在群組 TERM 後釋放檔案鎖；呼叫 `setsid` 的後代在 leader 退場後仍持鎖。移除逃逸行為的負向變異確實失敗。`verify_v2` 單列結果，不將候選接入受管 launcher；程序群組不足以證明任意後代退場。
- F50 需求與假 adapter 契約保留；App 本輪實際改名時將全形空格正規化為半形，尚無真實事件自動化。

## 未完成／下一步

1. **P0 未退出。** Mac 程序群組候選已由逃逸反例否決；尋找可限制或追蹤任意後代、且在 guardian 被殺或失聯後仍可核對退場的 Mac 機制。Windows Job Object 是文件候選，尚無 Windows 實測。先用合成 fixture 驗退場與失敗，證據不足維持阻擋；禁止用舊 PID 或時間推定退場。
2. 接可信真人核准、簽署金鑰發行／撤銷與額度來源。票據續期仍由合成父程序授權；遺失票據沒有重新驗身分路徑。接真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。模型探針須另得授權且只用訂閱額度。
3. 整理完整 runtime／import 與候選版本、LICENSE、digest，驗 Windows／Mac 架構門檻後再做 P1。F22 常態必讀超過 12,000 字元；完整接棒時間與 token 未量，現行 A4 不省。
4. Windows hook 同步、Mac Codex 真實注入與 R01–R09 邊界獨立複審維持待做；逐 ID 狀態看索引。

## 地雷與注意事項

- 僅合成暫存 fixture。Mac profile 禁 fork／spawn／signal；程序群組可被 `setsid` 脫離，不能據 leader 退場解除多程序阻擋。監護被殺、父程序凍結且租期尚未到、整機暫停及任意後代都不在回收保證內。
- materializer 只支援 broker 獨占的 POSIX 普通檔案。未知 phase、外部衝突或失效 epoch 保持 pending；不自動覆蓋、清掉或換 request ID。搬機、還原 DB、斷電及多 writer 尚未驗收。
- 票據庫權限須配合 OS 隔離；簽章測試使用一次性金鑰。原檔、票據與合成 Git object 不進本 repo。舊實驗庫若缺新指紋／前提／回收證據，不能自動收編。
- 現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。額外模型、真實部署、遠端保護與合入 main 仍依原授權邊界。

## 服務查證與期望快照

- 2026-11-08 `python3 -X utf8 tools/verify_bootstrap.py` exit 0，52 項全過，含 119 個 v2 測試；B7 須對最終 staged 快照再驗。
- 同日 `python3 -X utf8 tools/verify_v2.py --require-ready --json` 實測 exit 2，harness_passed=true、strict_ready=false，119 測試零失敗／skip；tree_probe=反例重現（一般後代退場、逃逸後代未退場）。四份本機指紋可讀。JSON 可重跑；不用聊天附件。
- 本 repo 無 verify_state.py／check_docs.py，依 AGENTS 使用替代入口。接線未改，信任重審不適用。無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 無新增待決。交棒為上下文管理；既有 v2 實作授權仍有效，P0 未驗收退出。
