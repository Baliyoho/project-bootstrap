# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-13 16:00（+08）
- **交棒者**：Claude Code（Fable 5.2）／ `Mac`（handoff-ab 兩輪實測、需求決策書 v3、開 `feature/v3`）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)把以 v2 做出來的成果改成 v3 的形狀。現在做**第 1 期：Claude Code＋macOS**，做完就是基本版；第 2 期 Codex＋macOS、第 3 期兩個工具＋Windows，前一期驗過才開始下一期。Antigravity 放棄。v3 的一句話：制度只負責模型不會自己知道的事，不教模型怎麼做，也不自己造執行屏障。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`feature/v3`（從 `main @ 8cd8107` 開；`main` 只多一個把本欄指過來的 commit）。v3 的工作都在這條分支，第 1 期驗過、使用者驗收後才併回 `main`。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111316｜v3第1期｜工作中｜交棒0次`，2026-11-13 16:20 (+08) 開工
- **骨架版本**：`2026-11-12.4`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；沒有 `python` 指令，用 `python3`。桌面 App 內附 Claude Code 2.1.321。handoff-ab 受測用的獨立設定目錄在系統暫存目錄，重開機可能被清掉，清掉要使用者重新登入一次（指令由 `run.py preflight` 印出）。

## 已完成

- **handoff-ab 對照實測**（[結果](experiments/handoff-ab/RESULTS.md)）：十個情境、36 次，Opus 5.5 拿 22 行的極簡骨架，機器查得到的結果不比現行完整版差，成本約一半到四分之三。只測了 Opus 5.5、單輪、macOS。
- **需求決策書 v3**：2026-11-13 起的現行需求權威，與 v2 檔並存（v3 Q32 (b)）。`AGENTS.md`、`AGENTS-reasons.md`、`ARCHITECT.md` 已改指 v3；讀 v2 檔的驗證器與測試沒有改。
- 同日使用者修訂：F50 回到必要、平台分三期、Antigravity 放棄。

## 未完成／下一步

第 1 期還沒動工。部署包、`src/kit/`、`VERSION`、各專案與全域 skill 都還是 v2 的樣子。

1. **改部署包來源**（`src/kit/`，改完跑 `build_kit.py` 重生部署包）成 v3 第 5 節的形狀：
   - `AGENTS.md` 範本的共用制度一節 ≤ 40 行。起點是 [極簡版](experiments/handoff-ab/minimal/AGENTS.md.tmpl)，補三條：看「待續分支」、不提交祕密與不整批加入、F50 的 session 命名。
   - 開場 hook 改成只報事實。起點是極簡版的 `session-facts.sh.tmpl`，加上 F50 要的時間戳與版本落後提示一行。
   - handoff skill 六個檔降為碰到才讀的參考，入口不得要求必讀。
   - Antigravity 的接線與轉接檔移出部署包。
2. **調整 `verify_bootstrap.py`**。準則：守的是 v3 仍為必要的需求就留；守的是已退役或降強度的需求、Antigravity、或「skill 必讀」這種結構的，就改或移除，每移除一項在 ARCHITECT 的驗證項表記日期與理由。拿不準的留著，列給使用者決定，不要自己砍。
3. **驗第 1 期**：把 handoff-ab 的「完整版」那一組換成新部署包，跑兩輪十個情境（用法見 [README](experiments/handoff-ab/README.md) 與 [ROUND2](experiments/handoff-ab/ROUND2.md)）。要呼叫模型，每一批都要使用者批准，單次決策 ≤ 24 次、只用訂閱額度（v3 D15）。F50 測不到，要在互動 session 另外驗。
4. 第 1 期過了再問使用者要不要併回 `main`。同步各專案一向另行授權。

v3 第 8 節還有兩題沒定：凍結的執行屏障模組要不要搬去封存（Q33）、各專案何時換新骨架（Q34）。定之前那些模組與測試原地不動。

## 地雷與注意事項

- **一致性檢查對 v2 已決的題號很敏感**：在 `README`、`AGENTS`、`ARCHITECT`、`HANDOFF` 這幾份裡，提到 v2 題號的那一行不要同時出現「待決」兩個字，否則 `test_contradictions_repo` 會判成已決的題目還被當成待決。
- **待決登記處有兩個**：工具認得的是 v2 決策書第 6 節；v3 新增的題目在 v3 第 8 節。
- handoff-ab 的評分器出過一次會翻轉結論的錯。每個 FAIL 都要先人工看原始資料再採用；改評分器要加專屬反例，`selfcheck.py` 兩輪都要過（第二輪加 `HANDOFF_AB_ROUND=2`）。
- 使用者的帳號允許超額使用，撞到訂閱上限會直接轉成計費而不報錯。`run.py` 有用量守門（超額、被限流、任一用量窗到 85% 就停），不要拿掉。
- Claude Code 會用家目錄的 handoff skill 蓋掉專案那份；改了 skill 目錄要一起覆蓋這台的全域副本。受測時要用獨立的設定目錄，`preflight` 會查。
- 改這個 repo 的其他地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」，碰到對應的檔才讀。

## 服務查證與期望快照

- 2026-11-13 16:00 `verify_bootstrap.py --staged`：exit 0；`uv run --locked pytest` 652 通過（3.15）。mutation 沒重跑。handoff-ab 的 `selfcheck.py` 兩輪全過。B4：本 repo 沒有 `check_docs.py`（已宣告例外）。B5：Codex hook 接線未改，不適用。
- 模型呼叫：本 session 共 36 次 Opus 5.5（`claude -p`，兩批各經使用者批准，只用訂閱額度，沒有用到超額）。

## 懸置事項（AI 勿自行處理）

- 無。
