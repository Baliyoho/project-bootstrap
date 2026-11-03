# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-03 10:34（+08）
- **交棒者**：Codex ／ `DESKTOP-M8MRS05`（六個維護中專案的制度收尾）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。
查核約定範圍已完成：15 條修正＋F12 協調邊界；原子 claim 另案。
本輪四項收尾均完成：六專案文件修正、協定遷移、Codex hook 信任與注入驗收、同步變更發布。
條目證據以 [project-bootstrap-audit-progress.md](project-bootstrap-audit-progress.md) 為準。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-02.8`
- 本機能力：Windows、Python 3.13、Git Bash、PowerShell；六專案 fetch／開工與收尾 push 成功。

## 已完成

- 六專案接棒均與各自 upstream 對齊、無占用；既有制度 dirty 已與權威版核對。
- 修正三份快照：兩份「待續分支」改成標準欄位、一份合併重複「已完成」章節；六份文件檢查均 exit 0。
- 六份舊協定人工遷移核心優先序、override、協調邊界與最終文件驗證；保留專案限制、理由與業務待辦。
- 前輪同步的 skill／hook／接線／文件檢查器已明確 stage、提交並推送原分支；功能分支未合併。
- 六專案 Windows 兩個 hook 原始命令從 tools 子目錄共 12 次實跑 exit 0；已透過正常互動介面儲存兩個 hook 的信任。
- 使用者明確授權後，六專案各一則 ChatGPT 訂閱最小探針均回 `HOOK_PRESENT`、exit 0、工具呼叫 0；新 session 的開場輸出進入 context。
- 六專案遠端標記均已清；五個 clean，另一個僅留使用者明示保留的兩份文件，雜湊未變、未提交。
- 未改業務程式、資料、NAS／路由器設定；只呼叫獲准的六個最小訂閱探針；部署、模型選型與 schema 例行檢查不適用。

## 未完成／下一步

- 本輪四項制度收尾已完成；後續依使用者指定的新任務。
- 原子 claim 與兩 clone／同工作樹並行實驗，依使用者 2026-11-02 決定留待另案。

## 地雷與注意事項

- 工作中標記與 preflight 都不是並行鎖；同一工作樹只允許一個 writer，不自動奪權。
- 不無範圍地用 `--all --write`；私人 inventory 與各專案身分不寫進公開 repo。
- `--allow-dirty`／逐檔 `--accept-drift` 只適用人工檢視的單一目標；不能略過占用。
- 漂移比對依權威 Git 歷史；缺歷史時保守拒絕。AI push 提醒仍是有限覆蓋，不是發布保證。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、50 項全過、無 skip。骨架仍 22 檔；文件檢查由此工具涵蓋。
六專案最終 `check_docs.py` 全 exit 0；兩個既有服務驗證 errors=0 skipped=0，四個 NOT_CONFIGURED（非服務實測）。
Windows hook 原始命令 12 次均 exit 0；Codex CLI 0.166.0 正常信任流程＋新 session 訂閱探針 6／6 通過。沒有使用信任 bypass，也未直接修改信任資料。
Python 3.8 下限仍是靜態擔保；本機部署生命週期不代表跨 OS／外部工具注入實測。

## 懸置事項（AI 勿自行處理）

- 各專案業務懸置事項仍在各自 repo；本輪授權不延伸至額外模型實跑或業務改動。
- 原子 claim 留待另案；Antigravity IDE hook 原因仍未知、不再追查。
