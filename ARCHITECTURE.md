# ARCHITECTURE — 這個 repo 的結構

> 最後更新：2026-11-20
> 本檔回答「現在長怎樣」：鳥瞰、檔案地圖、看程式碼看不出來的副本關係，以及刻意沒有的東西。規則在 [AGENTS.md](AGENTS.md)，做法在 [AI 維護手冊](docs/maintenance.md)，理由在[理由檔](docs/rationale.md)，進度在 [HANDOFF.md](HANDOFF.md)。結構怎麼變成這樣看 Git 歷史；2026-11-17 前的逐次紀錄封存在 `archive/docs/architect-log.md`（冷區，回溯先經使用者同意）。

## 一句話

唯一的產出物是安裝程式 [bootstrap.py](bootstrap.py)：只用標準函式庫、內嵌所有範本的單一檔，新專案跑它就寫出整套制度。它由 [src/kit/](src/kit/kit.md) 生成，部署包的說明與範本都在那裡。其餘每個檔案都是它的來源、說明、指標或測試；例外是 `HANDOFF.md`，它是範本 3.3 的實例，放本 repo 的交接快照與「工作中」標記。

## 碰到才讀的文件

`AGENTS.md` 與 `HANDOFF.md` 每個 session 開工都讀；其他文件碰到那件事才讀。

| 想做的事或想知道的事 | 先讀 |
|---|---|
| 需求、驗收、待決事項或替代工具 | [需求決策書 v3](project-bootstrap-requirements-decision-v3.md)：唯一需求書，新的待決登記在第 8 節 |
| 某個需求 ID 做到哪 | [現況索引](docs/status.json) |
| 路線、分期或暫緩項目 | [實施計畫 v3](project-bootstrap-implementation-plan-v3.md) |
| 決策書或計畫怎麼變成現在這樣、已決的 Q | [決策書歷史紀錄](docs/history/project-bootstrap-requirements-v3-history.md)、[計畫歷史紀錄](docs/history/project-bootstrap-implementation-v3-history.md)；熱歷史，碰到就讀，不用先問 |
| 改部署包、同步副本、改安裝程式、改 hook 訊息、寫本 repo 交接快照 | [AI 維護手冊](docs/maintenance.md) |
| 某條規則為什麼這樣 | [理由檔](docs/rationale.md)；被取代的理由在[理由檔歷史紀錄](docs/history/rationale-history.md) |
| 改本 repo 自己的檢查 | 程式在 `src/project_bootstrap/`、測試在 `tests/`，入口 `tools/run_tests.py`；部署包的檢查是 `tools/verify_bootstrap.py` |
| 部署包每一版改了什麼 | [CHANGELOG.md](CHANGELOG.md) |
| 有哪些檔、副本在哪 | 本檔的檔案地圖與副本拓撲 |
| 回溯已封存的東西 | [封存索引](archive/docs/README.md)；**平常不讀，要回溯先經使用者同意** |

## 檔案地圖

每一列只寫它是什麼；什麼時候改、怎麼改在 [AI 維護手冊](docs/maintenance.md)。

### 產物與制度來源

| 路徑 | 是什麼 |
|---|---|
| [bootstrap.py](bootstrap.py) | **安裝程式**，唯一產出物：訪談、寫檔（同名檔不覆寫，寫成 `.bootstrap-new`）、逐檔雜湊、`git init`、寫 HANDOFF 的第一批工作；`update` 依 `owners.json` 只換骨架的部分。內嵌全部範本與 `sync_project.py` 的合併函式，由 `tools/build_kit.py` 生成 |
| [src/kit/](src/kit/kit.md) | **制度的權威來源**：`kit.md` 是部署包說明，節號與範本的對照在它的第 2、3 節；`files/<部署路徑>.tmpl` 是範本；`owners.json` 是每個範本的歸屬，`sync_project.py` 的檔案清單由它算出；`capabilities.json` 是能力矩陣，「跨工具與跨平台」兩張表由它生成 |
| [src/project_bootstrap/installer.py](src/project_bootstrap/installer.py) | 安裝程式的安裝與更新邏輯原始碼；測試直接 import 它 |
| [tools/build_kit.py](tools/build_kit.py) | 由 `src/kit/` 生成 `bootstrap.py`；`kit_text()` 在記憶體組出部署包全文給驗證器與同步器；`--check` 只比對 |
| [tools/sync_project.py](tools/sync_project.py) | **部署包的發佈工具**：把最新內容推到已部署的專案，保留專案自己的設定；`AGENTS.md` 只換共用制度標記之間。只改檔案，不 commit |
| [VERSION](VERSION) | 一行版本號，等於部署包的版本行；各專案的開場 hook 抓它判斷自己落後沒有 |
| [CHANGELOG.md](CHANGELOG.md) | 部署包的逐版變更與每一版的理由，新的在上面 |

### 文件

