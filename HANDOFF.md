# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-07（+08；工作中安全點，未交棒）
- **交棒者**：Codex CLI ／ `baliyohodeMini`（本 session 續作限期重連資格與請求保存；尚未釋出 writer）

## 任務目標

使用者已授權按 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 重做 v2；下一棒直接續作，不重新徵詢是否開始。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。移交來源 `fdc0bbd:HANDOFF.md`；本檔只留停點與行動，索引不可讀就停止判定，不恢復舊摘要權威。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立；已驗證實作安全點 `119fcd6`）；勿重新從 main 開始。
- **工作中**：`baliyohodeMini` ／ `Codex CLI` ／ `㊣ 26110714｜補重連資格｜工作中｜交棒0次`，2026-11-07 14:23 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：macOS、Python 3.15.2、bash 3.2；未驗 Windows／Linux。未改 main、部署包、skill、hook、接線或 VERSION。

## 已完成

- F50 必要需求、51 ID 對照與狀態移交；session 狀態機及假 adapter 契約，尚未接真實事件自動化。
- [P0 原型](experiments/v2/README.md)：內容／事件交易、授權範圍、epoch／通知／ACK、執行中合成子程序中止與上下文替換。
- parent-only broker：管道綁身分、無管理 RPC、資源與請求序號限制；受隔離 Mac 合成 agent 正常動作成功，冒名／自行授權／直接寫入被拒。
- 新增 POSIX materializer：prepared→暫存／fsync→replace→applied；保留 mode，拒絕路徑／連結／別名風險及外部內容衝突。同資源前一事件未完成時阻止新寫入。
- 收據與內容／合成效果同交易；可信 parent 可輪替 capability 恢復 principal，重連不重做原動作。真子程序四個中斷點、收據／commit 失敗及回應遺失已有反例。
- 恢復覆核修正三處：重送寫盤須符合重連後權限；私有庫綁定 root 身分／完整映射；恢復已 replace 內容仍須目錄 fsync 才記 applied。新增五項測試，三個主反例已見修前失敗／修後通過。
- 新增 launcher 資格層：parent 產生 principal、私有票據重連、資源／有效期／撤銷，broker 受理及恢復寫盤前重查；Mac 合成 agent 探針已採用，source 仍非人類驗證。
- 新增 parent 請求 outbox：送出前保存原始 bytes、單一 pending、缺漏／不一致停止；兩個真子程序終止點與回應遺失恢復只執行一筆效果。共 14 個新增測試，含移除守門的負向對照。
- 原一鍵入口包含 P0 回歸，JSON 可重跑且附輸入 digest／環境／時間。三個原始繞過反例照留，strict_ready 仍為 false。

## 未完成／下一步

1. **P0 尚未退出；直接續作正式 launcher 的啟動生命週期**：先讀 `launcher.py`、`broker_fixture.py`、`supervisor.py`；整合固定啟動設定、舊程序確認退場、票據保管及過期後續作，不能只輪替 capability 就宣稱舊 child 已停止。
2. 補人類授權來源驗證與真實 client adapter。parent fixture 不是已驗收的人類服務；有效期與 outbox 已有合成反例，尚無票據更新／遺失、資料裁剪或跨機恢復程序。外部付費／破壞性動作不享有 SQLite 合成效果的 exactly-once 保證。
3. 對真實可控執行介面接 supervisor，補跨機推送、失聯與恢復；模型／桌面工具實際停止和上下文重建需另驗，不拿 ACK 冒充理解。
4. 鎖定實際採用元件版本／LICENSE／digest；驗 Windows／Mac 架構門檻，之後才做 P1 來源／測試模組化與短入口。
5. F22 常態必讀仍約 4.4 萬字元、超過 12,000；完整接棒時間及 token 未量。要做證據依賴／失效與分層後才能省 A4，不能靠原型綠燈略過。
6. 保留舊限制：Windows hook 同步、Mac Codex 真實注入、R01–R09 邊界獨立複審待做；F41 七缺口屬想要。逐 ID 達成狀態看索引。

## 地雷與注意事項

- 僅合成暫存 fixture，未遷移真實專案。materializer 限 broker 獨占的 POSIX 普通檔案；不支援建目錄／刪除／整批原子更新，不是與任意外部 writer 競爭的 CAS。
- 程序終止測試不是斷電測試。未知 phase、內容／mode 衝突、失效 epoch 保持 pending，不自動覆蓋或清掉；需明確處理，不能換 request ID 繞過。
- 已有事件但缺 root／映射綁定的舊實驗庫拒絕自動收編；搬機／換 root／變更映射尚無遷移程序，不宣稱跨機恢復完成。
- 授權時間依 parent 時鐘；只拒絕低於已提交 watermark 的倒退，非抗調時／DB 還原保證。低層 Lab 無期限授權及 Broker.attach 保留給內部 fixture，不是正式人類入口。
- `sandbox-exec` 已 deprecated，只作 OS 機制探針；未做逃逸審查或正式工具接線。原文、capability 與合成 Git object 不進本 repo。
- 不得擅自外部部署、付費／額外模型探針、改遠端保護或 merge main；額外模型先授權且只用訂閱額度。
- 現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 本輪 `python3 -X utf8 tools/verify_bootstrap.py`：exit 0，52 項通過、無 skip；含 71 個 v2 測試（非需求逐項驗收）。本機 HTTP 探針在 sandbox 被拒，經允許於沙箱外重跑。安全點提交前再以最終 stage 同入口確認。
- 本輪 `python3 -X utf8 tools/verify_v2.py --require-ready --json`：exit 2（2026-11-07）；harness_passed=true、strict_ready=false、71 測試無失敗／skip；Mac 管道 11 次請求成功。沙箱內 loopback bind 被拒，經允許於沙箱外重跑；不把權限錯誤當預期 exit 2。
- JSON 為暫存證據，不假設下一棒可取得；以相同命令重跑，需量完整舊驗證器再加 `--baseline`。F50 本次真正改名成功，但工具回傳將全形空格正規化為半形，格式差異已揭露。
- 無 verify_state.py／check_docs.py，依 AGENTS 用替代入口；接線未改，信任重審不適用。未呼叫額外模型、未安裝候選、未部署其他專案。

## 懸置事項（AI 勿自行處理）

- 無需再確認是否做 v2；本次交棒只為上下文管理，不是取消任務，也不是宣稱 P0／v2 已完成。
