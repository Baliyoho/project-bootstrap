# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-20 19:25（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（文件體系討論：協作系統原則草稿、ARCHITECT 改名 ARCHITECTURE 與整改、README 與維護手冊精簡）

## 任務目標

使用者在討論 AI 協作 repo 的文件體系，先跟 AI 取得共識再動手。共識寫在 [collaboration-system-principles-draft.md](collaboration-system-principles-draft.md)（前提、效用、設計原則；草稿，還不是約束文件，最終要跟決策書與計畫整合成一份新文件，名稱未定）。接著依原則整理本 repo 的實際文件，這一棒做了 README、維護手冊與 ARCHITECTURE。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無（`feat/bootstrap-installer`、`feat/retire-kit-doc` 都已併回 `main`，分支留在 origin 沒刪）。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-20`
- 本機能力：Mac mini；`git push` 可用；本機 `.venv` 可跑驗證器不跑的外部套件測試（`.venv/bin/python -m pytest tests`）。`/usr/bin/python3` 是 3.9.6，跑不了 `bootstrap.py`（要 3.12），用另裝的 `python3`（3.15.2）。

## 已完成

- **共識草稿**（`9e0e642`）：前提、效用、宗旨與六條設計原則；「寫進文件前先問三個問題」定為檢查清單，不立原則。
- **README 照慣例精簡、維護手冊的文件分工表移走**（`ca53a32`）：拿掉「最後更新」行與已封存的簽章發布通道一節；核心一節改成摘要加連結，保留驗證器要求的核心優先序宣告。
- **`ARCHITECT.md` 改名 `ARCHITECTURE.md`**（`0b4a0b9`，v3 Q52）：本 repo 與部署包範本都改；handoff skill 三個檔跟著改，部署包跳 `2026-11-20`。歷史檔與冷區 `archive/v2-experiments/README.md`（使用者同意）裡的舊連結改成純文字。
- **ARCHITECTURE 整改三批**（`c540701`、`aa6d49d`、`47d5a20`，264 → 141 行）：只留一句話、碰到才讀的文件、檔案地圖、副本拓撲、刻意沒有的東西。驗證器檢查表搬進 `verify_bootstrap.py` 檔頭；部署包範本表交給 kit.md；F46 例外宣告搬到決策書第 4 節 F46 底下（v3 Q53），「來源例外可見性」改讀決策書。下一個 Q 編號是 Q54。

## 未完成／下一步

1. **已部署專案的結構文件改名**：各專案仍是 `ARCHITECT.md`，`sync_project.py` 不會改名（歸專案的 seed 檔）。使用者還沒選做法：讓同步器改名，或各專案自己 `git mv`。**選之前不要把任何專案同步到 `2026-11-20`**，否則 skill 寫的檔名跟專案裡的對不上。
2. **這台 Mac 的兩份全域 handoff skill 還是 `2026-11-18.3`**：驗證器印「提醒」。覆蓋前要先問使用者。
3. **繼續依原則整理本 repo 文件**：使用者說「分類」與「索引」之後再談；AGENTS「這個 repo 是什麼」、README 第二段跟 ARCHITECTURE「一句話」三處重述同一件事，還沒處理。依草稿原則 4.2，「最後更新」只該寫日期；ARCHITECTURE、維護手冊、理由檔已改，其他文件的檔頭多半還寫著改了什麼。
4. **鍵鼠同部署_mac**：還在 `2026-11-17.3`，留著 `GEMINI.md` 與 `docs/ai-notes/handover-protocol.md`。2026-11-18 23:13 起 origin 上的「工作中」是 Windows 那台的 Codex session（本棒沒再查）；等它交棒、且第 1 項有了做法再同步。
5. **第 2 期（Codex＋macOS）、Q49 在 Windows 與 Codex 上跑**：使用者 2026-11-18 說先等等。序號卡、解決網路速度刻意停在舊版不動。

## 地雷與注意事項

- **討論模式**：使用者在文件體系的題目上要先討論取得共識，不要急著給方案；討論結論寫進草稿要使用者說了才寫。
- **換 v4 不是待辦**：真的換版時照 `docs/maintenance.md`「開發注意事項」的換版那條。
- **整個 `archive/` 是冷區**：AI 平常不讀，回溯或修改先經使用者同意。程式與測試不能引用 `archive/docs/` 的檔名，也不能指向 `archive/v<N>-`。
- **「版本更替」會掃程式檔的註解**：`v2` 用 `_` 或 `-` 黏在字上就算違反；寫歷史時用空格隔開。
- **驗證器不跑變異測試**：改到 `src/project_bootstrap/` 的檢查，要自己跑 `.venv/bin/python -X utf8 src/project_bootstrap/mutants.py --only tests.test_<模組>`。
- **根目錄有未追蹤檔時，`--staged` 會回 exit 2**：`comparison-adr-memory-bank.md` 是使用者自己放的。本棒每次提交前暫移到 scratchpad、驗證後原樣移回；不要刪它或提交它。
- **決策紀錄的狀態欄要寫出選了哪個字母**（例如「AI 依此選 (a)」）：只寫使用者原話，`test_trail_repo` 會把沒點名的選項算成沒交代理由。
- **README 的核心一節有兩句是檢查要的**：「核心優先序：SKILL.md」與「把漏做的機會壓低」，刪了「核心與實例優先序」「已修正的主張沒復活」會失敗。
- **`bootstrap.py` 是產物**：改 `src/kit/`、`installer.py` 或 `sync_project.py` 的合併函式後跑 `tools/build_kit.py`，同一個 commit 提交。
- **檔頭 `source: PROJECT-BOOTSTRAP.md v…` 的字樣不要改**：已部署專案的開場 hook 用這個字面比對版本。
- 其他開發時容易踩的地方在 `docs/maintenance.md` 的「開發注意事項」。

## 服務查證與期望快照

- 2026-11-20 macOS Mac mini，`47d5a20` 提交前：`python3 -X utf8 tools/verify_bootstrap.py --staged` → **exit 0，68 項全過**；`.venv/bin/python -m pytest tests` → 173 passed。全域 skill 兩份是 `2026-11-18.3`，該項只印提醒。
- 本棒沒跑變異測試（沒改 `src/project_bootstrap/` 的檢查邏輯，只改了 `contradictions.py`、`trail_sources.py`、`installer.py` 裡的檔名字串）。
- Windows 與已部署專案本棒沒跑；任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- 無。
