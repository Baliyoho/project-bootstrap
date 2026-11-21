# AI 維護手冊

> 最後更新：2026-11-21
> 這個 repo 由維護者與 AI session 維護。本檔是改這個 repo 時的做法：步驟、指令與踩過的坑，做到那件事才讀。規則在 [AGENTS.md](../AGENTS.md)，每個 session 開場自動載入；本檔提到規則時連回去，不重述。每條的現行理由在[理由檔](rationale.md)，被取代的理由與經過在[理由檔歷史紀錄](history/rationale-history.md)。**要改、質疑或想繞過某條規則之前，先讀它的理由。**

## 改部署包的流程

規則見 [AGENTS.md](../AGENTS.md) 的規則 10、11、13；這裡只寫操作細節。[為什麼](rationale.md#rule-1)

- 動到結構（根目錄增刪檔案、部署包增刪一節範本、驗證項增減、副本拓撲改變）就更新 [ARCHITECTURE.md](../ARCHITECTURE.md)，跟該變動同一個 commit，並更新它檔頭的「最後更新」；增刪範本時同步 `EXPECTED`。
- 新增範本：在 `src/kit/owners.json` 登記歸屬；歸 `region`／`key`／`lines`／`wiring` 四種的，要先在 `sync_project.py` 寫處理程式並更新 `HANDLED`，否則同步器拒絕啟動。改跨工具表改 `src/kit/capabilities.json`，不改 `kit.md`。
- 部署包跳版時 `VERSION` 跟版本行一起改；`src/kit/kit.md` 開頭只留新的「版本」行；舊的那一行改寫成「前一版」，移到 [CHANGELOG.md](../CHANGELOG.md) 最上面。不跳版的修改也在 CHANGELOG 最上面記一條。
- 驗證印「提醒」的項目不影響結束碼，但要轉告使用者。加 `--quiet` 只隱藏成功的明細，FAIL、`skip`、提醒與結束碼照常。
- 全套驗證在 macOS 約 35 秒，在原生 Windows 約 3–4 分鐘，超過指令工具預設的 120 秒上限，逾時不等於失敗。Windows 上 `python3` 是 WindowsApps 別名，要用 `python`。[為什麼](rationale.md#rule-4)

### 部署包怎麼變成檔案（改範本前先讀）

2026-11-11 起範本的權威在 `src/kit/files/<部署路徑>.tmpl`，`tools/build_kit.py` 把它們放回 `kit.md` 的圍籬區塊生成部署包；下面的規則講的是生成後的部署包，`build_kit.py` 拆分與重建用的是同一套讀法。

`verify_bootstrap.py` 的 `extract()` 就是「照著部署包生檔案」的機器版，規則只有四條：

1. **`### 3.x` 標題行裡的反引號路徑＝產出的檔名。** 改標題就是改檔名——3.2 的標題有兩個路徑，所以一節產兩檔。
2. **一節裡的 fence 依序對應標題上的檔名**；fence 比檔名少就全部沿用第一個（多數節是一檔一區塊）。fence 前的散文是給人看的說明，不會進檔案。
3. **標題行沒有路徑就不產檔**（3.21 是慣例說明）。

第 2 條在 2026-10-30 從「只取第一個 fence，第二個檔的標題再由腳本替換」改成現在這樣：當時 3.2 一節產兩個內容不同的檔（2026-11-17 起只剩 `CLAUDE.md`）。把其中一份合成在腳本裡，就等於讓範本內容有第二個家——部署包才是權威版。

所以：**新增一份範本＝在 `kit.md` 新增一節（區塊裡放 `<!-- kit-file: 路徑 -->`）＋新增 `src/kit/files/<路徑>.tmpl`＋把檔名加進 `EXPECTED`，再重生部署包**。只做前者，驗證會 FAIL 說「多出」；只做後者會 FAIL 說「缺少」。

## 同步到已部署的專案

Codex 的 Windows 接線與 Git Bash 啟動器可用 `python -X utf8 tools/sync_project.py <專案路徑> --codex-only` 預演；實際寫入依下面的段落先接棒並加 `--owner`，不改專案的 SKILL 或其他設定。接線變更後要重新審核並驗收實際執行，條件與理由見部署包 3.17。[為什麼](rationale.md#copy-6)

`sync_project.py --all` 預設只掃 Desktop 下一層；可用 `--root <目錄>` 改掃描根目錄、`--exclude <目錄名>` 排除已完結專案。工具列出每個候選的納入／排除原因，透過 Git 的 git-dir／common-dir 排除 linked worktree，全域 skill 副本仍須另行同步。

固定範圍建議使用私人 inventory：`--inventory <清單.json>`，內容如 `[{"path":"../project-a","status":"active"},{"path":"../project-b","status":"archived"}]`；相對路徑以清單所在目錄為準，清單不要提交到公開骨架。預演與寫入都檢查 dirty、工作中標記、整份覆蓋檔與 `check_docs.py` 共用程式區的客製漂移。已檢視的 dirty 僅能在單一專案加 `--allow-dirty`；未知共用內容須人工比對後逐檔加 `--accept-drift <路徑>`，占用不能略過。不 stash、不 commit；這些檢查也不是並行鎖（2026-11-02／F13）。

**跨專案寫入先逐一 A1–A5 接棒**（2026-11-03／R03）：在目標專案推送本 session 的開工標記，再以 `--owner '<工作中欄位完整值>'` 聲明目前 writer。同步器會 fetch origin、確認 HEAD 與 `origin/<目前分支>` 完全一致，並核對本機與遠端的標記都精確等於 owner；套用前再查一次。離線、無 upstream、領先／落後／分岔、他人標記或本機標記漂移均拒絕，`--allow-dirty` 不豁免。owner 是呼叫者明確核對的協調證據，不是身分認證或原子鎖，仍須確認同工作樹只有一個 writer。

`--all`／inventory 僅供批次預演；`--write` 必須指定單一專案與 owner，空閒標記不能寫入。同步後留在該專案完成 B7 最終檔案檢查、B8 發布與清標記；若要中途安全點則走 C，保留占用。這修正了舊工具「正常 A5 writer 被拒絕、陳舊空閒 checkout 卻能寫」的矛盾。

副本存在哪些地方見 [ARCHITECTURE.md](../ARCHITECTURE.md) 的副本拓撲；改 skill 的規則見 [AGENTS.md](../AGENTS.md) 規則 10、11。

## 改安裝程式

規則見 [AGENTS.md](../AGENTS.md) 的規則 10；這裡只寫操作細節。[為什麼](rationale.md#rule-1)

- `bootstrap.py` 是產物：安裝與更新邏輯在 `src/project_bootstrap/installer.py`，範本與 `owners.json` 在 `src/kit/`，`update` 用的合併函式是 `tools/sync_project.py` 裡 `build_kit.SHARED` 列的那些，原樣搬進去。改任何一邊都跑 `python3 -X utf8 tools/build_kit.py`，同一個 commit 提交。
- 新增一個要搬進 `bootstrap.py` 的同步函式，名字要加進 `build_kit.SHARED`；少了會在重生時報 `sync_project.py has no …`。
- 測試：`tests/test_installer.py` 直接 import `installer.py`、從 `src/kit/` 讀範本，是變異測試的對象；`tests/test_bootstrap_repo.py` 在暫存資料夾實跑建好的 `bootstrap.py`（空資料夾、已有檔案、更新、CRLF、兩支 hook）。
- 安裝程式只碰本機：不連網、不 commit、不推送、不建 GitHub repo。要加這類動作先改需求決策書（v3 Q49）。

## 開發注意事項

改這個 repo 時容易踩的地方，碰到對應的檔才需要讀。[為什麼](rationale.md#dev-notes)

- 改 handoff skill 的做法（規則見 [AGENTS.md](../AGENTS.md) 規則 10、11）：改 `src/kit/files/.claude/skills/handoff/*.tmpl`，AGENTS 範本的共用制度標記跟 skill 同版本，本 repo `AGENTS.md` 的共用制度副本要重貼。改到逐字搬來的行，「skill 拆分」會擋：要嘛還原，要嘛在 `tools/skill_split_baseline.json` 的 `rewritten` 寫明去處。改了模式檔的段落標題，「skill 規則對照表」會擋，要一起改 `reasons.md` 對照表。改完要重新覆蓋這台的兩個全域目錄。
- v2 的程式全部封存在 `archive/v2-*/`（v3 Q33、Q46），不執行、不維護；main 上的程式、測試與現況索引不能引用它們（`verify_bootstrap.py`「封存原件」擋）。要重新研究照各自的 README 在暫存目錄拼回。
- 換版（v3 Q47）：新版決策書成為權威時，`AGENTS.md` 改連新版，驗證器的「版本更替」就開始擋舊版本名稱。現行區裡檔名、資料夾名或程式識別字帶舊版本號的東西，逐一刪除、`git mv` 到 `archive/`，或改成新版本的名稱，同時更新讀它們的程式與文件。舊版的權威文件與它的熱歷史照決策書第 7 節搬進 `archive/docs/`。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件。HANDOFF 的「下一步」與懸置裡**不要把已有裁定的 Q 編號跟等待決定的字樣寫在一起**；懸置每條要引用決策書 v3 第 8 節的 `Q` 編號（或 `- 無。`）。v3 第 3 節 D 表每列要有「決定」與「理由」；第 8 節已決項目底下子項格式是「採用理由／未選 (x) 名稱：／暫緩 名稱：」，選項名不能省，省了就報 `alternative-incomplete`（2026-11-17 封存 v2 時在 v3 踩到）。這兩個解析器與需求清單的解析器都按節名找節、不看節號（2026-11-17 起），改節名會讓它們讀不到東西，測試會失敗。
- 提交指令要用 `&&` 綁住 verify 的結束碼。macOS 上 zsh 跟 bash 不同的三種寫法（管線結束碼、`echo =====`、未加引號的 `$變數`）2026-11-18 起寫在部署包 handoff skill 的 `env.md`「macOS」一節，本 repo 讀全域那份或 `src/kit/files/.claude/skills/handoff/env.md.tmpl`。
- 新增或改規則：每個 session 都要守的寫進 `AGENTS.md`，只有做那件事時才用得到的做法寫進本檔對應的一節；兩邊的「為什麼」都連到[理由檔](rationale.md)的錨點。理由改了就改寫理由檔那一節，舊理由加到[理由檔歷史紀錄](history/rationale-history.md)同一個錨點那組的最後（規則 12）。
- 讀 `tools/` 的測試不能放進 mutation 群組，所以拆成 `*_repo.py`。`mutants.py --only` 要給測試模組名（`tests.test_x`）。從 repo 根目錄跑模組要 `PYTHONPATH=src`；測試裡用 `-c` 起、要 import 本套件的子程序，`cwd` 要給 `src`。改了檢查模組就用 `mutants.py --only` 實跑對應的變異組。
- 改 `src/project_bootstrap/` 的檢查時，同時更新 `mutants.json` 對應的變異組並實跑。
- 刻意改寫或刪掉 handoff skill 拆分前的舊行時，在 `tools/skill_split_baseline.json` 的已改寫清單記一筆，寫明去處。
- 加減依賴時 `pyproject.toml` 與 `uv.lock` 一起改（`uv lock`），新套件同時登記授權。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。

## 副本規則

拓撲在 [ARCHITECTURE.md](../ARCHITECTURE.md)。動副本或接線之前，先讀對應理由段落的完整原文。

- 改完部署包，所有副本一起覆蓋，含選用的兩個全域 `skills/handoff/`。[為什麼](rationale.md#copy-1)
- Codex 與 Claude Code 掛同樣兩個 `.sh`，不在 `.codex/` 複製第二份；Windows 的 `codex-hook.cmd` 只做管線。[為什麼](rationale.md#copy-2)
- Antigravity 2026-11-13 起移出部署包（需求決策書 v3 D8）：舊 3.18–3.20 不再產出，已部署專案裡那三個檔不同步也不刪，清不清由使用者決定；要重新支援先讀理由裡的四個約束。[為什麼](rationale.md#copy-3)
- 接線路徑一律相對、不假設 cwd：前面掛 `$(git rev-parse --show-cdup)`；Antigravity 刻意不跟。[為什麼](rationale.md#copy-4)
- `.agents/` 只放指標與接線，skill 指標的 `description` 寫滿觸發詞。[為什麼](rationale.md#copy-5)
- Codex 啟動器也要同步（`sync_project.py --codex-only`）；接線改過要重新審核並驗收實際執行。[為什麼](rationale.md#copy-6)
- 本 repo 自己的 `HANDOFF.md`、兩支 `repo-*.sh`、`.claude/settings.json`、`.codex/hooks.json` 不在拓撲裡，`sync_project.py` 不碰；其中 `repo-git-check.sh`、`repo-pre-push.sh` 是 3.10、3.11 的手貼副本，改了範本要手動重貼，驗證器比對逐字相同。[為什麼](rationale.md#copy-7)

## 封存結案的文件

文件的分工與權威規則見 [ARCHITECTURE.md](../ARCHITECTURE.md)「碰到才讀的文件」與[需求決策書 v3](../project-bootstrap-requirements-decision-v3.md) 第 7 節；這裡只寫封存的做法。[為什麼](rationale.md#doc-roles)

結案或被取代的需求與計畫類文件用 `git mv` 移到 `archive/docs/`，在它的[索引](../archive/docs/README.md)加一行；只把還有效的內容併進兩份權威文件。程式與測試不讀封存區（`verify_bootstrap.py`「封存原件」守）。

## 本 repo 的交接快照

B6 核對並覆寫整份 `HANDOFF.md`（≤80 行）：移除已完成待辦；未知分清現行故障與歷史無法歸因；版本與驗證照實際結果；沒做完寫明風險與續作步驟；收工清掉工作中標記。驗證器只守必要欄位，不判斷待辦是否真的完成。要額外模型呼叫的探針先取得授權、只用訂閱額度；新增守門要附負向測試。[為什麼](rationale.md#snapshot)

## 這個 repo 自己的指標檔

`CLAUDE.md` 只有一行 `@AGENTS.md`，不要改回「去讀 AGENTS.md」的句子。本專案明確不支援 Gemini，不放 `GEMINI.md`。[為什麼](rationale.md#pointer)

## 行末

`.gitattributes` 強制 `eol=lf`；用 Python 改寫記得 `newline=''`。[為什麼](rationale.md#eol)

## 改兩支 hook 的訊息時

- 雙引號裡不寫反引號，欄位名用「」。[為什麼](rationale.md#hook-1)
- `$變數` 緊接中文或全形標點時寫成 `${變數}`。[為什麼](rationale.md#hook-2)
- 用腳本改時不把 patch 從 heredoc 餵進 `python -`。[為什麼](rationale.md#hook-3)
- 用腳本改 `.md` 不手寫 `\u` 轉義；patch 加「命中數 ≠ 1 就 abort」。[為什麼](rationale.md#hook-4)
