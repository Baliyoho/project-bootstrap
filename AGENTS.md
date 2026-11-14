# AGENTS.md — 改這個 repo 之前先讀

> 最後更新：2026-11-14（補裝 push 前 hook、拿掉動作提醒 hook；前面同日：本 repo 交接制度對齊 v3：開場 hook 換成部署包 3.10 的逐字副本，開工段改成只寫事實）；前次同日（貼入部署包的共用制度副本，全域 handoff skill 換成 v3）
> 本檔只放規則；每條的完整原文、理由與事故在 [AGENTS-reasons.md](AGENTS-reasons.md)。**要改、質疑或想繞過某條規則之前，先讀它的理由。**

<!-- 共用制度開始 source: PROJECT-BOOTSTRAP.md v2026-11-14.4 — 到下方的結束標記為止由部署包管理；專案只能加嚴或填空，要改回部署包改再同步 -->
## 目標

這個專案由不同的 session、模型、機器輪流做。你要讓下一棒不必問任何人，就能從 origin 拿到最新成果、知道現況，而且不會跟別人互相覆寫。怎麼做到由你判斷。

## 你不會自己知道的事

- 本機的檔案可能是舊的。別台機器可能已經推了新東西到 origin，包含更新過的 `HANDOFF.md`。
- 主幹不一定是 `main`：`HANDOFF.md` 的「待續分支」寫了分支名，就在那條分支上做。
- 可能有另一個 session 正在同一條分支上工作。唯一的訊號是 origin 上 `HANDOFF.md` 的「工作中」那一行：`無（已交棒）` 表示沒人在做，其他值表示有人。
- session 開始時會自動 fetch 一次，印出 `[facts]` 開頭的幾行。那是當下的快照，之後會過期。
- 逐步程序、異常判讀與規則的理由在 [`.claude/skills/handoff/`](.claude/skills/handoff/SKILL.md)，是碰到才讀的參考。

## 不可違反的條件

1. 改任何檔案之前，本機要跟 origin 一致，而且 origin 上的「工作中」要先推成你自己（`機器 ／ 工具 ／ session 名`，加開工時間）。推不上去就不算。只讀、只回答問題的 session 不寫。
2. origin 上的「工作中」是別人時，不改檔、不推送，停下來告訴使用者。
3. 使用者要求交棒時才交棒。交棒完成的定義：所有成果都在 origin 上；`HANDOFF.md` 整份覆寫成當下狀態（欄位照現有格式，80 行以內，不累積歷史）；「工作中」改回 `無（已交棒）`；本機沒有留下沒推的東西。使用者沒要求就保留你的「工作中」。
4. `main` 上的測試要一直是過的。沒做完的工作放分支推上去，在 `HANDOFF.md` 的「待續分支」寫明分支名。
5. 沒驗證過的事不寫成已驗證。
6. 不提交祕密或金鑰樣式的內容。提交前看 staged 清單，逐檔加入，不用 `git add -A` 或 `git add .`。
7. 不做這些事：`reset --hard`、force push、改寫已推送的歷史、刪分支、自行 stash、刪除不是你建立的檔案、提交 `.gitignore` 排除的東西。
8. 遇到本檔沒講、而且做錯無法復原的狀況（歷史分岔、fetch 失敗、來源不明的未提交變更），停下來告訴使用者。

## session 名稱（工具能改名才做）

格式 `<符號>　MM.DD.HH｜<主題>｜<狀態>｜交棒<N>次`，符號後接一個全形空格。三種狀態：`㊣` 工作中、`※` 待你決定、`↗` 已交棒。

- `MM.DD.HH` 用開場 `[facts]` 印的值，之後不改；主題 ≤10 字，還不知道寫 `待指派`；新 session 的 N 從 0 起算。
- 開始工作改 `㊣`；停下來等使用者決定改 `※`；交棒的 push 成功後才改 `↗`，N 加 1。是 `↗` 或 `※` 時收到任何新訊息，先改回 `㊣`，時間戳、主題與 N 不變。
- 接棒、交棒與停下來等決定的回覆各寫一行 `session：<實際標題>`；工具不能改名就寫 `session：不適用：<原因>；交棒<N>次`。用選項卡片發問也算停下來等決定，卡片之前先寫這一行。
<!-- 共用制度結束 -->

