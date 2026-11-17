# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-17 18:20（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（README 與 AGENTS 改成職能分工、交接協定移出部署包、變更紀錄搬出部署包；v3 Q40、Q41）

## 任務目標

本棒依使用者兩個意圖整理入口文件：README 改成標準 README，AGENTS 只留開工必讀的部分，其他內容刪掉或搬到該放的地方。範圍包括部署包範本和本 repo 自己的檔案。接著做了整體檢查，修掉矛盾、重複和錯放的內容；再把交接協定移出部署包，並把部署包開頭的版本紀錄搬到 `CHANGELOG.md`。制度方向不變，依需求決策書 v3。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-17.2`
- 本棒跳了兩次版（`2026-11-17`、`2026-11-17.2`），七個 skill 檔與共用制度標記同版；本 repo AGENTS.md 的共用制度副本已重貼。這台 Mac 的兩份全域 skill（`~/.claude`、`~/.codex`）已覆蓋並逐檔比對一致；覆蓋前它們停在 `2026-11-16.6`，漏了 .7。
- 本機能力：Mac mini；`git push` 可用；本機 `.venv` 可跑驗證器不跑的 3 支外部套件測試（`PYTHONPATH=src .venv/bin/python -m pytest`）。

## 已完成

- **README／AGENTS 職能分工**（`2a47602`，v3 Q40）
  - 部署包範本：README 改成標準 README，依序是一句話、為什麼做、快速開始（含原本 AGENTS 的連線資料）、開發與驗證、結構指標、協作方式、授權；交接 prompt、三個入口表、檔案樹與紅線都刪掉。AGENTS 範本只留共用制度與鐵律。
  - 本 repo：AGENTS.md 從 92 行減到 61 行，碰到才需要的五節搬到新的 `CONTRIBUTING.md`；README 改成標準 README。
- **整體檢查與 skill 修正**（`400a751`，骨架 `2026-11-17`）
  - skill 不再說 AGENTS 有知識庫地圖。交接協定、kit.md、README、ARCHITECT 對開場 hook 的舊描述已改。
  - ARCHITECT 的「開發注意事項」搬到 CONTRIBUTING；HANDOFF 範本的地雷不再重複規則。
- **交接協定移出部署包**（`9974886`，v3 Q41，骨架 `2026-11-17.2`）
  - 部署包少一個檔，3.6 保留編號、改成移除說明。
  - 協定獨有的內容搬進 skill：分支模型進 `mode-b.md` B1，漏交棒理由進 `reasons.md`，「verify_state 一律跑」進 `mode-a-stop.md` A4。
  - 已部署專案裡的舊協定，同步時不改寫也不刪，只列 MIGRATE。
- **變更紀錄搬出部署包**（`bc64b9f`）：kit.md 開頭約 80 行逐字搬到 `CHANGELOG.md`，kit.md 從 126 KB 降到 64 KB；以後跳版時，舊的版本行移到 CHANGELOG 最上面。
- 驗證器跟著改寫的檢查：理由連結、結構摘要、主張沒復活、核心優先序、接力協調邊界、過期敘述。每項都有負向測試；部署包要是又產出交接協定，驗證會失敗。

## 未完成／下一步

1. **已部署專案同步到 `2026-11-17.2`**：每個專案都要先推開工標記，再用 `--owner` 跑 `sync_project.py`。
   - README 是 seed，不會自動變成標準 README，要逐一手動遷移；連線資料表也要從 AGENTS 搬到 README。
   - 舊的 `handover-protocol.md` 同步時會列 MIGRATE。裡面若有專案 override，先搬進 AGENTS 鐵律，刪不刪由使用者決定。
2. **`learn coding with ai agent` 的骨架同步**：它 origin 上的「工作中」仍是另一個 session（2026-11-16 21:38 開工，主題「三方對比報告」）。要那個 session 交棒，或使用者確認標記已無人使用，才能同步。
3. **資料夾整理等使用者選方案**（還沒登記）：甲＝只把十幾份需求來回討論文件移到 `docs/history/`；乙＝全部分層進 `docs/`；丙＝乙再加上刪減已結案文件。使用者沒選之前不要開工。
4. **根目錄的 `readme-agents-by-function.md`**：使用者放的外部企劃，本棒已依它做完（採縮小版）。它沒追蹤、也沒提交；要放進 repo 還是刪掉，由使用者決定。
5. 序號卡、解決網路速度問題，依使用者 2026-11-17 指示刻意停在舊版；Windows 開發人員模式與桌面 App 的 F50 互動驗證沿用既有的暫緩。

## 地雷與注意事項

- **根目錄有未追蹤檔時，`--staged` 會回 exit 2**：本棒每次先把企劃檔暫時移到 scratchpad，跑完再移回，並比對雜湊值。不要為了讓它通過而刪檔或提交它。
- **`docs/history/` 是封存區**：AI 平常不讀，回溯歷史要先經使用者同意。v2 原件的 blob 寫死在 `FROZEN_ARCHIVES`。
- **改 skill 會牽動兩份檔**：改到從舊 SKILL.md 逐字搬來的行，要在 `tools/skill_split_baseline.json` 的 `rewritten` 登記去處；請照原檔的 1 格縮排手動插入，不要用 `json.dumps` 整份重排。改了 `reasons.md` 對照表的右欄，要寫成「檔名 § 完整標題」。
- **`docs/ai-notes/` 現在只剩 `roadmap.md`**：測試用 `git rm` 刪它時，Git 會連空目錄一起刪，寫回前要先建目錄。
- 其他開發時容易踩的地方（zsh、mutation 測試、決策書解析器、Windows 耗時）在 `CONTRIBUTING.md` 的「開發注意事項」與「改部署包的流程」。

## 服務查證與期望快照

- 2026-11-17 macOS Mac mini，`bc64b9f` 提交前：`python3 -X utf8 tools/verify_bootstrap.py --staged` → **exit 0，67 項全過，無 skip**。
- 交棒前的一致性掃描：已移除的檔名、舊分工用語、舊 hook 描述與 skill 檔數，在現行文件裡都沒有殘留；剩下的命中是歷史紀錄、測試固定資料，或刻意保留的移除說明。
- `verify_v2` 回報 F22 必讀量 11,590／12,000 字元，**通過**；上一棒是 13,900，超標，這次因為 AGENTS.md 瘦身而降回來。
- 本份 `HANDOFF.md` 提交前，同指令會再跑一次，結果見交棒回覆。Windows 本棒沒跑；任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- 無。
