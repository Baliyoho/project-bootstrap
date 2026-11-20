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
| [tools/verify_bootstrap.py](tools/verify_bootstrap.py) | **部署包的測試**，也守本 repo 的文件與接線 |
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

## 部署包的內部結構

部署包是 `src/kit/kit.md` 的散文加 `src/kit/files/` 的範本；2026-11-18 以前生成成根目錄的 `PROJECT-BOOTSTRAP.md` 提交，之後只在記憶體組出（v3 Q50）。下面的節號指組出來的全文，也就是 `kit.md` 的節號。

測試入口 `tools/run_tests.py` 不在部署包內。驗證器的「測試套件與現況索引」一項背景跑它：現況索引要跟決策書的 ID 一致，測試不能為空、失敗或略過；報告的壞形狀有負向測試。

| 節 | 內容 | 誰會讀它 |
|---|---|---|
| 表頭 | 安裝途徑（`bootstrap.py`）、版本日期、來源 | 拿到這份檔案的人 |
| 交接自動化怎麼運作 | 觸發（hook）／程序（skill）／防呆（hook）三層 | 想理解設計的人 |
| 跨工具與跨平台 | Claude Code／Codex CLI／Codex 桌面 App／Antigravity 的能力矩陣 | 要在別的工具上部署的人 |
| 0 | 這套骨架在解決什麼問題（失效模式 → 對策） | 想知道「為什麼要有這條規則」的人 |
| 1 | 部署前訪談：佔位符表（安裝程式問） | 想知道安裝程式問什麼的人 |
| 2 | 要建立的檔案結構 | 同上 |
| 3 | **各檔範本**（3.1–3.21，3.17 產兩檔），安裝程式寫檔時換佔位符 | 改範本的人，改到哪份讀哪節 |
| 4 | 先本機驗收，再首次發布（指向 `mode-0.md` 0-5） | 同上 |
| 5 | 部署後自檢清單（逐字搬進 `mode-0.md` 0-6） | 同上 |
| 6 | 之後怎麼維持（一頁操作卡） | 部署完的專案 |

第 3 節的範本清單就是 `verify_bootstrap.py` 裡 `EXPECTED` 的對照表：

| 節 | 產出 | 角色 |
|---|---|---|
| 3.1 | `AGENTS.md` | AI 開工時自動讀：開始／結束標記之間是共用制度（≤40 行，2026-11-13 起，v3 D11），標記外是專案鐵律（連線資料 2026-11-17 搬到 README，v3 Q40） |
| 3.2 | `CLAUDE.md` | 一行 `@AGENTS.md` import；2026-11-17 起這一節只產這一個檔（本專案不支援 Gemini） |
| 3.3 | `HANDOFF.md` | 當下狀態（≤80 行、覆寫不累積） |
| 3.4 | `README.md` | 標準 README：是什麼、為什麼做、快速開始（含連線資料）、開發與驗證、結構指標、協作方式、授權；不放交接 prompt（v3 Q40） |
| 3.5 | `ARCHITECTURE.md` | 結構的唯一權威（2026-09-07 加入） |
| 3.6 | （2026-11-17 移除，v3 Q41） | 原本是交接協定 `docs/ai-notes/handover-protocol.md`；獨有的分支模型與漏交棒理由搬進 3.8 的 skill，編號保留 |
| 3.7 | `docs/ai-notes/roadmap.md` | 持久待辦與決策記錄 |
| 3.8 | `.claude/skills/handoff/` 七個檔：`SKILL.md`、`mode-a.md`、`mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md`、`env.md`（2026-11-16.4 加） | **本骨架的核心**，**一節產六檔**（2026-11-10 拆分）：入口每次讀；`mode-a.md` 是正常接棒摘要；其餘四個逐字搬自單檔，依模式或異常才讀 |
| 3.9 | `.claude/settings.json` | 兩個 hook 的接線 |
| 3.10 | `.claude/hooks/git-freshness.sh` | SessionStart：fetch 一次，只報事實（最多五行 `[facts]`，2026-11-13 起） |
| 3.11 | `.claude/hooks/pre-push-handoff.sh` | PreToolUse：AI push 提醒（有限覆蓋，見部署包 3.11） |
| 3.12 | `.gitignore` | 祕密與運行資料 |
| 3.13 | `.gitattributes` | 行末 LF |
| 3.14 | `tools/check_docs.py` | 文件與交接快照的機械檢查 |
| 3.15 | `tools/verify_state.py` | 一鍵現況查證（骨架） |
| 3.16 | `.agents/skills/handoff/SKILL.md` | Codex 讀的指標檔 |
| 3.17 | `.codex/hooks.json`＋`.claude/hooks/codex-hook.cmd` | Codex 的 hook 接線與 Windows 啟動器（掛 3.10／3.11 同樣那兩個 `.sh`，Windows 明確找 Git Bash） |
| 3.18–3.20 | —— | 2026-11-13 移除（Antigravity 轉接層、Windows shim、`.agents/hooks.json`；v3 D8）。編號保留不重用 |
| 3.21 | —— | 其他 skills 的**慣例說明**，不產檔 |

