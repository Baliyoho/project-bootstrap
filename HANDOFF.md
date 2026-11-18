# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-18 14:25（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（歷史分冷熱兩區、冷區合併到 `archive/`、v2 的程式全部退出 main、版本更替守門）

## 任務目標

本棒依使用者指示整理資料夾結構與 v2 殘留：歷史分冷熱兩區（Q44）、兩個 archive 合併成根目錄冷區並把現況索引搬到 `docs/`（Q45）、v2 的程式全部封存或改成 v3（Q46）、守門改成任何版本都適用的「版本更替」（Q47）。之前同 session 還做了 Q42（權威文件只留現況）與 Q43（鐵律 7）。制度方向不變，依需求決策書 v3。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無（Q49 的 `feat/bootstrap-installer`、Q50 的 `feat/retire-kit-doc` 都已併回 `main`，分支留在 origin 沒刪）。
- **工作中**：`Mac mini` ／ `Claude Code` ／ `㊣　11.18.14｜待指派｜工作中｜交棒0次`，2026-11-18 14:30 (+08) 開工
- **骨架版本**：`2026-11-18.2`
- 本棒跳版兩次：`2026-11-18`（Q49）、`2026-11-18.2`（Q50），handoff skill 七個檔與 `AGENTS.md` 共用制度標記同版。這台 Mac 的兩份全域 skill（`~/.claude`、`~/.codex`）還停在 `2026-11-17.3`；已部署的專案依使用者指示沒動。
- 本機能力：Mac mini；`git push` 可用；本機 `.venv` 可跑驗證器不跑的外部套件測試（`.venv/bin/python -m pytest tests`）。

## 已完成

- **歷史分冷熱兩區**（`be3f01d`，Q44）：熱歷史 `docs/history/` 放決策書與實施計畫的歷史紀錄，碰到就讀、不用先問。
- **冷區合併**（`e1af144`，Q45）：封存文件在 `archive/docs/`，整個 `archive/` 平常不讀、要回溯先經使用者同意；現況索引搬到 `docs/status.json`。
- **v2 的程式全部退出 main**（`3e45aab`、`d04accf`，Q46）：簽章發布通道封存到 `archive/v2-channel/`（origin 上的 `channel/beta/*` tag 沒動，`release.yml` 一併封存），沒人用的原型封存到 `archive/v2-prototypes/`。`verify_v2.py` 改名 `tools/run_tests.py`；`surfaces` 不再依賴 `selftest`；現況索引只留 v3 的強度、處置與現行證據；`mutants.json` 只留 8 組 193 個變異。
- **版本更替守門**（`ac222e1`，Q47）：驗證器新增「版本更替」。現行版本取 AGENTS 連到的決策書；`archive/` 以外帶舊版本號的檔名、資料夾名、程式識別字，以及程式引用 `archive/v<N>-`，都會被擋。
- 同 session 稍早：6 個已部署專案同步到 `2026-11-17.3`，全域 skill 覆蓋到同版。
- **維護手冊與理由檔搬進 `docs/`**（`63c4193`，Q48）。
- **部署方式改成安裝程式**（Q49）：對外的安裝途徑改成 `bootstrap.py`（`build_kit.py` 生成，內嵌範本與 `sync_project.py` 的合併函式，原始碼在 `src/project_bootstrap/installer.py`）；`mode-0.md` 改成跑安裝程式再處理第一批工作，部署包第 5 節的清單搬進它的 0-6；`--zip` 與兩項 ZIP 檢查拿掉；新增「安裝程式由來源生成」、`tests/test_installer.py`（14 個變異全擋）與 `tests/test_bootstrap_repo.py`。
- **`PROJECT-BOOTSTRAP.md` 退休**（Q50）：不再生成與提交，驗證器與同步器在記憶體組出全文；同步器的「已發布版本」改從它的 Git 歷史加 `bootstrap.py` 的歷史取；檔頭 `source: PROJECT-BOOTSTRAP.md v…` 的字樣刻意不改（已部署的開場 hook 用它比對版本）。

## 未完成／下一步

