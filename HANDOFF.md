# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 22:28（+08）
- **交棒者**：Codex ／ `DESKTOP-M8MRS05`（續修 F10／F12／F13／F16）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。
查核 16 條已完成本輪約定範圍：15 條修正＋F12 協調邊界；原子 claim 依使用者決定另案。
細節與證據以 [project-bootstrap-audit-progress.md](project-bootstrap-audit-progress.md) 為準。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-02.8`
- 本機能力：Windows、Python 3.13、Git Bash、PowerShell；本輪 fetch／開工 push／F10 安全點 push 成功。

## 已完成

- F10：同步核心優先、override 範圍與 MIGRATE 提示；舊部署包實跑抓到 14 處缺失。
- F12：接力協調邊界、觀測 SHA、禁止到期奪權與失敗合併；8 個文字負向測試。
- F13：root／exclude／私人 inventory、Git 辨識 worktree、dirty／占用／客製漂移 preflight。
- F16：自訂 ignore 進 fence、首 commit 前本機驗收；local bare 發布與 clone 驗 100755／直接執行。
- 六個維護中專案與兩份全域 skill 已同步 .8 並比對；文件檢查三個 exit 0、三個既有問題 exit 2。
- 接線未改；重新審核不適用。未呼叫模型探針、未建立外部測試 repo。

## 未完成／下一步

1. 原子 claim 與兩 clone／同工作樹並行實驗留待另案；使用者 2026-11-02 已明確選擇本輪只做邊界文件。
2. 六個專案同步變更各自在自己的 session 收尾，不在骨架 session 代提交。
3. 六個專案舊協定須在各自專案人工遷移；工具印 MIGRATE，新 skill 核心優先，不覆蓋實例。
4. 兩個專案缺「待續分支」、一個有重複「已完成」章節，既有三個 exit 2 須在各專案處理。
5. 先前改過接線的專案仍須在 Codex 互動模式審核及驗收；新增模型探針先取得授權。

## 地雷與注意事項

- 工作中標記及 preflight 都不是並行鎖；同一工作樹只允許一個 writer，不自動奪權。
- 不無範圍地用 `--all --write`：用私人 inventory 或明確 exclude 排除已完結專案。
- `--allow-dirty`／逐檔 `--accept-drift` 只適用人工檢視的單一目標；不能略過占用。
- 漂移比對依權威 Git 歷史；缺歷史時保守拒絕，不把來源不明內容當舊版覆蓋。
- AI push 提醒仍只比字面命令、目前分支與 origin，GUI／script 等覆蓋有限。
- Python 3.8 下限仍是靜態擔保；本機生命週期測試不代表跨 OS／外部工具注入實測。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、50 項全過、無 skip；其後部署與同步保護的受影響項重驗通過。
骨架仍為 22 檔；F12 舊版抓到 17 處缺失，F16 舊 ignore／mode／順序均被拒絕。文件檢查由上述工具涵蓋，沒有獨立 check_docs.py。

## 懸置事項（AI 勿自行處理）

- 原子 claim 留待另案；新增模型探針須先授權且只用訂閱額度。
- Antigravity IDE hook 原因仍未知、不再追查。
