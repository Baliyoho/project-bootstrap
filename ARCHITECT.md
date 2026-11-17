# ARCHITECT — 這個 repo 的結構

> 最後更新：2026-11-17（根目錄的需求與計畫類文件只留[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)與[實施計畫 v3](project-bootstrap-implementation-plan-v3.md)，其餘封存到 `docs/history/`；本檔開頭原本約 140 行的逐次變更紀錄搬到 [docs/history/architect-log.md](docs/history/architect-log.md)，本檔只寫現況）
> 本檔回答「現在長怎樣」。進度看 [HANDOFF.md](HANDOFF.md)，部署包的逐版變更看 [CHANGELOG.md](CHANGELOG.md)，更早的結構變更經過看上面那份紀錄或 Git 歷史。

## 一句話

唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)——一份自帶所有檔案範本的部署包，複製到新專案資料夾就能生出整套制度。
其餘每個檔案都是它的**說明、指標或測試**，沒有第二個產出物（例外是 `HANDOFF.md`，它是範本 3.3 的*實例*，承載當下交接快照與「工作中」標記）。

## 碰到才讀的文件

下列文件都不是每輪必讀，碰到那件事才讀（2026-11-11 F22 第二輪從 AGENTS.md 原樣搬來）。

| 要做的事 | 先讀 |
|---|---|
| 討論需求、驗收、待決事項或替代工具 | [需求決策書 v3](project-bootstrap-requirements-decision-v3.md)：2026-11-13 起的現行需求權威（D1–D15、51 個穩定需求 ID，編號沿用 v2）；新的待決登記在它的第 8 節。2026-11-17 起它是唯一需求書；v2 決策書凍結封存在 `docs/history/`，**平常不讀，要回溯歷史先經使用者同意**。決策定稿不等於實作完成 |
| 查某個需求 ID 做到哪 | [現況索引](experiments/v2/status.json)（2026-11-17 起照 v3 的強度與處置）；HANDOFF 只留停點與行動 |
| 規劃路線、分期或暫緩項目 | [實施計畫 v3](project-bootstrap-implementation-plan-v3.md)：從現況走到 v3 需求的路線與取捨，只引用需求 ID |
| 回溯已封存的查核、計畫或需求討論 | [封存索引](docs/history/README.md)；**平常不讀，要回溯歷史先經使用者同意** |
| 動 v2 原型 | [v2 原型說明](experiments/v2/README.md) |
| 改部署包、同步副本、改 hook 訊息、寫本 repo 交接快照 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 結構問題（有哪些檔、副本在哪） | 本檔；動到結構就跟它同一個 commit 改 |

## 根目錄