## `tools/verify_bootstrap.py` 守的東西

| 檢查 | 守什麼 | 失敗代表 |
|---|---|---|
| 重生骨架 | 範本清單與 `EXPECTED` 一致 | 有人刪了範本沒發現，或新增範本沒登記 |
| 填佔位符 | 模擬部署後不該有殘留 | 範本用了訪談表沒有的佔位符 |
| `check_docs` | 在填好的骨架跑要 exit 0 | 範本裡有死連結或缺日期標頭 |
| 佔位符清單 | `PLACEHOLDER_NAMES` 涵蓋範本真正用到的名字 | 有個洞永遠不會被檢查到，而且沒有跡象 |
| 佔位符檢查（負向） | 種一個佔位符回去必須被擋下 | 第 5 項檢查本身壞了 |
| 日期標頭（負向） | 拿掉 `ARCHITECTURE.md` 的「最後更新」必須被擋下 | `check_docs` 的 `DATED_DIRS` 漏了它 |
| 工作中欄位格式（負向） | 四種壞格式（舊格式沒工具欄、主題含「無」、欄位重複、機器欄空白）都要 exit 2，正常的已交棒值不誤擋。2026-11-02 從「工具欄（負向測試）」擴大 | `check_docs` 用子字串判「已交棒」，正常任務名稱就能跳過整個格式驗證（F01） |
| 真實部署形狀 | 部署包在場＋非 ASCII 檔名時仍 exit 0 | 照說明部署的人一定會踩到 |
| 跨平台防呆 | 無絕對路徑、有 `python3` 退路 | 換一台機器會靜默失效 |
| AI push 提醒情境 | staged／unstaged 不放行、已提交開工／交棒放行；命令選項、remote、refspec、GUI／script 的已知邊界；恢復舊捷徑的負向測試 | 未提交修改不會隨 push 上傳，不能拿來放行；有限提醒不能冒充發布保證（2026-11-02／F06） |
| 工作中標記 | 範本有欄位，且 git-freshness 讀 `origin` 那一份後照原文印出（2026-11-13 起不再分 🔴／🟡／✅，v3 D12）：別台機器、主題含「無」原文完整、已交棒、欄位重複說有幾列、欄位不存在明講讀不到、工具環境變數不改變輸出；拿掉印出那一行的負向測試 | 下一棒看不到誰握著分支（F4 偵測） |
| `VERSION` 檔 | 與部署包版本行一致 | 落後偵測會說謊，落後的專案以為自己最新 |
| 版本落後偵測 | 共用制度版本取自 `AGENTS.md` 開始標記；餵**比本機新**的版本要講落後、餵**比本機舊**的要說「比上游新」、同版與 `BOOTSTRAP_VERSION_CHECK=off` 要閉嘴 | 專案不再自己回報落後（F18 提示） |
| 本 repo 自己的文件 | 本 repo 的 `.md` 無死連結、`AGENTS.md`／`ARCHITECTURE.md` 有日期標頭，受管非 Markdown 檔無已知部署佔位符；`src/kit/` 另有規則，`archive/docs/` 封存區不讀（v3 Q39） | 改檔名或搬段落留下死連結，或把未填的部署欄位帶進公開來源。部署包裡指向「部署後才存在的檔」的連結不算，判準是 `EXPECTED`，所以它指向本 repo 檔案的連結照樣會被抓 |
| 封存原件 | `archive/docs/` 的 v2 決策書 Git blob 不變（只看 index 記的 blob，不開檔）；程式、測試與設定檔不出現它的路徑（`ARCHIVE_READERS` 登記的除外，登記前要使用者同意）；文件檢查不讀封存區但不外溢。引用、改內容、搬走、略過外溢四種反例都要擋，已登記讀取者放行（2026-11-17，v3 Q39） | 有程式又開始讀 v2，或封存原件被改、被搬走 |
| 版本更替 | 現行版本取 AGENTS 連到的決策書（檔名的版本號要跟「決策版本」行相同）；`archive/` 以外的檔名、資料夾名與程式識別字不得帶比它舊的版本號，程式不得引用 `archive/` 底下的版本封存資料夾。文件內文的對照與歷史說明、`v2.1.277` 這種工具版本號不算；本檔自己的反例在執行時拼出版本號，換版後不會擋到自己。版本來源 3 種、檔名／識別字／封存引用 4 種反例（2026-11-18，v3 Q47） | 新版成為權威後，舊版本名稱的檔案或程式還留在現行區；也就是 v2 的程式留在 main 那種情形（v3 Q46） |
| 本 repo push 前 hook | `repo-pre-push.sh` 跟部署包 3.11 逐位元組相同；兩份接線的 PreToolUse 都指向它；接線守門 7 個負向測試（沒接、指向別支、matcher 退回 `Bash`、接回 PostToolUse、SessionStart 指錯、腳本不存在）（2026-11-14 取代「動作當下送規則」） | 改了 3.11 卻沒重貼，或接線被改掉，本 repo 推 `main` 時沒寫開工標記也不會被擋 |
| 本 repo 兩份接線 | `.claude/settings.json` 與 `.codex/hooks.json` 都是合法 JSON、`SessionStart` 都指向 `repo-git-check.sh`、`PreToolUse` 都指向 `repo-pre-push.sh`（2026-11-14 起；之前只有 Claude Code 那份可多接動作提醒），其他事件一律拒絕，而且沒被改成指向 `git-freshness.sh`／`pre-push-handoff.sh` | 開場檢查靜默不執行——看起來有防護、實際上沒有。這兩個檔是 JSON、塞不進 `source:` 標記，落後偵測看不到它們，這一項是唯一的守門人 |
| sync 拒絕本 repo | `sync_project.py <本 repo 路徑>` 要印出拒絕，**而且預演輸出裡零 `UPDATE`** | 一次手打路徑就把兩份接線改成指向這裡不存在的腳本。只檢查「有印拒絕」的話，一個印了話卻照樣改檔的版本會通過，比沒有這項更糟 |
| 改名寫進回報模板 | A5／B9 各有必填 `session：` 與無改名工具時的回報選項，附負向測試 | 改名漏做卻在 repo 內沒有任何跡象 |
| 續聊狀態與計數 | `AGENTS.md` 共用制度有「`↗`／`※` 時收到新訊息先改回 `㊣`」（2026-11-13 起取代 skill 與指標 description 的觸發詞，skill 不再必讀）；skill 參考檔保留時間與計數、只讀不寫 Git、改檔重跑 A、成功交棒才累加；附 17 個負向測試 | 已交棒後續聊沒恢復工作中，或計數被重算 |
| 本 repo 交接狀態 | 必要欄位與章節、≤80 行、骨架版本符合 VERSION、禁止這次已知過期待辦與只改兩欄的入口規則；附負向測試 | 標記清了卻保留已完成待辦，下一棒被迫從聊天重建現況；不保證任意待辦的語意正確，仍需 B6 人工核對 |
| 規則理由連結 | AGENTS.md 與 `docs/maintenance.md` 每節至少一個、鐵律／副本規則／hook 訊息每條各一個指向 `docs/rationale.md` 的連結（從各自的位置算相對路徑），連結的段落存在且非空；附負向測試 | 理由搬到別的檔之後被悄悄刪掉、新增規則沒有理由、連結指向不存在的段落。只查連結與段落存在，不判斷理由寫得對不對 |
| 來源例外可見性（F46 部分） | 每輪印出已宣告減項（2026-11-14 起剩 handoff skill、check_docs.py 兩項；pre-push 補裝了）；確認來源缺、產物有，並對漏宣告／來源增項／產物缺項跑負向變異 | 三項減項再次從驗證輸出中靜默消失；這只驗可見性，未完成來源／產物全部同組情境 |
| 來源／產物交接快照同組情境（F46 部分） | 同一組 11 種合成快照在來源檢查與部署後 `check_docs.py` 各跑一次：有效、整份缺失、占用欄缺失／重複、章節缺失、超行數、機器／工具欄正反例均須一致；來源檢查遇整份缺失須明確報錯 | 來源少了整份 `HANDOFF.md` 時只拋例外，或產物與來源對相同缺陷給出矛盾結論；實際接手流程仍待驗 |
| 來源／產物文件同組情境（F46 部分） | 同一份合成文件在來源文件檢查與部署後 `check_docs.py` 各跑一次：20 種正反例涵蓋根目錄及巢狀文件的缺檔、死連結、程式碼、角括號加 title、片段、日期及佔位符；沿用來源實際檢查函式 | 同樣的文件缺陷在來源與產物給出不同結論；其他文件項仍待驗 |
| 來源／產物文件設定同組情境（F46 部分） | 9 種合成設定情境對照非 Markdown 已知佔位符、未知樣板、專案自訂過期字串、同列歷史文字與連結／佔位符／過期字串路徑豁免；來源端同時掃自己受管的非 Markdown 檔 | 來源非 Markdown 檔殘留部署欄位，或來源與產物對相同設定給出不同結果；任意專案設定與跨工具遵循仍待驗 |
| 來源提交候選一致性（F46 部分） | 來源 `verify_bootstrap.py --staged` 拒絕未暫存或未追蹤檔；完整／部分 stage 與產物 `check_docs.py --staged` 跑同組 fixture，並對來源未追蹤檔作負向測試 | 用未提交的工作樹內容證明另一份 staged 內容；只驗提交候選形狀，不代表實際接手流程已驗收 |
| 本 repo 開場 hook | `repo-git-check.sh` 跟部署包 3.10 逐位元組相同；多一行與檔案不存在兩個負向測試（2026-11-14 取代「本 repo 工作中判讀」，那一項測的是已退場的判讀版） | 改了 3.10 卻沒重貼，本 repo 開場印的跟共用制度說的不一樣，或退回會下指示的判讀版 |
| 同步清單涵蓋骨架 | `sync_project.py` 的四份清單加起來要等於 `EXPECTED` | 新增範本沒歸類＝那個檔沒人同步，而且沒有徵兆。2026-10-30 就是這樣查出兩份 hook 接線從來沒被發下去 |
| 同步安全 | F02：骨架只擁有**指向骨架腳本的 handler**（同組的自訂 hook 要保留，matcher 衝突／重複組／異常分組要拒絕，`commandWindows` 要認得）。F03：任一項算不出來就零寫入，失敗與不存在的目標要非零退出、不准宣稱最新版 | 同步靜默刪掉專案設定；或失敗一半卻回 exit 0 並宣稱最新版，而落後的專案以為自己同步過了（2026-11-02／F02、F03） |
| 同步升級 mode | 替換前複製既存 mode；複製失敗保留原檔；新依賴仍可建立；移除複製的負向變異必須失敗。POSIX 另驗 0755／0640、開場 hook 直接執行、Git 無 mode diff | 新 inode 預設權限會讓更新後的 POSIX hook 無法執行；Windows 通過不代表 POSIX 實測 |
| 結構摘要一致性 | 本 repo 與生成 ARCHITECTURE 寫明 `CLAUDE.md` 用 import、表格不再列 Gemini 的指標檔，範本 3.4 那一列寫標準 README、不再寫交接 prompt；五個負向測試 | 權威範本已改，結構表格仍教舊寫法 |
| 接線合併 | 餵一份「舊 matcher ＋ 專案自己加的 permissions 與 hook」進去，要換掉舊值、保住專案設定、已一致時不動 | 同步會洗掉專案設定，或落後的專案根本修不好 |
| 跨工具表保鮮期 | 「跨工具與跨平台」那節的「查證日期」不得超過 90 天（`BOOTSTRAP_FRESHNESS=off` 可跳過） | 對外部工具能力的斷言在無聲中過期。這一項只保證有人看過日期，**不保證有人真的重查**——買到的是「必須有意識地決定」。會做成 fail 而不是警告，是因為上一次的對策就是一句警告，而警告沒擋住第二次（Antigravity 的 hooks、Codex 桌面 App 的 hooks，兩次同一種錯） |
| README 跨工具表一致性 | README 那張跨工具表與部署包那一張：同名列的判定符號一致、README 沒有孤兒版本號、有指回部署包的指標（附四種分岔的負向測試） | README 是**人的入口**，而保鮮期只守部署包那一份——事實在部署包被重查改對，README 留在舊事實上，沒有任何徵兆。2026-11-01 加這一項的當下就抓到一處已經發生的分岔（「自動載入程序檔」×「Codex CLI」）。不給 README 自己一個「查證日期」是因為那是同一個事實的第二個時鐘 |
| 跨工具過期敘述 | 部署包正文、本 repo 結構說明、重生的結構範本與 handoff skill，不得復活 CLI／2.0 測試狀態、Antigravity 接線、skill 入口與 IDE 追查決定的已知舊斷言；附回歸負向測試與範圍測試 | 同一份文件的表改對了，散文卻仍教下一棒照舊事實行動。只檢查已知回歸，不做通用語意判讀、不代替外部查證；表頭的歷史變更記錄與 IDE 未解結果仍保留 |
| Codex Windows 接線 | `commandWindows` 經 Git Bash 啟動器，兩個事件與本 repo 都指向原本那支 `.sh`；三個負向測試 | 真部署的已信任 hook 曾選到 WSL 而 exit 1 |
| Codex Windows 結束碼 | 實跑 PowerShell → cmd → Git Bash；保留 exit 2，拿掉明確 exit 時必須重現 exit 1 | 只測原生 cmd 會把工具仍放行的版本誤報成功；此項只在 Windows 執行 |
| Codex 接線升級 | 舊專案補齊啟動器、保留專案 hook 與 SKILL、預演零寫入、重跑零變更、不替沒有接線的專案補裝 | 只更新 JSON 卻漏掉新依賴會再度靜默失效 |
| Codex Windows 啟動器 | Windows 原生 cmd 實跑中文／空白路徑、不同 cwd、stdin／stdout／stderr／exit 2 與缺少 Git Bash 的情境 | 轉接層若吞掉 exit 2，pre-push 防呆會消失；此項只在 Windows 執行 |
| verify_state 失敗訊號 | 命令非零退出、HTTP 500、連不上、200 但回應內容不對都要讓結束碼非零；缺憑證是 SKIP，`--strict` 才非零、`OPTIONAL` 放行；未填仍回 0；祕密要遮罩。十個情境全部實跑 | 舊版每一種情況都 return 0，畫面印著 `rc7` 而下游拿 exit 0 當服務驗收（2026-11-02／F04） |
| 交接快照檢查 | `HANDOFF.md` 不見了、超過 80 行、缺必要章節或欄位重複都要 exit 2；`--docs-only` 要真的關得掉；程式碼範例、帶 title 與角括號連結不得誤報，但真的死連結仍要抓到 | 第 6 項只在 HANDOFF 出現在輸入清單時才驗，整份刪掉反而回報乾淨；而連結誤報會教人「這支腳本的 FAIL 可以無視」（2026-11-02／F08） |
| Python 版本下限 | 兩支維護工具檔頭的 `MIN_PY` 存在、會擋、兩邊同號；README 範本寫出部署後工具的下限；四支 `.py` 都沒有用到高於下限的 API（掃描前把註解與字串塗白） | 3.13-only 的 API 在舊版 python 上是執行到那一行才炸成 TypeError，不會說「版本太舊」。下限是靜態擔保、不是實測：沒有舊版可跑，要實測得先有 CI（2026-11-02／F14） |
| 已修正的主張沒復活 | 能力表 ✅ 的工具不得被散文說成沒有 skill、交接 prompt 不得有自己的 A／B 編號且要寫出模式、`verify_state` 不得以憑證為前提、版本序號只有一種定義、可攜層不得寫成「到哪都成立」；附九個負向測試 | 事實在部署包被改對，範本、操作卡與入口文件裡的舊說法照樣部署出去。綁結構不綁禁句，「」裡的引用不算主張（鐵律 3 要留為什麼）；守不了一整段敘述的準確度（2026-11-02／F15） |
| 協作狀態契約／Git 異常提示 | 六狀態與步驟契約、21 個負向測試，含 R07 先 stage 再驗證。Git 異常：部署 hook 實跑領先／分岔／fetch 失敗要照實報出、不得建議 rebase，`AGENTS.md` 共用制度要有停止條件；本 repo hook 照舊要求停止；2 個負向測試 | 程序順序矛盾或工具提示教人自行 rebase |
| 核心與實例優先序 | skill／README 宣告一致、override 範圍明確、部署包不再產出交接協定（v3 Q41）、7 個負向測試；同步對舊實例列版本與 MIGRATE，不改寫 | 不同步的舊協定會推翻新程序（F10） |
| 接力協調邊界 | A2.5／A5 明列協調訊號非鎖、SHA 比對與禁止自動奪權，4 個文字負向測試（協定 2026-11-17 移出部署包） | 不宣稱並行互斥；原子 claim 留待另案（F12） |
| skill 拆分 | 七個 skill 檔齊全、同版本、都在 `WHOLE`；入口＋`mode-a.md` ≤6,000 字元；入口 12 條、`mode-a.md` 12 條必備句；拆分前每一行逐字留存或列入已改寫清單（13 行） | 入口指向不存在的檔、同步只寫一半、濃縮時丟了停止條件或理由。不證明模型會去讀模式檔 |
| AGENTS.md 共用制度 | 開始／結束標記成對、26 條必備條件（v3 第 5 節；第 26 條是 F50 互動驗證後補的「選項卡片也算停下來」）、共用 ≤40 行、全檔 ≤100 行（v3 D11）、開始標記的版本等於 `VERSION`；30 個負向測試（2026-11-13 新增） | 每個 session 都載入的那一層缺了條件、長過預算，或版本提示失準。只證明文字在，不證明模型照做 |
| 同步補齊模式檔 | 只有單檔的舊專案會補上五個新檔、入口最後寫、不認得的檔列為 EXTRA；1 個負向測試 | 同步後新入口指向不存在的模式檔 |
| 同步共用制度 | `AGENTS.md` 沒有共用制度就插在第一個「## 」前、舊版整段換掉、標記外不動、已是權威版不寫、壞標記 FAIL 不寫、舊交接段落列 MIGRATE、先於 skill 入口寫；1 個負向測試 | 新 skill 指向舊專案 `AGENTS.md` 裡不存在的共用制度（2026-11-14 加，v3 Q34 前置） |
| 同步範圍與前置檢查 | 真 worktree、含 worktrees 普通目錄、已完結 inventory；fresh fetch／upstream 對齊／明確 owner、dirty／占用／整份檔與 check_docs 共用程式區客製漂移拒絕且零寫入；批次僅預演，單專案 A5 writer 才能寫入 | 路徑字串不是 worktree 證據，批次同步不能悄悄擴大範圍（F13） |
| 部署生命週期 | 訪談自訂 ignore、本機檢查→首 commit→local bare push→clone，clone 後開場 hook 印出 `[facts]`；`mode-0.md` 0-5 的驗收、提交、發布順序與不整批 `git add`（2026-11-18 起，v3 Q49）；6 個負向測試 | 圍欄外追加規則及發布後才驗收無法保護首 commit |
| 安裝程式由來源生成 | `bootstrap.py` 與 `src/kit`、`installer.py`、`sync_project.py` 的生成結果逐位元組相同；5 個負向測試（手改、改範本／installer／合併函式沒重生、少一個共用函式）。安裝、衝突、更新、CRLF 與兩支 hook 由 `tests/test_bootstrap_repo.py` 在暫存資料夾實跑 | 手改了安裝程式，或改了來源沒重生（2026-11-18，v3 Q49） |
| 部署包由來源生成 | `src/kit` 組得出部署包全文、每個範本剛好用一次、範本集合等於 `EXPECTED`，而且 `PROJECT-BOOTSTRAP.md` 沒被放回來；7 個負向測試（放回來、多／少範本、指錯、重複、缺結尾換行、範本含收尾圍籬） | 部署包全文是範本的第二份副本；2026-11-18 起不提交（v3 Q50），放回來就又多一份會過期的家 |
| 開發骨架 | pyproject 依賴都在 `uv.lock`、外部套件都有 sha256 與授權、最低 Python 3.12、`package = false`；`tools/` 與 `src/project_bootstrap` 的程式除 `DEV_EXTRAS` 列的模組外不 import 鎖檔裡的套件，也不 import 那些模組；import 它們的測試缺套件時 SkipTest；10 個負向測試。不需要 uv，鎖檔是否最新要另跑 `uv lock --check` | 依賴沒鎖或沒審授權；A4 在沒裝 uv 的機器跑不起來 |
| 全域 handoff skill 跟部署包同版 | 家目錄 `~/.claude/skills/handoff/`、`~/.codex/skills/handoff/` 的七個檔跟 `src/kit` 範本逐字相同（不只比 `source:` 版本號）；不同只印「提醒」、不影響結束碼，兩份都沒裝印 skip；4 個負向測試 | 改了部署包卻忘了重裝全域副本，沒有專案層 skill 的 session 讀到舊程序（2026-11-18 使用者指定） |
| 行末與雜項 | 全 LF、JSON 合法、腳本可執行 | Windows 寫出 CRLF、設定檔打錯字 |

