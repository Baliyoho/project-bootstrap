# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-17 20:41（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（需求與計畫文件只留兩份權威、其餘封存；第 1 期結案；現況索引改 v3；明確不支援 Gemini）

## 任務目標

本棒依使用者指示整理根目錄的需求與計畫文件：只留需求決策書 v3（要什麼）與新寫的實施計畫 v3（怎麼走過去），其餘封存到 `archive/docs/`；接著依使用者決定把第 1 期結案、現況索引改成 v3 寫法，做一輪矛盾與重複的清理，最後拿掉 Gemini 相關的一切。制度方向不變，依需求決策書 v3。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：Mac ／ Claude Code（桌面 App）／ 11.17.20｜待指派（2026-11-17 20:55 +08 開工）
- **骨架版本**：`2026-11-17.3`
- 本棒跳了一次版（`2026-11-17.3`，拿掉 `GEMINI.md`），七個 skill 檔與共用制度標記同版，本 repo AGENTS.md 的共用制度副本已重貼。**這台 Mac 的兩份全域 skill（`~/.claude`、`~/.codex`）還停在 `2026-11-17.2`**：覆蓋指令被工具權限擋下，見下一步 3。
- 本機能力：Mac mini；`git push` 可用；本機 `.venv` 可跑驗證器不跑的外部套件測試（`PYTHONPATH=src .venv/bin/python -m pytest`）。

## 已完成

- **兩份權威＋封存區**（`39cea71`）：新寫 `project-bootstrap-implementation-plan-v3.md`（使用者判定 v2 的 P0–P5 不再算數，照 v3 三期重新規劃，只引用需求 ID）。19 份查核、複審、計畫、需求歷史與需求來回討論 `git mv` 到 `archive/docs/`，加索引 `archive/docs/README.md`。分工規則在 CONTRIBUTING「需求與計畫文件的分工」。
- **封存檢查擴大**：`verify_bootstrap.py`「封存原件」改擋程式引用封存區任何檔名（索引除外），附負向測試；`trail_sources` 按節名讀 plan v3，`test_trail_repo` 跟著改。
- **第 1 期結案、現況索引改 v3**（`47b5b78`）：plan v3 記使用者判定；`status.json` 照 v3 強度，退役與「想要」標不適用，v2 時的「不通過」改回未驗證；`verify_v2` 不再以 12,000 字元判 F22。handoff-ab 的改進計畫與 ARCHITECT 開頭約 140 行的變更紀錄也封存；AGENTS 的封存規則涵蓋整個 `archive/docs/`。
- **明確不支援 Gemini**（`bbb4ef7`，骨架 `2026-11-17.3`）：部署包不再產出 `GEMINI.md`，本 repo 的也刪了；`sync_project.py` 對已部署的舊檔只列 MIGRATE；結構摘要檢查擋 `GEMINI.md` 回到表格；v2 原型拿掉 Gemini 的檢查與名稱。
- 根目錄的 `readme-agents-by-function.md` 依使用者指示移到 macOS 垃圾桶（沒有永久刪除）。

## 未完成／下一步

1. **已部署專案同步到 `2026-11-17.3`**：每個專案都要先推開工標記，再用 `--owner` 跑 `sync_project.py`。
   - README 是 seed，不會自動變成標準 README，要逐一手動遷移；連線資料表要從 AGENTS 搬到 README。
   - 舊的 `handover-protocol.md` 與 `GEMINI.md` 同步時會列 MIGRATE，不改寫也不刪；刪不刪由使用者決定。
2. **`learn coding with ai agent` 的骨架同步**：它 origin 上的「工作中」仍是另一個 session（2026-11-16 21:38 開工，主題「三方對比報告」）。要那個 session 交棒，或使用者確認標記已無人使用，才能同步。
3. **覆蓋這台 Mac 的兩份全域 skill 到 `2026-11-17.3`**：已比對過，跟新版只差三行 Gemini 與版本標記，沒有本機自訂。做法：在 repo 根目錄用 `verify_bootstrap.extract()` 重生到暫存目錄，再把 `.claude/skills/handoff/*.md` 複製到 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/`，逐檔比對一致。需要使用者准許寫入家目錄。
4. **第 2 期（Codex＋macOS）**：Codex 桌面 App 的 F50 標題項還沒判定；當時的 handoff-ab 結果要不要在現行版重跑，使用者沒有決定。路線見 plan v3 第 3 節。
5. 序號卡、解決網路速度問題，依使用者 2026-11-17 指示刻意停在舊版；Windows 開發人員模式與桌面 App 的 F50 互動驗證沿用既有的暫緩。

## 地雷與注意事項

- **`archive/docs/` 是封存區**：AI 平常不讀，回溯歷史先經使用者同意。程式與測試裡出現封存區任何檔名都會被「封存原件」擋；v2 原件的 blob 寫死在 `FROZEN_ARCHIVES`。
- **驗證器不跑變異測試**：改到 `src/project_bootstrap/` 或它的測試，要自己跑 `PYTHONPATH=src python3 -X utf8 -m project_bootstrap.mutants --only <測試模組>`。本棒曾因此讓 `trail_sources` 群組多出存活與過期的 mutant，下一個 commit 才修掉。`test_selftest` 群組的 `platform or THIS_PLATFORM` 本來就存活，不是本棒造成，沒修。
- **改 skill 會牽動兩份檔**：改到從舊 SKILL.md 逐字搬來的行，要在 `tools/skill_split_baseline.json` 的 `rewritten` 登記去處，照原檔 2 格縮排手動插入，不要用 `json.dumps` 整份重排。
- **根目錄有未追蹤檔時，`--staged` 會回 exit 2**：不要為了讓它通過而刪檔或提交它。
- **`docs/ai-notes/` 只剩 `roadmap.md`**：測試用 `git rm` 刪它時 Git 會連空目錄一起刪，寫回前要先建目錄。
- 其他開發時容易踩的地方在 `CONTRIBUTING.md` 的「開發注意事項」。

## 服務查證與期望快照

- 2026-11-17 macOS Mac mini，`bbb4ef7` 提交前：`python3 -X utf8 tools/verify_bootstrap.py --staged` → **exit 0，67 項全過，無 skip**；`.venv` 的 pytest 447 項全過；改到的變異群組 `trail_sources`、`contradictions`、`registry`、`gitclaim`、`surfaces` 全擋，`selftest` 1 個既有存活。
- F22 依 v3 D11 的行數預算判定，`verify_bootstrap.py` 守；`verify_v2` 印的常態入口字元數只是觀測值。
- 本份 `HANDOFF.md` 提交前，同指令會再跑一次，結果見交棒回覆。Windows 本棒沒跑；任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- 無。