| 路徑 | 是什麼 | 什麼時候動 |
|---|---|---|
| [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) | **部署包**（發給各專案的產物）：訪談表＋各檔範本＋上 GitHub＋自檢清單＋維持操作卡。2026-11-11 起由 `src/kit/` 生成，仍提交（專案複製它、`sync_project.py` 讀它與它的 Git 歷史） | 不手改；改 `src/kit/` 後跑 `tools/build_kit.py`（鐵律第 1 條） |
| [src/kit/](src/kit/kit.md) | **制度的權威來源**：`kit.md` 是部署包散文，第 3 節每個圍籬區塊裡只有一行 `<!-- kit-file: 部署路徑 -->`；`files/<部署路徑>.tmpl` 是 27 個範本（加 `.tmpl` 讓範本 `.gitignore`／`.gitattributes`／skill／接線不在本 repo 生效）；`release-keys.txt` 是發布公鑰（P2 第 3b 片；2026-11-11 E1 填入 CI 公鑰，指紋也寫在 README）；`owners.json` 是每個範本的歸屬（2026-11-11 P2 第一片；第 5 片起 `sync_project.py` 的檔案清單直接由它算出）；`capabilities.json` 是能力矩陣（2026-11-11 P2 第 4 片，決策書 Q24），「跨工具與跨平台」那兩張表由它生成，`kit.md` 那裡只有一行 `<!-- kit-table: 表名 -->` | 制度要改就改這裡，同一個 commit 重生部署包；新增範本要同時在 `owners.json` 登記歸屬；改跨工具表要改 `capabilities.json`，不改 `kit.md` |
| [tools/build_kit.py](tools/build_kit.py) | 由 `src/kit/` 生成 `PROJECT-BOOTSTRAP.md`；`--check` 只比對。只用標準函式庫，不部署 | 生成規則改變時 |
| [tools/release_package.py](tools/release_package.py) | P2 第 3b 片：CI 用的發布入口。要求 checkout 乾淨、建 debug 包、跑 `verify_bootstrap.py`、全部本輪實查通過才簽章，輸出包壓縮檔、簽過的紀錄與要建的 channel tag；自己不建 tag、不上傳。只用標準函式庫，不部署 | 發布流程改變時 |
| [tools/install_package.py](tools/install_package.py) | P2 第 3b 片：使用者用的安裝入口。第一次用 `src/kit/release-keys.txt` 的根公鑰、之後沿上一版的 `next_keys` 驗簽，裝進快取並寫專案指標；`--seed` 鋪空專案、`--check` 跑一次寫入檢查。不下載。只用標準函式庫，不部署 | 安裝流程改變時 |
| [.github/workflows/release.yml](.github/workflows/release.yml) | 本 repo 唯一的 workflow（2026-11-11，Q21）：push `release-request/<channel>` tag 觸發，跑在 macOS、金鑰在要核准的 `release` environment，成功後建 `channel/<channel>/<epoch>-<digest>` tag 與 GitHub Release。不用第三方 action | 發布流程改變時 |
| [tools/build_package.py](tools/build_package.py) | P2 第一片：由 `src/kit/` 生成正式包資料夾 `dist/package/`（Git 不追蹤）；`--check` 建兩次比 digest、不寫檔。一律 debug，正式版只能經發布步驟（第 3 片）。只用標準函式庫，不部署 | 包格式改變時 |
| [README.md](README.md) | 標準 README：解決什麼、怎麼用、部署後長什麼樣、跨工具相容性、發布公鑰、參與開發的指標、授權 | 用法或相容性改變 |
| [AGENTS.md](AGENTS.md) | AI 開工時自動讀：共用制度副本、跟部署出去的專案不同的地方、這個 repo 是什麼、鐵律 | 多一條開工必守的規則 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 碰到才讀的流程與規則：改部署包的操作細節、同步到已部署專案、副本規則、本 repo 交接快照、指標檔、行末、hook 訊息寫法；2026-11-17 從 AGENTS.md 與 README.md 搬來（v3 Q40） | 流程或碰到才需要的規則改變 |
| [AGENTS-reasons.md](AGENTS-reasons.md) | **AGENTS 與 CONTRIBUTING 每條規則的完整原文、理由與事故**；2026-11-10 從 AGENTS.md 逐字搬來，入口用「為什麼」連結指過來。不是每輪必讀，不部署、不同步 | 規則改了就在對應段落補帶日期的理由，不刪舊事故 |
| [CLAUDE.md](CLAUDE.md)、[GEMINI.md](GEMINI.md) | Claude 用 `@AGENTS.md` import；Gemini 用文字指標 | 幾乎不動 |
| [HANDOFF.md](HANDOFF.md) | **當下交接快照與跨機器工作標記**。範本 3.3 的*實例*，不是副本，不在副本拓撲裡、不要用 `sync_project.py` 同步。≤80 行、覆寫不累積，維護義務與事故見 [AGENTS.md](AGENTS.md)「本 repo 的交接快照」 | A5 寫標記；B6 核對整份現況、待辦、限制與驗證，清掉已完成待辦 |
| [project-bootstrap-requirements-decision-v3.md](project-bootstrap-requirements-decision-v3.md) | **現行需求權威（決策版本 3，2026-11-13）**：適用範圍、依據、D1–D15、51 條需求的處置與強度、目標部署形狀、驗收、Q32 起的決策登記處。不承載實作狀態，不部署、不同步 | 需求決策改變時 |
| [project-bootstrap-implementation-plan-v3.md](project-bootstrap-implementation-plan-v3.md) | **現行實施權威**（2026-11-17）：從現況走到 v3 需求的路線、三期的證據與還差什麼、暫緩與另案、非目標。只引用需求 ID，不寫進度（進度在 HANDOFF）。不部署、不同步；`tests/test_trail_repo.py` 讀它的「路線選擇」「分期」「非目標」三節 | 路線、分期或暫緩項目改變時 |
| [docs/history/](docs/history/README.md) | **封存區**（2026-11-17，v3 Q39）：`requirements-decision-v2.md` 是決策版本 2 的凍結原件（Q1–Q31 與逐條否決理由只在這裡），由 `git mv` 搬來、逐位元組不改，檔內相對連結因此失效，是已宣告例外。同日稍晚再封存 19 份結案或被取代的需求與計畫類文件，連到根目錄的連結已改成 `../../`；每份一行的說明在 `README.md` 索引。程式與測試不得引用封存區裡任何檔名（`verify_bootstrap.py`「封存原件」守）；文件檢查與行末檢查不讀這裡。**AI 平常不讀，要回溯歷史先經使用者同意**；程式要讀也一樣，同意後登記到 `ARCHIVE_READERS` | 不動。要改內容或讓程式讀它，先經使用者同意 |
| [experiments/handoff-ab/](experiments/handoff-ab/README.md) | 完整版與極簡版骨架的對照實測（2026-11-13 兩輪、36 次）：極簡版骨架、情境搭建、執行、評分與結果。v3 的依據 E1。實驗用，不部署、不同步；原始資料在 gitignored 的 `dist/` | 加跑或改情境時 |
| 本檔 | 結構 | 只有結構變動 |
| [LICENSE](LICENSE) | MIT（2026-09-07 起公開） | 授權改變 |
| [pyproject.toml](pyproject.toml)、[uv.lock](uv.lock) | **P1 開發骨架**（2026-11-11）：依賴、最低 Python 3.12、pytest 設定，以及鎖檔裡每個套件的授權表；`uv.lock` 鎖版本與 sha256。`[tool.uv] package = false`，打包屬 P2。不部署、不同步；A4 不需要它們 | 加減依賴時兩檔一起改（`uv lock`），新套件同時登記授權 |
| [src/project_bootstrap/](src/project_bootstrap/__init__.py) | v2 原型程式（2026-11-11 從 `experiments/v2` 搬來，內容不變）：契約、broker、偵測原型與 `mutants.py`／`mutants.json`。2026-11-14 起受管 worker、VM 探針等執行屏障模組封存在 `archive/v2-barrier/`（v3 Q33）。仍是合成 fixture 原型，不部署；只用標準函式庫，A4 的 `verify_v2.py` 不需要 uv 就能 import | 改原型時；之後的模組分組另做 |
| [archive/v2-barrier/](archive/v2-barrier/README.md) | v3 Q33 封存的 v2 執行屏障模組、測試與變異組（2026-11-14 從 `src/`、`tests/` 用 `git mv` 搬來，內容不改）。pytest、`verify_v2.py`、A4 都不跑；要重跑照它的 README 在暫存目錄拼回 | 只有要重新研究執行屏障時；不要把它搬回 `src/` 而不先改 Q33 |
| [tests/](tests/test_layout.py) | 全部測試（unittest 寫法，pytest 與 `verify_v2.py` 都跑）：v2 原型的測試加上開發骨架自己的 `test_layout.py`。讀本 repo 真文件的測試叫 `*_repo.py`，不放進 mutation 群組 | 加測試時 |
| [tools/verify_bootstrap.py](tools/verify_bootstrap.py) | **部署包的測試**，不是骨架的一部分、也不會被部署出去 | 部署包多一種失效模式時 |
| [tools/skill_split_baseline.json](tools/skill_split_baseline.json) | 拆分前單檔 `SKILL.md`（`VERSION` `2026-11-03`）每一行的雜湊，加上 11 行刻意改寫的去處。`verify_bootstrap.py`「skill 拆分」用它確認沒有行被弄丟。不部署、不同步 | 只有刻意改寫或刪掉舊文本的某一行時，並寫明去處 |
| [tools/sync_project.py](tools/sync_project.py) | **部署包的發佈工具**：把最新內容推到已部署的專案。`check_docs.py` 的專案設定區塊、兩份 hook 接線裡專案自己加的設定都會原樣保留。2026-11-14 起 `AGENTS.md` 歸 `lines`：只換開始／結束標記之間的共用制度（沒有就插在第一個「## 」前），標記外不動，標記外的舊交接段落列成 MIGRATE 要人工比對。只改檔案，不 commit。檔案清單（`WHOLE`／`WIRING`／`PARTIAL`／`INSTANCE`）2026-11-11 起由 `src/kit/owners.json` 算出 | 骨架多一個要同步的檔時：在 `owners.json` 登記；如果是 `region`／`key`／`lines`／`wiring` 這四種，要先替它寫處理程式並更新 `HANDLED`，否則同步器拒絕啟動 |
| [tools/migrate_project.py](tools/migrate_project.py) | P2 第 5 片（決策書 Q25）：把舊專案一次搬到包＋指標。預演只讀（不 fetch、不刷新 index），逐專案列要換、要補、要合併與要人工比對的檔；寫入只能單一專案、要 `--owner` 與一次正式發布，只換本 repo 發過的舊版，客製就整個專案不寫（CRLF 當 LF 比，Q26）。重用 `sync_project.py` 的合併與占用檢查。不 commit、不部署 | 遷移規則改變時；真實專案寫入要逐專案授權 |
| [VERSION](VERSION) | 一行版本號，與部署包開頭的版本行一致（`verify_bootstrap.py` 會擋不一致）。各專案的 `git-freshness.sh` 抓它判斷自己落後沒有 | 跟版本行一起改 |
| [CHANGELOG.md](CHANGELOG.md) | 部署包的逐版變更紀錄與每一版的理由，新的在上面；2026-11-17 從 `src/kit/kit.md` 開頭逐字搬來，部署包只留目前的版本行。不部署 | 每次跳版：舊的版本行改寫成「前一版」移到最上面 |
| `.claude/hooks/repo-pre-push.sh` | 本 repo 的 push 前 hook（2026-11-14，v3 F10，使用者決定補裝）：3.11 `pre-push-handoff.sh` 的**手貼逐字副本**，兩份接線的 PreToolUse 都指向它（Claude Code 的 matcher 跟 3.9 一樣是 `Bash\|PowerShell`，Codex 經 `codex-hook.cmd`）。「本 repo push 前 hook」逐位元組比對；不在 `sync_project.py` 的拓撲裡，改了 3.11 要手動重貼。取代 2026-11-10 試行的動作提醒 `repo-action-rules.sh`（同日使用者決定拿掉） | 改 3.11 時重貼 |
| `.claude/settings.json`＋`.codex/hooks.json`＋`.claude/hooks/repo-git-check.sh` | 本 repo 自己的 SessionStart 檢查。兩份接線掛的都是**同一支** `repo-git-check.sh`（2026-11-01 補 Codex 這一面），所以它們**不是部署包 3.9／3.17 的副本**。2026-11-14 起那支 hook 是 3.10 `git-freshness.sh` 的**手貼逐字副本**（v3 D12：只報事實，最多五行 `[facts]`），「本 repo 開場 hook」逐位元組比對；在那之前是本 repo 自己的判讀版（🔴／🟡、全綠行）。三個檔都不在 `sync_project.py` 的拓撲裡（它直接拒絕本 repo），改了 3.10 要手動重貼，理由在 AGENTS-reasons 的副本規則 7 | 改 3.10 時重貼 |
| `.gitignore`、`.gitattributes` | `dist/`、`.venv/` 不進 Git；全檔強制 `eol=lf` | 幾乎不動 |
| `dist/` | 建置產物（`--zip` 產出的骨架壓縮檔），**不進 Git** | 要發佈就重跑一次，不要留在 repo 裡跟部署包唱反調 |