2026-11-13 第 1 期對驗證項的取捨（留、改或移除哪些，以及 2026-11-14 使用者逐項定案的四項）在[理由檔歷史紀錄](docs/history/rationale-history.md)的「#rule-4」那組。

**exit 0 才算改完**（鐵律第 4 條）。印出 `skip` 的項目沒有被驗證，回報時要照實寫；印「提醒」的項目不影響結束碼，但要轉告使用者。

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

> **正式例外宣告（2026-11-06，使用者決定）＝ D4／F34 的「主動宣告」。**
>
> 需求 v3.10 新增的 **F46「制度來源自身的保護不低於它發出去的產物」**（偵測）與這個 repo 的「刻意沒有」直接衝突（宣告當時三項，2026-11-14 起兩項）。F46 的驗收允許兩條路——補裝，或把減項**宣告為例外**（D4：例外由使用者主動宣告；F34：主動宣告的例外要看得見）。**使用者 2026-11-06 選了宣告為例外。**
>
> **宣告的內容**：這個 repo 刻意不裝 **handoff skill**、**`check_docs.py`** 兩項，理由見下方。2026-11-14 使用者撤銷 pre-push 那一項、改成補裝（`repo-pre-push.sh`，3.11 的逐字副本）：v3 F10 是 v3 唯一要「阻擋」的需求，來源少這一層就比產物少一層保護。**這不是疏漏，也不是尚未排程。** 替代保障：接棒程序讀全域副本 `~/.claude/skills/handoff/`（沒有全域副本時讀部署包 3.8 節，2026-11-10 起 AGENTS 開工段落明寫）、`.md` 的死連結與日期標頭由 `verify_bootstrap.py` 顧、交接快照由 B6 逐項核對。
>
> ⚠️ **宣告不等於 F46 已達成。** F46 的強度是**偵測**——它還要求「對來源跑與產物同一組情境，缺的項目要**印出來**而不是略過」。2026-11-08 起 `verify_bootstrap.py` 逐項印出已宣告例外，並檢查來源與產物的檔案形狀；交接快照 11 種、文件 20 種、文件設定 9 種同組情境均成對跑，另以 `--staged` 核對提交候選，並在本機 bare origin 演練 Git 接力。跨工具／OS 接手與模型遵循仍未驗，所以 **F46 仍未整項通過**。待辦與現況看 [HANDOFF.md](HANDOFF.md)，需求條文看[需求決策書 v3](project-bootstrap-requirements-decision-v3.md) F46（v2 時期的 F46 驗收門檻只在封存的 v2 原件，平常不讀，v3 Q39）。
>
> 要撤銷這條宣告（改成補裝），是改使用者的決定，不是改措辭。

- **沒有 handoff skill、沒有 `check_docs.py`（2026-11-06 使用者宣告為例外）**：它是制度的來源，把這兩份套到自己身上，會出現權威版與副本互相同步的迴圈；接棒程序讀全域副本，`.md` 的檢查由 `verify_bootstrap.py` 做。[為什麼](docs/rationale.md#what)
- **但有 `HANDOFF.md` 與跨機器「工作中」標記（2026-10-30 起）**：多機維護時 `git fetch` 看不到別台機器未提交的變更，所以沿用範本 3.3 的載體與同一個欄位，不發明第二種標記。[為什麼](docs/rationale.md#what)
- **push 前 hook 原本不裝，2026-11-14 使用者決定補裝**：F10 擋的是沒寫開工標記就推權威分支，來源少這一層就比產物少一層保護。[為什麼](docs/rationale.md#what)
- **有自己的開場 hook（2026-11-14 起是 3.10 的逐字副本）**：只印 `[facts]`，不經 `sync_project.py` 同步。[為什麼](docs/rationale.md#copy-7)
- **沒有 CI（2026-09-13 起）**：驗證是一個指令，跑它是鐵律 4 的義務；現在本 repo 沒有任何 workflow。[為什麼](docs/rationale.md#rule-4)
