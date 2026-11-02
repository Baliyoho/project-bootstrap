# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 14:20（+08）
- **交棒者**：Claude Code ／ `DESKTOP-M8MRS05`（修查核報告的 F02 與 F03）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。依
[project-bootstrap-audit.md](project-bootstrap-audit.md) 分批修正；目前已修 **F01、F09、
F02、F03**（都是 P1），其餘 12 條未實作。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26110210｜修查核缺陷｜工作中｜交棒2次`，2026-11-02 14:52 (+08) 開工
- **骨架版本**：`2026-11-02`
- 本機能力：Windows、Python 3.13.15、Git Bash；本輪 fetch、開工標記與收尾 push 均成功。

## 已完成

- **F02**：`sync_project.py` 的所有權從「整組」降到 **handler** 層。同組的專案自訂 hook
  不再被靜默刪除（舊版還會印「專案其他設定原樣保留」）；組層 `matcher` 仍歸骨架，但同組
  有專案 handler 又要改 `matcher` 時**拒絕並印出新舊值**；重複組與異常分組也拒絕（舊版會
  讓同一支腳本掛兩次）；`handler_scripts()` 連 `commandWindows` 一起看。
- **F03**：改成 `Plan` → preflight → `apply_plan`。任一項算不出來就整個目標跳過、**零寫入**；
  寫入走暫存檔 ＋ `os.replace`；中途失敗列出已／未套用；目標不存在、是本 repo 自己、
  或任何目標沒完成都**非零退出**，不再宣稱「全部都已經是最新版」。
- 新增第 **38** 項「同步安全」：F02 五種形狀 ＋ F03 四種，**逐項對舊實作跑過，九項全部是反的**。
- 順帶實測到查核報告只做到靜態確認的那半：舊版壞 JSON 加 `--write` 回 exit 0，而 `SKILL.md`
  **已經被覆蓋**。部分寫入是真的，不只是程式順序推論。
- 前一輪（同日）已修 **F01**（三處占用判讀改精確解析）與 **F09**（版本偵測改判方向）。

## 未完成／下一步

1. **F01／F09 的副本仍未同步到六個專案與全域副本**，而落後的那一版會印錯誤綠燈。阻塞原因
   （F02／F03）**已經解除**：`sync_project.py` 只住在本 repo、不部署，所以這一輪沒有新的
   副本債。下一步可以跑 `python -X utf8 tools/sync_project.py --all`（先預演），確認每個
   專案的 `UPDATE` 清單後再 `--write`；完成後刪各專案的 `.claude/.bootstrap-version`。
   ⚠️ 預演若對某個專案印出 matcher 衝突或異常分組的拒絕，那是 F02 新加的保護，要人工處理。
   ⚠️ 兩個專案（`zotero_automate`、勾選系統）**不補裝**；`序號卡` 已完結、不要碰。
2. 其餘 12 條未實作。複核過的優先序：**F05 的 PreToolUse fail-open → F15／F14 → F08**。
   F04 與 F07 嚴重度低於報告所列；F12 只採納文件修正，不做 claim 機制。
3. F05 有一項報告沒寫的加重事實：push 防呆找不到腳本時 exit 127 ≠ 2，依其自身契約等於
   **放行**，而 Claude Code 的 hook cwd 會跟著 session 內的 `cd` 變。

## 地雷與注意事項

- **不要因為報告的建議去跳 `VERSION`**（報告第 6 節自己也這樣提醒）：它是「`SKILL.md` 的
  版本」，跳了各專案會永遠印「骨架落後」而且同步修不掉（鐵律 1）。
- 本輪**沒有**重跑報告的原始反例（`audit_probe.py` 等不在 repo 裡）；F01／F02／F03／F06／F09
  是本 session 自己重現的，F04 等只做程式與文件核實。
- 38 項全過不表示其餘 12 條不存在，也不表示六個專案現在是安全的（見下一步第 1 點）。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、**38 項全過**、重生骨架 22 檔，無 skip。
B4：本 repo 沒有 `check_docs.py`，由上述完整驗證涵蓋。
B5：未改接線、未跳 `VERSION`、未同步任何副本，故無接線重審需求。

## 懸置事項（AI 勿自行處理）

- 要不要現在把 F01／F09 同步到六個專案與全域副本，等使用者決定。
- 新增模型探針仍須先取得授權且只用訂閱額度；本輪未呼叫任何模型探針。
- Antigravity IDE hook 未觸發原因維持未知、不再追查；早期 exec／TUI 差異仍歷史無法歸因。