本 repo 的 `.claude/hooks/codex-hook.cmd` 是 **3.17 啟動器的副本**，跟 `repo-git-check.sh` 的角色不同；更新時從部署包抽取這一檔覆蓋，不把本 repo 當成 `sync_project.py` 的目標。它只尋找 Git Bash、加上避免 JSON 誤判的純文字標頭，並保留 stdin／輸出內容／結束碼，沒有交接規則。既有專案的 Codex 接線升級時會補齊這個新依賴；沒有 Codex 接線的專案仍不自動補裝。`--codex-only` 只同步這兩檔，專案 SKILL 與其他設定不變。

## 部署包的內部結構

v2 原型不在部署包內；詳見 [原型說明](experiments/v2/README.md)。來源驗證器的新增檢查「v2 P0 原型回歸（非需求達標）」執行合成契約、索引負向案例、三個預期架構反例、Mac 隔離與子程序上下文替換探針。它明列 `strict_ready=false`，不把實驗成功當成必要需求達標；空／缺項／SKIP／偽稱 ready 的報告有負向測試。

| 節 | 內容 | 誰會讀它 |
|---|---|---|
| 表頭 | 部署 prompt、版本日期、來源 | 拿到這份檔案的人 |
| 交接自動化怎麼運作 | 觸發（hook）／程序（skill）／防呆（hook）三層 | 想理解設計的人 |
| 跨工具與跨平台 | Claude Code／Codex CLI／Codex 桌面 App／Antigravity 的能力矩陣 | 要在別的工具上部署的人 |
| 0 | 這套骨架在解決什麼問題（失效模式 → 對策） | 想知道「為什麼要有這條規則」的人 |
| 1 | 部署前訪談：佔位符表 | 執行部署的 agent |
| 2 | 要建立的檔案結構 | 同上 |
| 3 | **各檔範本**（3.1–3.21，3.17 產兩檔），照抄只換佔位符 | 同上，改到哪份讀哪節 |
| 4 | 先本機驗收，再首次發布 | 同上 |
| 5 | 部署後自檢清單 | 同上 |
| 6 | 之後怎麼維持（一頁操作卡） | 部署完的專案 |

第 3 節的範本清單就是 `verify_bootstrap.py` 裡 `EXPECTED` 的對照表：

| 節 | 產出 | 角色 |
|---|---|---|
| 3.1 | `AGENTS.md` | AI 開工時自動讀：開始／結束標記之間是共用制度（≤40 行，2026-11-13 起，v3 D11），標記外是專案鐵律（連線資料 2026-11-17 搬到 README，v3 Q40） |
| 3.2 | `CLAUDE.md`＋`GEMINI.md` | **一節產兩檔**：Claude 用 import，Gemini 用文字指標 |
| 3.3 | `HANDOFF.md` | 當下狀態（≤80 行、覆寫不累積） |
| 3.4 | `README.md` | 標準 README：是什麼、為什麼做、快速開始（含連線資料）、開發與驗證、結構指標、協作方式、授權；不放交接 prompt（v3 Q40） |
| 3.5 | `ARCHITECT.md` | 結構的唯一權威（2026-09-07 加入） |
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

## 部署包 → 骨架的抽取規則（改範本前先讀這段）

2026-11-11 起範本的權威在 `src/kit/files/<部署路徑>.tmpl`，`tools/build_kit.py` 把它們放回 `kit.md` 的圍籬區塊生成部署包；下面的規則講的是生成後的部署包，`build_kit.py` 拆分與重建用的是同一套讀法。

`verify_bootstrap.py` 的 `extract()` 就是「照著部署包生檔案」的機器版，規則只有四條：

1. **`### 3.x` 標題行裡的反引號路徑＝產出的檔名。** 改標題就是改檔名——3.2 的標題有兩個路徑，所以一節產兩檔。
2. **一節裡的 fence 依序對應標題上的檔名**；fence 比檔名少就全部沿用第一個（多數節是一檔一區塊）。fence 前的散文是給人看的說明，不會進檔案。
3. **標題行沒有路徑就不產檔**（3.21 是慣例說明）。

第 2 條在 2026-10-30 從「只取第一個 fence，`GEMINI.md` 的標題再由腳本替換」改成現在這樣：3.2 的 `CLAUDE.md` 從此只有一行 `@AGENTS.md` import、`GEMINI.md` 維持指標寫法，兩份內容不同了。把其中一份合成在腳本裡，就等於讓範本內容有第二個家——部署包才是權威版。

