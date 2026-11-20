# AGENTS.md — 改這個 repo 之前先讀

> 最後更新：2026-11-20

<!-- 共用制度開始 source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 到下方的結束標記為止由部署包管理；專案只能加嚴或填空，要改回部署包改再同步 -->
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
3. 使用者要求交棒時才交棒。交棒前先 fetch，確認 origin 上的「工作中」標記確由本 session 推上。無法確認就停下回報，不改檔、不推送。交棒完成的定義：所有成果都在 origin 上；`HANDOFF.md` 整份覆寫成當下狀態（欄位照現有格式，80 行以內，不累積歷史）；「工作中」改回 `無（已交棒）`；本機沒有留下沒推的東西。使用者沒要求就保留你的「工作中」。
4. `main` 上的測試要一直是過的。沒做完的工作放分支推上去，在 `HANDOFF.md` 的「待續分支」寫明分支名。
5. 沒驗證過的事不寫成已驗證。
6. 不提交祕密或金鑰樣式的內容。提交前看 staged 清單，逐檔加入，不用 `git add -A` 或 `git add .`。
7. 不做這些事：`reset --hard`、force push、改寫已推送的歷史、刪分支、自行 stash、刪除不是你建立的檔案、提交 `.gitignore` 排除的東西。
8. 遇到本檔沒講、而且做錯無法復原的狀況（歷史分岔、fetch 失敗、來源不明的未提交變更），停下來告訴使用者。

## session 名稱（工具能改名才做）

格式 `<符號>　MM.DD.HH｜<主題>｜<狀態>｜交棒<N>次`，符號後接一個全形空格。兩種狀態：`㊣` 工作中、`↗` 已交棒。

- `MM.DD.HH` 用開場 `[facts]` 印的值，之後不改；主題 ≤10 字，還不知道寫 `待指派`；新 session 的 N 從 0 起算。
- 開始工作改 `㊣`；交棒的 push 成功後才改 `↗`，N 加 1。是 `↗` 時收到任何新訊息，先改回 `㊣`，時間戳、主題與 N 不變。
- 接棒與交棒的回覆各寫一行 `session：<實際標題>`；工具不能改名就寫 `session：不適用：<原因>；交棒<N>次`。
<!-- 共用制度結束 -->

上面兩個標記之間是部署包共用制度的逐字副本，不要就地改：改 `src/kit/files/AGENTS.md.tmpl` 後手動重貼，驗證器比對逐字相同。裡面的 skill 連結是部署後的路徑；和下面的規則重疊時兩邊都要守。[為什麼](docs/rationale.md#shared)

## 跟部署出去的專案不同的地方

- 驗證入口是 `verify_bootstrap.py`（鐵律 4），不是 `verify_state.py`；加 `--quiet` 只印摘要與失敗。
- 開場 hook 是 `.claude/hooks/repo-git-check.sh`，要重查開場事實就重跑它。
- 刻意沒有 `check_docs.py` 與專案層 handoff skill，要補裝由使用者決定。參考程序讀全域 `~/.claude/skills/handoff/`（Codex 是 `~/.codex/skills/handoff/`），這台機器沒有就讀 [src/kit/files/.claude/skills/handoff/](src/kit/files/.claude/skills/handoff/SKILL.md.tmpl)，不要搬檔或憑記憶重刻。[為什麼](docs/rationale.md#what)
- 根目錄 `archive/` 是冷區：平常不讀，要回溯先經使用者同意。

這些寫在這裡而不只放 hook，是因為有些工具不跑 hook。[為什麼](docs/rationale.md#start)

## 鐵律

每條後面寫哪個檢查會擋、哪些擋不到；擋不到的要自己守。

1. 部署包的權威是 `src/kit/`。改 `src/kit/` 的來源、`src/project_bootstrap/installer.py` 或 `tools/sync_project.py` 的合併函式後，跑 `python3 -X utf8 tools/build_kit.py` 重生 `bootstrap.py`，來源與產物同一個 commit。不要手改 `bootstrap.py`，不要把 `PROJECT-BOOTSTRAP.md` 放回來，不要在單一專案就地改 skill 或 hook；覆蓋到專案用 `tools/sync_project.py`。只有 `.claude/skills/handoff/` 目錄裡的檔真的改了內容才跳 `VERSION`。
   - 會擋：驗證器擋手改或沒重生的 `bootstrap.py`、放回來的 `PROJECT-BOOTSTRAP.md`。
   - 擋不到：skill 內容改了卻沒跳 `VERSION`（只印提醒）；其他專案裡就地改的 skill 或 hook。[為什麼](docs/rationale.md#rule-1)
2. 改 skill／hook 內容時，同步更新檔頭 `source:` 標記的日期；同一天第二次起加 `.2`、`.3`，序號算的是當天第幾個帶 `source:` 標記的改動，跟部署包「版本」行不保證同號。
   - 擋不到：內容改了卻沒更新標記。[為什麼](docs/rationale.md#rule-2)
3. 每條規則的「為什麼」可以搬到理由檔，不能刪。
   - 會擋：驗證器擋規則沒有理由連結、連結指不到段落、段落是空的。
   - 擋不到：理由本身寫錯或過期。[為什麼](docs/rationale.md#rule-3)
4. 改完跑 `python3 -X utf8 tools/verify_bootstrap.py`，exit 0 才算改完；提交前逐檔 stage，再加 `--staged` 跑；印 `skip` 的項目照實回報。
   - 會擋：`--staged` 遇到未暫存或未追蹤的檔回 exit 2。
   - 擋不到：忘了跑。[為什麼](docs/rationale.md#rule-4)
5. 部署包只放通用制度與佔位符，不放專案專屬內容（網址、docId、憑證檔名、業務規則）。
   - 擋不到：沒有檢查看內容是不是專案專屬。[為什麼](docs/rationale.md#rule-5)
6. 這是公開 repo（MIT）：不寫客戶／單位名稱、內部代號、本機絕對路徑。
   - 會擋：驗證器擋部署包裡的本機絕對路徑。
   - 擋不到：本 repo 自己文件裡的絕對路徑、名稱與代號；提交前自己看 staged 內容。[為什麼](docs/rationale.md#rule-6)
7. 唯一需求書是[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)（51 個穩定需求 ID），路線在[實施計畫 v3](project-bootstrap-implementation-plan-v3.md)，兩份是本 repo 的約束文件。要偏離先改它們；改要有使用者在聊天中的決定，並在 `docs/history/` 成對的歷史紀錄同一個 commit 記一筆，AI 只能提案。兩份都沒寫到的事照常做，會新增或改變需求就先問；跟本檔衝突時停下來回報。
   - 會擋：驗證器擋決策紀錄缺採用理由或沒選的選項。
   - 擋不到：改了兩份約束文件卻沒記歷史。[為什麼](docs/rationale.md#rule-7)

## 碰到才讀

| 什麼時候 | 讀哪份 |
|---|---|
| 要改、質疑或想繞過某條規則 | [理由檔](docs/rationale.md) |
| 改部署包、同步到已部署專案、改 hook 訊息、寫本 repo 的交接快照 | [AI 維護手冊](docs/maintenance.md) |
| 找檔案在哪、某份文件回答什麼問題 | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 接棒、交棒，或開場 `[facts]` 有不正常的值 | 全域 handoff skill（路徑見「跟部署出去的專案不同的地方」） |
