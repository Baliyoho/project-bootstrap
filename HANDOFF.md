# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-17 15:08（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（v2 決策書退休，v3 成為唯一需求書，v3 Q39）

## 任務目標

本棒讓 v2 需求決策書正式退休：v3 是唯一需求書，v2 凍結封存、不被任何程式讀取；回溯歷史要先經使用者同意。另提出根目錄資料夾整理方案（甲／乙／丙），使用者還沒選。制度方向不變，依需求決策書 v3。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：Mac mini ／ Claude Code（桌面 App）／ ㊣　11.17.17｜README職能分工｜工作中｜交棒0次；開工 2026-11-17 17:34（+08）
- **骨架版本**：`2026-11-17.2`
- 本棒沒動 `src/kit/`、部署包與 `VERSION`，各專案不需同步。
- 本機能力：Mac mini；`git push` 可用；本機 `.venv` 可跑驗證器不跑的 3 支外部套件測試（`PYTHONPATH=src .venv/bin/python -m pytest`）。

## 已完成

- **v2 退休**（`1266088`，需求決策書 v3 Q39，撤銷 Q32 (b) 的並存）：v2 以 `git mv` 封存到 `docs/history/requirements-decision-v2.md`，逐位元組不改。`verify_v2.py`、`test_registry_repo.py`（新）、`test_trail_repo.py` 與一致性檢查改讀 v3；需求清單與 v3 第 8 節改按節名找；讀 v2 第 7 節那條測試改成讀 v3 第 3 節的 D 表。
- **新守門「封存原件」**（`verify_bootstrap.py`）：封存檔 Git blob 不變、程式與測試不引用 v2 路徑（經使用者同意才可登記 `ARCHIVE_READERS`）、文件與行末檢查不讀 `docs/history/`；四種反例都擋。
- **修好 `test_registry` 的 mutation 假擋下**：原本 mutation 只複製 `src/`、`tests/`，這支讀不到真文件、每次出錯，8 個變異全是假擋下。改成合成資料，真文件部分拆到 `test_registry_repo.py`；registry 組 10 個、trail_sources 兩組 41 個（27＋14）變異實跑全部擋下（一個等效變異已換掉）。
- **macOS 驗證補跑**：前一棒在 Windows 做完後，macOS 沒重跑；本棒開工時跑過 exit 0。

## 未完成／下一步

1. **資料夾整理等使用者選方案**（本棒聊天中提出，尚未登記）：甲＝只把 14 份需求來回討論文件移到 `docs/history/`；乙＝全部分層進 `docs/`（需求書、設計、歷史），要改 5 支程式的路徑與 `src/kit/kit.md` 的 4 個 `audit.md` 連結並重生部署包；丙＝乙加刪減已結案文件，並把 ARCHITECT 開頭 134 行更新紀錄移出。使用者沒選之前不要開工。
2. **`learn coding with ai agent` 的骨架同步**：這台 Mac 有這個專案，但它 origin 的「工作中」是另一個 session（2026-11-16 21:38 開工，主題「三方對比報告」）。要那個 session 交棒，或使用者確認標記已無人使用，才能同步。
3. 序號卡、解決網路速度問題依使用者 2026-11-17 指示刻意停在舊版；Windows 開發人員模式與桌面 App 的 F50 互動驗證沿用既有暫緩。
4. F22 必讀量 13,900／12,000 字元，超標是既有狀態（本棒前 13,862），未處理；只印報告，不影響驗證結束碼。

## 地雷與注意事項

- **`docs/history/` 是封存區**：AI 平常不讀，回溯歷史要先經使用者同意。v2 原件的 blob 寫死在 `FROZEN_ARCHIVES`，改內容或搬走都會被擋。若資料夾整理把其他檔移進來：它們會被文件檢查略過，但不會自動凍結。
- 決策書解析器按節名（需求清單、方案約束、待決事項）找節，改節名會讓測試失敗。v3 第 8 節已決項的「未選／暫緩」子項要寫選項名，否則報 `alternative-incomplete`。
- 一致性檢查：同一行同時有 Q 編號和「待決」兩字（包括「等待決定」）會報 `decided-still-pending`。本棒寫 ARCHITECT 時踩到兩次。
- mutation 只複製 `src/`、`tests/`：讀真文件或 `tools/` 的測試一律放 `*_repo.py`，不放進 mutation 群組。
- **全套驗證在原生 Windows 約 3–4 分鐘**，超過指令工具預設的 120 秒上限；macOS 約 35 秒。逾時不等於失敗。
- `--staged` 在 index 空的時候 0 秒回 exit 2，那既不是過也不是失敗。Windows 上 `python3` 是 WindowsApps 別名，要用 `python`。
- 用腳本改 Python 時，heredoc 會吃掉反斜線；改完 grep 回驗。跳版時別忘了根目錄的 `VERSION`。
- 跨專案寫入一律先在該專案推開工標記，再用 `--owner`；同步完刪該專案的 `.claude/.bootstrap-version`。`sync_project.py` 的 MIGRATE 只比對標題。

## 服務查證與期望快照

- 2026-11-17 macOS Mac mini，`1266088` 提交前：`python3 -X utf8 tools/verify_bootstrap.py --staged` → **exit 0，67 項全過，無 skip**（含新的「封存原件」）。`verify_v2` 440 個測試 0 失敗、0 跳過；另外 3 支外部套件測試用 `.venv` 跑，7 passed。
- 本份 `HANDOFF.md` 提交前同指令再跑一次，結果見交棒回覆。
- Windows 本棒沒跑；前一棒 2026-11-17 是 68 項全過。兩平台項數不同，是部分檢查只在特定平台執行；接棒者在任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- 無。