所以：**新增一份範本＝在 `kit.md` 新增一節（區塊裡放 `<!-- kit-file: 路徑 -->`）＋新增 `src/kit/files/<路徑>.tmpl`＋把檔名加進 `EXPECTED`，再重生部署包**。只做前者，驗證會 FAIL 說「多出」；只做後者會 FAIL 說「缺少」。

## `tools/verify_bootstrap.py` 守的東西

| 檢查 | 守什麼 | 失敗代表 |
|---|---|---|
| 重生骨架 | 範本清單與 `EXPECTED` 一致 | 有人刪了範本沒發現，或新增範本沒登記 |
| 填佔位符 | 模擬部署後不該有殘留 | 範本用了訪談表沒有的佔位符 |
| `check_docs` | 在填好的骨架跑要 exit 0 | 範本裡有死連結或缺日期標頭 |
| 佔位符清單 | `PLACEHOLDER_NAMES` 涵蓋範本真正用到的名字 | 有個洞永遠不會被檢查到，而且沒有跡象 |
| 佔位符檢查（負向） | 種一個佔位符回去必須被擋下 | 第 5 項檢查本身壞了 |
| 日期標頭（負向） | 拿掉 `ARCHITECT.md` 的「最後更新」必須被擋下 | `check_docs` 的 `DATED_DIRS` 漏了它 |
| 工作中欄位格式（負向） | 四種壞格式（舊格式沒工具欄、主題含「無」、欄位重複、機器欄空白）都要 exit 2，正常的已交棒值不誤擋。2026-11-02 從「工具欄（負向測試）」擴大 | `check_docs` 用子字串判「已交棒」，正常任務名稱就能跳過整個格式驗證（F01） |
| 真實部署形狀 | 部署包在場＋非 ASCII 檔名時仍 exit 0 | 照說明部署的人一定會踩到 |
| 跨平台防呆 | 無絕對路徑、有 `python3` 退路 | 換一台機器會靜默失效 |
| AI push 提醒情境 | staged／unstaged 不放行、已提交開工／交棒放行；命令選項、remote、refspec、GUI／script 的已知邊界；恢復舊捷徑的負向測試 | 未提交修改不會隨 push 上傳，不能拿來放行；有限提醒不能冒充發布保證（2026-11-02／F06） |
| 工作中標記 | 範本有欄位，且 git-freshness 讀 `origin` 那一份後照原文印出（2026-11-13 起不再分 🔴／🟡／✅，v3 D12）：別台機器、主題含「無」原文完整、已交棒、欄位重複說有幾列、欄位不存在明講讀不到、工具環境變數不改變輸出；拿掉印出那一行的負向測試 | 下一棒看不到誰握著分支（F4 偵測） |
| `VERSION` 檔 | 與部署包版本行一致 | 落後偵測會說謊，落後的專案以為自己最新 |
| 版本落後偵測 | 共用制度版本取自 `AGENTS.md` 開始標記；餵**比本機新**的版本要講落後、餵**比本機舊**的要說「比上游新」、同版與 `BOOTSTRAP_VERSION_CHECK=off` 要閉嘴 | 專案不再自己回報落後（F18 提示） |
| 本 repo 自己的文件 | 本 repo 的 `.md` 無死連結、`AGENTS.md`／`ARCHITECT.md` 有日期標頭，受管非 Markdown 檔無已知部署佔位符；`src/kit/` 另有規則，`docs/history/` 封存區不讀（v3 Q39） | 改檔名或搬段落留下死連結，或把未填的部署欄位帶進公開來源。部署包裡指向「部署後才存在的檔」的連結不算，判準是 `EXPECTED`，所以它指向本 repo 檔案的連結照樣會被抓 |
| 封存原件 | `docs/history/` 的 v2 決策書 Git blob 不變（只看 index 記的 blob，不開檔）；程式、測試與設定檔不出現它的路徑（`ARCHIVE_READERS` 登記的除外，登記前要使用者同意）；文件檢查不讀封存區但不外溢。引用、改內容、搬走、略過外溢四種反例都要擋，已登記讀取者放行（2026-11-17，v3 Q39） | 有程式又開始讀 v2，或封存原件被改、被搬走 |
| 本 repo push 前 hook | `repo-pre-push.sh` 跟部署包 3.11 逐位元組相同；兩份接線的 PreToolUse 都指向它；接線守門 7 個負向測試（沒接、指向別支、matcher 退回 `Bash`、接回 PostToolUse、SessionStart 指錯、腳本不存在）（2026-11-14 取代「動作當下送規則」） | 改了 3.11 卻沒重貼，或接線被改掉，本 repo 推 `main` 時沒寫開工標記也不會被擋 |
| 本 repo 兩份接線 | `.claude/settings.json` 與 `.codex/hooks.json` 都是合法 JSON、`SessionStart` 都指向 `repo-git-check.sh`、`PreToolUse` 都指向 `repo-pre-push.sh`（2026-11-14 起；之前只有 Claude Code 那份可多接動作提醒），其他事件一律拒絕，而且沒被改成指向 `git-freshness.sh`／`pre-push-handoff.sh` | 開場檢查靜默不執行——看起來有防護、實際上沒有。這兩個檔是 JSON、塞不進 `source:` 標記，落後偵測看不到它們，這一項是唯一的守門人 |
| sync 拒絕本 repo | `sync_project.py <本 repo 路徑>` 要印出拒絕，**而且預演輸出裡零 `UPDATE`** | 一次手打路徑就把兩份接線改成指向這裡不存在的腳本。只檢查「有印拒絕」的話，一個印了話卻照樣改檔的版本會通過，比沒有這項更糟 |
| 改名寫進回報模板 | A5／B9 各有必填 `session：` 與無改名工具時的回報選項，附負向測試 | 改名漏做卻在 repo 內沒有任何跡象 |
| 續聊狀態與計數 | `AGENTS.md` 共用制度有「`↗`／`※` 時收到新訊息先改回 `㊣`」（2026-11-13 起取代 skill 與指標 description 的觸發詞，skill 不再必讀）；skill 參考檔保留時間與計數、只讀不寫 Git、改檔重跑 A、成功交棒才累加；附 17 個負向測試 | 已交棒後續聊沒恢復工作中，或計數被重算 |
| 本 repo 交接狀態 | 必要欄位與章節、≤80 行、骨架版本符合 VERSION、禁止這次已知過期待辦與只改兩欄的入口規則；附負向測試 | 標記清了卻保留已完成待辦，下一棒被迫從聊天重建現況；不保證任意待辦的語意正確，仍需 B6 人工核對 |
| 規則理由連結 | AGENTS.md 與 CONTRIBUTING.md 每節至少一個、鐵律／副本規則／hook 訊息每條各一個指向 AGENTS-reasons.md 的連結，連結的段落存在且非空；附負向測試 | 理由搬到別的檔之後被悄悄刪掉、新增規則沒有理由、連結指向不存在的段落。只查連結與段落存在，不判斷理由寫得對不對 |
| 來源例外可見性（F46 部分） | 每輪印出已宣告減項（2026-11-14 起剩 handoff skill、check_docs.py 兩項；pre-push 補裝了）；確認來源缺、產物有，並對漏宣告／來源增項／產物缺項跑負向變異 | 三項減項再次從驗證輸出中靜默消失；這只驗可見性，未完成來源／產物全部同組情境 |
| 來源／產物交接快照同組情境（F46 部分） | 同一組 11 種合成快照在來源檢查與部署後 `check_docs.py` 各跑一次：有效、整份缺失、占用欄缺失／重複、章節缺失、超行數、機器／工具欄正反例均須一致；來源檢查遇整份缺失須明確報錯 | 來源少了整份 `HANDOFF.md` 時只拋例外，或產物與來源對相同缺陷給出矛盾結論；實際接手流程仍待驗 |
| 來源／產物文件同組情境（F46 部分） | 同一份合成文件在來源文件檢查與部署後 `check_docs.py` 各跑一次：20 種正反例涵蓋根目錄及巢狀文件的缺檔、死連結、程式碼、角括號加 title、片段、日期及佔位符；沿用來源實際檢查函式 | 同樣的文件缺陷在來源與產物給出不同結論；其他文件項仍待驗 |
| 來源／產物文件設定同組情境（F46 部分） | 9 種合成設定情境對照非 Markdown 已知佔位符、未知樣板、專案自訂過期字串、同列歷史文字與連結／佔位符／過期字串路徑豁免；來源端同時掃自己受管的非 Markdown 檔 | 來源非 Markdown 檔殘留部署欄位，或來源與產物對相同設定給出不同結果；任意專案設定與跨工具遵循仍待驗 |
| 來源提交候選一致性（F46 部分） | 來源 `verify_bootstrap.py --staged` 拒絕未暫存或未追蹤檔；完整／部分 stage 與產物 `check_docs.py --staged` 跑同組 fixture，並對來源未追蹤檔作負向測試 | 用未提交的工作樹內容證明另一份 staged 內容；只驗提交候選形狀，不代表實際接手流程已驗收 |
| 本 repo 開場 hook | `repo-git-check.sh` 跟部署包 3.10 逐位元組相同；多一行與檔案不存在兩個負向測試（2026-11-14 取代「本 repo 工作中判讀」，那一項測的是已退場的判讀版） | 改了 3.10 卻沒重貼，本 repo 開場印的跟共用制度說的不一樣，或退回會下指示的判讀版 |
| 同步清單涵蓋骨架 | `sync_project.py` 的四份清單加起來要等於 `EXPECTED` | 新增範本沒歸類＝那個檔沒人同步，而且沒有徵兆。2026-10-30 就是這樣查出兩份 hook 接線從來沒被發下去 |
| 同步安全 | F02：骨架只擁有**指向骨架腳本的 handler**（同組的自訂 hook 要保留，matcher 衝突／重複組／異常分組要拒絕，`commandWindows` 要認得）。F03：任一項算不出來就零寫入，失敗與不存在的目標要非零退出、不准宣稱最新版 | 同步靜默刪掉專案設定；或失敗一半卻回 exit 0 並宣稱最新版，而落後的專案以為自己同步過了（2026-11-02／F02、F03） |
| 同步升級 mode | 替換前複製既存 mode；複製失敗保留原檔；新依賴仍可建立；移除複製的負向變異必須失敗。POSIX 另驗 0755／0640、開場 hook 直接執行、Git 無 mode diff | 新 inode 預設權限會讓更新後的 POSIX hook 無法執行；Windows 通過不代表 POSIX 實測 |
| 結構摘要一致性 | 本 repo 與生成 ARCHITECT 區分 Claude import／Gemini 文字指標，範本 3.4 那一列寫標準 README、不再寫交接 prompt；三個負向測試 | 權威範本已改，結構表格仍教舊寫法 |
| 接線合併 | 餵一份「舊 matcher ＋ 專案自己加的 permissions 與 hook」進去，要換掉舊值、保住專案設定、已一致時不動 | 同步會洗掉專案設定，或落後的專案根本修不好 |
| 跨工具表保鮮期 | 「跨工具與跨平台」那節的「查證日期」不得超過 90 天（`BOOTSTRAP_FRESHNESS=off` 可跳過） | 對外部工具能力的斷言在無聲中過期。這一項只保證有人看過日期，**不保證有人真的重查**——買到的是「必須有意識地決定」。會做成 fail 而不是警告，是因為上一次的對策就是一句警告，而警告沒擋住第二次（Antigravity 的 hooks、Codex 桌面 App 的 hooks，兩次同一種錯） |
| README 跨工具表一致性 | README 那張跨工具表與部署包那一張：同名列的判定符號一致、README 沒有孤兒版本號、有指回部署包的指標（附四種分岔的負向測試） | README 是**人的入口**，而保鮮期只守部署包那一份——事實在部署包被重查改對，README 留在舊事實上，沒有任何徵兆。2026-11-01 加這一項的當下就抓到一處已經發生的分岔（「自動載入程序檔」×「Codex CLI」）。不給 README 自己一個「查證日期」是因為那是同一個事實的第二個時鐘 |
| ZIP 說明指標 | ZIP 隨附說明的工具差異只連到同包部署包的「跨工具與跨平台」及第 5 節，不另列逐工具能力摘要（附六個負向測試） | 壓縮檔第一份說明成為另一個會過期的家；2026-11-01 確認它仍寫著 Codex 桌面 App、Antigravity 沒有 hook，矩陣與 README 的檢查都看不到它 |
| 跨工具過期敘述 | 部署包正文、本 repo 結構說明、重生的結構範本與 handoff skill，不得復活 CLI／2.0 測試狀態、Antigravity 接線、skill 入口與 IDE 追查決定的已知舊斷言；附回歸負向測試與範圍測試 | 同一份文件的表改對了，散文卻仍教下一棒照舊事實行動。只檢查已知回歸，不做通用語意判讀、不代替外部查證；表頭的歷史變更記錄與 IDE 未解結果仍保留 |
| Codex Windows 接線 | `commandWindows` 經 Git Bash 啟動器，兩個事件與本 repo 都指向原本那支 `.sh`；三個負向測試 | 真部署的已信任 hook 曾選到 WSL 而 exit 1 |
| Codex Windows 結束碼 | 實跑 PowerShell → cmd → Git Bash；保留 exit 2，拿掉明確 exit 時必須重現 exit 1 | 只測原生 cmd 會把工具仍放行的版本誤報成功；此項只在 Windows 執行 |
| Codex 接線升級 | 舊專案補齊啟動器、保留專案 hook 與 SKILL、預演零寫入、重跑零變更、不替沒有接線的專案補裝 | 只更新 JSON 卻漏掉新依賴會再度靜默失效 |
| Codex Windows 啟動器 | Windows 原生 cmd 實跑中文／空白路徑、不同 cwd、stdin／stdout／stderr／exit 2 與缺少 Git Bash 的情境 | 轉接層若吞掉 exit 2，pre-push 防呆會消失；此項只在 Windows 執行 |
| verify_state 失敗訊號 | 命令非零退出、HTTP 500、連不上、200 但回應內容不對都要讓結束碼非零；缺憑證是 SKIP，`--strict` 才非零、`OPTIONAL` 放行；未填仍回 0；祕密要遮罩。十個情境全部實跑 | 舊版每一種情況都 return 0，畫面印著 `rc7` 而下游拿 exit 0 當服務驗收（2026-11-02／F04） |
| 交接快照檢查 | `HANDOFF.md` 不見了、超過 80 行、缺必要章節或欄位重複都要 exit 2；`--docs-only` 要真的關得掉；程式碼範例、帶 title 與角括號連結不得誤報，但真的死連結仍要抓到 | 第 6 項只在 HANDOFF 出現在輸入清單時才驗，整份刪掉反而回報乾淨；而連結誤報會教人「這支腳本的 FAIL 可以無視」（2026-11-02／F08） |
| Python 版本下限 | 兩支維護工具檔頭的 `MIN_PY` 存在、會擋、兩邊同號；README 範本寫出部署後工具的下限；四支 `.py` 都沒有用到高於下限的 API（掃描前把註解與字串塗白） | 3.13-only 的 API 在舊版 python 上是執行到那一行才炸成 TypeError，不會說「版本太舊」。下限是靜態擔保、不是實測：沒有舊版可跑，要實測得先有 CI（2026-11-02／F14） |
| 已修正的主張沒復活 | 能力表 ✅ 的工具不得被散文說成沒有 skill、交接 prompt 不得有自己的 A／B 編號且要寫出模式、`verify_state` 不得以憑證為前提、版本序號只有一種定義、可攜層不得寫成「到哪都成立」；附九個負向測試 | 事實在部署包被改對，範本、操作卡與入口文件裡的舊說法照樣部署出去。綁結構不綁禁句，「」裡的引用不算主張（鐵律 3 要留為什麼）；守不了一整段敘述的準確度（2026-11-02／F15） |
| ZIP 發布門檻 | 注入結果走 CLI 與實際 ZIP：全過才正常打包；SKIP 預設拒絕，顯式例外附 UNVERIFIED.json 與說明、仍 exit 1；FAIL 不可繞過；拒絕時保留舊檔。含移除門檻的負向測試 | 舊流程有 SKIP 仍先打包再回 1，看似正式產物但未完整驗證（2026-11-02／F07） |
| 協作狀態契約／Git 異常提示 | 六狀態與步驟契約、21 個負向測試，含 R07 先 stage 再驗證。Git 異常：部署 hook 實跑領先／分岔／fetch 失敗要照實報出、不得建議 rebase，`AGENTS.md` 共用制度要有停止條件；本 repo hook 照舊要求停止；2 個負向測試 | 程序順序矛盾或工具提示教人自行 rebase |
| 核心與實例優先序 | skill／README 宣告一致、override 範圍明確、部署包不再產出交接協定（v3 Q41）、7 個負向測試；同步對舊實例列版本與 MIGRATE，不改寫 | 不同步的舊協定會推翻新程序（F10） |
| 接力協調邊界 | A2.5／A5 明列協調訊號非鎖、SHA 比對與禁止自動奪權，4 個文字負向測試（協定 2026-11-17 移出部署包） | 不宣稱並行互斥；原子 claim 留待另案（F12） |
| skill 拆分 | 七個 skill 檔齊全、同版本、都在 `WHOLE`；入口＋`mode-a.md` ≤6,000 字元；入口 12 條、`mode-a.md` 12 條必備句；拆分前每一行逐字留存或列入已改寫清單（13 行） | 入口指向不存在的檔、同步只寫一半、濃縮時丟了停止條件或理由。不證明模型會去讀模式檔 |
| AGENTS.md 共用制度 | 開始／結束標記成對、26 條必備條件（v3 第 5 節；第 26 條是 F50 互動驗證後補的「選項卡片也算停下來」）、共用 ≤40 行、全檔 ≤100 行（v3 D11）、開始標記的版本等於 `VERSION`；30 個負向測試（2026-11-13 新增） | 每個 session 都載入的那一層缺了條件、長過預算，或版本提示失準。只證明文字在，不證明模型照做 |
| 同步補齊模式檔 | 只有單檔的舊專案會補上五個新檔、入口最後寫、不認得的檔列為 EXTRA；1 個負向測試 | 同步後新入口指向不存在的模式檔 |
| 同步共用制度 | `AGENTS.md` 沒有共用制度就插在第一個「## 」前、舊版整段換掉、標記外不動、已是權威版不寫、壞標記 FAIL 不寫、舊交接段落列 MIGRATE、先於 skill 入口寫；1 個負向測試 | 新 skill 指向舊專案 `AGENTS.md` 裡不存在的共用制度（2026-11-14 加，v3 Q34 前置） |
| 同步範圍與前置檢查 | 真 worktree、含 worktrees 普通目錄、已完結 inventory；fresh fetch／upstream 對齊／明確 owner、dirty／占用／整份檔與 check_docs 共用程式區客製漂移拒絕且零寫入；批次僅預演，單專案 A5 writer 才能寫入 | 路徑字串不是 worktree 證據，批次同步不能悄悄擴大範圍（F13） |
| 部署生命週期 | 訪談自訂 ignore、本機檢查→首 commit→local bare push→clone，clone 後開場 hook 印出 `[facts]`；5 個負向測試 | 圍欄外追加規則及發布後才驗收無法保護首 commit |
| 部署包由來源生成 | `src/kit` 生成結果與 `PROJECT-BOOTSTRAP.md` 逐位元組相同、每個範本剛好用一次、範本集合等於 `EXPECTED`；9 個負向測試（手改部署包、改範本或散文沒重生、多／少範本、指錯、重複、缺結尾換行、範本含收尾圍籬） | 有人手改了部署包，或改了來源沒重生 |
| P1 開發骨架 | pyproject 依賴都在 `uv.lock`、外部套件都有 sha256 與授權、最低 Python 3.12、`package = false`；`tools/` 與 `src/project_bootstrap` 的程式除 `P1_EXTRAS` 列的模組外不 import 鎖檔裡的套件，也不 import 那些模組；import 它們的測試缺套件時 SkipTest；10 個負向測試。不需要 uv，鎖檔是否最新要另跑 `uv lock --check` | 依賴沒鎖或沒審授權；A4 在沒裝 uv 的機器跑不起來 |
| 行末與雜項 | 全 LF、JSON 合法、腳本可執行 | Windows 寫出 CRLF、設定檔打錯字 |