上面兩個標記之間是部署包 3.1 共用制度的逐字副本，給全域 handoff skill 指向；裡面的 skill 連結指的是部署後的路徑，本 repo 讀全域那份。不要就地改：改 `src/kit/files/AGENTS.md.tmpl` 後手動重貼，驗證器比對逐字相同。和下面規則重疊時兩邊都要守。[為什麼](AGENTS-reasons.md#shared)

## 跟部署出去的專案不同的地方

- 驗證入口是 `python3 -X utf8 tools/verify_bootstrap.py`（不是 `verify_state.py`），exit 0 才算改完；提交前先逐檔 stage，再加 `--staged` 跑。可加 `--quiet` 只印摘要與失敗，檢查集合與結束碼不變。
- 沒有 `check_docs.py`。開場 hook `.claude/hooks/repo-git-check.sh` 與 push 前 hook `.claude/hooks/repo-pre-push.sh` 是部署包 3.10、3.11 的逐字副本；要重查開場事實就重跑前者。
- 沒有專案層的 handoff skill。要看參考程序就讀全域 `~/.claude/skills/handoff/`（Codex 是 `~/.codex/skills/handoff/`）；這台機器沒有就讀 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的「3.8」節，不要搬檔或憑記憶重刻。
- 其他文件碰到那件事才讀，對照表在 [ARCHITECT.md](ARCHITECT.md) 的「碰到才讀的文件」。

這些寫在這裡而不只放 hook，是因為有些工具不跑 hook。[為什麼](AGENTS-reasons.md#start)

## 這個 repo 是什麼

AI 協作專案管理骨架的權威版，唯一產出物是部署包 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)（用法見 [README.md](README.md)）；不是知識庫，不存各專案的知識或狀態。現行需求權威是[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)（51 個穩定需求 ID，編號沿用 v2）；[v2](project-bootstrap-requirements-decision.md) 並存供工具讀取與 Q1–Q31 追溯，衝突以 v3 為準。不部署的例外（測試、v2 原型、開發骨架、`HANDOFF.md`）與刻意沒有的 handoff skill、`check_docs.py` 列在 ARCHITECT：那是已宣告的例外，不是空白，改成補裝由使用者決定。原型通過不授權切換程序。[為什麼](AGENTS-reasons.md#what)

## 鐵律

1. **制度權威是 `src/kit/`**：改 `src/kit/kit.md` 或 `src/kit/files/<部署路徑>.tmpl`，跑 `python3 -X utf8 tools/build_kit.py` 重生 `PROJECT-BOOTSTRAP.md`，兩者同一個 commit；不要手改部署包，也不要在單一專案就地改 skill 或 hook。覆蓋到專案用 `tools/sync_project.py`，用法與前提先讀理由。只有 `.claude/skills/handoff/` 目錄裡的檔真的改了內容才跳 `VERSION`，六個檔的 `source:` 標記同版本。[為什麼](AGENTS-reasons.md#rule-1)
2. **改 skill／hook 內容時同步更新檔頭的 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->`**；同一天第二次起加 `.2`、`.3`，序號算的是當天第幾個帶 `source:` 標記的改動，跟部署包「版本」行不保證同號。[為什麼](AGENTS-reasons.md#rule-2)
3. **保留每條規則的「為什麼」**：可以搬到理由檔，不能刪；驗證器會擋。[為什麼](AGENTS-reasons.md#rule-3)
4. **改完跑 `verify_bootstrap.py`，exit 0 才算改完**；印 `skip` 的項目會回傳 1，照實回報。[為什麼](AGENTS-reasons.md#rule-4)
5. **不塞專案專屬內容**（網址、docId、憑證檔名、業務規則），部署包只放通用制度與佔位符。[為什麼](AGENTS-reasons.md#rule-5)
6. **這是公開 repo（MIT）**：不寫客戶／單位名稱、內部代號、本機絕對路徑，提交前擋。[為什麼](AGENTS-reasons.md#rule-6)

## 副本規則

拓撲在 [ARCHITECT.md](ARCHITECT.md)。動副本或接線之前，先讀對應理由段落的完整原文。

- 改完部署包，所有副本一起覆蓋，含選用的兩個全域 `skills/handoff/`。[為什麼](AGENTS-reasons.md#copy-1)
- Codex 與 Claude Code 掛同樣兩個 `.sh`，不在 `.codex/` 複製第二份；Windows 的 `codex-hook.cmd` 只做管線。[為什麼](AGENTS-reasons.md#copy-2)
- Antigravity 2026-11-13 起移出部署包（需求決策書 v3 D8）：舊 3.18–3.20 不再產出，已部署專案裡那三個檔不同步也不刪，清不清由使用者決定；要重新支援先讀理由裡的四個約束。[為什麼](AGENTS-reasons.md#copy-3)
- 接線路徑一律相對、不假設 cwd：前面掛 `$(git rev-parse --show-cdup)`；Antigravity 刻意不跟。[為什麼](AGENTS-reasons.md#copy-4)
- `.agents/` 只放指標與接線，skill 指標的 `description` 寫滿觸發詞。[為什麼](AGENTS-reasons.md#copy-5)
- Codex 啟動器也要同步（`sync_project.py --codex-only`）；接線改過要重新審核並驗收實際執行。[為什麼](AGENTS-reasons.md#copy-6)
- 本 repo 自己的 `HANDOFF.md`、兩支 `repo-*.sh`、`.claude/settings.json`、`.codex/hooks.json` 不在拓撲裡，`sync_project.py` 不碰；其中 `repo-git-check.sh`、`repo-pre-push.sh` 是 3.10、3.11 的手貼副本，改了範本要手動重貼，驗證器比對逐字相同。[為什麼](AGENTS-reasons.md#copy-7)

## 本 repo 的交接快照

B6 核對並覆寫整份 `HANDOFF.md`（≤80 行）：移除已完成待辦；未知分清現行故障與歷史無法歸因；版本與驗證照實際結果；沒做完寫明風險與續作步驟；收工清掉工作中標記。驗證器只守必要欄位，不判斷待辦是否真的完成。要額外模型呼叫的探針先取得授權、只用訂閱額度；新增守門要附負向測試。[為什麼](AGENTS-reasons.md#snapshot)

## 這個 repo 自己的指標檔

`CLAUDE.md` 只有一行 `@AGENTS.md`，不要改回「去讀 AGENTS.md」的句子；`GEMINI.md` 維持指標寫法。[為什麼](AGENTS-reasons.md#pointer)

## 行末

`.gitattributes` 強制 `eol=lf`；用 Python 改寫記得 `newline=''`。[為什麼](AGENTS-reasons.md#eol)

## 改兩支 hook 的訊息時

- 雙引號裡不寫反引號，欄位名用「」。[為什麼](AGENTS-reasons.md#hook-1)
- `$變數` 緊接中文或全形標點時寫成 `${變數}`。[為什麼](AGENTS-reasons.md#hook-2)
- 用腳本改時不把 patch 從 heredoc 餵進 `python -`。[為什麼](AGENTS-reasons.md#hook-3)
- 用腳本改 `.md` 不手寫 `\u` 轉義；patch 加「命中數 ≠ 1 就 abort」。[為什麼](AGENTS-reasons.md#hook-4)
