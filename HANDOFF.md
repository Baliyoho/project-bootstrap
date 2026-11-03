# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-03 22:46（+08）
- **交棒者**：Codex ／ `DESKTOP-M8MRS05`（完成第二輪複審九項修正與副本遷移）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。
[第二輪複審 R01–R09](project-bootstrap-reaudit-2026-11-03.md) 已完成本輪修正與驗證；報告維持凍結，當下狀態以本快照為準。
使用者要求持續完成工作、避免過早交棒或硬做至上下文壓縮；效率計畫仍未實施。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-03`
- 本機能力：Windows、Python 3.13、Git Bash、PowerShell；驗證 fixture 需沙箱外執行。

## 已完成

- R01／R02：以明列命令形狀辨識 handler 所有權，不明命令回 conflict；同組自訂 handler 的缺省 matcher／組層設定不得被靜默改變。補函式組合、CLI 零寫入及負向變異；修正前完整同步器跑新斷言確實失敗。
- R03：同步器 fresh fetch、核對 origin upstream 與 HEAD 對齊、本機／遠端標記及明確 owner；A5 自身 writer 可寫，批次僅預演。套用前重查 SHA；不以 allow-dirty 豁免資格。
- R03 守門人走真 bare remote 的 A5→同步→B7→B8，涵蓋他人占用、ahead／behind／分岔、離線、無 upstream、本機標記漂移及移除資格檢查的負向變異。
- R04：完整 stdout／stderr 先遮罩再摘要，補 300／200 字元邊界與恢復舊判準的負向測試；只保證已知單一憑證值遮罩。
- R05／R06：inventory active 失效列 failures 並非零退出；README 核心優先序與 skill／協定一致。補混合清單、archived、重複路徑、反向宣告與負向測試。
- R07：B7 先 stage 並檢視清單，再 check_docs --staged；拒絕本次文件／檢查器部分 stage。新增文件、index 壞但工作樹好、程序順序與負向測試均涵蓋。
- R08／R09：機器／工具 trim 後不得空白；連結先去 title 再去角括號。空欄、空白檔名與組合寫法、恢復舊實作均有測試。
- VERSION 與三個受影響範本 source 標記為 2026-11-03；六個維護中專案及兩份全域 skill 已同步並比對。
- 使用者明確授權後，六專案原分支均已提交／push、遠端工作中標記清除；五個 clean，另一個僅留原先兩份使用者文件，雜湊未變且未提交；未合併功能分支。
- 四份通用 verify_state 實例已保留設定人工遷移；兩份專案自訂實作保留。六份協定只更新 B7 摘要，其他規則不變；既有業務驗證與未驗證限制保留並標示證據時段。
- hook／接線未改；信任重審與模型探針不適用。沒有額外模型呼叫，已完結專案未動。

## 未完成／下一步

1. 本輪 R01–R09 無剩餘實作待辦；下一個任務待使用者指定。新 session 仍先 A 模式並讀複審報告，避免把凍結報告當即時進度。
2. POSIX 同步後 mode 保留仍是複審額外觀察，未實機驗證；其他低影響摘要漂移可另案整理，不能把九項結案擴稱所有風險消失。
3. 效率提案尚未採納；不得自行省略現行驗證或實施流程改造。

## 地雷與注意事項

- --write 現在必須單一專案搭配 --owner；先在目標推送 A5 標記。owner 是明確協調證據，不是身分驗證或原子鎖。
- 不明命令形狀須人工比對，不能退回檔名子字串所有權；NOT_CONFIGURED 不代表服務通過。
- 原 review_probe.py／review-results.json 未隨 Git 發布；本輪依報告重建反例，未取得或重跑原始聊天探針。
- 私人專案身分、路徑及完整服務輸出不寫進公開 repo；副本操作備份與完整日誌留在本聊天私人產物。

## 服務查證與期望快照

`python -u -X utf8 tools/verify_bootstrap.py`：固定程式快照完整驗證 exit 0、50 項全過、無 skip；骨架仍 22 檔，11 份本 repo Markdown。
本快照與最後文件改動完成後，提交前重跑本 repo 文件與交接快照檢查；程式與驗證依據不再改動。
六專案最終 check_docs --staged 全 exit 0；兩個自訂服務查證 errors=0 skipped=0，其餘四個 NOT_CONFIGURED（未驗證服務）。
Python 3.8 下限仍是靜態擔保，未實跑其他 OS；沒有跨 OS 或模型遵循驗證。

## 懸置事項（AI 勿自行處理）

- 原子 claim 與並行實驗另案；Antigravity IDE 未解原因不再追查。
- 額外模型探針仍須另行授權且只用訂閱額度；效率流程改造未授權。
