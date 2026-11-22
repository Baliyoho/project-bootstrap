# 路線與分期進度

> 最後更新：2026-11-22
> v4 草稿，從實施計畫 v3 第 2、3、4 節拆出，全檔都出自計畫，不逐條標出處。回答「選了哪條路、每期走到哪、哪些先放著」。各期的範圍與退出條件在[目標與範圍](goal-and-scope.md)與[驗收](acceptance.md)，這裡不重述。

## 選定的路線

從現況照三期逐期收尾。路線的單位就是驗收的分期單位；每期只補該期缺的證據。舊規劃的工作拆解與估算作廢，每期剩下的事要重列。

## 各期的證據與還差什麼

| 期 | 範圍 | 證據與還差什麼 |
|---|---|---|
| 第 1 期 | Claude Code＋macOS；F50 | handoff-ab 兩輪見 [RESULTS](../experiments/handoff-ab/RESULTS.md)「v3 第 1 期」，F50 見 [F50.md](../experiments/handoff-ab/F50.md)，都跑在部署包 `2026-11-13`。**已結案**，以這兩份證據為準，不整期重跑；之後改制度照 D10、D14 逐條對照 |
| 第 2 期 | Codex＋macOS；F14 | handoff-ab 兩輪見 [CODEX-RESULTS](../experiments/handoff-ab/CODEX-RESULTS.md)（2026-11-14）。**進行中**。還差：Codex 桌面 App 的 F50 標題項判定；這批結果跑在當時的部署包，要不要在現行版重跑待使用者決定 |
| 第 3 期 | 兩個工具＋Windows；F15 | Codex＋原生 Windows 有部分紀錄（CODEX-RESULTS 的 Windows 各節，2026-11-16），`midway` 斷線情境的失敗在 B1 改了之後還沒重跑。Claude Code＋Windows 沒跑。Windows 開發人員模式與桌面 App 的 F50 暫緩 |

## 安裝程式的期別分攤

安裝程式照上表的期別分攤，不另開一期：

- macOS 的安裝、更新、換行與兩支 hook 在 `tests/test_bootstrap_repo.py` 實跑，跟著第 1 期的範圍。第 1 期已結案，不因此重開，也不把這些測試當成 handoff-ab 的結果檢查。
- 在 Codex 上照 HANDOFF 的第一批工作接手，歸第 2 期，還沒跑。
- Windows 的安裝、`.gitattributes` 換行與 hook 實跑歸第 3 期，還沒跑。測試裡的 CRLF 只是在 macOS 上模擬。
- 已部署專案用 `sync_project.py` 升級，不排進任何一期。

## 暫緩與另案

| 項目 | 牽涉的 ID | 狀態與條件 |
|---|---|---|
| 原子 claim，以及兩個 clone／同一工作樹的並行實驗 | F12、F25；D1 | 另案，未排期。跟 D1「訊號不是鎖」有張力；要重開先在待決事項登記 |
| 驗證分層與沿用結果：局部修改只跑相關測試、同機器同內容沿用結果、A4 快速模式不跑全套測試（`tools/run_tests.py`） | F22、F24 | 待排。提交前仍跑全套，exit 0 才算完成（AGENTS 的驗證規則） |