| 路徑 | 是什麼 |
|---|---|
| [README.md](README.md) | 標準 README：解決什麼、怎麼用、部署後長什麼樣、跨工具相容性、參與開發、授權 |
| [AGENTS.md](AGENTS.md) | AI 開工時自動讀：共用制度副本、跟部署出去的專案不同的地方、這個 repo 是什麼、鐵律 |
| [CLAUDE.md](CLAUDE.md) | Claude Code 用 `@AGENTS.md` import |
| [HANDOFF.md](HANDOFF.md) | **當下交接快照與跨機器工作標記**：範本 3.3 的實例，不是副本；≤80 行、覆寫不累積 |
| 本檔 | 結構 |
| [docs/maintenance.md](docs/maintenance.md) | **AI 維護手冊**：改這個 repo 時的步驟、指令與坑 |
| [docs/rationale.md](docs/rationale.md)、[docs/history/rationale-history.md](docs/history/rationale-history.md) | **理由檔**：AGENTS 與維護手冊每條規則的現行理由；它的歷史紀錄放被取代的理由與拆分前的原文 |
| [project-bootstrap-requirements-decision-v3.md](project-bootstrap-requirements-decision-v3.md)、[docs/history/project-bootstrap-requirements-v3-history.md](docs/history/project-bootstrap-requirements-v3-history.md) | **現行需求權威**與它的歷史紀錄（修改紀錄、已決的 Q）。`tests/test_trail_repo.py` 讀歷史紀錄的「決策紀錄」 |
| [project-bootstrap-implementation-plan-v3.md](project-bootstrap-implementation-plan-v3.md)、[docs/history/project-bootstrap-implementation-v3-history.md](docs/history/project-bootstrap-implementation-v3-history.md) | **現行實施權威**與它的歷史紀錄。`tests/test_trail_repo.py` 讀計畫的「路線選擇」「分期」「非目標」 |
| [collaboration-system-principles-draft.md](collaboration-system-principles-draft.md) | 協作系統的前提、效用與設計原則（共識草稿）：還不是約束文件，最終要跟決策書與計畫整合成一份新文件 |
| [docs/status.json](docs/status.json) | **現況索引**：逐 ID 的實作狀態與現行證據。`registry.validate`、`schema_check`、`tools/run_tests.py` 與 `test_registry_repo` 讀它 |
| [experiments/handoff-ab/](experiments/handoff-ab/README.md) | 完整版與極簡版骨架的對照實測，v3 的依據 E1；原始資料在 gitignored 的 `dist/` |
| [LICENSE](LICENSE) | MIT |

### 檢查與測試

| 路徑 | 是什麼 |
|---|---|
| [tools/verify_bootstrap.py](tools/verify_bootstrap.py) | **部署包的測試**，也守本 repo 的文件與接線；每一項守什麼、失敗代表什麼列在它的檔頭 |
| [tools/skill_split_baseline.json](tools/skill_split_baseline.json) | 拆分前單檔 `SKILL.md` 每一行的雜湊，加上刻意改寫的行與去處；「skill 拆分」用它確認沒有行被弄丟 |
| [tools/run_tests.py](tools/run_tests.py) | **測試入口**：核對現況索引與決策書的 ID，跑全套 unittest；驗證器每輪背景跑它 |
| [src/project_bootstrap/](src/project_bootstrap/__init__.py) | **本 repo 自己的檢查**：`mdlinks`、`trail`／`trail_sources`、`surfaces`、`resume`、`capabilities`、`contradictions`、`registry`／`schema_check` 與 `mutants.py`／`mutants.json`（變異測試） |
| [tests/](tests/test_layout.py) | 上面那些檢查的測試，加上開發骨架與驗證器自己的測試；讀本 repo 真文件的叫 `*_repo.py`，不放進變異組 |
| [pyproject.toml](pyproject.toml)、[uv.lock](uv.lock) | **開發骨架**：依賴、最低 Python 3.12、pytest 設定與每個套件的授權；不是可安裝的套件 |

### 本 repo 自己的接線

| 路徑 | 是什麼 |
|---|---|
| `.claude/settings.json`、`.codex/hooks.json` | 本 repo 的開場與 push 前接線，兩份都掛下面兩支腳本；不是部署包 3.9／3.17 的副本（見副本拓撲） |
| `.claude/hooks/repo-git-check.sh` | 開場 hook，3.10 `git-freshness.sh` 的手貼逐字副本 |
| `.claude/hooks/repo-pre-push.sh` | push 前 hook，3.11 `pre-push-handoff.sh` 的手貼逐字副本 |
| `.gitignore`、`.gitattributes` | `dist/`、`.venv/` 不進 Git；全檔強制 `eol=lf` |

### 冷區

