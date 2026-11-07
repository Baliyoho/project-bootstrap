# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-07 14:20（+08）
- **交棒者**：Codex CLI ／ `baliyohodeMini`（P0 恢復邊界覆核；使用者授權依上下文餘量選擇交棒）

## 任務目標

使用者已授權按 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 重做 v2；下一棒直接續作，不重新徵詢是否開始。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。移交來源 `fdc0bbd:HANDOFF.md`；本檔只留停點與行動，索引不可讀就停止判定，不恢復舊摘要權威。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立；已驗證實作安全點 `119fcd6`）；勿重新從 main 開始。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-03`
- 本機能力：macOS、Python 3.15.2、bash 3.2；未驗 Windows／Linux。未改 main、部署包、skill、hook、接線或 VERSION。

## 已完成

- F50 必要需求、51 ID 對照與狀態移交；session 狀態機及假 adapter 契約，尚未接真實事件自動化。
- [P0 原型](experiments/v2/README.md)：內容／事件交易、授權範圍、epoch／通知／ACK、執行中合成子程序中止與上下文替換。
- parent-only broker：管道綁身分、無管理 RPC、資源與請求序號限制；受隔離 Mac 合成 agent 正常動作成功，冒名／自行授權／直接寫入被拒。
- 新增 POSIX materializer：prepared→暫存／fsync→replace→applied；保留 mode，拒絕路徑／連結／別名風險及外部內容衝突。同資源前一事件未完成時阻止新寫入。
- 收據與內容／合成效果同交易；可信 parent 可輪替 capability 恢復 principal，重連不重做原動作。真子程序四個中斷點、收據／commit 失敗及回應遺失已有反例。
- 恢復覆核修正三處：重送寫盤須符合重連後權限；私有庫綁定 root 身分／完整映射；恢復已 replace 內容仍須目錄 fsync 才記 applied。新增五項測試，三個主反例已見修前失敗／修後通過。
- 原一鍵入口包含 P0 回歸，JSON 可重跑且附輸入 digest／環境／時間。三個原始繞過反例照留，strict_ready 仍為 false。

## 未完成／下一步

1. **P0 尚未退出；下一棒直接續作可信 launcher 與重連資格**：先讀 `broker.py` 的 attach／dispatch、`contracts.py` 的 resume／grant 與 `broker_fixture.py` 的啟動邊界；定義假造 principal、過期授權、重連丟失原請求的反例，再實作。
2. 補正式可信 launcher、人類授權簽發／有效期與 client 請求保存；parent fixture 不是已驗收的人類服務。受理收據不等於寫盤完成；外部付費／破壞性動作不享有 SQLite 合成效果的 exactly-once 保證。本輪覆核不代表完整安全審查。
3. 對真實可控執行介面接 supervisor，補跨機推送、失聯與恢復；模型／桌面工具實際停止和上下文重建需另驗，不拿 ACK 冒充理解。
4. 鎖定實際採用元件版本／LICENSE／digest；驗 Windows／Mac 架構門檻，之後才做 P1 來源／測試模組化與短入口。
5. F22 常態必讀仍約 4.4 萬字元、超過 12,000；完整接棒時間及 token 未量。要做證據依賴／失效與分層後才能省 A4，不能靠原型綠燈略過。
6. 保留舊限制：Windows hook 同步、Mac Codex 真實注入、R01–R09 邊界獨立複審待做；F41 七缺口屬想要。逐 ID 達成狀態看索引。

## 地雷與注意事項

- 僅合成暫存 fixture，未遷移真實專案。materializer 限 broker 獨占的 POSIX 普通檔案；不支援建目錄／刪除／整批原子更新，不是與任意外部 writer 競爭的 CAS。
- 程序終止測試不是斷電測試。未知 phase、內容／mode 衝突、失效 epoch 保持 pending，不自動覆蓋或清掉；需明確處理，不能換 request ID 繞過。
- 已有事件但缺 root／映射綁定的舊實驗庫拒絕自動收編；搬機／換 root／變更映射尚無遷移程序，不宣稱跨機恢復完成。
- `sandbox-exec` 已 deprecated，只作 OS 機制探針；未做逃逸審查或正式工具接線。原文、capability 與合成 Git object 不進本 repo。
- 不得擅自外部部署、付費／額外模型探針、改遠端保護或 merge main；額外模型先授權且只用訂閱額度。
- 現行 A／B／C 照跑；原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 本輪 `python3 -X utf8 tools/verify_bootstrap.py`：exit 0，52 項通過、無 skip；其中 P0 執行 57 個 v2 測試（不是需求 ID 的逐項驗收）。交棒最終 stage 後以同入口驗證。
- 本輪 `python3 -X utf8 tools/verify_v2.py --require-ready --json` 實測 exit 2（2026-11-07 14:18 +08）：harness_passed=true、strict_ready=false、57 測試無失敗／skip。沙箱內 loopback bind 被拒，經允許於沙箱外重跑取得結果；不把權限錯誤當預期 exit 2。
- JSON 為暫存證據，不假設下一棒可取得；以相同命令重跑，需量完整舊驗證器再加 `--baseline`。F50 本次真正改名成功，但工具回傳將全形空格正規化為半形，格式差異已揭露。
- 無 verify_state.py／check_docs.py，依 AGENTS 用替代入口；接線未改，信任重審不適用。未呼叫額外模型、未安裝候選、未部署其他專案。

## 懸置事項（AI 勿自行處理）

- 無需再確認是否做 v2；本次交棒只為上下文管理，不是取消任務，也不是宣稱 P0／v2 已完成。
