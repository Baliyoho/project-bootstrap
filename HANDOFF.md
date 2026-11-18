# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-18 23:45（+08），中途更新，本 session 仍在工作中
- **交棒者**：Claude Code（桌面 App）／Mac mini（待辦查核與執行：Q51、2026-11-18.3、全域 skill 檢查、同步 6 個專案）

## 任務目標

使用者要求先核對上一棒 HANDOFF 的 10 條待辦，再逐條決定：zsh 怪癖上移部署包、決策紀錄可標「被取代」、驗證器檢查全域 skill 版本、能升的已部署專案升級並刪掉 `GEMINI.md`；第 2 期與 Q49 的 Windows／Codex 先等等，序號卡、網路速度不動。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無（`feat/bootstrap-installer`、`feat/retire-kit-doc` 都已併回 `main`，分支留在 origin 沒刪）。
- **工作中**：`Mac mini` ／ `Claude Code（桌面 App）` ／ `㊣　11.18.23｜待辦執行｜工作中｜交棒0次`，2026-11-18 23:26 (+08) 開工
- **骨架版本**：`2026-11-18.3`
- 本機能力：Mac mini；`git push` 可用；本機 `.venv` 可跑驗證器不跑的外部套件測試（`.venv/bin/python -m pytest tests`）。`/usr/bin/python3` 是 3.9.6，跑不了 `bootstrap.py`（要 3.12），用另裝的 `python3`（3.15.2）。

## 已完成

- **zsh 三種寫法上移到 `env.md`**（`c9378fe`，跳版 `2026-11-18.3`）：維護手冊那條改成指向部署包。
- **決策紀錄可標「被取代」**（`c97111a`，v3 Q51）：子項「被取代：Qn：」與「部分被取代：Qn：」；Q32 被 Q39 取代，Q40、Q42、Q44、Q46 部分被取代。`trail.py` 加 `amended-by-unknown`、`successor-older`，變異組加 6 個。
- **驗證器檢查全域 handoff skill**（`d362198`）：這台 Mac 的兩份已依使用者同意覆蓋成 `2026-11-18.3`。家目錄兩份跟 `src/kit` 範本逐字比對，不同印「提醒」不影響結束碼（使用者選定），兩份都沒裝印 skip。
- **已部署專案升到 `2026-11-18.3` 並刪掉 `GEMINI.md`**（使用者 2026-11-18 指示）：NAA_TR（`feature/W15-research-shell`，`34da855`）、NAS_MAINT（`91a8983`）、academic-summary-skill（`cb15533`）、claude code內部操作（`e5fa5a5`）、grist-workflow（`a188f74`）、learn coding with ai agent（`bb0196a`，從 `2026-11-14.4` 升上來）。各自先推開工標記、`sync_project.py --write --owner`、改掉 AGENTS／README／ARCHITECT 指向 `GEMINI.md` 的說法、`check_docs.py` exit 0、推上後清回 `無（已交棒）`。

## 未完成／下一步

1. **鍵鼠同部署_mac**：還在 `2026-11-17.3`、留著 `GEMINI.md`。2026-11-18 23:13 起 origin 上的「工作中」是 Windows 那台的 Codex session；等它交棒再同步、刪檔（使用者已同意這兩件）。
2. **已部署專案的舊交接協定 `docs/ai-notes/handover-protocol.md`**：6 個專案都還在，同步器列 MIGRATE。刪不刪使用者還沒決定（這次只決定刪 `GEMINI.md`）。academic-summary-skill 的 AGENTS 標記外另有舊段落「跨模型／跨機器協作規範」，同步器要人工比對。
3. **第 2 期（Codex＋macOS）**：Codex 桌面 App 的 F50 標題項還沒判定、handoff-ab 要不要在現行版重跑；使用者 2026-11-18 說先等等。
4. **Q49 在 Windows 與 Codex 上跑**：分別歸第 3、2 期，使用者 2026-11-18 說先等等。
5. 序號卡、解決網路速度依使用者 2026-11-17 指示刻意停在舊版，2026-11-18 再確認不動（這兩個專案不在 GitHub projects 資料夾）；Windows 開發人員模式與桌面 App 的 F50 互動驗證沿用既有的暫緩。

## 地雷與注意事項

- **換 v4 不是待辦**：使用者說這是假設性的提醒。真的換版時照 `docs/maintenance.md`「開發注意事項」的換版那條，把 v3 的決策書、計畫、兩份歷史紀錄，以及寫死 v3 檔名的 `contradictions.py`、`run_tests.py`、3 支 `*_repo` 測試封存或改名。
- **整個 `archive/` 是冷區**：AI 平常不讀，回溯先經使用者同意。程式與測試不能引用 `archive/docs/` 的檔名，也不能指向 `archive/v<N>-`。
- **「版本更替」會掃程式檔的註解**：`v2` 用 `_` 或 `-` 黏在字上就算違反；寫歷史時用空格隔開。
- **驗證器不跑變異測試**：改到 `src/project_bootstrap/` 的檢查，要自己跑 `.venv/bin/python -X utf8 src/project_bootstrap/mutants.py --only tests.test_<模組>`。
- **根目錄有未追蹤檔時，`--staged` 會回 exit 2**：根目錄的 `comparison-adr-memory-bank.md` 是使用者自己放的（看起來是 learn coding 那份對比報告的副本）。本棒經使用者同意每次提交前暫移到 scratchpad、驗證後原樣移回（sha 不變）；不要刪它或提交它。
- **`docs/ai-notes/` 只剩 `roadmap.md`**：測試用 `git rm` 刪它時 Git 會連空目錄一起刪，寫回前要先建目錄。
- **`bootstrap.py` 是產物**：改 `src/kit/`、`installer.py` 或 `sync_project.py` 的合併函式後跑 `tools/build_kit.py`，同一個 commit 提交。`PROJECT-BOOTSTRAP.md` 已退休，放回來會被擋。
- **檔頭 `source: PROJECT-BOOTSTRAP.md v…` 的字樣不要改**：已部署專案的開場 hook 用這個字面比對版本。
- 其他開發時容易踩的地方在 `docs/maintenance.md` 的「開發注意事項」。

## 服務查證與期望快照

- 2026-11-18 23:45 macOS Mac mini，本份 HANDOFF 提交前：`python3 -X utf8 tools/verify_bootstrap.py --staged` → **exit 0，68 項全過，無 skip，無提醒**（兩份全域 skill 已依使用者同意用 `2026-11-18.3` 範本覆蓋）；`mutants.py` 的 `test_trail` 27 個、`test_trail_sources` 45 個全擋。
- 6 個已部署專案：`check_docs.py` 都 exit 0；`verify_state.py` 5 個 exit 0，grist-workflow exit 2（`errors=0 skipped=2`，缺 `GRIST_API_KEY`，跟它 HANDOFF 記的既有狀態相同）。
- Windows 本棒沒跑；任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- 無。