| 路徑 | 是什麼 |
|---|---|
| [archive/docs/](archive/docs/README.md) | **封存區**：v2 決策書的凍結原件，與結案或被取代的需求、計畫、查核文件；每份一行說明在它的 `README.md`。程式與測試不得引用。**AI 平常不讀，要回溯先經使用者同意** |
| [archive/v2-barrier/](archive/v2-barrier/README.md)、`archive/v2-channel/`、`archive/v2-prototypes/`、`archive/v2-experiments/` | 退休的 v2 程式、簽章發布通道、原型與實驗說明。不執行，程式與現況索引都不引用。**平常不讀，要回溯先經使用者同意** |

## 副本拓撲

同一份內容存在於多個地方的，只有下面這些。改權威的那一份，其餘照箭頭覆蓋；規則見 [AGENTS.md](AGENTS.md) 鐵律 1、2 與維護手冊「副本規則」。

```text
handoff skill 目錄（七個檔，同版本，整個目錄一起覆蓋）
  src/kit/files/.claude/skills/handoff/（權威，部署包 3.8）
    ├─→ bootstrap.py（內嵌）
    └─→ 各專案 .claude/skills/handoff/
          ├─→ （選用）~/.claude/skills/handoff/   ← 模式 0 建制真正載入的地方；本 repo 沒有專案層 skill，也讀這份
          ├─→ （選用）~/.codex/skills/handoff/    ← Codex CLI 與桌面 App
          └─→ .agents/skills/handoff/SKILL.md     ← 只放指標，不複製內容；description 與權威版相同

AGENTS.md 共用制度（開始與結束標記之間）
  src/kit/files/AGENTS.md.tmpl（權威，部署包 3.1）
    ├─→ 本 repo AGENTS.md          ← 手貼，驗證器逐字比對
    └─→ 各專案 AGENTS.md           ← sync_project.py 只換標記之間

兩支 hook .sh
  部署包 3.10／3.11（權威）
    ├─→ 各專案 .claude/hooks/*.sh  ← 只有這一份腳本，兩份接線都指向它
    └─→ 本 repo repo-git-check.sh、repo-pre-push.sh  ← 手貼，驗證器逐位元組比對

check_docs.py
  部署包 3.14（權威，「專案設定」區塊除外）
    └─→ 各專案 tools/check_docs.py

兩份 hook 接線（JSON）
  部署包 3.9／3.17（權威，只管指向骨架腳本的那幾組；專案自己加的設定原樣保留）
    ├─→ 各專案 .claude/settings.json
    └─→ 各專案 .codex/hooks.json

其餘範本與同步器的合併函式
  src/kit/files/*.tmpl、tools/sync_project.py
    └─→ bootstrap.py               ← build_kit.py 生成，驗證器逐位元組比對

版本
  VERSION ＝ src/kit/kit.md 的「版本」行      ← 驗證器擋不一致
  七個 skill 檔與 AGENTS 共用制度開始標記的 source: 版本相同，等於 VERSION
```

**本 repo 的兩份接線不是副本**：路徑跟 3.9／3.17 同名，掛的卻是本 repo 自己的兩支腳本，沒有同步義務。路徑同名的風險由 `sync_project.py` 拒絕本 repo 擋下。[為什麼](docs/rationale.md#copy-7)

**JSON 放不了 `source:` 標記**：兩份接線在落後偵測裡看不見，靠 `sync_project.py` 的 `WIRING` 清單與驗證器「同步清單涵蓋骨架」守。[為什麼](docs/rationale.md#copy-1)

## 這個 repo 刻意沒有的東西

第一條的兩項是 F46 的正式例外，宣告在[需求決策書 v3](project-bootstrap-requirements-decision-v3.md) 第 4 節 F46 底下。

- **沒有 handoff skill、沒有 `check_docs.py`（2026-11-06 使用者宣告為例外）**：它是制度的來源，把這兩份套到自己身上，會出現權威版與副本互相同步的迴圈；接棒程序讀全域副本，`.md` 的檢查由 `verify_bootstrap.py` 做。[為什麼](docs/rationale.md#what)
- **但有 `HANDOFF.md` 與跨機器「工作中」標記（2026-10-30 起）**：多機維護時 `git fetch` 看不到別台機器未提交的變更，所以沿用範本 3.3 的載體與同一個欄位，不發明第二種標記。[為什麼](docs/rationale.md#what)
- **push 前 hook 原本不裝，2026-11-14 使用者決定補裝**：F10 擋的是沒寫開工標記就推權威分支，來源少這一層就比產物少一層保護。[為什麼](docs/rationale.md#what)
- **有自己的開場 hook（2026-11-14 起是 3.10 的逐字副本）**：只印 `[facts]`，不經 `sync_project.py` 同步。[為什麼](docs/rationale.md#copy-7)
- **沒有 CI（2026-09-13 起）**：驗證是一個指令，跑它是鐵律 4 的義務；現在本 repo 沒有任何 workflow。[為什麼](docs/rationale.md#rule-4)
