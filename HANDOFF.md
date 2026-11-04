# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-03 23:02（+08）
- **交棒者**：Codex ／ `DESKTOP-M8MRS05`（完成同步 mode 修正、POSIX 實驗與結構摘要整理）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。
[第二輪複審](project-bootstrap-reaudit-2026-11-03.md) 是凍結快照，R01–R09 已修；額外 mode 風險及本 repo／生成 ARCHITECT 摘要漂移也已處理。
使用者要求成批完成待辦，約上下文 70% 時評估交棒；若工作已完成則在安全點收尾，不為填滿窗口擴張範圍。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Codex CLI` ／ `㊣　26110409｜規劃檔案架構｜工作中｜交棒0次`，2026-11-04 10:03 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：Windows、Python 3.13、Git Bash、PowerShell；驗證 fixture 需沙箱外執行。另用 WSL Linux 隔離 root、Python 3.12 實測 mode。

## 已完成

- R01／R02：明列命令形狀辨識 handler；不明命令 conflict；同組自訂 handler 的缺省 matcher／組層設定不得靜默改變，含 CLI 零寫入與負向變異。
- R03：同步 fresh fetch、origin upstream／HEAD 對齊、本機／遠端標記與明確 owner；A5 自身 writer 可寫，批次只預演；套用前重查 SHA。真 bare remote 涵蓋 A5→同步→B7→B8 與拒絕情境。
- R04：完整 stdout／stderr 先遮罩再摘要，含截斷邊界負向測試；只保證已知單一憑證值遮罩。
- R05／R06：active inventory 失效非零退出；README 核心優先序一致，含負向測試。
- R07–R09：B7 先 stage 再 --staged 檢查，拒絕部分 stage；機器／工具 trim 後非空；連結先去 title 再去角括號，均有行為與負向測試。
- 前輪六個維護專案及兩份全域 skill 已同步；六專案原分支已 commit／push 並釋出標記。四份通用 verify_state 人工遷移、兩份自訂保留。該輪五個 clean，另一個保留兩份使用者文件；這輪未重新驗收私人專案。
- 同步原子替換前 copymode，保留原檔 mode；複製失敗先停止、原檔不變，新依賴照常建立。
- 新「同步升級 mode」守門人：Windows 驗呼叫／錯誤契約；POSIX 驗 0755／0640、Git 無 mode diff、原始 ag-wrap.sh 直接執行；移除 copymode 的變異必須失敗。
- WSL Linux 原生檔案系統實驗 exit 0；舊行為變異確實觸發 mode 改變、Git mode diff、wrapper 拒絕執行、0640 丟失等六個反例。
- 本 repo 與生成 ARCHITECT 改為 Claude import／Gemini 文字指標；README prompt 摘要改收工／開工。新增「結構摘要一致性」與三個負向測試，骨架仍 22 檔。
- 只改同步工具、驗證器、ARCHITECT 範本與本 repo 說明；skill／hook／接線沒變，VERSION 與 source 標記不跳。ARCHITECT 是專案實例，不自動覆蓋既有專案。

## 未完成／下一步

1. 本輪已授權實作待辦均完成，下一個任務待使用者指定。新 session 仍先 A 模式並讀複審報告；不要把凍結報告當即時待辦。
2. 效率提案尚未採納，不自行省略現行驗證或實施流程改造。

## 地雷與注意事項

- --write 必須單一專案搭配 --owner，先推 A5 標記；owner 是協調證據，不是身分驗證或原子鎖。
- 不明命令形狀須人工比對，不能退回檔名子字串所有權；NOT_CONFIGURED 不代表服務通過。
- 原 review_probe.py／review-results.json 未隨 Git 發布；本輪未取得或重跑原始聊天探針。
- 私人專案路徑與完整服務輸出不進公開 repo。POSIX 臨時 root／探針留本機私人產物；可在 POSIX 呼叫驗證器 step_sync_mode 重做同一測試，不假設臨時產物可跨機器取得。

## 服務查證與期望快照

`python -u -X utf8 tools/verify_bootstrap.py`：本輪完整驗證 exit 0、52 項全過、無 skip；骨架 22 檔，本 repo Markdown 11 份。
Linux 原生 mode fixture：Python 3.12／Alpine 隔離 root，step_sync_mode exit 0；包含原始 wrapper 執行與負向變異，不是整套跨 OS 驗證。
B6 更新後本 repo 文件／交接快照／結構摘要／行末檢查 exit 0；index 與工作樹一致，程式與驗證依據不再變動。
前輪六專案 check_docs --staged 全 exit 0；兩個自訂服務 errors=0 skipped=0，其餘四個 NOT_CONFIGURED；這輪未呼叫業務服務。
Python 3.8 下限仍為靜態擔保；沒有 macOS、完整 Linux suite 或模型遵循驗證。hook／接線未改，信任重審與額外模型探針不適用。

## 懸置事項（AI 勿自行處理）

- 原子 claim 與並行實驗另案；Antigravity IDE 未解原因不再追查。
- 額外模型探針須另行授權且只用訂閱額度；效率流程改造未授權。
