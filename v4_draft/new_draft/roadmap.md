# 實施計畫

> 最後更新：2026-11-23
> v4 重寫稿，不是現行約束文件。回答「從現況怎麼走到[需求](requirements.md)：選了哪條路線、各期的證據在哪、什麼先放著」。各期的範圍與退出條件在需求的「分期」與「驗收」；各期走到哪寫在 `HANDOFF.md`，不寫在這裡。

## 選定的路線

從現況照三期逐期收尾。路線的單位就是需求「分期」的驗收單位；每期只補該期缺的證據。不沿用舊規劃的工作拆解與估算，每期剩下的事重新列。

## 各期的證據

| 期 | 證據在哪 | 計畫上的決定 |
|---|---|---|
| 第 1 期 | handoff-ab 兩輪見 [RESULTS](../../experiments/handoff-ab/RESULTS.md)「v3 第 1 期」，F50 見 [F50.md](../../experiments/handoff-ab/F50.md)，都跑在部署包 `2026-11-13` | 以這兩份證據為準，不整期重跑；之後改制度照[設計原則](principles.md)「規則的增減」逐條對照 |
| 第 2 期 | handoff-ab 兩輪見 [CODEX-RESULTS](../../experiments/handoff-ab/CODEX-RESULTS.md)（2026-11-14） | 這批結果跑在當時的部署包，要不要在現行版重跑見[待決事項](open-questions.md) |
| 第 3 期 | Codex＋原生 Windows 有部分紀錄（CODEX-RESULTS 的 Windows 各節，2026-11-16） | |

## 安裝程式的期別分攤

安裝程式照上表的期別分攤，不另開一期：

- macOS 的安裝、更新、換行與兩支 hook 在 `tests/test_bootstrap_repo.py` 實跑，跟著第 1 期的範圍；不因此重開第 1 期，也不把這些測試當成 handoff-ab 的結果檢查。
- 在 Codex 上照 HANDOFF 的第一批工作接手，歸第 2 期。
- Windows 的安裝、`.gitattributes` 換行與 hook 實跑歸第 3 期；測試裡的 CRLF 只是在 macOS 上模擬。
- 已部署專案用 `sync_project.py` 升級，不排進任何一期。

## 暫緩與另案

| 項目 | 牽涉的 ID | 狀態與條件 |
|---|---|---|
| 原子 claim，以及兩個 clone／同一工作樹的並行實驗 | F12、F25；D1 | 另案，未排期。跟 D1「訊號不是鎖」有張力；要重開先在待決事項登記 |
| 驗證分層與沿用結果：局部修改只跑相關測試、同機器同內容沿用結果、A4 快速模式不跑全套測試（`tools/run_tests.py`） | F22、F24 | 待排。提交前仍跑全套，exit 0 才算完成 |
| Windows 開發人員模式與桌面 App 的 F50 | F50、F15 | 暫緩 |

## v4 生效時要一起做的事

整合時新增，待你確認。

- **整體進度搬進 main 的 `HANDOFF.md`**。照實施計畫 v3 的記載（2026-11-23 確認）：第 1 期已結案；第 2 期進行中，還差 Codex 桌面 App 的 F50 標題項判定；第 3 期 `midway` 斷線情境的失敗在 B1 改了之後還沒重跑，Claude Code＋Windows 沒跑；安裝程式在 Codex 與 Windows 上都還沒跑。
- **部署目標形狀併進部署包說明**：拆出的安裝程式規格與部署檔案表（`v4_draft/target-shape.md`）跟 [src/kit/kit.md](../../src/kit/kit.md) 比對，缺的補進 kit.md。
- **改讀 v3 結構的程式**：測試入口讀的需求書路徑、待決事項標題與 51 個 ID 的檢查、F46 例外宣告的讀取位置、計畫路線與非目標的解析、歷史紀錄決策紀錄的解析、現況索引。
- **切換約束文件**：`AGENTS.md` 專用規則 3 改連 v4 的約束文件；這組文件搬到正式位置，歷史紀錄進 `docs/history/`；v3 兩份與它們的歷史紀錄照[設計原則](principles.md)「版本更替」封存。
