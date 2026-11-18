# 參與開發

> 最後更新：2026-11-18（歷史紀錄搬進熱歷史 `docs/history/`，封存區改名 `docs/archive/`，需求決策書 v3 Q44）；前次 2026-11-17（「需求與計畫文件的分工」加兩份成對的歷史紀錄，需求決策書 v3 Q42）；前次同日（指標檔一節拿掉 `GEMINI.md`：本專案不支援 Gemini）；前次同日（開發注意事項去掉跟 AGENTS 鐵律 1 重複的句子，v2 原型三條併成一條；加「需求與計畫文件的分工」，舊的需求與計畫文件封存到 `docs/history/`）；前次同日（建立：AGENTS.md 裡碰到才需要的規則、README.md 裡的開發流程與副本同步用法、ARCHITECT.md 的開發注意事項搬來這裡，需求決策書 v3 Q40）
> 這個 repo 由 AI session 輪流做。開工必守的規則在 [AGENTS.md](AGENTS.md)，AI 工具開工時會自動讀到；本檔是碰到才讀的流程與規則：改部署包、動副本或接線、寫本 repo 的交接快照、改兩支 hook 的訊息時才讀。每條的完整原文、理由與事故在 [AGENTS-reasons.md](AGENTS-reasons.md)。**要改、質疑或想繞過某條規則之前，先讀它的理由。**

## 改部署包的流程

