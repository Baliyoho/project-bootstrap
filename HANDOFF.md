# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 18:04（+08）
- **交棒者**：Codex ／ `DESKTOP-M8MRS05`（完成 F07）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。
查核 16 條已修 11 條，剩 F10–F13、F16；細節以
[project-bootstrap-audit-progress.md](project-bootstrap-audit-progress.md) 為準，查核報告仍是凍結快照。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Codex CLI` ／ `㊣　26110217｜續修查核缺陷｜工作中｜交棒2次`，2026-11-02 18:06 (+08) 開工
- **骨架版本**：`2026-11-02.4`
- 本機能力：Windows、Python 3.13.15、Git Bash、PowerShell；本輪 fetch、開工 push 成功。

## 已完成

- F07：SKIP 預設不產出 ZIP；顯式 --allow-unverified-zip 產出未驗證調試包，仍 exit 1。
  包內有 UNVERIFIED.json 與醒目說明；FAIL 不能繞過，拒絕時保留既有產物。
- 新增第 44 項「ZIP 發布門檻」：10 個 CLI／ZIP 情境與移除門檻的負向測試。
- 只改維護工具與文件；VERSION 不變，副本同步與 hook 重新審核本輪不適用。
- 前輪 F06 已完成並同步六個專案與兩份全域 skill，細節見進度報告。

## 未完成／下一步

1. 從 F11 開始，再按 F10 → F12 → F13 → F16；先讀進度報告的驗收門檻。
2. 六個專案同步變更仍各自在自己的 session 收尾，不在骨架 session 代提交。
3. F06 輪重跑文件檢查：兩個專案仍缺「待續分支」，一個仍有重複「已完成」章節，
   共三個 exit 2；其餘三個 exit 0。這些既有問題須在各專案處理。
4. 先前改過接線的專案仍要在 Codex 互動模式審核及驗收；本輪未呼叫模型探針。

## 地雷與注意事項

- 提醒只比字面 git push、目前分支與 origin；不解析選項／remote／refspec。
  GUI／script 可能漏判，純文字可能誤擋；已提交開工標記也會過，不代表已交棒。
- 不用 `sync_project.py --all --write`：會掃到已完結專案。後續同步須明確排除它。
- 其他專案含既有未提交檔案，必須明確 stage；依使用者既定範圍不代處理。
- Python 3.8 下限仍是靜態擔保，不是實機測試。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、44 項全過、無 skip；重生骨架 22 檔。
B4：沒有獨立 check_docs.py，由上述驗證涵蓋。F07 的 10 情境與負向測試全部通過。

## 懸置事項（AI 勿自行處理）

- 新增模型探針須先授權且只用訂閱額度。
- Antigravity IDE hook 原因仍未知、不再追查。
