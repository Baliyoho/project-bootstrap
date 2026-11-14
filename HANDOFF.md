# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-13 21:58（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（v3 第 1 期：部署包改成 v3 形狀、驗證器跟著改、handoff-ab 與 F50 驗過、併回 `main`）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)把 v2 的成果改成 v3 的形狀，分三期：第 1 期 Claude Code＋macOS（**已完成並併回 `main`**），第 2 期 Codex＋macOS，第 3 期兩個工具＋Windows；前一期驗過才開始下一期。Antigravity 放棄。v3 的一句話：制度只負責模型不會自己知道的事，不教模型怎麼做，也不自己造執行屏障。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：無（`feature/v3` 2026-11-13 併回 `main`，保留不刪，它那份 HANDOFF 已指回 `main`）。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111406｜待指派｜工作中｜交棒0次`，2026-11-14 06:55 (+08) 開工
- **骨架版本**：`2026-11-13`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；沒有 `python` 指令，用 `python3`。桌面 App 內附 Claude Code 2.1.321。handoff-ab 受測工作區與登入過的設定目錄在系統暫存目錄（`pb-handoff-ab-v3p1`、`pb-handoff-ab-v3p1-r2`、`pb-f50`），重開機可能被清掉。

## 已完成

- **v3 第 1 期**，使用者 2026-11-13 驗收後併回 `main`：
  - 部署包：3.1 `AGENTS.md` 範本用開始／結束標記夾住共用制度（32 行，上限 40）；3.10 開場 hook 只報事實（≤5 行 `[facts]`，檔名不變）；3.8 handoff skill 降為碰到才讀的參考；舊 3.18–3.20（Antigravity）移除。
  - `verify_bootstrap.py`：hook 相關檢查改看 `[facts]`，新增「AGENTS.md 共用制度」（26 條必備、行數預算、版本＝`VERSION`），入口必備句 18 → 12，移除 Antigravity 一項；取捨逐條記在 ARCHITECT 驗證項表下方。`sync_project.py`／`migrate_project.py`／`owners.json` 不再處理 Antigravity。
  - handoff-ab：只重跑完整組（換成新部署包），兩輪 18／18、0 損害，與 v2 完整版相同，成本約三分之二（[RESULTS](experiments/handoff-ab/RESULTS.md) 最後一節）。`run.py` 加了呼叫前的用量守門、`--arm`、`HANDOFF_AB_CONFIG`。
  - F50 互動驗證三次（[F50.md](experiments/handoff-ab/F50.md)）：名稱十五步全對；用選項卡片停下時漏寫 `session：` 行（重現兩次），共用制度補一句後第三次通過。

## 未完成／下一步

1. **各專案與這台的全域 skill 都還是 v2**。各專案的開場 hook 現在會提示骨架落後，直到同步為止；什麼時候換新骨架是 v3 Q34，同步一向另行授權。全域 `~/.claude/skills/handoff/` 刻意留在 v2：新版 skill 說必守條件在 `AGENTS.md` 共用制度，各專案的 `AGENTS.md` 還沒有那一節。兩件事要一起做。
2. **ARCHITECT 驗證項表下方「列給使用者決定」那一條**：push 提醒仍 exit 2 擋、`check_docs.py` 對壞格式 exit 2、skill 參考檔句子的契約檢查、README 跨工具表仍有 Antigravity 欄。等使用者逐項決定留或改。
3. 第 2 期 Codex＋macOS：同一套 handoff-ab 兩輪＋互動驗證，換 Codex 跑。開始前先問使用者。
4. v3 第 8 節未定：凍結的執行屏障模組要不要封存（Q33）、各專案何時換新骨架（Q34）。

## 地雷與注意事項

- **一致性檢查對 v2 已決的題號很敏感**：在 `README`、`AGENTS`、`ARCHITECT`、`HANDOFF` 這幾份裡，提到 v2 題號的那一行不要同時出現「待決」兩個字，否則 `test_contradictions_repo` 會判成已決的題目還被當成待決。
- **待決登記處有兩個**：工具認得的是 v2 決策書第 6 節；v3 新增的題目在 v3 第 8 節。「懸置事項」只能寫已登記的題目，v3 的題目寫在它那裡會被一致性檢查判成未登記，所以等使用者決定的事放在「未完成／下一步」並寫明「等使用者決定」。
- **共用制度的版本就是 `VERSION`**：開場 hook 拿 `AGENTS.md` 開始標記裡的版本比上游；「AGENTS.md 共用制度」檢查要求兩者相同，而「skill 拆分」要求六個 skill 檔也同版。改了共用制度卻不改 skill 時怎麼跳版還沒定案；2026-11-13 那一次因為還沒發布所以沒跳。
- handoff-ab 的評分器出過會翻轉結論的錯，這次又漏改一處（完整組的 hook 標記）。每個 FAIL／INVALID 先看原始資料；改評分器要加專屬反例，`selfcheck.py` 兩輪都要過（第二輪加 `HANDOFF_AB_ROUND=2`）。
- 帳號允許超額，撞到訂閱上限會直接扣額外用量而不報錯。`run.py` 有用量守門，不要拿掉；互動測試沒有守門，三輪 F50 加上這個 session 把 5 小時窗用到 94%（額外用量沒動）。
- Claude Code 會用家目錄的 handoff skill 蓋掉專案那份。受測期間要把全域副本暫時換成部署包那一版、跑完換回（v2 原檔＝git `f568ca7` 的部署包）；空家目錄底下登入存不進鑰匙圈，要用 `HANDOFF_AB_HOME=real`。
- 改這個 repo 的其他地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」，碰到對應的檔才讀。

## 服務查證與期望快照

- 2026-11-13 21:5x 在 `main`（併回後）：`verify_bootstrap.py --staged` exit 0（66 項 ok、0 skip）；`uv run --locked pytest` 651 通過（少的 1 個是刪掉的 Antigravity IDE 測試）。mutation 沒重跑。`selfcheck.py` 兩輪全過。B4：本 repo 沒有 `check_docs.py`（已宣告例外）。B5：Codex 接線內容未改，不適用。
- 模型呼叫：handoff-ab 18 次 Opus 5.5（12＋6，各經使用者批准，只用訂閱額度，守門沒觸發）；F50 由使用者在桌面 App 操作三次。

## 懸置事項（AI 勿自行處理）

- 無。
