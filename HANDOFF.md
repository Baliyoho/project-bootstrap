# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-20 20:12（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（session 名稱拿掉 `※` 待你決定、更新這台 Mac 的全域 handoff skill）

## 任務目標

使用者在討論 AI 協作 repo 的文件體系，先跟 AI 取得共識再動手。共識寫在 [collaboration-system-principles-draft.md](collaboration-system-principles-draft.md)（前提、效用、設計原則；草稿，還不是約束文件，最終要跟決策書與計畫整合成一份新文件，名稱未定）。上一棒依原則整理了 README、維護手冊與 ARCHITECTURE；這一棒照使用者指示改了 session 狀態標記。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無（`feat/bootstrap-installer`、`feat/retire-kit-doc` 都已併回 `main`，分支留在 origin 沒刪）。
- **工作中**：`Mac mini` ／ `Claude Code` ／ `㊣　11.20.20｜整理文件｜工作中｜交棒0次`，2026-11-20 20:17 (+08) 開工
- **骨架版本**：`2026-11-21.2`
- 本機能力：Mac mini；`git push` 可用；本機 `.venv` 可跑驗證器不跑的外部套件測試（`.venv/bin/python -m pytest tests`）。`/usr/bin/python3` 是 3.9.6，跑不了 `bootstrap.py`（要 3.12），用另裝的 `python3`（3.15.2）。

## 已完成

- **session 名稱拿掉 `※` 待你決定**（`94211d8`，決策書 v3 Q54，使用者指定）：共用制度只剩 `㊣` 工作中、`↗` 已交棒；停下等決定的回覆不再要求 `session：` 一行（AI 連帶拿掉，已告知使用者，要加回再說）。handoff skill 四個檔拿掉 `※` 的規則與理由一節，七個檔與共用制度標記跳 `2026-11-20.2`；原理由留在 CHANGELOG。決策書 F50 與第 5 節跟著改，下一個 Q 編號是 Q55。
- **這台 Mac 的兩份全域 handoff skill 更新到 `2026-11-20.2`**（`~/.claude/skills/handoff/`、`~/.codex/skills/handoff/`）：覆蓋前核對過 14 個檔都跟 `2026-11-18.3` 範本逐位元組相同，沒有本機改動。驗證器的同版提醒已消失。

## 未完成／下一步

1. **已部署專案的結構文件改名**：各專案仍是 `ARCHITECT.md`，`sync_project.py` 不會改名（歸專案的 seed 檔）。使用者還沒選做法：讓同步器改名，或各專案自己 `git mv`。**選之前不要把任何專案同步到 `2026-11-20` 以後的版本**，否則 skill 寫的檔名跟專案裡的對不上。
2. **繼續依原則整理本 repo 文件**：使用者說「分類」與「索引」之後再談；AGENTS「這個 repo 是什麼」、README 第二段跟 ARCHITECTURE「一句話」三處重述同一件事，還沒處理。依草稿原則 4.2，「最後更新」只該寫日期；ARCHITECTURE、維護手冊、理由檔、AGENTS、CHANGELOG、決策書與其歷史紀錄已改，其他文件的檔頭多半還寫著改了什麼。
3. **鍵鼠同部署_mac**：還在 `2026-11-17.3`，留著 `GEMINI.md` 與 `docs/ai-notes/handover-protocol.md`。2026-11-18 23:13 起 origin 上的「工作中」是 Windows 那台的 Codex session（本棒沒再查）；等它交棒、且第 1 項有了做法再同步。
4. **第 2 期（Codex＋macOS）、Q49 在 Windows 與 Codex 上跑**：使用者 2026-11-18 說先等等。序號卡、解決網路速度刻意停在舊版不動。
5. **`verify_bootstrap.py` 檔頭表「skill 拆分」一列寫「已改寫清單（13 行）」**：實際已是 69 行，這一棒之前就過期了，沒改。

## 地雷與注意事項

- **討論模式**：使用者在文件體系的題目上要先討論取得共識，不要急著給方案；討論結論寫進草稿要使用者說了才寫。
- **換 v4 不是待辦**：真的換版時照 `docs/maintenance.md`「開發注意事項」的換版那條。
- **整個 `archive/` 是冷區**：AI 平常不讀，回溯或修改先經使用者同意。程式與測試不能引用 `archive/docs/` 的檔名，也不能指向 `archive/v<N>-`。
- **「版本更替」會掃程式檔的註解**：`v2` 用 `_` 或 `-` 黏在字上就算違反；寫歷史時用空格隔開。
- **驗證器不跑變異測試**：改到 `src/project_bootstrap/` 的檢查，要自己跑 `.venv/bin/python -X utf8 src/project_bootstrap/mutants.py --only tests.test_<模組>`。
- **根目錄有未追蹤檔時，`--staged` 會回 exit 2**：`comparison-adr-memory-bank.md` 是使用者自己放的。提交前暫移到 scratchpad、驗證後原樣移回；不要刪它或提交它。
- **決策紀錄要有子項**：`採用理由：`、每個沒選的字母一條 `未選 (x)：`，狀態欄寫出選了哪個字母（例如「AI 依此選 (a)」）；少了 `test_trail_repo` 會失敗。
- **刪改 skill 的行要登記 `tools/skill_split_baseline.json` 的 `rewritten`**：拆分前單檔的每一行要嘛留著、要嘛寫去處，否則「skill 拆分」FAIL。這個檔是 1 格縮排，重寫時保持原格式。
- **README 的核心一節有兩句是檢查要的**：「核心優先序：SKILL.md」與「把漏做的機會壓低」，刪了「核心與實例優先序」「已修正的主張沒復活」會失敗。
- **`bootstrap.py` 是產物**：改 `src/kit/`、`installer.py` 或 `sync_project.py` 的合併函式後跑 `tools/build_kit.py`，同一個 commit 提交。
- **檔頭 `source: PROJECT-BOOTSTRAP.md v…` 的字樣不要改**：已部署專案的開場 hook 用這個字面比對版本。
- 其他開發時容易踩的地方在 `docs/maintenance.md` 的「開發注意事項」。

## 服務查證與期望快照

- 2026-11-20 macOS Mac mini，`94211d8` 提交前：`python3 -X utf8 tools/verify_bootstrap.py --staged` → **exit 0，68 項全過**；`.venv/bin/python -m pytest tests` → 173 passed。全域 skill 更新後重跑全套驗證 exit 0，沒有提醒。
- 本棒沒跑變異測試（沒改 `src/project_bootstrap/`）。
- `※` 拿掉後的規則沒有在互動 session 實測過（F50 的互動驗證是 `2026-11-13` 版）。
- Windows 與已部署專案本棒沒跑；任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- 無。