> **2026-11-13 驗證項取捨（v3 第 1 期）**。準則：守 v3 仍為必要的需求就留；守已退役或降強度的需求、Antigravity、或「skill 必讀」結構的就改或移除。
> - **移除「Antigravity 接線」**：v3 D8 放棄 Antigravity，三個檔移出部署包。
> - **改「git-freshness.sh」「工作中標記」「版本落後偵測」「接線 cwd 定位」「F46 接手流程」「Git 異常提示」**：部署 hook 只報事實（v3 D12），檢查改看 `[facts]` 原文與「最多五行、沒有指示行」，本 repo 自己的 hook 照舊。
> - **「全綠行」縮到本 repo 的 hook**：部署 hook 不再印這一行。
> - **「skill 拆分」入口必備句 18 → 12**：拿掉的六句（A2.5 占用、A1–A4 不改檔、找不到模式檔就停、每則新訊息看 session 狀態、續聊改檔前重走 A1–A5、`session：` 一行）改由新增的「AGENTS.md 共用制度」守，因為 skill 不再必讀（v3 第 5 節）。
> - **「續聊狀態與計數」**：觸發詞從 skill description 搬到 `AGENTS.md` 共用制度。
> - **「部署生命週期」「同步升級 mode」**：拿掉 Antigravity wrapper 的 100755 兩項，改用開場 hook。
> - **2026-11-13 列給使用者決定的四項，2026-11-14 使用者逐項定案**：「AI push 提醒情境」維持 exit 2 擋下——依據是 v3 D13「強制進 hook」，擋的是沒寫開工標記就推 `main`（違反共用制度條件 1）；v3 F10 原本字面寫「偵測＋可選提醒」，同日使用者決定把 F10 改成「偵測＋阻擋（限 push 前 hook）」，跟 D13 與部署包一致。「工作中欄位格式（負向）」保留：`check_docs.py` 回非零是檢查工具回報失敗，屬偵測（D2），不是自製執行屏障，已對齊 v3。「接力協調邊界」與「協作狀態契約」保留：skill 雖是碰到才讀，異常時模型讀的就是那些句子，檢查防它們靜默消失；代價是改措辭要同步改檢查器。「跨工具表保鮮期」保留；README 跨工具表拿掉 Antigravity 欄、檔案樹拿掉不再部署的 Antigravity 檔，補一句 2026-11-13 起放棄（v3 D8）；README 那張是部署包能力矩陣的轉述（一致性檢查綁住），所以 `src/kit/capabilities.json` 的 tools 表同步拿掉那一欄，「README 跨工具表一致性」改成接受至少三個工具欄。