1. **換 v4 時**：AGENTS 改連新版決策書後，「版本更替」會擋下 v3 的決策書、實施計畫、兩份歷史紀錄，以及寫死 v3 檔名的 `contradictions.py`、`run_tests.py` 和 3 支 `*_repo` 測試。照 `docs/maintenance.md`「開發注意事項」的換版那條逐一封存或改名。
2. **第 2 期（Codex＋macOS）**：Codex 桌面 App 的 F50 標題項還沒判定；當時的 handoff-ab 結果要不要在現行版重跑，使用者沒有決定。路線見 plan v3 第 3 節。
3. **`learn coding with ai agent` 的骨架同步**：它 origin 上的「工作中」仍是另一個 session（2026-11-16 開工，主題「三方對比報告」），骨架停在 `2026-11-14.4`。使用者 2026-11-17 說先放著；要那個 session 交棒，或使用者確認標記已無人使用，才能同步。
4. **已部署專案的舊 `GEMINI.md` 與舊交接協定檔**：6 個專案都還留著 `GEMINI.md`，刪不刪由使用者決定，不要自己刪。
5. **決策紀錄的「被取代」狀態**：曾提議加這個狀態（例如 Q32 被 Q39 取代、Q42 的位置被 Q44 取代）並寫明欄位格式，使用者還沒回覆；要做先問。
6. **工具與平台怪癖上移到部署包 `env.md`（Q48 另案，要先問使用者）**：`docs/maintenance.md`「開發注意事項」裡 zsh 的三條（管線結束碼用 `${pipestatus[1]}`、`echo =====` 會被當成檔名展開、未加引號的 `$變數` 不拆字）適合上移；Windows 驗證超過 120 秒與 `python3` 別名 `env.md` 已有。改部署包要跳版並同步。
7. 序號卡、解決網路速度問題依使用者 2026-11-17 指示刻意停在舊版；Windows 開發人員模式與桌面 App 的 F50 互動驗證沿用既有的暫緩。
8. **verify_bootstrap.py 檢查本機全域 handoff skill 是否和目前部署包同版**，不同就提醒重裝；沒裝印 skip（使用者 2026-11-18 指定，這次不做）。
9. **已部署專案升級到 `2026-11-18.2`**：照舊用 `sync_project.py`（Q50 使用者選定）；它們沒有 `.bootstrap/answers.json`，`bootstrap.py update` 會拒絕。同步要使用者授權。
10. **Q49 還沒在 Windows 與 Codex 上跑**：Windows 的安裝、換行與 hook 歸第 3 期，Codex 接手第一批工作歸第 2 期（計畫 v3 第 3 節）。

## 地雷與注意事項

- **整個 `archive/` 是冷區**：AI 平常不讀，回溯先經使用者同意。程式與測試不能引用 `archive/docs/` 的檔名，也不能指向 `archive/v<N>-`。
- **新驗證項「版本更替」會掃程式檔的註解**：`v2` 用 `_` 或 `-` 黏在字上（例如 `step_v2`）就算違反；寫歷史時用空格隔開。
- **驗證器不跑變異測試**：改到 `src/project_bootstrap/` 的檢查，要自己跑 `.venv/bin/python -X utf8 src/project_bootstrap/mutants.py --only tests.test_<模組>`。
- **根目錄有未追蹤檔時，`--staged` 會回 exit 2**：目前根目錄有使用者自己放的 `comparison-adr-memory-bank.md`（未追蹤，不是本棒建立）。本棒每次提交前都先經使用者同意把它暫移到 scratchpad、驗證後原樣移回；不要刪它或提交它。
- **`docs/ai-notes/` 只剩 `roadmap.md`**：測試用 `git rm` 刪它時 Git 會連空目錄一起刪，寫回前要先建目錄。
- 其他開發時容易踩的地方在 `docs/maintenance.md` 的「開發注意事項」。

## 服務查證與期望快照

- 2026-11-18 macOS Mac mini，Q50 提交前：`python3 -X utf8 tools/verify_bootstrap.py --staged` → **exit 0，67 項全過，無 skip**；`.venv` 的 pytest 171 項全過；`mutants.py` 207 個全擋。
- Windows 本棒沒跑；任一平台看到失敗都是回歸。

## 懸置事項（AI 勿自行處理）

- 無。
