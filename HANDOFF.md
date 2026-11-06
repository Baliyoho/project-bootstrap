# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-06 17:10（+08）
- **交棒者**：Codex CLI ／ `baliyohodeMini`（需求歷史與現行決策分家）

## 任務目標

使用者要求保留需求原件為 history，另寫清晰、可執行的 decision，並授權 AI 決定整理中的待定與不妥處。
現行需求見 [需求決策書](project-bootstrap-requirements-decision.md)；原 v3.10 全文見 [歷史原件](project-bootstrap-requirements-history.md)。需求整理不代表功能已實作。F42–F49 仍未實作、未驗收。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-03`
- 本輪只改需求與入口文件，未改部署包、skill、hook、接線或 VERSION。
- 本機能力：`DESKTOP-M8MRS05`＝Windows 11、Python 3.13、Git Bash、PowerShell；`baliyohodeMini`＝macOS、Python 3.15（只有 `python3`）、`/bin/bash` 3.2.57。

## 已完成

- 原需求全文保留並改名 history；新增 decision（約 7,500 字元，原約 42,800），保留 50 ID、46 必要／4 想要及強度，移除現行正文中的過期敘述與修訂流水帳。
- 本輪授權下補 F11(a) 失效判準、F22 成本上限、F24／F30／F31 容量基準，澄清 F42／F44／F48 有效範圍內授權不重問；理由見決策書第 7 節。
- AGENTS 改為短入口；ARCHITECT 登記分家，舊報告連結改指 history，歷史正文保留。
- 前輪 Mac bash 3.2 修正與驗證器 Git maintenance 競態修正保留；部署專案同步與 Codex 開場 hook 實際注入仍待驗收。

## 未完成／下一步

1. **把這次 hook 修正同步到各部署專案**（部署專案都在 Windows 那台，Mac 上一個都沒有）：在那台逐專案先完成 A1–A5，再跑 `python -X utf8 tools/sync_project.py <專案路徑> --owner '<工作中欄位完整值>' --write`。只有 `git-freshness.sh` 與 `ag-wrap.sh` 變、`SKILL.md` 沒變，所以**不會**印「骨架落後」，不同步也沒有任何提醒。
2. **Mac 的 Codex 開場 hook 驗收**（使用者自己做，會用到 Codex 額度）：在 Codex App 開啟本 repo 並信任 → Hooks 設定審核 SessionStart → 新 session 送一則短訊息，確認出現 `[repo-check]` 開場訊息（skill B5）。
3. **F42–F49 八條全部未實作、未驗收**。每條都要按 F29 附會失敗的反例。建議順序：**F45** → **F43**(a) → **F44** → 其餘。
4. **F46 的偵測部分未實作**（宣告為例外已寫進 ARCHITECT）；`verify_bootstrap.py` 還不會把那三項列成已宣告的例外。
5. **F21 的阻擋層尚未實作**：要先指出擋在哪一層。
6. **F41 的七個缺口未修**（想要，不是排程），詳見 F41 驗收。
7. 依決策書第 5 節建立 **50 條現況對照**；新增成本基準須實測，不因本次定案而當作達成。
8. [第二輪複審快照](project-bootstrap-reaudit-2026-11-03.md) R01–R09 未逐項核對修正邊界。
9. [效率計畫](project-bootstrap-efficiency-plan.md) P0／P1 未實作；第 14 章 S1 仍待採納。

## 地雷與注意事項

- 冷啟動先依 [AGENTS.md](AGENTS.md) 完成 A；改檔前重新取得自己的工作中標記。
- **Mac 上 `python` 不存在**，所有 `python -X utf8 …` 都改用 `python3`。Python 3.7+ 會在 C 語系下自動把子程序設成 `C.UTF-8`，所以 Mac 上 `verify_bootstrap.py` 實跑的 hook 一定在 UTF-8 下——這正是這次 bug 會現形的原因。
- **新增 shell 訊息時 `$變數` 緊接全形字一律加大括號**；靜態掃描會擋，但它不懂引號，單引號裡的 `$x）` 也會被要求改（往嚴的方向）。
- **決策書第 6 節**是需求待決唯一入口；歷史原件不再指示現行操作。
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