**exit 0 才算改完**（鐵律第 4 條）。印出 `skip` 的項目沒有被驗證，回報時要照實寫。

## 副本拓撲（同一份東西存在於多個地方的，只有這些）

```text
handoff skill 目錄（2026-11-10 起六個檔，2026-11-16.4 起七個，同版本、整個目錄一起覆蓋）
  部署包 3.8（權威）
    └─→ 各專案 .claude/skills/handoff/
          ├─→ （選用）~/.claude/skills/handoff/   ← 模式 0 建制真正會被載入的地方
          ├─→ （選用）~/.codex/skills/handoff/    ← Codex CLI 與桌面 App（2026-10-30 實測
          │                                          CLI 0.164.0 仍讀這個路徑，雖然官方
          │                                          文件已經不列它）
          └─→ .agents/skills/handoff/SKILL.md     ← 只放指標，不複製內容。Codex 把它當
                                                     專案層 skill 來源（Antigravity 2026-11-13
                                                     移出部署包），description 與權威版相同
                                                     （那是它被發現的唯一依據）

兩支 hook .sh
  部署包 3.10／3.11（權威）
    └─→ 各專案 .claude/hooks/*.sh   ← 只有這一份腳本
          ├─← .claude/settings.json 指向它
          └─← .codex/hooks.json 指向同樣那兩個（不複製第二份）

check_docs.py
  部署包 3.14（權威，「專案設定」區塊除外——那塊本來就該依專案調）
    └─→ 各專案 tools/check_docs.py

兩份 hook 接線（JSON；Antigravity 那份 2026-11-13 移出部署包，已部署的不同步、不刪除）
  部署包 3.9／3.17（權威，只管「指向骨架那幾個 .sh」的那幾組；
                        專案自己加的 permissions／env／額外 hook 原樣保留）
    ├─→ 各專案 .claude/settings.json
    └─→ 各專案 .codex/hooks.json
```

