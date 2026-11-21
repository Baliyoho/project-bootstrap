# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-21 15:57（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（依原則草稿精簡 AGENTS 與 HANDOFF）

## 任務目標

使用者在依[協作系統原則草稿](collaboration-system-principles-draft.md)整理這個 repo 的文件與程式，目標是更簡潔、每個事實只有一個家。草稿還不是約束文件。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-21.3`
- 本機能力：Mac mini；`git push` 可用；`.venv` 可跑外部套件測試（`.venv/bin/python -m pytest tests`）。`/usr/bin/python3` 是 3.9.6，低於全 repo 下限 3.12，要用另裝的 `python3`（3.15.2）。

## 目前進度

- 已照原則整理：`AGENTS.md`、驗證器、HANDOFF 格式（決策書 v3 Q59）。
- 還沒整理：handoff skill、`src/kit/kit.md`、其他文件檔頭的「最後更新」、文件分類與索引。
- 共用規則（Q57、Q58）與 HANDOFF 格式（Q59）都沒經 handoff-ab 實驗驗證；使用者要等規則全部定案再一次跑，不要每改一次就提。

## 未完成／下一步

1. **handoff skill 整理、`src/kit/kit.md` 對齊原則**：使用者排定之後做，沒說何時。兩份都混著「某天起……、舊版寫……」的經過（kit.md 帶日期的行佔約一半字數）。做的時候一起處理驗證器 B 層：「skill 拆分」與 `tools/skill_split_baseline.json`、「同步補齊模式檔」（先確認已部署專案都不是單檔 skill）、「跨工具過期敘述」、「已修正的主張沒復活」「跨工具表保鮮期」。檔頭表「skill 拆分」一列寫的「已改寫清單（13 行）」過期，到時一起改。
2. **這台 Mac 的全域 handoff skill 是 `2026-11-20.2`**，跟部署包不同版。使用者 2026-11-21 說先不要重裝；要重裝時步驟見驗證器的提醒。
3. **Windows 那台也在用的已部署專案**：還在 `2026-11-17.3`，留著 `GEMINI.md` 與 `docs/ai-notes/handover-protocol.md`；2026-11-18 看到 origin 的「工作中」是 Windows 那台的 Codex session，之後沒再查。等它交棒、且 Q60 有了做法再同步；同步工具對它的 MIGRATE 提示刻意留著。
4. **Windows 那台的 Python 版本沒確認**：低於 3.12 的機器跑維護工具會在檔頭停下。
5. **繼續整理文件**：使用者說「分類」與「索引」之後再談；原則草稿定案後，在 AGENTS「碰到才讀」加一列指向原則文件，現在不加。

## 地雷與注意事項

- 根目錄的 `comparison-adr-memory-bank.md` 是使用者自己放的未追蹤檔，`--staged` 會因它回 exit 2：提交前暫移到 scratchpad、驗證後原樣移回；不要刪它或提交它。

## 服務查證與期望快照

- 2026-11-21 macOS Mac mini：`python3 -X utf8 tools/verify_bootstrap.py --staged` → exit 0，65 項全過（全域 skill 不同版只印提醒）；`.venv/bin/python -m pytest -q` → 170 passed。
- `src/project_bootstrap/` 沒改，沒跑變異測試；handoff-ab 沒跑。驗證器「已修正的主張沒復活」的序號算法檢查改查維護手冊，負向測試照跑通過。同步工具的「## 已完成」改名只有函式層的負向測試，沒有對已部署專案實跑。
- Windows 與已部署專案沒跑；任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- Q60：已部署專案的 `ARCHITECT.md` 怎麼改名成 `ARCHITECTURE.md`；定案前不要把任何專案同步到 `2026-11-20` 以後的版本。
- Q61：第 2 期（Codex＋macOS）與 Q49 在 Windows、Codex 上的實跑什麼時候續做。
