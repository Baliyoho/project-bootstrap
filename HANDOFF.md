# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 09:39（+08）
- **交棒者**：Codex ／ `DESKTOP-M8MRS05`（續聊恢復工作中與交棒計數）

## 任務目標

維護 AI 協作專案管理骨架的權威版 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。
本檔是當下快照，≤80 行、覆寫不累積；維護規則見 [AGENTS.md](AGENTS.md)「本 repo 的交接快照」。
它是範本 3.3 的實例，不是副本，不用 `sync_project.py` 同步，也不因本檔變更跳版。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Codex CLI` ／ `㊣　26110209｜查核協作制度｜工作中｜交棒0次`，2026-11-02 10:14 (+08) 開工
- **骨架版本**：`2026-11-02`
- 本機能力：Windows ＋ Git Bash；本輪已成功 fetch、push 開工標記及六個專案同步結果。

## 已完成

- 已交棒的 session 收到每則使用者新訊息，先恢復工作中，包括只讀問答；原時間、主題與交棒次數保留。
- 累計次數的家在 session 標題，無改名工具時由同一 session 的回報保存；成功 B 模式才加 1，同一輪跨 repo 收尾只算一次。
- skill 與入口指標 description 補續聊觸發，A5／B9 與等待狀態格式皆保留計數；舊版未知總數用下限、不編精確值。
- 新增「續聊狀態與計數」程序契約檢查與 18 個負向測試；結構說明同步更新。
- 六個使用中專案與兩份全域 handoff 副本均已同步；六個專案已在原分支 push、工作標記清除。
- 使用者已廢棄的一個專案本輪排除，沒有修改或代刪該目錄。

## 未完成／下一步

目前沒有已確認的必要待辦。已開著的舊 session 要採用新版，須明確重新讀取 handoff skill 或重開 session。

## 地雷與注意事項

- 只讀續聊只改 session 狀態，不新增 Git 開工／交棒紀錄；要改檔前重新走 A1–A5，防止前次交棒後別人已接手。
- `㊣` 是側欄活動狀態，不證明 origin 有開工標記；交棒計數不寫成 HANDOFF 的逐 session 歷史表。
- 新檢查只守程序文字與入口描述，不代表量過各工具逐訊息的實際行為；本輪沒有新增模型探針。
- 交接前仍要逐項核對待辦與實況，不能只清工作標記。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：本輪 exit 0、37 項全過，重生骨架 22 檔。
六個專案 `verify_state.py` 與 `check_docs.py` 均 exit 0；其中三個 verify_state 仍為既有 NOT_CONFIGURED，不代表服務實測。
B4：本 repo 沒有 check_docs.py，由上述完整驗證涵蓋。B5：未改 hook 接線，無重新審核需求。
副本檔案已與權威抽取結果逐位元組比對一致；SKILL source 與 VERSION 均為 `2026-11-02`。

## 懸置事項（AI 勿自行處理）

- 早期 exec 成功／TUI 失敗的差異仍無法回溯歸因（前輪確認原探針資料不在）。
  現行 hook 已驗收；這是歷史未知，不是現行故障，也沒有排定重做探針。
- Antigravity IDE 的 hook 未觸發原因保留為未知，已決定不再追查；不要重新列成待辦。