**本 repo 自己的兩份接線（`.claude/settings.json`、`.codex/hooks.json`）不在上面這張圖裡。**
它們跟 3.9／3.17 路徑同名、形狀也幾乎一樣，但掛的是這個 repo 自己那支 `repo-git-check.sh`——
所以是**同名而非同源**，沒有同步義務，也不跳 `source:` 版本。（那支 hook 本身 2026-11-14 起是 3.10 的手貼逐字副本，
由「本 repo 開場 hook」逐位元組比對，不靠 `sync_project.py`。）而「路徑同名」本身就是風險：
`sync_project.py` 的 `WIRING` 清單認的是路徑，手打一次 `sync_project.py <本 repo>` 就會把它們
改成指向這裡不存在的 `git-freshness.sh`。2026-11-01 起那支腳本直接拒絕本 repo（`--all` 本來就
掃不到它），`verify_bootstrap.py` 的「sync 拒絕本 repo」與「本 repo 兩份接線」兩項各守一端。

**JSON 沒辦法放 `source:` 標記**，所以上面那兩份接線在落後偵測裡是隱形的——它們唯一的守門人是 `sync_project.py` 的 `WIRING` 清單加上 `verify_bootstrap.py` 的「同步清單涵蓋骨架」。2026-10-30 把它們補進拓撲，是因為 2026-09-13 給 3.9 補的 `Bash|PowerShell` matcher 一直沒發下去：三個專案停在舊的 `Bash`，而那台機器的主 shell 正是 PowerShell，pre-push 防呆於是在那些專案等於沒裝，一個半月沒有任何徵兆。

