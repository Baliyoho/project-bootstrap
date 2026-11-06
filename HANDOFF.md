# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-06 16:45（+08）
- **交棒者**：Claude Code ／ `baliyohodeMini`（第一次在 Mac 上接棒；修 macOS bash 3.2 在 UTF-8 語系下吃掉 `$變數` 後全形字的 bug）

## 任務目標

**使用者 2026-11-06 指示**：把 repo 同步到 Mac 並套用本專案的交接棒制度 → 同意安裝兩份全域 skill → 「修它」（Mac 上驗證三項 FAIL 的那個 bug）。

**需求層的現況不變**：[需求文件](project-bootstrap-requirements.md) v3.10，50 條每條都有強度，第 6 節沒有待決項；F42–F49 八條**全部沒有實作、沒有驗收**（上一輪 Windows 的結論，本輪未動需求）。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-03`
- 本輪刻意不跳版：`SKILL.md` 沒動，只改了 3.10／3.18 兩支 hook（鐵律 1）。
- 本機能力：`DESKTOP-M8MRS05`＝Windows 11、Python 3.13、Git Bash、PowerShell；`baliyohodeMini`＝macOS、Python 3.15（只有 `python3`）、`/bin/bash` 3.2.57。

## 已完成

- **Mac 端就位**：repo clone 到 Mac；全域 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/` 已裝，內容與部署包重生的 `SKILL.md`（`v2026-11-03`）逐位元組相同。
- **bash 3.2 多位元組變數 bug**：macOS 的 bash 3.2 在 UTF-8 語系下會把 `$變數` 後緊接的中文／全形字的第一個位元組吃進變數名（`（branch=$branch）` 印成 `（branch=��`）。判斷邏輯不受影響，壞的是結論訊息；`ag-wrap.sh` 找不到腳本時連 JSON 都吐不出來。Windows 的 bash 5 不重現。
  - 部署包 3.10 `git-freshness.sh` 21 處、3.18 `ag-wrap.sh` 1 處、本 repo `repo-git-check.sh` 17 處改成 `${變數}`；3.10／3.18 的 `source:` 標記更新為 `v2026-11-06`（當天第一個帶標記的改動）。3.11 與其他範本沒有命中、沒動。
  - `verify_bootstrap.py` 新增「bash 3.2 多位元組變數」靜態掃描（骨架與本 repo 全部 `.sh`，略過整行註解）＋ 6 個正負向探針；拿修正前的 `repo-git-check.sh` 給它跑抓到 17 處。
  - 部署包修訂記錄加一筆「刻意不跳版」；`AGENTS.md`「改兩支 hook 的訊息時」補這條規則與理由。
- **驗證器在 Mac 上的偶發崩潰**：Git 2.54（Apple Git-157）每次 commit／push 後都在背景跑 `git maintenance run --auto --detach`，小 repo 也會 repack＋寫 MIDX，跟 R03 owner 情境緊接的本機 clone 撞車（約一半機率 `failed to copy file`，整支驗證器崩潰）。GIT_TRACE2 確認過。`GIT_ENV` 的 `GIT_CONFIG_GLOBAL` 從 `/dev/null` 改成只寫 `maintenance.auto=false` 的臨時檔；`GIT_CONFIG_COUNT` 不行，本機 push 會把它從 receive-pack 那端清掉。只動測試環境，部署包與 `sync_project.py` 沒動。

## 未完成／下一步

1. **把這次 hook 修正同步到各部署專案**（部署專案都在 Windows 那台，Mac 上一個都沒有）：在那台逐專案先完成 A1–A5，再跑 `python -X utf8 tools/sync_project.py <專案路徑> --owner '<工作中欄位完整值>' --write`。只有 `git-freshness.sh` 與 `ag-wrap.sh` 變、`SKILL.md` 沒變，所以**不會**印「骨架落後」，不同步也沒有任何提醒。
2. **F42–F49 八條全部未實作、未驗收**。每條都要按 F29 附會失敗的反例。建議順序：**F45** → **F43**(a) → **F44** → 其餘。
3. **F46 的偵測部分未實作**（宣告為例外已寫進 ARCHITECT）；`verify_bootstrap.py` 還不會把那三項列成已宣告的例外。
4. **F21 的阻擋層尚未實作**：要先指出擋在哪一層。
5. **F41 的七個缺口未修**（想要，不是排程），詳見 F41 驗收。
6. 需求第 7 節第 1 步的**現況對照**未建立（50 條）。
7. [第二輪複審快照](project-bootstrap-reaudit-2026-11-03.md) R01–R09 未逐項核對修正邊界。
8. [效率計畫](project-bootstrap-efficiency-plan.md) P0／P1 未實作；第 14 章 S1 仍待採納。

## 地雷與注意事項

- 冷啟動先依 [AGENTS.md](AGENTS.md) 完成 A；改檔前重新取得自己的工作中標記。
- **Mac 上 `python` 不存在**，所有 `python -X utf8 …` 都改用 `python3`。Python 3.7+ 會在 C 語系下自動把子程序設成 `C.UTF-8`，所以 Mac 上 `verify_bootstrap.py` 實跑的 hook 一定在 UTF-8 下——這正是這次 bug 會現形的原因。
- **新增 shell 訊息時 `$變數` 緊接全形字一律加大括號**；靜態掃描會擋，但它不懂引號，單引號裡的 `$x）` 也會被要求改（往嚴的方向）。
- **第 6 節空了只代表決策沒有缺口**；下次有未決事項要寫回第 6 節。
- **F45 還沒實作**，「待決沒登記」「兩節互相矛盾」仍然只靠人讀。
- **50 條的強度全部是使用者的決定**，不得從現行程式能力反推或下調；v3.3–v3.10 同一天採納，必須看版本。
- 歷史小節與帶日期的審閱敘述**不改寫**，追加帶日期的勘誤並在原處留「已更正」指標。
- 用腳本改 `.md` 不要手寫 `\u` 轉義，patch 一律「命中數 ≠ 1 就 abort」。
- **根目錄多／少一個 `.md` 就要同一個 commit 改 ARCHITECT**，沒有檢查守得住。
- **操作者 1 人仍是未查證的工作假設**。

## 服務查證與期望快照

`python3 -X utf8 tools/verify_bootstrap.py`（Mac）：exit 0、**51 項全過、無 skip**。修正前同一台是 exit 2、3 項 FAIL（Antigravity 接線、git-freshness 工作中標記、本 repo 工作中判讀）。
Windows 上次是 52 項；差別是「Codex Windows 啟動器／結束碼」兩項只在 Windows 執行、其他平台不記錄（不算 skip），加上本輪新增 1 項，所以 Windows 下一次應是 **53 項**。本輪未在 Windows 重跑。
本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用上述替代入口。Codex 接線未改，不需重審 hook。

## 懸置事項（AI 勿自行處理）

- 需求層目前沒有待決項。F21 阻擋層、F41 缺口與 F42–F49 都是實作待辦，不是待決。
- 原子 claim 另案，Antigravity IDE 不重開；額外模型探針須先授權且只用訂閱額度（這條本身現在是 F48）。