規則在 AGENTS.md 的鐵律 1、4 與「跟部署出去的專案不同的地方」；這裡只補操作細節。[為什麼](AGENTS-reasons.md#rule-1)

- 動到結構（增刪檔案、部署包增刪一節範本、驗證項增減）就更新 [ARCHITECT.md](ARCHITECT.md)，跟該變動同一個 commit。
- 部署包跳版時，`src/kit/kit.md` 開頭只留新的「版本」行；舊的那一行改寫成「前一版」，移到 [CHANGELOG.md](CHANGELOG.md) 最上面。不跳版的修改也在 CHANGELOG 最上面記一條。
- 全套驗證在 macOS 約 35 秒，在原生 Windows 約 3–4 分鐘，超過指令工具預設的 120 秒上限，逾時不等於失敗。Windows 上 `python3` 是 WindowsApps 別名，要用 `python`。[為什麼](AGENTS-reasons.md#rule-4)
- 需要 ZIP 時跑 `python -X utf8 tools/verify_bootstrap.py --zip`（可在 `--zip` 後指定路徑）。只有全過才產出正式包；FAIL 回 2、SKIP 回 1，兩者預設都不產出或覆寫 ZIP。若確實需要未完整驗證的調試包，明確加 `--allow-unverified-zip`：僅容許 SKIP，仍回 1，包內附 `UNVERIFIED.json`（跳過項目與原因），「讀我」也會標示未驗證；FAIL 仍禁止。這避免「缺 bash 的檢查被跳過，卻產出看似驗證全過的 ZIP」（2026-11-02／F07）。

## 同步到已部署的專案

Codex 的 Windows 接線與 Git Bash 啟動器可用 `python -X utf8 tools/sync_project.py <專案路徑> --codex-only` 預演；實際寫入依下面的段落先接棒並加 `--owner`，不改專案的 SKILL 或其他設定。接線變更後要重新審核並驗收實際執行，條件與理由見部署包 3.17。[為什麼](AGENTS-reasons.md#copy-6)

`sync_project.py --all` 預設只掃 Desktop 下一層；可用 `--root <目錄>` 改掃描根目錄、`--exclude <目錄名>` 排除已完結專案。工具列出每個候選的納入／排除原因，透過 Git 的 git-dir／common-dir 排除 linked worktree，全域 skill 副本仍須另行同步。

固定範圍建議使用私人 inventory：`--inventory <清單.json>`，內容如 `[{"path":"../project-a","status":"active"},{"path":"../project-b","status":"archived"}]`；相對路徑以清單所在目錄為準，清單不要提交到公開骨架。預演與寫入都檢查 dirty、工作中標記、整份覆蓋檔與 `check_docs.py` 共用程式區的客製漂移。已檢視的 dirty 僅能在單一專案加 `--allow-dirty`；未知共用內容須人工比對後逐檔加 `--accept-drift <路徑>`，占用不能略過。不 stash、不 commit；這些檢查也不是並行鎖（2026-11-02／F13）。

**跨專案寫入先逐一 A1–A5 接棒**（2026-11-03／R03）：在目標專案推送本 session 的開工標記，再以 `--owner '<工作中欄位完整值>'` 聲明目前 writer。同步器會 fetch origin、確認 HEAD 與 `origin/<目前分支>` 完全一致，並核對本機與遠端的標記都精確等於 owner；套用前再查一次。離線、無 upstream、領先／落後／分岔、他人標記或本機標記漂移均拒絕，`--allow-dirty` 不豁免。owner 是呼叫者明確核對的協調證據，不是身分認證或原子鎖，仍須確認同工作樹只有一個 writer。

`--all`／inventory 僅供批次預演；`--write` 必須指定單一專案與 owner，空閒標記不能寫入。同步後留在該專案完成 B7 最終檔案檢查、B8 發布與清標記；若要中途安全點則走 C，保留占用。這修正了舊工具「正常 A5 writer 被拒絕、陳舊空閒 checkout 卻能寫」的矛盾。

副本存在哪些地方見 [ARCHITECT.md](ARCHITECT.md) 的副本拓撲；改 skill 的規則見 AGENTS.md 鐵律 1、2。

## 開發注意事項

改這個 repo 時容易踩的地方，碰到對應的檔才需要讀。[為什麼](AGENTS-reasons.md#dev-notes)

- 手改部署包會被「部署包由來源生成」擋（規則本身是 AGENTS 鐵律 1）。handoff skill 的七個檔改 `src/kit/files/.claude/skills/handoff/*.tmpl`，七個 `source:` 標記、AGENTS 共用制度標記與 `VERSION` 要同版本，本 repo AGENTS.md 的共用制度副本要重貼；同一天再改要加序號。改到逐字搬來的行，「skill 拆分」會擋：要嘛還原，要嘛在 `tools/skill_split_baseline.json` 的 `rewritten` 寫明去處。改了模式檔的段落標題，「skill 規則對照表」會擋，要一起改 `reasons.md` 對照表。改完要重新覆蓋這台的兩個全域目錄。
- v2 的原型都是**偵測**或合成阻擋，沒有接進任何工具，不要寫成保障。執行屏障那一批（VM 腳本、`guest_runs.py`、`crash_release.py` 等）2026-11-14 起封存在 `archive/v2-barrier/`，不再維護（v3 Q33）；要重新研究照它的 README 拼回。崩潰解除的終端確認只抬高 agent 代答門檻，開機識別登記值與錨點都在同 UID 可寫的地方；錨點拒絕的解除是人工步驟，agent 不要自己刪錨點檔。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件。HANDOFF 的「下一步」與懸置裡**不要把已有裁定的 Q 編號跟等待決定的字樣寫在一起**；懸置每條要引用決策書 v3 第 8 節的 `Q` 編號（或 `- 無。`）。v3 第 3 節 D 表每列要有「決定」與「理由」；第 8 節已決項目底下子項格式是「採用理由／未選 (x) 名稱：／暫緩 名稱：」，選項名不能省，省了就報 `alternative-incomplete`（2026-11-17 封存 v2 時在 v3 踩到）。這兩個解析器與需求清單的解析器都按節名找節、不看節號（2026-11-17 起），改節名會讓它們讀不到東西，測試會失敗。
- 提交指令要用 `&&` 綁住 verify 的結束碼。這台的互動殼層是 zsh：管線的結束碼是 `${pipestatus[1]}`，不是 bash 的 `PIPESTATUS`；`echo =====` 在 zsh 會被當成檔名展開而失敗；沒加引號的 `$變數` 在 zsh 不會被拆成多個參數，拿它裝多個 git pathspec 會變成一個比對不到任何檔的 pathspec，結果是「零命中」而不是錯誤（2026-11-17 踩到）。
- AGENTS.md 與本檔只有規則；新增或改規則時在 [AGENTS-reasons.md](AGENTS-reasons.md) 補段落與錨點。開工必守的放 AGENTS.md，碰到才需要的放 CONTRIBUTING.md。
- 讀 `tools/` 的測試不能放進 mutation 群組，所以拆成 `*_repo.py`。`mutants.py --only` 要給測試模組名（`tests.test_x`）。從 repo 根目錄跑模組要 `PYTHONPATH=src`；測試裡用 `-c` 起、要 import 本套件的子程序，`cwd` 要給 `src`。新守門用 `denied(code, ...)` 寫法。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。
- 推含 `.github/workflows/` 改動的 commit，`gh` 權杖要有 `workflow` 權限，否則 GitHub 拒收（2026-11-11 E2 踩到）；補權限要使用者自己跑 `gh auth refresh -h github.com -s workflow`。
- 發正式包：在要發的 commit 上 push `release-request/<channel>` tag，使用者在 GitHub 核准 `release` environment；不要代按核准。workflow 從 tag 名取 channel，所以每次發布都用同一個觸發 tag：第二次起要先刪掉遠端舊的 `release-request/<channel>` 再重推（2026-11-12 發 `beta` epoch 2 時第一次碰到，刪之前問過使用者）；它只是觸發器，刪掉不影響 `channel/…` 發布紀錄。channel tag 沒有伺服器端保護（決策書 Q23），不要為了測試在 `beta`／`stable` 建、移或刪 tag。

## 副本規則

拓撲在 [ARCHITECT.md](ARCHITECT.md)。動副本或接線之前，先讀對應理由段落的完整原文。

- 改完部署包，所有副本一起覆蓋，含選用的兩個全域 `skills/handoff/`。[為什麼](AGENTS-reasons.md#copy-1)
- Codex 與 Claude Code 掛同樣兩個 `.sh`，不在 `.codex/` 複製第二份；Windows 的 `codex-hook.cmd` 只做管線。[為什麼](AGENTS-reasons.md#copy-2)
- Antigravity 2026-11-13 起移出部署包（需求決策書 v3 D8）：舊 3.18–3.20 不再產出，已部署專案裡那三個檔不同步也不刪，清不清由使用者決定；要重新支援先讀理由裡的四個約束。[為什麼](AGENTS-reasons.md#copy-3)
- 接線路徑一律相對、不假設 cwd：前面掛 `$(git rev-parse --show-cdup)`；Antigravity 刻意不跟。[為什麼](AGENTS-reasons.md#copy-4)
- `.agents/` 只放指標與接線，skill 指標的 `description` 寫滿觸發詞。[為什麼](AGENTS-reasons.md#copy-5)
- Codex 啟動器也要同步（`sync_project.py --codex-only`）；接線改過要重新審核並驗收實際執行。[為什麼](AGENTS-reasons.md#copy-6)
- 本 repo 自己的 `HANDOFF.md`、兩支 `repo-*.sh`、`.claude/settings.json`、`.codex/hooks.json` 不在拓撲裡，`sync_project.py` 不碰；其中 `repo-git-check.sh`、`repo-pre-push.sh` 是 3.10、3.11 的手貼副本，改了範本要手動重貼，驗證器比對逐字相同。[為什麼](AGENTS-reasons.md#copy-7)

## 需求與計畫文件的分工

每份文件各答一個問題，同一件事只寫在一處；兩份權威文件之間只引用、不重複。[為什麼](AGENTS-reasons.md#doc-roles)

| 文件 | 回答 | 寫什麼 |
|---|---|---|
| [需求決策書 v3](project-bootstrap-requirements-decision-v3.md) | 要什麼 | 需求、強度、驗收、待決事項 |
| [實施計畫 v3](project-bootstrap-implementation-plan-v3.md) | 怎麼走過去 | 從現況到需求的路線、分期與取捨；只引用需求 ID，不重述需求內容 |
| [需求決策書 v3 歷史紀錄](docs/history/project-bootstrap-requirements-v3-history.md) | 決策書怎麼變成這樣 | 修改紀錄、已決的 Q（決策紀錄）、從條文移出的原文 |
| [實施計畫 v3 歷史紀錄](docs/history/project-bootstrap-implementation-v3-history.md) | 計畫怎麼變成這樣 | 修改紀錄、從內文移出的原文 |
| [ARCHITECT.md](ARCHITECT.md) | 現在長怎樣 | 現況與結構 |
| [HANDOFF.md](HANDOFF.md) | 做到哪 | 進度與停點 |

兩份權威文件只寫現況：改它們時直接改寫條文，只附 Q 編號或日期當出處，同一個 commit 在成對的歷史紀錄「修改紀錄」加一筆；決策書第 8 節的 Q 決定後，完整紀錄搬到歷史紀錄的「決策紀錄」（`tests/test_trail_repo.py` 讀它，查 F7）。歷史紀錄不是封存：放在熱歷史 `docs/history/`，會一直加、程式會讀，碰到才讀、不用先經使用者同意；到 v4 時跟 v3 的兩份權威一起搬進 `docs/archive/`（v3 Q44）。[為什麼](AGENTS-reasons.md#doc-roles)

結案或被取代的需求與計畫類文件用 `git mv` 移到 `docs/archive/`，在它的[索引](docs/archive/README.md)加一行；只把還有效的內容併進兩份權威文件。程式與測試不讀封存區（`verify_bootstrap.py`「封存原件」守）。

## 本 repo 的交接快照

B6 核對並覆寫整份 `HANDOFF.md`（≤80 行）：移除已完成待辦；未知分清現行故障與歷史無法歸因；版本與驗證照實際結果；沒做完寫明風險與續作步驟；收工清掉工作中標記。驗證器只守必要欄位，不判斷待辦是否真的完成。要額外模型呼叫的探針先取得授權、只用訂閱額度；新增守門要附負向測試。[為什麼](AGENTS-reasons.md#snapshot)

## 這個 repo 自己的指標檔

`CLAUDE.md` 只有一行 `@AGENTS.md`，不要改回「去讀 AGENTS.md」的句子。本專案明確不支援 Gemini，不放 `GEMINI.md`。[為什麼](AGENTS-reasons.md#pointer)

## 行末

`.gitattributes` 強制 `eol=lf`；用 Python 改寫記得 `newline=''`。[為什麼](AGENTS-reasons.md#eol)

## 改兩支 hook 的訊息時

- 雙引號裡不寫反引號，欄位名用「」。[為什麼](AGENTS-reasons.md#hook-1)
- `$變數` 緊接中文或全形標點時寫成 `${變數}`。[為什麼](AGENTS-reasons.md#hook-2)
- 用腳本改時不把 patch 從 heredoc 餵進 `python -`。[為什麼](AGENTS-reasons.md#hook-3)
- 用腳本改 `.md` 不手寫 `\u` 轉義；patch 加「命中數 ≠ 1 就 abort」。[為什麼](AGENTS-reasons.md#hook-4)