每份副本檔頭有 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->`，**改內容就要跳版**，否則沒人分得出哪份落後（鐵律第 2 條）。同一天改第二次起要在日期後面加序號（`v2026-10-24.2`）——日期粒度只能證明「不早於那一天」，2026-10-24 就因此誤判過一次。
沒改內容的檔案不要跟著跳版——謊報「副本落後」之後，這個標記就沒人再信。

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

- **沒有 handoff skill、沒有 `check_docs.py`**（2026-11-14 前還有 `pre-push-handoff.sh`，見下面那條）。 它是制度的**來源**，不是一個交接中的工作專案；把骨架的這幾份套到它自己身上，就會出現「權威版與它的副本互相同步」的迴圈。跨 session 現況看 `HANDOFF.md`，歷史與版本證據看 `git log` 與各檔的 `source:` 標記；接棒程序讀全域副本 `~/.claude/skills/handoff/`。**`HANDOFF.md` 是 2026-10-30 補回來的例外**，見下一條；`pre-push-handoff.sh` 同一天重新評估過，結論仍是不裝，但理由已經換成另一個，見下面那條。
- **跨機器「工作中」標記：2026-10-30 先是接受這個缺口，同一天決定多機維護就補上了。** 當初不裝的理由是它需要 `HANDOFF.md` 當載體，而那一份得每輪交棒維護——只為防呆而裝，就是多一份沒人讀、然後開始腐化的文件；那時 single writer 靠人顧。改成多機維護之後這個理由不成立了：`git log` 與 `git fetch` **看不到別台機器未提交的變更**，而開場那個 ✅ 只證明「本機沒落後 origin」，誤接棒就會整批繞過那些變更。所以補上 `HANDOFF.md`（範本 3.3 的*實例*，不是副本，沒有同步義務），並在 `repo-git-check.sh` 加判讀段——**沿用 3.10 的同一個載體與同一個欄位，沒有發明第二種標記**，那會變成「這裡會擋、別處不會擋」的不對稱。當時為減少維護成本而限制更新欄位，卻仍保留完整狀態段落，導致已完成待辦凍結；2026-11-01 已取消此限制，維護義務與事故見 [AGENTS.md](AGENTS.md)「本 repo 的交接快照」。**天花板要講明白**：標記只告訴你「東西在那台機器上」，東西本身仍得回那台 push，這不是實作缺漏。
- **`pre-push-handoff.sh`：2026-10-30 決定不裝，2026-11-01 恢復交接快照後重新評估仍不裝；2026-11-14 使用者決定補裝**（`repo-pre-push.sh`）。補裝的理由：v3 把 F10 定成「偵測＋阻擋（限 push 前 hook）」，擋的正是「沒寫開工標記就推權威分支」這一種，不再宣稱它驗得出交接內容正確；下面 2026-11-01 那段「攔不住 stale 事故」的觀察仍然成立，只是不再是不裝的理由。以下是當時的評估原文： 原理由是標記之外沒有狀態要寫，推進度時只會逼人編變更或關掉防呆；如今這個前提已取消，不能沿用舊理由。重新評估的限制是：骨架那支 hook 只檢查這批 commit 是否碰過 `HANDOFF.md`，而 A5 的開工標記本來就會碰它；本次三輪 stale 事故正是「檔案都有改、待辦沒改」。因此原樣裝上也攔不住已知故障，還會讓人誤信狀態已被驗證。現階段由 B6 核對整份快照，`verify_bootstrap.py` 檢查版本與已知回歸；不以時間戳或碰過檔案冒充內容正確。若將來有能檢查實質交接的機制再評估。
- **但有一支自己的 SessionStart hook**（`.claude/hooks/repo-git-check.sh`，2026-10-30 加）：做 git 新鮮度比對、「工作中」判讀（2026-10-30 加）與開工改名提示（2026-11-01 加）；2026-11-14 起改成部署包 3.10 的逐字副本，只印事實、不再判讀或提示（v3 D12）。**2026-11-01 起 Codex 這一面也接上了**（`.codex/hooks.json`，掛同一支腳本、不複製第二份）——在此之前只有 Claude Code 會跑它，而這個 repo 本來就在多工具維護；代價是它跟那六個專案一樣進了「Codex 要各審一次」的清單（信任綁 `hooks.json` 的絕對路徑），2026-11-01 已完成現行 hook 的注入與阻擋驗收，本次桌面 session 亦收到開場輸出；檔頭明寫**不是 3.10 的副本、不要同步**（2026-11-14 起改成 3.10 的手貼逐字副本，見根目錄表與 AGENTS-reasons 的副本規則 7）。在此之前這個 repo 開場完全沒有提醒，A1 的 fetch 全靠使用者記得打「接棒」把全域 skill 載進來。為什麼不直接抄 3.10——`sync_project.py` 的 `discover()` 靠 handoff skill 發現專案，這個 repo 沒有 skill，`--all` 永遠掃不到它，抄過來就會變成「所有專案都同步了、只有來源自己落後」而且毫無跡象的那一份副本。
- **沒有把驗證交給 CI。**（2026-09-13 隨本檔首版 `7a5d1ec` 寫入「沒有 CI」；日期取自 git 首次出現，當時沒有記錄另外的評估）驗證是一個指令（`python -X utf8 tools/verify_bootstrap.py`），跑它是鐵律第 4 條的義務。2026-11-11 起有一支 workflow（`.github/workflows/release.yml`，決策書 Q21），但它只在有人 push `release-request/<channel>` tag、而且使用者在 `release` environment 核准後才跑，用途是發布正式包；push 與 PR 不會觸發驗證，鐵律第 4 條照舊。
- `tools/` 保存來源維護入口：`verify_bootstrap.py` 測試部署包及 v2 原型、`sync_project.py` 同步它；2026-11-06 新增 `verify_v2.py` 執行隔離原型。三支都不部署。`experiments/v2/` 的程式是未部署的候選實作，沒有從部署包移轉任何現行規則權威。

## 全域約束（誰強制什麼）

| 約束 | 由誰強制 | 理由與做法 |
|---|---|---|
| 全檔 LF | `.gitattributes` 的 `eol=lf`＋`verify_bootstrap.py` 的行末檢查 | [CONTRIBUTING.md 行末那節](CONTRIBUTING.md) |
| 不寫單位名／內部代號／本機絕對路徑 | 人（提交前擋）＋骨架端的跨平台防呆檢查 | [AGENTS.md 鐵律第 6 條](AGENTS.md) |
| 只放通用制度與 `{{佔位符}}` | `verify_bootstrap.py` 的佔位符清單比對 | [AGENTS.md 鐵律第 5 條](AGENTS.md) |
| 副本改內容就跳 `source:` 版本 | 人 | [AGENTS.md 鐵律第 2 條](AGENTS.md) |

## 改本檔的時機

根目錄多／少一個檔案、部署包增刪一節範本（記得同步 `EXPECTED` 與上面的 3.x 對照表）、`verify_bootstrap.py` 增減檢查項、副本拓撲改變。
**跟該變動同一個 commit**，並更新檔頭的「最後更新」。
