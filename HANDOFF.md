# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-13 16:00（+08）
- **交棒者**：Claude Code（Fable 5.2）／ `Mac`（handoff-ab 兩輪實測、需求決策書 v3、開 `feature/v3`）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)把以 v2 做出來的成果改成 v3 的形狀。現在做**第 1 期：Claude Code＋macOS**，做完就是基本版；第 2 期 Codex＋macOS、第 3 期兩個工具＋Windows，前一期驗過才開始下一期。Antigravity 放棄。v3 的一句話：制度只負責模型不會自己知道的事，不教模型怎麼做，也不自己造執行屏障。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：無（2026-11-13 使用者驗收 v3 第 1 期後，`feature/v3` 併回 `main`，主幹回到 `main`；`feature/v3` 保留不刪）。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111316｜v3第1期｜工作中｜交棒0次`，2026-11-13 16:20 (+08) 開工
- **骨架版本**：`2026-11-13`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；沒有 `python` 指令，用 `python3`。桌面 App 內附 Claude Code 2.1.321。handoff-ab 受測用的獨立設定目錄在系統暫存目錄，重開機可能被清掉，清掉要使用者重新登入一次（指令由 `run.py preflight` 印出）。

## 已完成

- **v3 第 1 期（Claude Code＋macOS）**，2026-11-13 使用者驗收後併回 `main`，`VERSION` `2026-11-13`：
  - 部署包：`AGENTS.md` 範本有開始／結束標記夾住的共用制度（32 行），開場 hook 只報事實（≤5 行 `[facts]`），handoff skill 降為碰到才讀的參考，Antigravity 三個檔移出。
  - `verify_bootstrap.py` 跟著改（取捨記在 ARCHITECT 驗證項表下方），新增「AGENTS.md 共用制度」一項；`sync_project.py`／`owners.json` 不再處理 Antigravity。
  - handoff-ab 新部署包兩輪 18／18、0 損害，與 v2 完整版相同，成本約三分之二（[結果](experiments/handoff-ab/RESULTS.md)）。
  - F50 互動驗證三次（[紀錄](experiments/handoff-ab/F50.md)）：名稱十五步全對；用選項卡片停下時漏寫 `session：` 行，補一句共用制度後第三次通過。
- 之前：handoff-ab 極簡版對照實測、需求決策書 v3。

## 未完成／下一步

1. **各專案與全域 skill 都還是 v2**。`main` 是 `2026-11-13` 之後，各專案的開場 hook 會提示骨架落後；什麼時候換新骨架是 v3 Q34，同步一向另行授權。這台的全域 `~/.claude/skills/handoff/` 刻意留在 v2：新版 skill 說必守條件在 `AGENTS.md` 共用制度，而各專案的 `AGENTS.md` 還沒有那一節。
2. **ARCHITECT 驗證項表下方列了幾項守 v2 強度的檢查**（push 提醒 exit 2、`check_docs.py` 對壞格式 exit 2、README 跨工具表的 Antigravity 欄等），留給使用者決定。
3. 第 2 期 Codex＋macOS、第 3 期兩個工具＋Windows，前一期驗過才開始。
4. v3 第 8 節未定：凍結的執行屏障模組要不要封存（Q33）、各專案何時換新骨架（Q34）。

## 地雷與注意事項

- **一致性檢查對 v2 已決的題號很敏感**：在 `README`、`AGENTS`、`ARCHITECT`、`HANDOFF` 這幾份裡，提到 v2 題號的那一行不要同時出現「待決」兩個字，否則 `test_contradictions_repo` 會判成已決的題目還被當成待決。
- **待決登記處有兩個**：工具認得的是 v2 決策書第 6 節；v3 新增的題目在 v3 第 8 節。
- handoff-ab 的評分器出過一次會翻轉結論的錯。每個 FAIL 都要先人工看原始資料再採用；改評分器要加專屬反例，`selfcheck.py` 兩輪都要過（第二輪加 `HANDOFF_AB_ROUND=2`）。
- 使用者的帳號允許超額使用，撞到訂閱上限會直接轉成計費而不報錯。`run.py` 有用量守門（超額、被限流、任一用量窗到 85% 就停），不要拿掉。
- Claude Code 會用家目錄的 handoff skill 蓋掉專案那份。handoff-ab 與 F50 受測期間要把全域副本暫時換成部署包那一版、跑完換回（v2 原檔就是 git `f568ca7` 的部署包）；受測用的設定目錄在暫存目錄，空家目錄底下登入存不進鑰匙圈，要用 `HANDOFF_AB_HOME=real`。
- 改這個 repo 的其他地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」，碰到對應的檔才讀。

## 服務查證與期望快照

- 2026-11-13 16:00 `verify_bootstrap.py --staged`：exit 0；`uv run --locked pytest` 652 通過（3.15）。mutation 沒重跑。handoff-ab 的 `selfcheck.py` 兩輪全過。B4：本 repo 沒有 `check_docs.py`（已宣告例外）。B5：Codex hook 接線未改，不適用。
- 模型呼叫：本 session 共 36 次 Opus 5.5（`claude -p`，兩批各經使用者批准，只用訂閱額度，沒有用到超額）。

## 懸置事項（AI 勿自行處理）

- 無。
