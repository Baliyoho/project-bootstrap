# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-08 09:30（+08；中途安全點，未交棒）
- **交棒者**：Codex CLI ／ `baliyohodeMini`（監護回收與單程序隔離邊界；本 session 持續工作中）

## 任務目標

使用者已授權按 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 重做 v2；下一棒直接續作，不重新徵詢是否開始。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。移交來源 `fdc0bbd:HANDOFF.md`；本檔只留停點與行動，索引不可讀就停止判定，不恢復舊摘要權威。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立；前次實作安全點 `f0e11cc`，本次安全點見 Git HEAD）；main 尚未合入 v2，勿重新從 main 開始。
- **工作中**：`baliyohodeMini` ／ `Codex CLI` ／ `㊣　26110721｜續作程序控制｜工作中｜交棒0次`，2026-11-07 21:44 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：macOS、Python 3.15.2、bash 3.2；未驗 Windows／Linux。未改 main、部署包、skill、hook、接線或 VERSION。

## 已完成

- F50 必要需求、51 ID 對照與狀態移交；session 狀態機及假 adapter 契約，尚未接真實事件自動化。
- [P0 原型](experiments/v2/README.md)：內容／事件交易、授權範圍、epoch／通知／ACK、執行中合成子程序中止與上下文替換。
- parent-only broker：管道身分、資源／序號限制、無管理 RPC；收據與內容／合成效果同交易。Mac 合成 agent 正常操作成功，冒名／自行授權／直接寫入被拒。
- POSIX materializer：prepared→暫存／fsync→replace→applied，保留 mode、拒絕路徑／連結／別名／外部衝突；root／映射持久綁定，恢復重查資源資格及目錄 fsync。四個真子程序中斷點與交易失敗可重跑。
- `496e489`：launcher 資格層由 parent 產生 principal、私有票據重連、限期資源資格／撤銷；parent outbox 送出前保存原始 bytes，缺漏／不一致停止。兩個真子程序終止點與遺失回應恢復不重做合成效果，新增 14 個測試。
- `f0e11cc`：固定啟動計畫與持久程序狀態；舊直接 child wait 退場後才發新管道，未解 parent 重啟拒絕替換。POSIX 票據庫拒絕權限／連結／FIFO 異常；Mac 管道已接入，閒置資格失效會結束 transport。新增 14 個測試，含移除停止檢查後兩 child 同時存活的負向對照。
- 本次：新增可信 guardian，parent 生命管道 EOF 後回收直接 worker，私有回收證據到達才記 stopped；Mac fixture 禁 fork／spawn／signal。新增 9 個測試，含真 parent SIGKILL、移除監護／OS 防護、監護被殺、未隔離後代存活、FD 與無關程序保護。
- 原一鍵入口包含 P0 回歸，JSON 可重跑且附輸入 digest／環境／時間。三個原始繞過反例照留，strict_ready 仍為 false。

## 未完成／下一步

1. **P0 尚未退出；直接續作同一執行面的接合**：先讀 `guardian.py`、`lifecycle.py`、`broker_fixture.py` 與 `supervisor.py`，將 outbox、受管生命週期及前提切換接在同一單程序 fixture。不得把禁 fork 的合成介面外推成可執行一般 shell 的多程序工具；程序樹容器需另驗。
2. 補人類授權來源、票據更新／遺失、過期後續作及未解狀態的明確恢復。parent 被殺的直接 worker 可由存活 guardian 回收，但重啟仍不憑 PID／時間清狀態；guardian 被殺、parent 凍結、一般後代回收未解。parent fixture 非人類服務；runtime/import manifest、資料裁剪、跨機恢復與外部效果冪等仍缺。
3. 對真實可控執行介面接 supervisor，補跨機推送、失聯與恢復；模型／桌面工具實際停止和上下文重建需另驗，不拿 ACK 冒充理解。
4. 鎖定實際採用元件版本／LICENSE／digest；驗 Windows／Mac 架構門檻，之後才做 P1 來源／測試模組化與短入口。
5. F22 常態必讀仍約 4.4 萬字元、超過 12,000；完整接棒時間及 token 未量。要做證據依賴／失效與分層後才能省 A4，不能靠原型綠燈略過。
6. 保留舊限制：Windows hook 同步、Mac Codex 真實注入、R01–R09 邊界獨立複審待做；F41 七缺口屬想要。逐 ID 達成狀態看索引。

## 地雷與注意事項

- 僅合成暫存 fixture，未遷移真實專案。materializer 限 broker 獨占的 POSIX 普通檔案；不支援建目錄／刪除／整批原子更新，不是與任意外部 writer 競爭的 CAS。
- 程序終止測試不是斷電測試。未知 phase、內容／mode 衝突、失效 epoch 保持 pending，不自動覆蓋或清掉；需明確處理，不能換 request ID 繞過。
- 已有事件但缺 root／映射綁定的舊實驗庫拒絕自動收編；搬機／換 root／變更映射尚無遷移程序，不宣稱跨機恢復完成。
- 授權時間依 parent 時鐘；只拒絕低於已提交 watermark 的倒退，非抗調時／DB 還原保證。低層 Lab 無期限授權及 Broker.attach 保留給內部 fixture，不是正式人類入口。
- 票據庫 0700／0600 不是同 UID 隔離；需 OS profile 保護。固定 argv／入口 executable／cwd 綁定不涵蓋所有 import 與 runtime；guardian 原碼與 runtime 仍由可信 parent 保護。未隔離後代在直接 worker stopped 後仍可存活，已有反例；Windows、guardian 失效後回收未驗收。
- `sandbox-exec` 已 deprecated，只作 OS 機制探針；未做逃逸審查或正式工具接線。原文、capability 與合成 Git object 不進本 repo。
- 不得擅自外部部署、付費／額外模型探針、改遠端保護或 merge main；額外模型先授權且只用訂閱額度。
- 現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 本輪 `python3 -X utf8 tools/verify_bootstrap.py`：exit 0，52 項全過、無 skip；內含 94 個 v2 測試（2026-11-08）。中途安全點最終 stage 後仍用此入口驗證；本機 HTTP／隔離探針經允許於沙箱外執行。
- 本輪 `python3 -X utf8 tools/verify_v2.py --require-ready --json`：實測 exit 2（2026-11-08）；harness_passed=true、strict_ready=false、94 測試無失敗／skip，Mac 管道 11 次請求成功。一般 sandbox 拒絕 loopback 時經允許重跑，不把環境錯誤當預期 exit 2。
- JSON 為暫存證據，不假設下一棒可取得；以相同命令重跑，需量完整舊驗證器再加 `--baseline`。F50 本次真正改名成功，但工具回傳將全形空格正規化為半形，格式差異已揭露。
- 無 verify_state.py／check_docs.py，依 AGENTS 用替代入口；接線未改，信任重審不適用。未呼叫額外模型、未安裝候選、未部署其他專案。

## 懸置事項（AI 勿自行處理）

- 無需再確認是否做 v2；本次是 C 模式安全點，保留本 session owner，未交棒、未宣稱 P0／v2 已完成。
