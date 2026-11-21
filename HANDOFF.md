# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-21 15:25（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（AGENTS 改成共用與專用兩大段、驗證器精簡）

## 任務目標

使用者在依[協作系統原則草稿](collaboration-system-principles-draft.md)整理這個 repo 的文件與程式，目標是更簡潔、每個事實只有一個家。草稿還不是約束文件。這一棒把 AGENTS 的規則改到使用者定案的結構，再把驗證器砍掉重複與經過敘述。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無（`feat/bootstrap-installer`、`feat/retire-kit-doc` 都已併回 `main`，分支留在 origin 沒刪）。
- **工作中**：`Mac mini` ／ `Claude Code` ／ `㊣　11.21.15｜待指派｜工作中｜交棒0次`，2026-11-21 15:36 (+08) 開工
- **骨架版本**：`2026-11-21.2`
- 本機能力：Mac mini；`git push` 可用；`.venv` 可跑外部套件測試（`.venv/bin/python -m pytest tests`）。`/usr/bin/python3` 是 3.9.6，太舊（全 repo 下限已是 3.12），用另裝的 `python3`（3.15.2）。

## 已完成

- **AGENTS 規則整併（決策書 v3 Q55–Q58，使用者逐項選定）**：鐵律與不可違反的條件合成「規則」；原本的 15 條規則去重；整份分成「## 共用制度」（協作目標、環境事實、共用規則 1–9）與「## 專案專用」（專用規則、碰到才讀），共用與專用各自編號，引用一律寫「共用規則 N」或「專用規則 N」，驗證器「規則引用有前綴」擋沒前綴的寫法。skill 位置改成共用規則 8（開場 `[facts]` 不正常或要交棒時讀），session 命名是共用規則 9。部署包跳到 `2026-11-21.2`。原則草稿第 4 節第 4 點改成「共用、專用各一份清單」。
- **驗證器精簡**（`bfffd8f`、`7a9d971`、`3e0bf37`、`36b85a0`、`c3354a9`）：5,732 行 → 5,085 行，69 項 → 65 項。刪檔頭重疊清單與經過敘述、併掉三項重複的負向測試；README 跨工具一節改成摘要加連結並刪掉表格一致性檢查；Python 下限全部對齊 3.12（維護工具、部署後兩支、安裝程式、pyproject），開發骨架改用 `tomllib`；刪三處守著退場功能的檢查；本 repo 的文件與交接快照檢查改用部署後 `check_docs.py` 的同一份函式（不裝副本，F46 構造上成立），來源自己重寫的那套刪掉。

## 未完成／下一步

1. **handoff skill 整理、`src/kit/kit.md` 對齊原則**：使用者排定之後做，沒說何時。兩份都混著「某天起……、舊版寫……」的經過（kit.md 帶日期的行佔約一半字數）。做的時候一起處理驗證器 B 層：「skill 拆分」與 `tools/skill_split_baseline.json`、「同步補齊模式檔」（先確認已部署專案都不是單檔 skill）、「跨工具過期敘述」、「已修正的主張沒復活」「跨工具表保鮮期」。檔頭表「skill 拆分」一列寫「已改寫清單（13 行）」早就過期，到時一起改。
2. **handoff-ab 對照**：Q57、Q58 改過的共用規則還沒實驗驗證。使用者說等規則全部定案再一次跑，不要每改一次就提。
3. **這台 Mac 的全域 handoff skill 還是 `2026-11-20.2`**（驗證器只印提醒）。要重裝得使用者同意或自己做：把 `src/kit/files/.claude/skills/handoff/` 的七個範本去掉 `.tmpl` 覆蓋到 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/`。
4. **已部署專案的結構文件改名**：各專案仍是 `ARCHITECT.md`，`sync_project.py` 不會改名。使用者還沒選做法（讓同步器改名，或各專案自己 `git mv`）。**選之前不要把任何專案同步到 `2026-11-20` 以後的版本**。
5. **鍵鼠同部署_mac**：還在 `2026-11-17.3`，留著 `GEMINI.md` 與 `docs/ai-notes/handover-protocol.md`；2026-11-18 起 origin 的「工作中」是 Windows 那台的 Codex session（本棒沒再查）。等它交棒、且第 4 項有了做法再同步；同步工具對它的 MIGRATE 提示刻意留著。
6. **Windows 那台的 Python 版本沒確認**：全 repo 下限改成 3.12 後，低於 3.12 的機器跑維護工具會在檔頭停下。
7. **繼續整理文件**：使用者說「分類」與「索引」之後再談；原則草稿定案後，在 AGENTS「碰到才讀」加一列指向原則文件，現在不加。其他文件檔頭的「最後更新」多半還寫著改了什麼。
8. **第 2 期（Codex＋macOS）、Q49 在 Windows 與 Codex 上跑**：使用者 2026-11-18 說先等等。

## 地雷與注意事項

- **討論模式**：文件體系的題目先討論取得共識；改約束文件要使用者在聊天中決定，並在 `docs/history/` 成對記一筆。決策書下一個 Q 是 Q59。
- **引用規則要寫前綴**：寫「共用規則 N」或「專用規則 N」；`CHANGELOG.md`、`docs/history/`、`archive/`、`experiments/` 不查。
- **共用制度改了要跳版**：`VERSION`、共用制度標記與七個 skill 檔的 `source:` 一起換；本 repo `AGENTS.md` 的共用段要從 `src/kit/files/AGENTS.md.tmpl` 逐字重貼。
- **本 repo 的文件檢查跑的是部署後的 `check_docs.py`**：改 `src/kit/files/tools/check_docs.py.tmpl` 會同時改到本 repo 的檢查；讀 `AGENTS.md` 時共用段靠 `SharedBlanked`（Path 子類別）塗白，要 Python 3.12。
- **整個 `archive/` 是冷區**：AI 平常不讀，回溯或修改先經使用者同意。
- **根目錄有未追蹤檔時 `--staged` 回 exit 2**：`comparison-adr-memory-bank.md` 是使用者自己放的。提交前暫移到 scratchpad、驗證後原樣移回；不要刪它或提交它。
- **決策紀錄要有子項**：`採用理由：`、每個沒選的字母一條 `未選 (x)`，狀態欄寫出選了哪個字母；少了 `test_trail_repo` 會失敗。
- **`bootstrap.py` 是產物**：改 `src/kit/`、`installer.py` 或 `sync_project.py` 的合併函式後跑 `tools/build_kit.py`，同一個 commit 提交。
- **檔頭 `source: PROJECT-BOOTSTRAP.md v…` 的字樣不要改**：已部署專案的開場 hook 用這個字面比對版本。
- **驗證器不跑變異測試**：改到 `src/project_bootstrap/` 的檢查，自己跑 `mutants.py --only tests.test_<模組>`。
- 其他開發時容易踩的地方在 `docs/maintenance.md` 的「開發注意事項」。

## 服務查證與期望快照

- 2026-11-21 macOS Mac mini，`c3354a9`：`python3 -X utf8 tools/verify_bootstrap.py --staged` → **exit 0，65 項全過**（全域 skill 同版只印提醒）；`.venv/bin/python -m pytest -q` → 170 passed。
- 本棒沒跑變異測試（`src/project_bootstrap/` 只改了說明與註解）。handoff-ab 沒重跑。
- Windows 與已部署專案本棒沒跑；任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- 無。
