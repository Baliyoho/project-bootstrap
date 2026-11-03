# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-03 22:25（+08）
- **交棒者**：Codex ／ `DESKTOP-M8MRS05`（複審首批四項修正）

## 任務目標

逐項修完 [第二輪複審 R01–R09](project-bootstrap-reaudit-2026-11-03.md)，不實施效率計畫。
使用者授權持續修正；不要每修一項就交棒，須在上下文壓縮前保留餘裕收尾，不硬做。
本輪完成 R01、R02、R05、R06；另五項仍未修。報告維持凍結，進度以本快照為準。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Codex CLI` ／ `㊣　26110322｜修複審缺口｜工作中｜交棒1次`，2026-11-03 22:30 (+08) 開工
- **骨架版本**：`2026-11-02.8`
- 本機能力：Windows、Python 3.13、Git Bash、PowerShell；驗證 fixture 需在沙箱外執行。

## 已完成

- R01：handler 改用明列命令形狀辨識所有權；參數提及、echo、同名客製腳本、複合／不明命令回 conflict，不刪除也不補重複接線。兩命令欄均須可確認。
- R02：同組有專案 handler 時，缺省／空字串／萬用／明確 matcher 及其他組層欄位差異均保守拒絕，不改其觸發語意；一致設定可正常合併。
- R01／R02 守門人「同步安全」補函式組合、真 CLI 拒絕且零寫入、兩個負向變異；另以修正前完整同步器跑新斷言，實得 12 處缺口。
- R05：inventory active 目標失效列 FAIL，混合清單納入 failures 並非零退出；archived 正常排除。補一好一壞、archived、全失敗、重複路徑與 CLI 負向變異。
- R06：README 改為 SKILL 核心優先、使用者指示優先；「核心與實例優先序」納入 README，新增三個反向／缺失宣告測試。
- AGENTS 移除「九項尚未修」的過期狀態敘述，保留先讀複審報告及 HANDOFF 狀態入口。
- 僅改本 repo 工具與文件；未動部署包、skill、hook、接線或 VERSION，副本同步與信任重審不適用。

## 未完成／下一步

1. 先跑 A 模式並讀複審報告；接續優先 R03：同步 preflight 與 A1／A5 的 upstream、遠端標記及自身 writer 授權證據相容。不要用 allow-dirty 豁免占用，也不要只放寬本機欄位。
2. R04：verify_state 先對完整輸出遮罩再截斷，補 stdout／stderr 邊界測試；舊 verify_state 是 INSTANCE，遷移需另列證據。
3. R07：B7 的驗證集合與 stage 順序；R08：機器／工具欄 trim 後非空；R09：角括號 destination 與 title 合用。
4. 制度變動仍須改權威部署包、source 標記與必要 VERSION，再安全同步副本；R03 未修前不無範圍 --all --write。
5. POSIX 同步後 mode 保留仍是未實機確認的風險，其他摘要漂移可後續整理；Python 3.8／其他 OS 未實跑。

## 地雷與注意事項

- 原 review_probe.py／review-results.json 未入 Git；本輪依報告重建四項反例，沒有取得或重跑原始探針。
- 命令辨識刻意保守：未列命令形狀先人工比對，不能退回腳本檔名子字串所有權。
- 不把 50 項通過寫成 R03／R04／R07–R09 已修；新增守門檢查須附負向測試。
- 效率計畫仍為提案；六專案前輪收尾證據見原進度報告，本輪沒有重驗真專案或呼叫額外模型。

## 服務查證與期望快照

`python -u -X utf8 tools/verify_bootstrap.py`：本輪程式改完後完整驗證 exit 0、50 項全過、無 skip。
骨架仍 22 檔、11 份本 repo Markdown；「同步安全」「同步範圍與前置檢查」「核心與實例優先序」含本輪反例與負向變異。
本快照填寫後，提交前重跑本 repo 文件與交接快照檢查；程式與驗證依據不再改動。

## 懸置事項（AI 勿自行處理）

- 原子 claim 與並行實驗另案；Antigravity IDE 未解原因不再追查。
- 額外模型探針仍須另行授權且只用訂閱額度；不得把修正授權延伸為效率流程改造。
