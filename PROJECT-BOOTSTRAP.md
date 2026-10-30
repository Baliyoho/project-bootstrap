# PROJECT-BOOTSTRAP.md — AI 協作專案管理骨架（部署包）

> 把這一份檔案複製到**新專案的空資料夾**，然後開一個 AI session 貼上：
>
> ```text
> 請完全依照本資料夾的 PROJECT-BOOTSTRAP.md 建立本專案的管理骨架：先做第 1 節訪談問我問題，
> 拿到答案後照第 3 節逐檔建立（內容照抄、只替換佔位符），再依第 4 節上 GitHub，最後跑第 5 節自檢並回報。
> 過程中不要自行增刪制度，也不要把佔位符留在檔案裡。
> ```
>
> 也可以完全手動：照第 3 節把每個檔案自己建出來，效果一樣。
> 骨架建好後，**這份 PROJECT-BOOTSTRAP.md 就可以刪掉**（內容已分散進 AGENTS.md／handover-protocol.md／`handoff` skill）。
> 版本：**2026-10-30.2**（`HANDOFF.md` 加**工作中標記**：接棒時（skill A5）確定要動手才把機器與 session 寫進 HANDOFF 並 push，交棒時（B6）改回「無（已交棒）」，下一棒接棒前（A2.5）先檢查。補的是跨機器接力的洞——A 機器忘記交棒就關掉，B 機器看到綠勾就接棒。既有三層防呆全都掛在「下一個動作」上，而**直接關掉視窗沒有下一個動作**；這個標記掛在「開工」，所以繞不過去。`git-freshness.sh` 同步讀它，並改掉那行誤導的 `✅ 與 origin 同步`——它只證明「本機沒落後」，不證明「沒有別台在做」，而一個綠勾會讓人直接往下做。`check_docs.py` 加第 6 項擋欄位不見，否則防呆會靜默失效。
> 同日第二件事：加 `VERSION` 檔 ＋ `tools/sync_project.py`，並讓 `git-freshness.sh` 比對上游版本。這之前「哪些專案裝了這套骨架」沒人記得住、也沒有任何東西負責把權威版發下去，所以同步一直是手工的——今天盤點就掃出 4 個專案留著上一輪沒 commit 的同步殘留。偵測放在開場這個必然發生的時刻，落後的專案會自己講；修則是一行指令。跟「工作中」標記同一招）。
> 同日第三件事（跳版 `.2`）：**改名與 git 解耦**。舊版 A5 把「改 session 名稱」排在「開工標記 push 成功」之後，於是沒有 `HANDOFF.md` 的專案（包括骨架自己這個 repo）、或這一輪只讀的 session，永遠到不了改名那一步——側欄上三個 session 全是 `↗ 已交棒`，一個 `㊣ 工作中` 都沒有過，正好是這條規則要解決的問題在它的老家失效。改名現在只看 session 狀態：回報完就 `㊣`、停下來等人就 `※`（不限「必須停下來問使用者」那張表），只有宣稱 git 事實的 `↗ 已交棒` 仍要等 push 成功。
> 同日第四件事（**刻意不跳版**，理由見下）：**修正「跨工具與跨平台」那張表的 Antigravity 一欄。**舊表寫「❌ 沒有 hook 機制」，那是 2026-08-05 的事實，重查官方文件已經不成立——它現在有 `.agents/hooks.json`，而且有 `SessionStart`。照舊表判斷會白白放棄一層防呆，而且錯得毫無徵兆：表上有查證日期，但**沒有人會因為日期舊就去重查**。`ARCHITECT.md` 與 `docs/ai-notes/handover-protocol.md` 兩份範本裡跟著錯的句子一併修掉。`.agents/hooks.json` 範本**刻意還沒附**，理由見那一節。**為什麼不跳版**：`VERSION` 不是「部署包的版本」，是**偵測器拿去跟 `SKILL.md` 的 `source:` 標記比對的那個值**（`git-freshness.sh` 的 `mine=` 那一行）。這次改的全是不同步的檔（兩份範本都在 `INSTANCE`），`SKILL.md` 一個字沒動——跳版就會讓每個專案永遠印「骨架落後」，而且跑 `sync_project.py` 修不掉（同步回去的 `SKILL.md` 標記還是舊的）。這個耦合 2026-10-30 當天就被 `verify_bootstrap.py` 的「同版→閉嘴」抓到，警告寫進 AGENTS.md 鐵律 1。
> 前幾版——
> 2026-10-24：版本號加序號（同一天改第二次起在日期後面加 `.2`、`.3`，因為日期粒度只能證明「不早於那一天」——當天改第三次時，三份副本的標記長得一模一樣，落後的那份看不出來）；handoff skill 加 **session 命名**：接棒／交棒／踩到「必須停下來問使用者」時各改一次 session 名稱。側欄上十幾個 session 全叫「接棒」認不出哪個是哪個，而其中「停在等人回答」的那個最需要被一眼看見。
> 2026-09-30：兩個 hook 腳本補上 `source:` 版本標記——鐵律第 2 條的作用是一眼認出落後的副本，而最無從用肉眼辨識新舊的正好是這兩支 `.sh`。
> 2026-09-20：handoff skill 加 **A6 回推補交接**，協定範本加對應的「漏交棒的補救」一節——三層防呆全都掛在「下一個動作」上，**直接關掉視窗沒有下一個動作**，所以這是程序責任不是工具責任。
> 2026-09-07：加入 `ARCHITECT.md`＝結構的唯一權威，以及 handoff skill 的**模式 0 建制**——在還沒有這套制度的資料夾裡，由 agent 照本部署包把骨架生出來，而不是憑印象重刻一份。
> 2026-08-05：加入 `handoff` skill、push 前防呆 hook，並把「殘留佔位符」從人工核取方塊改成 `check_docs.py` 的第 5 項檢查。
> 萃取自兩個實際運行的專案：一個是表單資料庫＋NAS＋custom widget 的案件審核工作流，一個是文本識別系統。兩個都是多模型、多機器協作。

## 交接自動化怎麼運作（本骨架的核心）

制度寫成文件，agent 不一定會照做。本骨架用三層讓它**自動發生**：

| 層 | 檔案 | 什麼時候動 |
|---|---|---|
| **觸發** | `.claude/hooks/git-freshness.sh`（SessionStart hook） | 每次 session 開始自動 fetch、報告落後／分岔、**讀 origin 的「工作中」標記揭露別台機器正在動同一條分支**，並提醒「接棒先走 handoff skill」 |
| **程序** | `.claude/skills/handoff/SKILL.md` | agent 判斷要接棒／交棒／同步時自動載入；使用者也可打 `/handoff` 直接叫它 |
| **防呆** | `.claude/hooks/pre-push-handoff.sh`（PreToolUse hook） | 要推到權威分支、但這批 commit 沒更新 `HANDOFF.md` 時擋下，要求先走交棒程序 |

**分工**：`docs/ai-notes/handover-protocol.md`＝**規則與理由**（為什麼、什麼算對）；skill＝**怎麼做**（指令、判讀表、模板）。
兩者衝突以協定為準。這樣才不會變成「同一套程序有兩份會各自演化的副本」。

**還沒有這套制度的資料夾走 skill 的模式 0（建制）**：使用者講一句「幫我把交接機制建起來」，agent 就照本部署包逐檔生成，而不是憑印象重刻——憑印象生出來的版本缺的永遠是最貴的那部分（每條規則後面的「為什麼」、hook 的邊界條件），看起來像那套制度，實際擋不住任何事。
這裡有個雞生蛋問題：skill 是部署**之後**才存在於專案裡的。所以模式 0 真正會被載入的地方是**全域副本**（`~/.claude/skills/handoff/`、`~/.codex/skills/handoff/`）；專案內那份仍保留模式 0，是為了讓副本可以無腦整份覆蓋，不必維護兩種版本。

## 跨工具與跨平台（2026-08-05 查證；Antigravity 一欄 2026-10-30 重查）

**把三層拆成兩種可靠度**，不要假設哪個工具一定有自動化：

- **可攜層——到哪都成立**：`AGENTS.md`（Claude Code／Codex／Antigravity 都原生讀）＋ 純 Markdown 的程序檔。就算一個 hook 都沒掛，agent 讀 `AGENTS.md` 開頭那段就知道要先走交接程序。**正確性靠這一層，不靠 hook。**
- **工具層——有就更省事**：hooks。它只是讓人不必記得，不是制度成立的前提。

| | Claude Code | Codex CLI | Codex 桌面 App | Antigravity |
|---|---|---|---|---|
| 讀 `AGENTS.md` | ✅ 經 `CLAUDE.md` 指標 | ✅ 原生 | ✅ 原生 | ✅ 原生（優先於 `GEMINI.md`） |
| 自動載入程序檔 | ✅ `.claude/skills/`，可打 `/handoff` | ⬜ 靠 `AGENTS.md` 指路 | ✅ 全域 `~/.codex/skills/<name>/SKILL.md`；專案的 `.agents/skills/` 也讀得到 | ✅ 原生讀 `.agents/skills/` |
| Hooks | ✅ `.claude/settings.json` | ✅ `<repo>/.codex/hooks.json` | ❌ **這個 build 沒有 hooks**，`/hooks` 指令不存在 | ✅ `.agents/hooks.json`（2026-10-30 重查，見下） |

**Codex 要分 CLI 與桌面 App，兩者能力不同**（2026-08-06 在 App 版 `26.721.41059` 實測）：

- **CLI** 有 hooks，格式與語意跟 Claude Code 相同（stdin 收 JSON、exit 2 擋下並把 stderr 交給模型），首次要打 `/hooks` 信任該定義。因為格式相同，**兩邊掛的是同樣那兩個 `.sh` 檔**，不要各複製一份——那正是「同一個事實有多個家」的起點。
- **桌面 App 沒有 hooks**，但有原生的 skill 系統：使用者 skill 放 `~/.codex/skills/<name>/SKILL.md`，格式與 Claude Code 相同（`name` ＋ `description` frontmatter）。把 `.claude/skills/handoff/SKILL.md` 複製過去即可，`~/.codex/rules/` 是指令核准白名單、不是放指示的地方。

實測時 App 還主動讀到了專案的 `.agents/skills/handoff/SKILL.md`，並照指標找到 `.claude/` 的權威版——所以那個指標檔不只對 Antigravity 有用。

**Antigravity 有 hooks**（2026-10-30 重查官方文件 `antigravity.google/docs/hooks`）：專案層 `.agents/hooks.json`、全域 `~/.gemini/config/hooks.json`，App／CLI／IDE 三種吃同一份契約。事件有 `SessionStart`（「一個新 session 開始時觸發一次，在第一次模型呼叫之前」，matcher 忽略）、`PreToolUse`、`PostToolUse`、`PreInvocation`、`PostInvocation`、`Stop`——`SessionStart` 跟 Claude Code 同語意，`PreToolUse` 也對得上 pre-push 那一層。

⚠️ **這一欄到 2026-10-30 之前都寫著「沒有 hook 機制」**，那是 2026-08-05 查的，兩個半月就過時了。錯的代價是白白放棄一層防呆，而且沒有徵兆——表上標了查證日期，但沒有人會因為日期舊就主動重查。**對外部工具能力的斷言都有保鮮期**，拿它做「做不到所以不做」的決定之前先重查。

**但骨架刻意還沒附 `.agents/hooks.json` 範本**，因為有兩件事官方文件沒寫，而猜錯就是靜默失效：

1. **相對路徑解析到哪，沒有定義。** 範例用 `./scripts/lint.sh`，整頁沒有一句講 working directory；第三方說法互相矛盾（一說必須寫絕對路徑、相對路徑對著啟動終端的目錄解析；另一份 bug 報告則是 cwd 為 `.agents` 時被接成 `.agents/.agents/...`）。而本骨架的規則是**接線路徑一律相對**（絕對路徑換機器會靜默失效，`verify_bootstrap.py` 的跨平台防呆會擋）——兩邊直接相撞，**只能在機器上實測，查文件查不出來**。
2. **`SessionStart` 的 stdout 是 JSON 契約，不是給人看的文字。** 它定義的輸出是選用的 `injectSteps`（`systemMessage`／`userMessage`／`ephemeralMessage`／`toolCall`），而 `git-freshness.sh` 是直接 `echo` 一行給人讀——Claude Code 會顯示，Antigravity 多半當成不合格式而丟掉。要接上得多一層轉換，而那一層就是第二份會各自演化的東西（正是「同樣那兩個 `.sh`」要避免的）。

所以這一欄現在是「做得到、但要先實測」。**沒實測就先別建**：一個不會觸發的 hook 比沒有更糟，它看起來像有防護。

`.codex/hooks.json` 建了不會有害（哪天改用 CLI 就生效），但**在 App 上是空轉的**：沒有開場檢查、沒有 push 攔截。這正是可攜層必須自己站得住的理由。

**共同前提**：兩個 hook 是 bash 腳本，macOS／Linux 內建；Windows 需要 Git for Windows 附的 bash。Python 腳本在 macOS 上常常只有 `python3` 沒有 `python`——所有文件一律寫「`python` 不存在就用 `python3`」。

---

## 0. 這套骨架在解決什麼問題

跨 session、跨模型（Claude／Gemini／Codex）、跨機器（PC↔Mac）協作時，反覆出現的失效模式與對策：

| 失效模式（都真的發生過） | 對策（本骨架的組成） |
|---|---|
| AI 對著**過期的本機快照**工作數小時，最後 commit 造成分岔 | `.claude/hooks/git-freshness.sh`：session 一開始自動 fetch 並把落後／分岔警告注入對話 |
| 交接文件愈寫愈長，接手者要讀 20 分鐘才知道現在做到哪 | **三層分工**：持久知識→`docs/ai-notes/`；當下狀態→`HANDOFF.md`（≤80 行、不累積歷史）；歷史→Git |
| 同一個事實散在三個檔案，各自演進到互相矛盾 | **每個事實只有一個家**：其他地方只放指標，不複製內容 |
| 文件說 A、實際是 B，AI 照文件做就炸 | **以實況為準**＋`tools/verify_state.py` 一鍵查證＋`tools/check_docs.py` 查死連結／過期網址／缺日期 |
| 純文件修正被「等功能驗收」擋住，接手者拿到過期文檔集 | **兩類分支**：功能分支需驗收才併；文件／基建分支驗證過就能併 `main` |
| 連線失敗被誤判成「本機沒有憑證」，寫下錯誤結論 | **SKIPPED 判準**：先排除「設定沒帶到」才能標 SKIPPED；禁止自行挖憑證 |
| 祕密／運行資料被推上 GitHub | 鐵律＋`.gitignore`＋提交前固定檢查 staged 清單 |
| 交接品質看 agent 心情：有時漏驗證、有時忘了寫 HANDOFF 就 push | `handoff` skill 把協定變成**可執行程序**（判讀表、指令、停止判準）；SessionStart hook 自動提醒，pre-push hook 擋下沒交棒的 push |

**保留「為什麼」**：每條規則後面都有一次實際事故。移植時不要把理由砍掉——理由沒了，下一棒就會覺得規則是多餘的而繞過它。

---

## 1. 部署前訪談（AI 執行時必做，一次問完）

把答案填進下列佔位符；**檔案裡不能留下任何 `{{...}}`**。

| 佔位符 | 意義 | 例 |
|---|---|---|
| `{{PROJECT_NAME}}` | 專案中文名 | 客戶報價系統 |
| `{{ONELINER}}` | 一句話說明它是什麼、給誰用 | 業務用的報價單產生與追蹤系統，資料在 Postgres，介面是 Next.js |
| `{{GH_OWNER}}` / `{{GH_REPO}}` | GitHub 帳號／repo 名 | `Baliyoho` / `quote-system` |
| `{{GH_VISIBILITY}}` | `private` 或 `public` | private |
| `{{LANG}}` | 使用者溝通語言 | 繁體中文 |
| `{{TZ}}` | 時區（HANDOFF 時間戳用） | Asia/Taipei |
| `{{TODAY}}` | 部署當天日期（絕對日期，YYYY-MM-DD） | 2026-07-26 |
| `{{SECRETS}}` | 絕不進 Git 的憑證檔 | `.env`、`*.pem` |
| `{{RUNTIME_DIRS}}` | 絕不進 Git 的運行／資料目錄 | `data/`、`backups/`、`uploads/` |
| `{{STACK_DIRS}}` | 專案主要程式目錄（寫進 README 檔案結構） | `src/`、`migrations/` |
| `{{VERIFY_TARGETS}}` | 「一鍵驗證」該查什麼（沒有就先留空） | 健康檢查 API、docker 容器狀態 |

追問一句就好：**「這個專案有沒有已知的『絕對不能做』的操作？」**（例：不能直接改資料庫檔、不能在正式環境跑 migration）。有的話寫進 AGENTS.md 鐵律第 4 條之後；沒有就先放空著，日後踩到再補。

---

## 2. 要建立的檔案結構

```text
{{GH_REPO}}/
├─ README.md                        ← 人的入口（第一次接觸專案看這份）
├─ AGENTS.md                        ← AI 的入口（唯一權威來源）
├─ CLAUDE.md                        ← 指標，指向 AGENTS.md
├─ GEMINI.md                        ← 指標，指向 AGENTS.md
├─ HANDOFF.md                       ← 當下工作狀態（≤80 行，不累積歷史）
├─ ARCHITECT.md                     ← 專案結構的唯一權威（只有結構變動才改）
├─ .gitignore
├─ .gitattributes
├─ .claude/                         ← Claude Code 讀這裡
│   ├─ settings.json                ← hook 設定（進 Git）
│   ├─ settings.local.json          ← 各機器本地設定（不進 Git）
│   ├─ hooks/git-freshness.sh       ← SessionStart：git 新鮮度檢查＋提醒走交接程序
│   ├─ hooks/pre-push-handoff.sh    ← PreToolUse：沒更新 HANDOFF 就想 push 時擋下
│   ├─ skills/handoff/SKILL.md      ← 交接與同步的可執行程序（本骨架的核心、權威版）
│   └─ skills/<其他>/SKILL.md       ← 需要時才建：可重複使用的操作食譜（權威版）
├─ .codex/hooks.json                ← Codex 讀這裡：掛上面同樣那兩個腳本，不另寫一份
├─ .agents/skills/handoff/SKILL.md  ← Antigravity 原生讀 .agents/：指向權威版的指標
├─ .agents/skills/<其他>/SKILL.md   ← 需要時才建：同樣只放指標，不複製內容
├─ docs/
│   ├─ ai-notes/
│   │   ├─ handover-protocol.md     ← 交接協定（接棒／交棒／分支模型）
│   │   └─ roadmap.md               ← 持久待辦總表
│   └─ mockups/                     ← 選用：與使用者定案的 UI 規格
└─ tools/
    ├─ check_docs.py                ← 文檔一致性檢查
    └─ verify_state.py              ← 一鍵現況查證（骨架，依專案填）
```

**選用目錄**（有需要再建，不要為了對齊而空建）：`tests/`、`deploy/`、`apps/`、`archive/`。

---

## 3. 各檔案內容（照抄，只換佔位符）

### 3.1 `AGENTS.md`

````markdown
# AGENTS.md — AI 協作交接指引

> 適用於所有參與本專案的 AI 代理（Claude Code、Codex、Antigravity、Gemini…）。**開工前先讀完本檔**，再依任務讀下方知識庫。
> 本檔是唯一入口與權威來源；`CLAUDE.md`、`GEMINI.md` 只是指到這裡的指標。
> 最後更新：{{TODAY}}（建立）

## 開工第一件事（任何工具、任何模型都適用）

**先讀 [`.claude/skills/handoff/SKILL.md`](.claude/skills/handoff/SKILL.md)，照 A 模式接棒；A 沒跑完之前不要修改任何檔案。** 收工時走 B 模式交棒，中途要拉最新或推安全點走 C 模式。

那份檔案是純 Markdown，路徑掛在 `.claude/` 下只是因為 Claude Code 會自動載入該位置——**其他工具直接讀它就好**，不要因為資料夾名字而略過。部分工具有自動化輔助（Claude Code 可打 `/handoff`、session 開始會自動檢查 git；Codex 可掛同樣的 hooks；Antigravity 原生讀 `.agents/skills/`），但**有沒有自動化都不改變義務**：沒有被自動提醒，就自己走。

## 專案是什麼

{{ONELINER}}。source／交接文件同步至 {{GH_VISIBILITY}} GitHub `{{GH_OWNER}}/{{GH_REPO}}`；**Git 不是資料備份**。專案概觀、檔案結構、啟動方式見 [README.md](README.md)。使用者以 **{{LANG}}** 溝通。

## 鐵律（違反會造成實際損害，無例外）

1. **嚴禁提交祕密或運行資料到 Git**：{{SECRETS}}、API／SSH private key、{{RUNTIME_DIRS}} 均不可 commit/push；{{GH_VISIBILITY}} repository 也不是例外。提交前固定檢查 staged 檔案清單。
2. **破壞性操作前先備份**：改 schema、批次改資料、刪檔、覆寫設定之前，先產出可還原的副本並說明放在哪。
3. **憑證原則**：憑證由使用者提供並存於 {{SECRETS}}，直接讀取即可；**不要**從系統檔、其他主機、Git history 自行挖取或搬運憑證。
4. **不確定的破壞性操作先問**，不要用「應該沒問題」推進。
<!-- 5. 專案專屬鐵律寫在這裡：每一條都要附「為什麼」與發生日期，否則下一棒會繞過它。 -->

## 連線基本資料

| 項目 | 值 |
|---|---|
| 服務網址 | <部署後填> |
| 驗證方式 | <部署後填；只寫「key 在 {{SECRETS}} 的 XXX」，不要寫值> |
| 主要資源 ID | <部署後填> |

## 知識庫地圖（依任務讀）

| 任務 | 必讀 |
|---|---|
| 接手／交棒工作 | **[.claude/skills/handoff/SKILL.md](.claude/skills/handoff/SKILL.md)**（可執行程序：A 接棒／B 交棒／C 同步，含指令與判讀表）＋ [HANDOFF.md](HANDOFF.md)（當下狀態）＋ [docs/ai-notes/handover-protocol.md](docs/ai-notes/handover-protocol.md)（規則與判準、分支模型） |
| 想知道整個專案怎麼組起來、東西放在哪、哪一份是權威版 | [ARCHITECT.md](ARCHITECT.md)（結構的唯一權威；**只有結構變動才改**，改就跟該變動同一個 commit） |
| 還有哪些事沒做（持久待辦、相依、優先序） | [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md) |
| <新主題> | <新增 docs/ai-notes/xxx.md 後，回來把這一列補上> |

`.claude/skills/` 資料夾雖然掛在 Claude 的路徑下，內容是純 Markdown，**任何模型都應直接讀取**。
`.agents/skills/` 下的同名檔案只是給 Antigravity 這類原生讀 `.agents/` 的工具用的**指標**，內容不重複——看到指標請回頭讀 `.claude/skills/` 的權威版。

## 跨模型／跨機器協作規範

1. **先同步 Git，再相信本機文件**：開工先 `git status -sb`、`git fetch origin`。異常（dirty／diverged／遠端意外前進）一律停在安全點，禁止 `reset --hard`、force push 或覆寫。
2. **single writer**：同一時間只讓一個 agent／一台機器修改 `main` 與 `HANDOFF.md`。非小型工作走 `feature/<ID>-<slug>`；未完成分支不得偷塞進 main。
3. **知識寫進 repo，不留在私有記憶。** 踩到新坑、確立新流程、改了 schema——當場更新 `docs/ai-notes/` 或對應 SKILL.md，並附**絕對日期**。私有記憶只放「先讀 AGENTS.md」這類指標與個人偏好。
4. **文件與現實衝突時，以實況為準**（安全唯讀查證），就地修正文件並註記日期。該機器缺憑證時只能明記 SKIPPED，**不得自行挖憑證**。
5. **不要重複造文件——每個事實只有一個家。** 結構寫 `ARCHITECT.md`；設計與決策寫 `docs/ai-notes/`；操作步驟寫對應的部署／應用目錄；狀態寫 `roadmap.md`（持久）與 `HANDOFF.md`（當下）。其他地方只放指標。新知識歸入現有檔案，只有全新主題才開新檔並更新上方地圖。

> ⬆️ 完整的接棒／交棒步驟、分支規則、HANDOFF 模板與標準 prompt 全在 **[handover-protocol.md](docs/ai-notes/handover-protocol.md)**，本節只是原則摘要，細節不在此重複。
````

### 3.2 `CLAUDE.md` 與 `GEMINI.md`（兩檔內容相同，只有標題不同）

````markdown
# CLAUDE.md

本專案的 AI 協作指引統一放在 **[AGENTS.md](AGENTS.md)**——開工前先讀它（鐵律、連線資料、知識庫地圖、跨模型協作規範）。本檔刻意保持極簡，請勿在此累積知識；新知識依 AGENTS.md 的規範寫進 `docs/ai-notes/` 或對應 SKILL.md。
````

> `GEMINI.md` 就是把第一行換成 `# GEMINI.md`。若也用 Codex／其他工具，比照再加一份指標檔即可——**內容永遠只是指標**。

### 3.3 `HANDOFF.md`（初始狀態，之後每次交棒覆寫）

````markdown
# HANDOFF — 工作交接狀態

- **交接時間**：{{TODAY}} HH:MM（{{TZ}}）
- **交棒者**：<模型／機器>（專案管理骨架部署完成）

## 任務目標

專案剛建立，管理骨架（AGENTS／HANDOFF／交接協定／hook／驗證腳本）已就緒。下一步是定義專案本體的第一批工作。

## Git 狀態

- Repo：{{GH_VISIBILITY}} `{{GH_OWNER}}/{{GH_REPO}}`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- 本機能力：<作業系統；哪些憑證可用／未配置，不寫祕密值>

## 已完成

- 管理骨架部署：README／AGENTS／CLAUDE／GEMINI／HANDOFF／handover-protocol／roadmap／`handoff` skill／兩個 `.claude` hook／`tools/check_docs.py`／`tools/verify_state.py`。
- `check_docs.py` 通過；首次 commit 已 push 到 `main`。

## 未完成／下一步

1. 填 AGENTS.md 的「連線基本資料」與專案專屬鐵律。
2. 填 `tools/verify_state.py` 的檢查項目（目前是骨架）。
3. 把第一批工作寫進 [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md)。

## 地雷與注意事項

- **single writer**：不要兩台機器同時改 `main`／`HANDOFF.md`。
- 開工前先 `git fetch origin`；hook 只是保險，不能取代這一步。
- 該機器沒有 `python` 指令就用 `python3`（macOS／Linux 常見）。

## 服務查證與期望快照

`python -X utf8 tools/verify_state.py`
<目前實際關鍵輸出；未能查的層級寫 SKIPPED 與原因>

## 懸置事項（AI 勿自行處理）

- <等使用者決定的事>
````

### 3.4 `README.md`

````markdown
# {{PROJECT_NAME}}

{{ONELINER}}

> 最後更新：{{TODAY}}。**本檔是給「人」看的入口**；AI 代理請讀 [AGENTS.md](AGENTS.md)，接手工作請讀 [HANDOFF.md](HANDOFF.md)。

## 三個入口，別走錯

| 你是 | 讀這份 | 內容 |
|---|---|---|
| **人**（第一次接觸本專案） | 本檔 README | 系統是什麼、怎麼連、檔案結構 |
| **AI 代理**（Claude／Gemini／Codex） | [AGENTS.md](AGENTS.md) | 鐵律、連線資料、知識庫地圖、跨模型協作規範 |
| **接手者**（換 session／換機器） | [HANDOFF.md](HANDOFF.md) ＋ [handover-protocol.md](docs/ai-notes/handover-protocol.md) | 現在做到哪、下一步、交接程序 |

要動結構之前（新增／搬移目錄、換掉一個元件）先讀 [ARCHITECT.md](ARCHITECT.md)——它是結構的唯一權威，下面的檔案結構只是它的摘要。

## 怎麼連

| 用途 | 網址／指令 | 說明 |
|---|---|---|
| <主服務> | <部署後填> | <部署後填> |

## 換一個 AI 接手工作（交接 prompt）

程序已經寫成 **[handoff skill](.claude/skills/handoff/SKILL.md)**（A 接棒／B 交棒／C 同步）。在 Claude Code 直接打 `/handoff` 就會執行；其他工具（Gemini／Codex）沒有 skill 機制，用下面的 prompt 指路即可——SKILL.md 是純 Markdown，它們照讀就能做。

### A. 請目前這個 AI 交棒（工作告一段落時）

```text
請執行 .claude/skills/handoff/SKILL.md 的 B 模式（交棒），B1–B9 逐步做完，不要跳步：
收斂安全點、知識落地（每個事實一個家、附絕對日期）、跑 verify_state、動過 .md 就跑 check_docs.py、
條件式例行檢查、更新 ≤80 行 HANDOFF、檢查 staged 清單後 commit、fetch 確認遠端再 push。
最後 5 行內回報分支、最終 commit hash、push 結果、驗證與最大地雷。
```

### B. 請新的 AI 接棒（開新 session 的第一句）

```text
你要接手這個 GitHub 多 AI 專案。請執行 .claude/skills/handoff/SKILL.md 的 A 模式（接棒），A1–A5 逐步做完：
先同步 Git（異常一律停在安全點回報，不得 reset/force push/覆寫）、依 HANDOFF 的「待續分支」站對分支、
只讀 AGENTS.md 與 HANDOFF.md、有憑證才跑 verify_state（連線失敗先排除設定問題再標 SKIPPED，禁止自行找憑證）、
回報 3–5 行後才動手。全程遵守 AGENTS.md；不確定的破壞性操作先問；結束時依 B 模式交棒。
```

> 順序是 **A 再 B**：先讓舊 session 交棒（它會把狀態寫進 `HANDOFF.md` 並 push），新 session 才讀得到。跳過 A 直接開 B，新 AI 會拿到過期的狀態。
> 完整協定（分支模型、SKIPPED 判準、交棒者義務）見 [handover-protocol.md](docs/ai-notes/handover-protocol.md)。

## 檔案結構

```text
AGENTS.md / CLAUDE.md / GEMINI.md   AI 入口（後兩者只是指標）
HANDOFF.md                          當下工作狀態（≤80 行，不累積歷史）
ARCHITECT.md                        專案結構的唯一權威（只有結構變動才改）
docs/ai-notes/                      持久知識庫（清單見 AGENTS.md 的地圖）
.claude/                            hook 與 skills（純 Markdown，任何模型都該讀）
tools/                              維運腳本（見下）
{{STACK_DIRS}}                      專案本體
```

**不在 Git 裡**（各機器本地，見 `.gitignore`）：{{SECRETS}}、{{RUNTIME_DIRS}}。Git 存的是 source 與文件，**不是資料備份**。

## 維運腳本

| 腳本 | 做什麼 |
|---|---|
| `tools/verify_state.py` | **一鍵驗證**服務現況，輸出 key=value 事實快照，與 HANDOFF 的期望快照比對 |
| `tools/check_docs.py` | **文檔一致性檢查**：死連結、過期網址、缺日期標頭、硬編數量、殘留佔位符。動過 `.md` 就跑 |

```bash
python -X utf8 tools/verify_state.py
```

macOS／Linux 常常只有 `python3` 沒有 `python`——該機器上 `python` 不存在就改用 `python3`，兩支腳本都一樣。

## 動手前必讀的紅線

1. **絕不提交祕密或運行資料**：{{SECRETS}}、{{RUNTIME_DIRS}}，{{GH_VISIBILITY}} repo 也不例外。
2. **破壞性操作前先備份**，並說明副本放在哪。
3. **不確定就先問**，不要用「應該沒問題」推進。

完整鐵律見 [AGENTS.md](AGENTS.md)。
````

### 3.5 `ARCHITECT.md`（結構的唯一權威）

> **為什麼要有這一份**：結構問題（「這個東西放哪」「哪一份是權威版」「資料從哪進來」）本來散在 README 的檔案結構、AGENTS.md 的知識庫地圖與每個人腦袋裡，於是每一棒都要重新拼一次，拼錯了就照著不存在的路徑動手。
> 它與 `HANDOFF.md` 是**故意相反的節奏**：HANDOFF 每次交棒都覆寫，本檔只有結構真的變了才動——一份會頻繁改的結構圖，接手者遲早不會再相信它。

````markdown
# ARCHITECT — 專案結構

> **本檔＝結構的唯一權威**：這個專案由什麼組成、每樣東西的家在哪、哪一份是權威版。
> 最後更新：{{TODAY}}（建立）
>
> **什麼時候改**：只有**結構**變動才改——新增／刪除／搬移長期存在的目錄或檔案、換掉一個元件、改變資料流向、改變「哪一份是權威版」。
> 改功能、修 bug、更新進度**都不要動這一份**。它刻意比 [HANDOFF.md](HANDOFF.md) 慢：HANDOFF 每次交棒覆寫，本檔可能好幾個月不動。

## 這一份與其他檔案的分工（同一件事不要有兩個家）

| 你想知道 | 讀哪一份 |
|---|---|
| 專案由什麼組成、東西放在哪、誰是權威版 | **本檔** |
| 我可以做什麼、不可以做什麼（鐵律、連線資料、知識庫地圖） | [AGENTS.md](AGENTS.md) |
| 這是什麼系統、怎麼連、怎麼跑起來（給人看） | [README.md](README.md) |
| 現在做到哪、下一步 | [HANDOFF.md](HANDOFF.md) |
| 還有哪些事沒做、什麼被否決 | [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md) |
| 交接的規則與理由 | [docs/ai-notes/handover-protocol.md](docs/ai-notes/handover-protocol.md) |
| 交接怎麼做（指令、判讀表、模板） | [.claude/skills/handoff/SKILL.md](.claude/skills/handoff/SKILL.md) |

README 的「檔案結構」只列到人看得懂的程度；**細節與理由在本檔**。兩邊衝突以本檔為準，並就地修 README。

## 全貌

```text
{{GH_REPO}}/
├─ 管理骨架     跨專案共通，部署時生成（見下表）
├─ 專案本體     {{STACK_DIRS}}（見下方「專案本體」）
└─ 不進 Git     {{SECRETS}}、{{RUNTIME_DIRS}}
```

## 管理骨架（部署時生成，跨專案共通）

| 檔案 | 是什麼 | 權威版在哪 | 什麼時候動 |
|---|---|---|---|
| [README.md](README.md) | 人的入口 | 本專案 | 對外說明或連線方式改變 |
| [AGENTS.md](AGENTS.md) | AI 的入口：鐵律、連線資料、知識庫地圖 | 本專案 | 多一條鐵律、多一份知識庫 |
| [CLAUDE.md](CLAUDE.md)、[GEMINI.md](GEMINI.md) | 指標，內容只有一句「去讀 AGENTS.md」 | 指向 AGENTS.md | 幾乎不動 |
| [HANDOFF.md](HANDOFF.md) | 當下狀態（≤80 行、覆寫不累積） | 本專案 | **每次交棒** |
| 本檔 | 結構 | 本專案 | 只有結構變動 |
| [docs/ai-notes/handover-protocol.md](docs/ai-notes/handover-protocol.md) | 交接的規則與理由 | 本專案 | 協定本身改變 |
| [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md) | 持久待辦與決策記錄 | 本專案 | 有新待辦或決策 |
| [.claude/skills/handoff/SKILL.md](.claude/skills/handoff/SKILL.md) | 交接的可執行程序（0 建制／A 接棒／B 交棒／C 同步） | **部署包**（本專案這份是副本，檔頭 `source:` 標記可辨識落後） | 改制度先改部署包，再整份覆蓋下來 |
| [.claude/hooks/git-freshness.sh](.claude/hooks/git-freshness.sh) | SessionStart：自動 fetch、報告落後／分岔 | 同上 | 同上 |
| [.claude/hooks/pre-push-handoff.sh](.claude/hooks/pre-push-handoff.sh) | PreToolUse：沒更新 HANDOFF 就想 push 時擋下 | 同上 | 同上 |
| [.claude/settings.json](.claude/settings.json) | 上面兩個 hook 的接線（進 Git） | 本專案 | 加減 hook |
| `.claude/settings.local.json` | 各機器本地設定（**不進 Git**） | 各機器自己 | 換機器 |
| [.codex/hooks.json](.codex/hooks.json) | Codex CLI 的 hook 接線——掛的是上面**同樣那兩個 `.sh`**，不另存一份腳本 | 本專案 | 加減 hook |
| [.agents/skills/handoff/SKILL.md](.agents/skills/handoff/SKILL.md) | Antigravity 原生讀 `.agents/`：只放指向權威版的指標 | 指向 `.claude/` 那份 | 幾乎不動 |
| [tools/check_docs.py](tools/check_docs.py) | 文檔一致性檢查：死連結／過期字串／缺日期標頭／硬編數量／殘留佔位符 | 部署包（「專案設定」區塊除外，那塊本來就該依專案調） | 專案設定要調 |
| [tools/verify_state.py](tools/verify_state.py) | 一鍵現況查證，輸出 key=value 事實快照 | 本專案（骨架來自部署包） | 服務或檢查項改變 |
| [.gitignore](.gitignore)、[.gitattributes](.gitattributes) | 排除祕密與運行資料；行末強制 LF | 本專案 | 新增祕密檔或運行目錄 |

**跨工具的可靠度不一樣**：`AGENTS.md` 與純 Markdown 的程序檔是**可攜層**（Claude Code／Codex／Antigravity 都讀得到）；hooks 在 Claude Code、Codex CLI 與 Antigravity 有效（Antigravity 2026-10-30 重查確認，Codex 桌面 App 沒有）。正確性押在可攜層，不押在 hook 上——換一個工具 hook 就沒了，制度不能跟著沒。

## 專案本體

<還沒有程式碼就照實寫「尚未有程式碼」。**不要先畫一個想像中的架構**——想像的架構會被下一棒當成既成事實去對齊，然後花一整天把程式碼扭成文件的形狀。>

| 目錄／元件 | 職責 | 進入點 | 相依 |
|---|---|---|---|
| <{{STACK_DIRS}} 之一> | <做什麼> | <哪個檔或指令> | <依賴誰> |

## 資料流

<一段話講清楚：資料從哪裡進來、經過什麼、存到哪裡、誰讀它。部署後填。>

## 不在 Git 裡的東西

{{SECRETS}}、{{RUNTIME_DIRS}}——各機器保有自己的本地副本。**Git 存的是 source 與文件，不是資料備份。**
換機器時這些不會跟著過去，所以 `HANDOFF.md` 的「本機能力」要寫明這台有哪些、缺哪些。

## 改本檔的規矩

1. **跟結構變動同一個 commit**。分開改就會出現「文件說有 `foo/`、實際已經搬走」的空窗；接手者照結構圖找不到檔案時，通常不會回頭修文件，只會下次不再相信它。
2. **附絕對日期**（寫 `2026-09-07`，不要寫「今天」），並更新檔頭的「最後更新」。
3. **只寫結構，不寫進度**。「正在重構 X」屬於 `HANDOFF.md`；「打算重構 X」屬於 roadmap。
4. **每個事實只有一個家**：這裡只寫誰是權威版，不要把權威版的內容複製過來。
````

### 3.6 `docs/ai-notes/handover-protocol.md`

````markdown
# 交接協定（跨 session／agent／機器通用）

> 適用於同一模型換 session、跨模型、跨日及跨機器續作。
> 建立：{{TODAY}}。最後更新：{{TODAY}}。
>
> **本檔＝規則與判準**（為什麼這樣做、什麼算做對）。**可執行程序**（指令序列、Git 判讀表、HANDOFF 模板）在 [handoff skill](../../.claude/skills/handoff/SKILL.md)，不在此重複——那是唯一該照著做的一份。兩者衝突時**以本檔為準**，並就地修正 skill。

## 三層分工

| 層 | 放哪裡 | 性質 |
|---|---|---|
| 持久知識 | `AGENTS.md`（規則）、`ARCHITECT.md`（結構）、`docs/ai-notes/`、skills | 三個月後仍成立的鐵律、結構、schema、流程、踩坑 |
| 當下狀態 | `HANDOFF.md` | 單一、精簡、只描述目前做到哪與下一步 |
| 傳輸／歷史 | {{GH_VISIBILITY}} GitHub `{{GH_OWNER}}/{{GH_REPO}}` | source/docs 的跨機器同步與版本史；**不是**資料備份 |

持久知識不要塞進 HANDOFF；HANDOFF 不累積歷史，舊版由 Git history 查。{{SECRETS}}、{{RUNTIME_DIRS}} 永遠不進 Git。

持久知識這一層再分兩種家，別混：**規則與判準**寫 `AGENTS.md`（「不可以做什麼」），**結構**寫 `ARCHITECT.md`（「東西在哪、誰是權威版」）。
結構之所以要獨立一份、而且刻意寫得比 HANDOFF 慢，是因為它被引用來「找檔案」——夾在每次交棒都覆寫的檔案裡，它會跟著被改爛；而一份改爛過一次的結構圖，接手者就不會再相信它。

---

## 一、接棒（順序不可反）

> **自動防呆有兩層**（都只是保險，下面每一步仍必做——離線、非 Claude 端或設定沒載入時 hook 不會跑）：
> ① SessionStart hook（`.claude/hooks/git-freshness.sh`）：session 開始自動 fetch，注入落後／分岔／未推送警告，讀 `origin` 的「工作中」標記揭露別台機器正在動同一條分支，並提醒走 handoff skill。
> ② PreToolUse hook（`.claude/hooks/pre-push-handoff.sh`）：要推到權威分支、但這批 commit 沒更新 `HANDOFF.md` 時擋下（`HANDOFF_HOOK=off` 可停用）。

1. **先同步 Git**：**未同步前不要相信本機 HANDOFF。** 工作樹乾淨、有 upstream 且能 fast-forward 才可自行往下走（指令與完整判讀表見 skill A1）。
2. **確認你該站在哪條分支**：讀 HANDOFF 的「待續分支」。**若它指向 feature branch，該分支才是主幹**——`main` 可能明顯落後。不要因為 `main` 是預設分支就以為它最新。
3. **檢查這條分支有沒有人正在工作**：讀該分支 `HANDOFF.md` 的「工作中」欄位，**讀 `origin/` 那一份**（本機可能還沒 pull）。指向別台機器就**停下來問使用者**——同一條分支同時兩台違反 single writer（指令與三個選項見 skill **A2.5**）。
4. **異常就停在安全點**：未知 dirty changes、diverged、遠端意外前進或 pull 不能 fast-forward 時，**禁止** `reset --hard`、force push、自動 stash 或覆寫。先辨認變更來源並回報。
5. **最小讀取**：只讀 `AGENTS.md` ＋ `HANDOFF.md`。其他知識庫依實際任務 lazy load。
6. **一鍵驗證**：有憑證就跑 `tools/verify_state.py`，與 HANDOFF 的期望快照比對；不一致以實況為準（見 skill A4）。
7. **3–5 行回報後動手**：Git 狀態、驗證結果、理解的現況與下一步。不要重述整份 HANDOFF。**確定要動手才寫「工作中」標記並 push**；**session 名稱在回報完就改，不等標記**（見 skill A5）。

### 🔴 SKIPPED 的判準

**連線失敗 ≠ 本機未配置。** 標 SKIPPED 前必須先排除「設定沒帶到」：

- 環境變數／金鑰路徑沒設，會得到看起來像「未配置」的權限錯誤，其實憑證就在機器上。先檢查該機器的設定方式。
- **暫時性網路錯誤也不是未配置**：重試 2–3 次再下結論。

確認「憑證真的不存在」才寫 `SKIPPED（本機未配置）`。**不得**從系統資料庫、其他主機、Git history 自行挖取／搬運憑證。

---

## 二、分支模型

**兩類分支，判準是「需不需要使用者驗收」：**

| 類型 | 例 | 能不能自己併 main |
|---|---|---|
| **功能分支**（需驗收） | `feature/<ID>-<slug>` | ❌ 要使用者驗收通過才併 |
| **文件／基建分支**（不需驗收） | `docs/cleanup`、`chore/…` | ✅ 驗證通過（`check_docs.py`＋`verify_state.py`）即可併 main |

規則：

- **文件／基建變更不得被功能驗收阻塞。** 這是最容易踩的坑：文件被關在某個功能的驗收閘門後面，接手者「先同步 main」就拿到過期文檔集。
- 小型文件修正可直接在 `main`；成批整理才開分支。
- **同一時間只能有一個 writer 修改 `main` 與 `HANDOFF.md`**。
- 功能分支若已成為事實上的主幹（`main` 明顯落後），**新分支從該分支開，不要從 `main` 開**——否則是在過期基礎上工作，且日後必定衝突。開之前先在回報中說明。
- push 前必須重新 `git fetch origin`。遠端意外前進時**禁止 force push**，先整合或停下請人判斷。
- 不得把半成品併進 `main`。本輪無法完成就 push 分支，並在 HANDOFF 記錄該分支、已知安全 commit、未完成內容與風險。

---

## 三、交棒者義務

1. **收斂安全點**：完成並驗證，或把未完成變更 commit/push 到分支並清楚標風險；不留來源不明的工作樹。
2. **持久知識落地**：新規則／坑／schema 寫入既有 ai-notes 或 skill，**附絕對日期**。遵守 AGENTS.md「每個事實只有一個家」，其他地方只放指標。不要重複造文件。
3. **服務驗證**：跑可用層級的 `verify_state.py`，以實況修正文件；缺憑證的層級依上方判準確認後才記 SKIPPED。
4. **文檔驗證**：動過任何 `.md` 就跑 `tools/check_docs.py`——死連結、過期字串、缺日期標頭、硬編數量，**exit 2 表示要修**（這些 `verify_state.py` 一項都查不到）。
5. **條件式例行檢查**：本專案若有固定流程（部署、版本號、測試），有動到就執行並記錄；未動就明記不適用。
6. **更新 HANDOFF**：≤80 行，填服務快照、Git 狀態、下一步、待續分支與懸置決策。**不要在 HANDOFF 寫「它自己的最終 commit hash」**——那會因提交 HANDOFF 而立刻過時；最終 hash 放交棒回覆。
7. **安全提交**：先 `git diff --check`；明確 stage 需要的檔案，檢查 `git diff --cached --name-only`／`--stat`，確保沒有祕密、runtime、備份或實際資料，再 commit。
8. **發布交棒**：`git fetch origin` 確認遠端未意外前進後 push；最後 `git status -sb` 必須 clean 且與 upstream 對齊。**push 失敗就不是完成交棒。**
9. **最後回報**：5 行內列出結果、驗證、分支、最終 commit hash／是否已 push，以及**接手者最容易搞砸的一件事**。

## 四、接棒者義務

1. 依「一、接棒」先同步 Git，確認站對分支，再讀 AGENTS ＋ HANDOFF。
2. 比對 HANDOFF 的服務快照；不一致以**實況為準**並修文件。缺憑證先排除設定問題，再標 SKIPPED，不擴張權限。
3. 檢查 HANDOFF 指向的待續分支；要續作才 switch，**不能憑猜測合併或刪 branch**。
4. 以 3–5 行回報後開始任務；結束依本協定交棒。

---

## 五、漏交棒的補救

一輪工作**做完就關掉、沒走交棒**：工作樹留著未提交變更與整個結果目錄，而 `HANDOFF.md`
還停在前一輪，寫著與實況矛盾的話（典型的是費用欄——「本輪未產生費用」）。這件事真的會
發生，而且往往隔了好幾週、換了機器或模型才被下一棒發現。

**代價不是那個沒有的 commit，是知識。** 產物還在磁碟上，數字都查得回來；**當時的判斷與
取捨永久消失**——為什麼選這組參數、哪條路試過但放棄、哪些結果是在非基準組態下取得的。
補寫的人只能誠實標註「本節為事後回推，當時無記錄」。

**三層防呆（SessionStart／`hooks.json`／pre-push）一個都擋不住**，因為它們全都掛在
「下一個動作」上，而**直接關掉視窗沒有下一個動作**。所以這是**程序責任，不是工具責任**。

### 2026-10-30：「工作中」標記補了其中一塊

接棒時（skill **A5**）就把機器與 session 寫進 `HANDOFF.md` 並 push，交棒時（**B6**）改回
`無（已交棒）`，下一棒接棒前（**A2.5**）先檢查。**關鍵在它寫在開工而不是收工**——不依賴任何
人記得收尾，所以「直接關掉視窗」繞不過它。跨機器接力時，A 機器忘記交棒、B 機器看到
`✅ 與 origin 同步` 就接棒，是這之前完全沒有任何一層擋得住的洞。

**但它只縮小了洞，沒有補平**：

- **救不回 A 的未提交變更**——那些仍然只在 A 的磁碟上。標記讓你知道「有東西在那台機器」，
  東西還是得回去拿。
- **A 在 A5 之前就關掉**（還沒寫標記）→ `origin` 上什麼都沒有，跟以前一樣。
- **A 用沒有 hook 的工具**（Codex 桌面 App；Antigravity 2026-10-30 起有 hooks，但骨架還沒附接線）→
  沒有自動提醒，只剩程序擔保。

所以下面這套補救程序仍然必要，**能補回來的只有留在磁碟上的那部分**這句話也沒有改變。

### 接棒者發現這種狀況時

1. **先停下來問使用者**這批變更是誰留下的（Git 判讀表已經要求這麼做），不要自己猜著往下做。
2. 確認是前一輪遺留後，**回推補交接**（可執行步驟見 skill 的 **A6**）：從產物、檔案 mtime、
   `git reflog` 重建**可查證的事實**，寫進對應 ai-notes，**並在該節標明「這是回推補寫的、
   當時無記錄」**。回推得到的是數字；**不要把推測寫成當時的理由**，那會變成下一棒眼中的既成事實。
3. 順序是**先落地知識、再 commit**，讓知識與產生它的程式碼進同一批 commit。
4. 修掉 `HANDOFF.md` 裡與實況矛盾的陳述，否則下一棒會拿它當事實引用。

### 給交棒者的一句話

**會花錢、或會產生無法重現之產物的那一輪，不交棒就等於沒做。** 補救成本遠高於當場寫
10 行 HANDOFF；而且能補回來的只有留在磁碟上的那部分。

---

## HANDOFF.md 模板

**模板在 [handoff skill](../../.claude/skills/handoff/SKILL.md) 的 B6**——模板是交棒時照填的東西＝程序，本檔只定義它必須包含什麼：
交接時間與交棒者、任務目標、Git 狀態（含待續分支、**工作中標記**與本機憑證能力）、已完成、未完成／下一步、地雷、服務查證快照、懸置事項。
≤80 行、覆寫不累積、**不寫自己的最終 commit hash**。
**「工作中」欄位必須常駐，而且只有兩種值**（`無（已交棒）`，或機器與 session）：欄位缺席是模稜兩可的——是忘了寫，還是沒人在做？寫「無」才是明確的。`check_docs.py` 第 6 項會擋欄位不見。

## 標準 prompt

**prompt A（交棒）／B（接棒）的正本在 [README.md](../../README.md)「換一個 AI 接手工作」**——那兩段是**人**要複製貼上的東西，家應該在人看的 README，不該在 AI 讀的協定裡各存一份。
本檔負責定義規則，README 負責提供可直接使用的指令。
````

### 3.7 `docs/ai-notes/roadmap.md`

````markdown
# 待辦總表 / Roadmap（未完成工作盤點）

> **本檔＝狀態表**：有哪些事、做到哪、相依、優先、誰能動。
> **規格與實作細節不寫在這裡**，一律指回專門文件——本檔只記「狀態」與「決策」。
> 與只描述當下進度的 [HANDOFF.md](../../HANDOFF.md) 分工：roadmap 是持久清單，HANDOFF 是這一輪。
> 建立：{{TODAY}}。最後更新：{{TODAY}}。優先序為**建議值**，可隨時調整。

**優先**：P1 先做／解鎖其他／高風險 ｜ P2 次要 ｜ P3 之後 ｜ P4 不急
**誰能動**：🧑 使用者手動 ｜ 🤝 等使用者點頭後 AI 做 ｜ 🤖 AI 可做

## 一、<分類名稱>

| ID | 項目 | 狀態 | 相依 | 優先 | 誰 |
|---|---|---|---|---|---|
| R1 | <第一件事> | 未開始 | — | P1 | 🤝 |

## 決策記錄（做過但被否決／暫緩的，寫在這裡免得反覆重提）

| 日期 | 決策 | 理由 |
|---|---|---|
| {{TODAY}} | <例：先不做 X> | <理由> |

<!-- 完成的項目用 ~~R1~~ ✅ 標記並保留，狀態欄寫「YYYY-MM-DD 完成」＋指向細節文件的連結。 -->
````

### 3.8 `.claude/skills/handoff/SKILL.md`（交接程序，本骨架的核心）

> **這一份就是「教 agent 自動交接同步」的東西。** 內容照抄不要改，包含檔頭的 `source:` 版本標記——它讓你日後能一眼看出某個專案的副本是不是落後了。
> 檔案裡的 `docs/ai-notes/handover-protocol.md` 刻意寫成純路徑而非連結，這樣同一份文字放進全域 `~/.claude/skills/` 也不會產生死連結。

````markdown
---
name: handoff
description: 接棒／交棒／跨機器同步的固定程序（Git 同步判讀、站對分支、驗證、寫 HANDOFF、安全提交與 push），以及在還沒有這套制度的資料夾裡把骨架建起來（模式 0 建制）。Use at the start of a work session in a repo that has AGENTS.md/HANDOFF.md, when picking up where a previous session, model, or machine left off, when wrapping up or handing work over, when syncing mid-session, and before any git push. Also use when a folder or project does NOT yet have AGENTS.md/HANDOFF.md and the user asks to set up, bootstrap, scaffold, or introduce this handoff system. Triggers on 接手、接棒、交棒、收工、換機器、換模型、同步進度、繼續上次的工作、建制、導入這套制度、建立交接機制、幫我建 HANDOFF、新專案骨架、handoff、hand off、pick up where we left off、resume work、bootstrap project、set up handoff。
---

<!-- source: PROJECT-BOOTSTRAP.md v2026-10-30.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 交接與同步程序（可執行）

> **本檔＝程序**：做什麼、下哪些指令、什麼時候必須停下來問人。
> **規則與理由**（三層分工、分支模型、SKIPPED 判準、事故史）在 `docs/ai-notes/handover-protocol.md`。兩者衝突時**以協定為準**，並就地修正本檔。
> **例外是模式 0（建制）**：那一段的權威是 `PROJECT-BOOTSTRAP.md` 部署包（協定檔本身也是它生出來的），衝突時以部署包為準。
> 純 Markdown，任何模型（Claude／Gemini／Codex）都應直接讀取，不限某一家工具。

## 適用判斷（先做這一步）

| 專案根目錄的狀態 | 走哪裡 |
|---|---|
| 有 `AGENTS.md` ＋ `HANDOFF.md` | 適用，往下照「判斷模式」選 A／B／C |
| 沒有，而且使用者**明講**要導入這套制度（建交接機制／建骨架／bootstrap） | **模式 0 建制** |
| 沒有，使用者也沒提 | **本程序不適用**。直接做他要的事，**不要憑空建立交接檔案**；最多問一句「要不要導入這套交接制度？」，他說要才走模式 0 |

最後一列是硬規定：這支 skill 會在使用者只是想改一行程式時被載入，未經同意就在別人的 repo 裡長出十幾個檔案是災難，而且他多半不會逐一刪乾淨——會留下半套制度，比沒有更糟。

專案沒有 `tools/verify_state.py`／`tools/check_docs.py` 也能用：對應步驟改為「跳過並在回報寫明沒有該工具」，**不要自己發明驗證**。

## 判斷模式（先選一個）

| 情況 | 模式 |
|---|---|
| 這個資料夾還沒有這套制度，使用者要求建起來 | **0 建制** |
| session 剛開始／要續作／換機器／換模型 | **A 接棒** |
| 工作告一段落、要收工或換人接手 | **B 交棒** |
| 工作中想拉最新或推一個安全點，還沒要交棒 | **C 同步** |
| 準備 `git push` | 先做 **B**——push 是交棒的最後一步，不是獨立動作 |

不確定就走 A（不是 0）。**A 沒跑完之前不要修改任何檔案。**

> 模式 0 在**已經部署好的專案裡永遠用不到**——這裡有雞生蛋問題：skill 是部署之後才存在於專案的。
> 它真正會被載入的地方是**全域副本**（`~/.claude/skills/handoff/`、`~/.codex/skills/handoff/`）。
> 專案內這份仍保留模式 0，是為了讓副本可以整份無腦覆蓋，不必維護兩種版本——分版本就是下一個「同一個事實有多個家」。

---

## session 命名（環境支援才做）

側欄上十幾個 session 全叫「接棒」，要一個個點進去才知道哪個是哪個。**所以每換一次狀態就改一次 session 名稱**——有這個能力才做（例如 Claude Code 桌面版的 `set_session_title`），**沒有就安靜跳過，不要為此停下來問使用者**：Codex CLI 與 Gemini CLI 目前沒有對應能力，為一個做不到的步驟回報失敗只是噪音。

```text
<符號>　YYMMDDHH｜<主題>｜<狀態>
```

| 符號 | 狀態 | 什麼時候改 |
|---|---|---|
| `㊣` | 工作中 | **A5** 回報完之後，**不等開工標記**——只讀、只掃，或專案根本沒有 `HANDOFF.md` 的時候都寫不了標記，改名照樣要做 |
| `↗` | 已交棒 | **B9**，而且是 **push 成功之後**（push 失敗不改，照 B8 那不算交棒） |
| `※` | 待你決定 | **任何時候你把問題丟回去等回答就改**，不限「必須停下來問使用者」那張表 |

範例（同一個 session 從接棒到交棒）：

```text
㊣　26102414｜session改名｜工作中
↗　26102414｜session改名｜已交棒
```

- **`YYMMDDHH` 取接棒當下的時間，之後永遠不更新。** 交棒時一起改掉的話，同一個 session 在側欄的名字會跳掉，使用者記得的時間點就對不上了。
- **主題 ≤10 字，取自 `HANDOFF.md` 的任務目標，壓成動詞＋受詞。** 不要寫「更新文件」「修 bug」這種放哪個 session 都成立的詞——那會退化回「全部長一樣」，等於沒改。還不知道要做什麼就先寫 `待指派`，第一件事確定後就地改一次。
- **符號後面接一個全形空格（U+3000）再開始日期。** 半形空格撐不開，`↗` 這種細筆畫的符號會黏在數字上。
- **符號放最前面**，是因為側欄窄的時候是從尾巴開始截字；狀態是最該被看見的東西，不能放在第一個被截掉的位置。尾綴那幾個字是版面夠寬時的補充，截掉不損失資訊。
- 同一天同一個主題開第二個 session 才在主題後面加數字（`匯入格式2`），不是每個都編號。
- **改名的依據是 session 的狀態，不是 git 的結果。** 側欄要回答的是「這個 session 現在在幹嘛」，`HANDOFF.md` 的「工作中」欄位要回答的是「哪台機器握著這條分支」——兩件事、兩個讀者，不要綁在一起。綁住的代價 2026-10-30 在骨架自己的 repo 上現形：舊版 A5 寫「push 成功才改名」，而 project-bootstrap 刻意沒有 `HANDOFF.md`、寫不了開工標記，於是改名那一步永遠到不了，這個 repo 的 session 全部停在「接棒」兩個字，直到交棒才一次拿到名字——那時候它已經不需要被認出來了。唯一的例外是 `↗ 已交棒`：它本身就在宣稱一件 git 的事，所以只有它要等 push。
- **側欄的 `㊣` 不證明 origin 上有開工標記。** 跨機器防呆看的是 `HANDOFF.md` 的欄位（A2.5），側欄只是給人看的；別拿它當防呆的證據。
- **模式 C 中途同步不改名**——狀態沒變。
- 模式 0 建制照 B9 收尾，主題寫 `骨架建制`。
- **改完這份規則、同步完副本之後，當下開著的 session 仍會照舊版做事。** `SKILL.md` 是 session 載入它的那一刻讀進 context 的快照，之後改磁碟上的檔案不會回溯生效——要重開 session 才會拿到新版，已經寫下的 session 名稱也不會自己更新，要補只能手動改名。2026-10-24 加上全形空格那條時就是這樣：副本 15:20 全部同步完，一個 15:29 才交棒的 session 名字裡照樣沒有空格——那不是漏同步，查錯方向會白花一輪。

---

## 0. 建制（這個資料夾還沒有這套制度）

**這一模式是「把骨架生出來」，不是交接。** 產物的權威是 `PROJECT-BOOTSTRAP.md` 部署包，本節只是它的執行順序與停止判準。

### 0-1 先確認你在對的資料夾、對的情境

```bash
pwd && ls -a && git status -sb
```

| 看到 | 動作 |
|---|---|
| 空資料夾，或只有部署包 | 標準情境，往下走 |
| 已有 `AGENTS.md`／`HANDOFF.md` | **這不是建制**——改走模式 A 接棒 |
| 已有程式碼、README 或 Git 歷史 | **停**：這是「既有專案補裝」。既存檔案只補段落**不覆蓋**，動手前先把打算新增／修改的清單列給使用者看過 |
| 這是家目錄、桌面或某個大目錄 | **停**：先確認資料夾。灑錯地方的檔案沒人會逐一刪乾淨 |

🚫 使用者點頭之前不要建立任何檔案。

### 0-2 取得部署包（沒有它就停）

`PROJECT-BOOTSTRAP.md` 在這個資料夾嗎？在 → 用它，逐檔照抄。不在 → **停下來跟使用者要**（來源：`project-bootstrap` repo 的 `PROJECT-BOOTSTRAP.md`，或它產出的骨架 zip）。

🔴 **絕對不要憑記憶重刻骨架。** 憑印象生出來的版本，缺的永遠是最貴的那部分——每條規則後面的「為什麼」、hook 的邊界條件、`check_docs.py` 那幾項檢查。看起來像那套制度，實際上擋不住任何事，而且沒有任何跡象；下一棒會以為自己有防護網。

### 0-3 訪談：一次問完（部署包第 1 節）

照第 1 節那張表把佔位符**一次問完**，不要分五輪擠牙膏。最後追問一句：**「這個專案有沒有已知的『絕對不能做』的操作？」**

拿不到的答案就留 `<部署後填>`，**不要自己編一個看起來合理的值**——編出來的網址、憑證檔名會被下一棒當成事實，然後照著它去連一個不存在的東西。

### 0-4 逐檔建立（部署包第 3 節）

內容照抄、只換佔位符；**不要自行增刪制度**，也不要「順手優化」措辭——那些句子後面各有一次事故。
全檔 LF。macOS／Linux 建完要 `chmod +x .claude/hooks/*.sh`。

### 0-5 上 Git（部署包第 4 節）

⚠️ **`.gitignore` 必須先就位再 `git add`**。順序反了祕密就進第一個 commit，之後刪不掉——那是要重建 repo 的等級。
建 GitHub repo 與第一次 push 前**先問使用者確認**（owner／repo 名、public 或 private）：這是外部動作，不是本機檔案操作。

### 0-6 自檢（部署包第 5 節）

逐項跑、逐項回報通過／不適用／有問題。至少要有：

```bash
python -X utf8 tools/check_docs.py
```

（`python` 不存在就用 `python3`。）**exit 0 才算過**；`SKILL.md` 前三行必須是 frontmatter，壞掉 skill 就不會被載入，整套自動化靜默失效。

### 0-7 寫第一份 `HANDOFF.md` 與 `ARCHITECT.md`

建制本身就是第一段工作，所以照 **B6** 寫第一份 HANDOFF（任務目標＝骨架已就緒；下一步＝填連線資料與 `verify_state.py` 的檢查項）。
`ARCHITECT.md` 的「專案本體」這時候通常還是空的，**照實寫「尚未有程式碼」**——不要先畫一個想像中的架構，那會被下一棒當成既成事實去對齊。

### 0-8 刪掉部署包，回報

自檢全過之後才刪 `PROJECT-BOOTSTRAP.md`（以及壓縮檔附的 `讀我-先看這個.md`）。留著就是第二份會腐化的副本；而那份說明檔寫著「佔位符還沒填」，下一棒讀到會以為部署沒做完，再跑一次訪談。

回報 ≤5 行：建了什麼、自檢結果、repo 與分支、**還沒填的洞**、下一棒第一件事。

---

## A. 接棒

### A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF）

```bash
git status -sb && git fetch origin && git log --oneline -3
```

判讀表——**只有前兩列可以自己往下走**：

| 看到 | 動作 |
|---|---|
| 乾淨、落後 origin | `git pull --ff-only` 後繼續 |
| 乾淨、與 origin 一致 | 直接繼續 |
| 有未提交變更，來源不明 | **停**：貼 `git status --porcelain` 與 `git diff --stat`，問使用者這是誰留下的 |
| 已分岔（同時 ahead＋behind） | **停**：回報落後／領先數與雙方 commit 標題，等指示 |
| pull 不能 fast-forward | **停**：不要 rebase／merge 到一半才問 |
| 沒有 upstream | **停**：回報，不要自行 `push -u` 建立 |

🚫 全程禁止：`reset --hard`、`push --force`、自行 `stash`、覆寫他人 commit、刪 branch。

### A2 站對分支

讀 `HANDOFF.md` 的「待續分支」：

- 寫「無」→ 待在權威分支（通常 `main`）。
- 指向 `feature/...` → **那條才是主幹，`main` 可能明顯落後**。要續作就 `git switch <branch>`；不要因為 `main` 是預設分支就以為它最新。
- 要開新分支 → 從**現在的主幹**開，不是從 `main` 開。

### A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆）

**站對分支之後、讀文件之前**，看該分支 `HANDOFF.md` 的「工作中」欄位：

```bash
git show "origin/$(git rev-parse --abbrev-ref HEAD):HANDOFF.md" | grep -F "**工作中**"
```

讀 `origin/` 那一份、**不讀本機的**——此刻可能還沒 pull，本機那份是舊快照。

| 看到 | 動作 |
|---|---|
| `無（已交棒）` | 正常，往下走 |
| 沒有這個欄位 | 這個專案的骨架還沒升級到有這個機制，照舊往下走——但**別把「沒有欄位」當成「沒人在做」**，這一輪沒有防呆，心裡要有數。欄位由 **A5** 寫標記時一併補上，那也就是這個專案的升級點 |
| 指向**別台**機器 | **停**，見下方三個選項 |
| 指向**這台**機器 | 多半是你自己還開著的另一個 session（側欄會有一個 `㊣`）。確認是自己的就往下走；不是的話照「別台機器」處理 |

**指向別台機器時不要自己決定**，把這三個選項給使用者：

1. **回那台機器走完交棒**（預設建議）——那台的未提交變更只在那台的磁碟上，這裡拿不到
2. 使用者確認那台已經沒在跑 → 授權在這裡接手，由本 session 清掉舊標記並照 **A6** 回推補交接
3. 這次只讀不寫 → 不接棒、不寫標記、不動任何檔案

同時把 session 名稱改成 `※　YYMMDDHH｜<主題>｜待你決定`（見「session 命名」）。

> **為什麼標記寫在開工而不是收工**：既有三層防呆全都掛在「下一個動作」上，而**直接關掉視窗沒有下一個動作**。寫在開工的標記不依賴任何人記得收尾——A 沒交棒，標記就留在 origin 上，下一棒一定看得到。
> **它救不回什麼**：A 那些未提交的變更仍然只在 A 的磁碟上。標記只讓你知道「有東西在那台機器」，東西還是得回去拿。

### A3 最小讀取

只讀 `AGENTS.md` ＋ `HANDOFF.md`。其他知識庫等任務真的碰到再讀（`AGENTS.md` 有知識庫地圖）。
**不要**為了「先了解全貌」把 `docs/` 全讀一遍——那是 token 黑洞，也不會讓你更準。

### A4 一鍵驗證

```bash
python -X utf8 tools/verify_state.py
```

（`python` 不存在就用 `python3`；腳本不存在就跳過並在回報寫明。）
與 HANDOFF 的「服務查證與期望快照」比對。不一致時**以實況為準**，就地修文件並註記絕對日期。

🔴 **標 SKIPPED 前先排除「設定沒帶到」**：連線失敗 ≠ 本機沒有憑證。先確認該機器的憑證路徑／環境變數是不是沒設，是不是暫時性網路錯誤（重試 2–3 次）。確認憑證真的不存在才寫 `SKIPPED（本機未配置）`。**不得**從系統資料庫、其他主機、Git history 或別台機器自行挖取／搬運憑證。

### A5 回報後才動手（3–5 行）

```text
Git：<分支>、<與 origin 關係>、<待續分支>
驗證：<verify_state 關鍵值／SKIPPED 與原因>
現況：<用自己的話講一句現在做到哪>
下一步：<我打算做的第一件事>
```

不要重述整份 HANDOFF。有疑問就多一行問題。

**回報完就改 session 名稱**成 `㊣　YYMMDDHH｜<主題>｜工作中`（規則見「session 命名」；環境沒有這個能力就跳過，不必回報）。這一步跟下面的開工標記是兩件事，**不要等它**。

**確定要動手改東西，才寫開工標記。** 只讀、只問問題的 session 不寫——那會在權威分支的歷史裡堆一堆沒有內容的 commit，而被灌爆的歷史沒人會認真看。

1. 把該分支 `HANDOFF.md` 的「工作中」欄位改成本機與本 session。舊專案沒有這一欄，就在「Git 狀態」那節補一列（這就是該專案的升級點，不用另外安排一次升級）：

   ```markdown
   - **工作中**：`desk-win` ／ `㊣　26103009｜匯入格式｜工作中`，2026-10-30 09:12 (+08) 開工
   ```

   記 session 名稱比只記機器名有用——可以直接拿它回側欄把那個 session 點開。

2. **只** stage `HANDOFF.md`，commit 後 push 到**當前分支**。訊息用 `chore(handoff): <機器> 開工` 這類前綴，之後掃歷史時一眼可略過。
**push 失敗就不是「已標記」**：明確告訴使用者「這次沒有標記保護，別台機器不會知道我在做」，問他要不要在這個狀態下繼續。**不要靜默往下做**——你會以為有保護，實際上沒有。（名稱照樣是 `㊣`——它說的是「這個 session 在做事」，不是「標記已經在 origin 上」。）

規則一句話：**側欄講的是這個 session，HANDOFF 講的是這條分支。** 只有 `↗ 已交棒` 是在宣稱一件 git 的事，所以只有它要等 push 成功。

### A6 回推補交接（只有在 A1 判定「前一輪漏交棒」時才走）

前一輪做完沒交棒，工作樹留著未提交變更，`HANDOFF.md` 停在更早的狀態。
**這種情況下最貴的損失不是那個 commit，是知識**——理由與取捨會永久消失，
只有留在磁碟上的東西救得回來。規則與事故的完整記述在
`docs/ai-notes/handover-protocol.md` 的「漏交棒的補救」一節（章節編號各專案不同，
這裡刻意不寫死；純路徑而非連結，是為了讓同一份文字放進全域副本也不會產生死連結）。

1. 先**唯讀**盤點產物：新產出的結果目錄、檔案 mtime、`git reflog`、結果檔裡的
   費用／參數。算出實際花了多少錢——`HANDOFF.md` 的費用欄多半已經錯了。
2. 問使用者三件事：**要不要收斂進這條分支**、**有沒有已知該留／該刪的東西**、
   **要不要補跑未完成的部分**（會花錢的一律等他點頭）。
3. **先落地知識（B2）再 commit（B7）**，讓知識與產生它的程式碼進同一批 commit。
4. 回推寫成的段落**一定要標明「這是事後回推、當時無記錄」**，
   **不要替它補理由**——編出來的理由會變成下一棒眼中的既成事實。
5. 修掉 `HANDOFF.md` 裡與實況矛盾的陳述，然後照 B 模式正常收工。

> 三層防呆（SessionStart／`hooks.json`／pre-push）擋不住這件事：它們全都掛在
> 「下一個動作」上，**直接關掉視窗沒有下一個動作**。所以這是程序責任，不是工具責任。

---

## B. 交棒

九步，**順序就是執行順序**，做完一步再下一步。

### B1 收斂到安全點

未完成的東西二選一：完成並驗證；或 commit／push 到分支並在 HANDOFF 標明風險與已知安全 commit。
**不留來源不明的工作樹**，也不要把半成品併進 `main`。

### B2 持久知識落地（今天學到的寫進 repo，不要留在對話裡）

| 你剛剛得到什麼 | 寫進 |
|---|---|
| 一條「以後都要這樣做」的規則、一次踩坑 | `AGENTS.md` 鐵律（重大）或 `docs/ai-notes/<主題>.md`（細節） |
| 做過兩次以上、而且踩過坑的操作步驟 | `.claude/skills/<slug>/SKILL.md` |
| 還有哪些事沒做、什麼被否決／暫緩及理由 | `docs/ai-notes/roadmap.md` |
| **專案結構變了**：新增／搬移目錄、換掉一個元件、改變資料流或權威版位置 | `ARCHITECT.md`（只有結構變動才動它，而且跟該變動同一個 commit） |
| 現在做到哪、下一步 | `HANDOFF.md`（B6 才寫） |

規則：**附絕對日期**（寫 `2026-08-05`，不要寫「今天」「上週」）；**每個事實只有一個家**，其他地方只放指標；新開 `docs/ai-notes/` 檔案要回頭把 `AGENTS.md` 的知識庫地圖補上一列，否則沒人找得到它。

### B3 服務驗證

```bash
python -X utf8 tools/verify_state.py
```

### B4 文檔驗證（動過任何 `.md` 就必跑）

```bash
python -X utf8 tools/check_docs.py
```

**exit 2 表示要修**（死連結／過期字串／缺日期標頭）。這些 `verify_state.py` 一項都查不到。

### B5 條件式例行檢查

本專案若有固定流程（部署、版本號 bump、測試、備份），對照 `AGENTS.md` 鐵律：這輪有動到就執行並記錄；沒動到就在 HANDOFF 明記「不適用」。
**不要靜默略過**——接手者無法分辨「沒做」與「不用做」。

### B6 更新 `HANDOFF.md`（覆寫，≤80 行，不累積歷史）

```markdown
# HANDOFF — 工作交接狀態

- **交接時間**：YYYY-MM-DD HH:MM（<時區>）
- **交棒者**：<模型／機器>（主題一句話）

## 任務目標
<目前目標>

## Git 狀態
- Repo：`<owner>/<repo>`
- **待續分支**：<無，或 feature/... @ 已知安全 commit>；若 main 落後主幹要註明
- **工作中**：無（已交棒）　← 交棒時必須是這個值；開工時由 A5 改成機器與 session
- 本機能力：<機器；哪些憑證可用／未配置，不寫祕密值>

## 已完成
- <事項與驗證>

## 未完成／下一步
1. <可執行步驟>

## 地雷與注意事項
- <最容易搞砸的事>

## 服務查證與期望快照
`python -X utf8 tools/verify_state.py`
<目前實際關鍵輸出；未能查的層級寫 SKIPPED 與原因>

## 懸置事項（AI 勿自行處理）
- <等使用者決定的事>
```

⚠️ **不要在 HANDOFF 裡寫它自己的最終 commit hash**——提交 HANDOFF 的當下就過時了。最終 hash 放交棒回覆（B9）。
⚠️ **「工作中」欄位要改回 `無（已交棒）`。** 這一欄是覆寫時最容易被原封不動抄過去的——交棒了卻還寫著「工作中」，下一棒會被擋在 A2.5，然後回頭去找一台其實已經收工的機器。
⚠️ 舊內容直接覆寫，不要往下疊成日誌；歷史由 Git 查。

### B7 安全提交

```bash
git diff --check && git status --porcelain
```

明確 stage 需要的檔案（**不要無腦 `git add -A`**），然後看過清單再 commit：

```bash
git diff --cached --name-only && git diff --cached --stat
```

祕密掃描（有輸出就停下來逐條確認）：

```bash
git diff --cached -U0 | grep -nEi "(api[_-]?key|secret|token|passwd|password|BEGIN [A-Z ]*PRIVATE KEY)" | head -20
```

確認沒有憑證、運行資料、備份、實際業務資料後才 commit。

### B8 發布

```bash
git fetch origin && git status -sb
```

遠端意外前進 → **停下**，禁止 force push，先整合或請使用者判斷。正常才 push；push 後 `git status -sb` 必須 clean 且與 upstream 對齊。
**push 失敗就不是完成交棒**，不要在回覆裡寫「已交棒」。

### B9 回報（≤5 行）

結果／驗證結果／分支／最終 commit hash 與是否已 push／**接手者最容易搞砸的一件事**。

**push 成功之後**把 session 名稱的符號與尾綴換成 `↗` 與 `已交棒`，前面的 `YYMMDDHH｜<主題>` 原封不動（見「session 命名」）。push 失敗就不要改——那不算交棒。

順便確認推上去的那一份「工作中」真的已經清掉（本機改對了但沒推上去，下一棒看到的還是舊的）：

```bash
git show "origin/$(git rev-parse --abbrev-ref HEAD):HANDOFF.md" | grep -F "**工作中**"
```

---

## C. 中途同步（還沒要交棒）

- 拉最新：照 A1 判讀表走，異常一樣停。
- 推安全點：B7 → B8（可略過 B6；但這批 commit 若會被別人或別台機器看到，仍要在 HANDOFF 補一句現況）。
- **換機器前一定要 push，下一台機器一定要先 fetch。**
- **single writer**：同一時間只有一個 agent／一台機器可以改 `main` 與 `HANDOFF.md`。要換手就先交棒。

---

## 必須停下來問使用者（不得自行決定）

- Git 異常：dirty 來源不明、diverged、不能 fast-forward、遠端意外前進、沒有 upstream
- **A2.5 偵測到別台機器的「工作中」標記**（同一條分支同時兩台＝違反 single writer）
- `push --force`、`reset --hard`、刪分支、改寫歷史
- 功能分支要併進 `main`（需使用者驗收；文件／基建分支驗證過可自己併）
- 憑證缺失，或需要跨機器搬憑證
- HANDOFF 沒授權的破壞性操作（刪檔、批次改資料、改 schema）
- **建制（模式 0）**：資料夾不是空的、已有 Git 歷史或 README；要覆蓋既有的 `.gitignore`／`README.md`；建 GitHub repo 與第一次 push

**停下來的同時把 session 名稱改成 `※　YYMMDDHH｜<主題>｜待你決定`**（見「session 命名」）。**不只這張表**——「接下來做哪一件」這種普通的徵詢也是在等人回答，一樣要改。否則使用者在側欄只看到一個「工作中」的 session，不會知道它其實卡在等他回答——這種等待很容易一整天沒人發現。

## 反例（真的發生過，別重演）

- ❌ 開工沒 fetch，對著落後數十個 commit 的本機 HANDOFF 工作數小時 → 分岔，收拾一整天。
- ❌ 連線失敗直接寫「本機未配置」→ 其實只是金鑰環境變數沒設，結論全錯。
- ❌ 純文件修正卡在功能分支等驗收 → 接手者同步 `main` 拿到過期文檔集。
- ❌ 知識寫在對話裡或私有記憶 → 換模型、換機器後全部消失。
- ❌ HANDOFF 愈疊愈長變成日誌 → 接手者要讀 20 分鐘才知道現在做到哪。
- ❌ push 完才想起沒更新 HANDOFF → 下一棒拿到過期狀態（pre-push hook 會擋，但別靠它）。
- ❌ A 機器沒交棒就關掉，B 機器開 session 看到 `✅ 與 origin 同步` 就接棒 → 那個綠勾只證明「B 沒落後」，**不證明「沒有別台在做」**；A 的未提交變更整批被繞過。這就是「工作中」標記要擋的那件事。
- ❌ 會花錢的那一輪跑完直接關掉視窗 → 數字還在磁碟上，**當時的判斷與取捨永久消失**；三層防呆全都掛在「下一個動作」上，擋不住這件事。
- ❌ 建制時沒拿到部署包，憑印象生一套「差不多的」骨架 → 規則沒了理由、hook 沒了邊界條件，看起來有制度、實際擋不住任何事。
- ❌ 使用者只說「幫我看一下這個 repo」，agent 自作主張把整套骨架灑進去 → 別人的 repo 多出十幾個沒人要的檔案，而且不會被逐一刪乾淨。
- ❌ 建完沒刪部署包 → 第二份會腐化的副本，下一棒還會以為部署沒做完而重跑一次訪談。
- ❌ session 名稱全部一樣 → 側欄認不出哪個是哪個；主題寫成「更新文件」也一樣，改了名還是分不出來。
- ❌ 停下來問使用者卻沒改名 → 側欄顯示「工作中」，使用者以為它還在跑，實際上在等他。只把「必須停下來問使用者」那張表當成改名時機也一樣——普通的「要選哪個」同樣是在等人。
- ❌ 把改名綁在「開工標記 push 成功」之後 → 這輪只讀、或專案刻意沒有 `HANDOFF.md`，標記寫不了，側欄就永遠停在「接棒」。2026-10-30 在骨架自己的 repo 上發現：三個 session 全是 `↗ 已交棒`，一個 `㊣ 工作中` 都沒有過。
````

**同步規則（重要）**：這份 SKILL.md 會同時存在於 ①本部署包 ②每個專案的 `.claude/skills/handoff/` ③（選用）全域 `~/.claude/skills/handoff/`。
**權威版是本部署包**；要改就改這裡，再覆蓋下去，不要在單一專案裡就地改——那正是「同一個事實有多個家」的典型失控起點。

### 3.9 `.claude/settings.json`

````json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/git-freshness.sh",
            "timeout": 30,
            "statusMessage": "檢查 git 是否與 origin 同步…"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre-push-handoff.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
````

> Codex 的接線見 3.17——它掛的是**同樣這兩個 `.sh`**，不要複製第二份腳本進 `.codex/`。兩份各自演化就會出現「Claude 端會擋、Codex 端不會擋」的不對稱。

### 3.10 `.claude/hooks/git-freshness.sh`

> Windows 需要 Git for Windows 附的 bash（Claude Code 內建可用）。建立後在 macOS／Linux 上加執行權限：`chmod +x .claude/hooks/git-freshness.sh`。

````bash
#!/usr/bin/env bash
# source: PROJECT-BOOTSTRAP.md v2026-10-30 — 權威版在部署包，改這裡之前先改部署包再同步各專案。
# SessionStart hook：git 新鮮度檢查（多機分岔防呆）
# 起因：某台機器的複本停在舊快照、session 對著過時 HANDOFF 工作數小時後 commit，造成分岔。
# 此腳本在每次 session 開始時由 harness 自動執行：fetch origin 並比對本地分支，
# 落後／分岔時把警告直接注入對話開頭，不依賴任何人記得先 pull。
# 輸出到 stdout 的內容會成為 session 起始 context。只讀不寫，絕不自動 pull/push。

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0

if ! git fetch --quiet origin 2>/dev/null; then
  echo "[git-check] ⚠️ 無法 fetch origin（離線或金鑰問題）——無法確認本地是否最新，讀 HANDOFF 前請自行確認。branch=$branch"
  exit 0
fi

counts=$(git rev-list --left-right --count "@{upstream}...HEAD" 2>/dev/null)
if [ -z "$counts" ]; then
  echo "[git-check] ⚠️ branch=$branch 沒有 upstream，跳過比對。"
  exit 0
fi
behind=$(echo "$counts" | awk '{print $1}')
ahead=$(echo "$counts" | awk '{print $2}')
dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

if [ "$behind" -gt 0 ] && [ "$ahead" -gt 0 ]; then
  echo "[git-check] 🔴 已分岔：落後 origin $behind、領先 $ahead（branch=$branch）。開工前必須先整合（git pull --rebase），禁止直接 push 或 reset --hard。"
elif [ "$behind" -gt 0 ]; then
  echo "[git-check] 🔴 本地過時：落後 origin $behind 個 commit（branch=$branch）。本地 HANDOFF.md／docs 可能是舊快照——先 git pull --ff-only 再讀任何文件、再動任何工作。"
elif [ "$ahead" -gt 0 ]; then
  echo "[git-check] 🟡 有 $ahead 個未推送 commit（branch=$branch）。上一棒可能沒完成交棒 push；收工前記得推。"
else
  echo "[git-check] ✅ 本機沒落後 origin（branch=$branch）——這一行只比對本機與 origin 的落差，不代表沒有別台機器在做。"
fi
if [ "$dirty" -gt 0 ]; then
  echo "[git-check] 🟡 工作區有 $dirty 個未提交變更（可能是上一棒未收斂，先辨認來源再動）。"
fi

# 工作中標記（跨機器誤接棒防呆，2026-10-30）
# 起因：A 機器忘記交棒就關掉，B 機器開 session 看到「與 origin 同步」的綠勾就接棒——
# 那個綠勾只證明「B 沒落後」，不證明「沒有別台在做」，於是 A 的未提交變更整批被繞過。
# 讀 origin 那一份、不讀本機的：此刻還沒 pull，本機那份可能是舊快照。
# 只讀、只提醒，絕不寫入——往權威分支自動 commit／push 是整套制度最不該自動化的地方
# （本機落後時會當場分岔，工作樹 dirty 時會把別人的東西一起包進 commit）。寫入是 skill A5 的事。
# 已知限制：本 hook 跑在 skill 的 A2「站對分支」之前，只看得到當前分支；
# 切到 feature/... 之後的檢查由 A2.5 的程序負責。
# 欄位在的時候一定印一句結論（✅／🟡／🔴），不要「沒事就不說話」：沉默跟「查過了沒事」
# 分不出來，而這個機制的全部價值就在於讓人知道「有沒有被查」。
remote_handoff=$(git show "origin/$branch:HANDOFF.md" 2>/dev/null)
if [ -n "$remote_handoff" ]; then
  busy=$(printf '%s\n' "$remote_handoff" | grep -F '**工作中**' | head -1)
  case "$busy" in
    '')
      echo "[git-check] 🟡 origin 的 HANDOFF.md 沒有「工作中」欄位，無法確認有沒有別台機器在動 $branch（這個專案的骨架還沒升級到有這個機制；下次交棒時照 B6 補上）。"
      ;;
    *無*)
      echo "[git-check] ✅ 「工作中」是「無（已交棒）」，沒有別台機器佔著 $branch。"
      ;;
    *)
      who=${busy#*：}
      me=${HOSTNAME:-$(hostname 2>/dev/null || uname -n 2>/dev/null)}
      same=no
      [ -n "$me" ] && case "$busy" in *"$me"*) same=yes ;; esac
      if [ "$same" = yes ]; then
        echo "[git-check] 🟡 這台機器（$me）還有一個 session 在 $branch 上沒交棒：$who"
        echo "[git-check]    確認是你自己開的另一個視窗就繼續；不是的話先回去那個 session 收尾。"
      else
        echo "[git-check] 🔴 另一台機器正在 $branch 上工作，尚未交棒：$who"
        echo "[git-check]    依 single writer 規則，同一時間只能有一台機器動同一條分支。"
        echo "[git-check]    停下來問使用者（handoff skill 的 A2.5），不要直接接棒。"
      fi
      ;;
  esac
fi
# origin 上沒有 HANDOFF.md（沒用這套制度，或這條分支還沒推過）就整段安靜跳過——
# 那不是本 hook 該管的事，在這種 repo 裡每次開場嘮叨一句只會讓人學會無視 [git-check]。

# 骨架版本落後偵測（2026-10-30）
# 起因：同步是手工的，而「這台機器上有哪些專案裝了這套骨架」沒人記得住——盤點時得用 find
# 掃一遍，而且掃出 4 個專案留著上一輪沒 commit 的同步殘留。所以偵測放在「開場」這個你一定
# 會經過的時刻：哪個專案落後，哪個就在你打開它的當下自己講，你永遠不必先知道有哪些專案。
# 跟「工作中」標記同一招——把檢查掛在必然發生的動作上，而不是掛在要人記得的動作上。
# 抓不到（離線、沒有 curl、fork 改過網址）就安靜跳過：這是提醒，不是關卡。
# 結果快取 12 小時，免得每開一次 session 就打一次網路。關掉：BOOTSTRAP_VERSION_CHECK=off
UPSTREAM_VERSION_URL=https://raw.githubusercontent.com/Baliyoho/project-bootstrap/main/VERSION  # fork 的人改這一行
skill=.claude/skills/handoff/SKILL.md
if [ "$BOOTSTRAP_VERSION_CHECK" != off ] && [ -f "$skill" ]; then
  mine=$(sed -n 's/.*source: PROJECT-BOOTSTRAP\.md v\([0-9][0-9.-]*\).*/\1/p' "$skill" | head -1)
  cache=.claude/.bootstrap-version
  if [ -n "$(find "$cache" -mmin -720 2>/dev/null)" ]; then
    latest=$(cat "$cache" 2>/dev/null)
  else
    latest=$(curl -fsS --max-time 5 "$UPSTREAM_VERSION_URL" 2>/dev/null | tr -d '\r\n \t')
    [ -n "$latest" ] && printf '%s' "$latest" > "$cache" 2>/dev/null
  fi
  if [ -n "$mine" ] && [ -n "$latest" ] && [ "$mine" != "$latest" ]; then
    echo "[git-check] 🟡 handoff 骨架落後：本機 v$mine，最新 v$latest。"
    echo "[git-check]    到 project-bootstrap 跑：python -X utf8 tools/sync_project.py <本專案路徑>（python 不存在就用 python3）"
  fi
fi

if [ -f .claude/skills/handoff/SKILL.md ]; then
  echo "[handoff] 本專案有交接制度：接棒先走 handoff skill 的 A 模式（.claude/skills/handoff/SKILL.md）——同步 Git、站對分支、A2.5 檢查「工作中」標記、只讀 AGENTS.md＋HANDOFF.md，回報 3–5 行後再動手；收工走 B 模式。"
fi
exit 0
````

### 3.11 `.claude/hooks/pre-push-handoff.sh`（push 前防呆）

> 只擋「推到權威分支、但這批 commit 沒更新 `HANDOFF.md`」這一種情況；feature 分支中途推進度不擋，判斷不了也放行。
> 退出碼 2 會擋下該次 Bash 呼叫並把訊息交給模型——這是唯一能讓 agent「當場改走交棒程序」的機制，警告訊息模型不一定看得到。

````bash
#!/usr/bin/env bash
# PreToolUse hook：push 前確認 HANDOFF 已更新（交棒防呆，2026-08-05）
# 起因：push 完才想起沒寫 HANDOFF，下一棒拿到過期狀態。
# 只在「要推到權威分支、且這批 commit 沒動過 HANDOFF.md」時擋下；
# 其他情況（非 push 指令、feature 分支中途推進度、判斷不了）一律放行——寧可漏擋，不要誤擋。
# 退出碼：0＝放行；2＝擋下並把 stderr 交給模型（模型會看到訊息並改走交棒程序）。
# 臨時停用：HANDOFF_HOOK=off
# source: PROJECT-BOOTSTRAP.md v2026-09-30 — 權威版在部署包，改這裡之前先改部署包再同步各專案。

[ "$HANDOFF_HOOK" = "off" ] && exit 0

payload=$(cat 2>/dev/null)
case "$payload" in
  *'git push'*) ;;
  *) exit 0 ;;
esac

root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0
[ -f HANDOFF.md ] || exit 0                    # 沒有這套交接制度就不管

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0
main=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
main=${main#origin/}
[ -n "$main" ] || main=main
[ "$branch" = "$main" ] || exit 0               # feature 分支中途推進度不擋

git rev-parse --quiet --verify "refs/remotes/origin/$branch" >/dev/null 2>&1 || exit 0
[ -n "$(git rev-list "origin/$branch..HEAD" 2>/dev/null)" ] || exit 0   # 沒有要推的 commit
git diff --name-only "origin/$branch..HEAD" 2>/dev/null | grep -qx 'HANDOFF.md' && exit 0
git diff --quiet -- HANDOFF.md 2>/dev/null || exit 0                    # 工作樹正在改，等一下會提交

>&2 echo "[handoff-check] 這批要推到 $branch 的 commit 沒有更新 HANDOFF.md。"
>&2 echo "[handoff-check] 依交接協定，push 是交棒的最後一步：先跑 handoff skill 的 B 模式（B2 知識落地、B3/B4 驗證、B6 更新 HANDOFF、B7 檢查 staged 清單）再 push。"
>&2 echo "[handoff-check] 若真的只是中途推進度：改推 feature 分支，或本次設 HANDOFF_HOOK=off。"
exit 2
````

### 3.12 `.gitignore`

````gitignore
# Credentials (each machine keeps its own local copy)
.env
.env.*
!.env.example

# Runtime state, downloaded backups, and operational data
data/
backups/
persist/
archive/

# Local scratch artefacts
tmp/
scratch/
.claude/settings.local.json
.claude/.bootstrap-version
__pycache__/
*.py[cod]
*.log

# Editor and operating-system metadata
.DS_Store
Thumbs.db
.obsidian/
````

> 依訪談把 `{{SECRETS}}`／`{{RUNTIME_DIRS}}` 補進去，再加語言／框架專屬項目（`node_modules/`、`.venv/`、`dist/`、`.build/` …）。**寧可多擋不要少擋。**

### 3.13 `.gitattributes`

````gitattributes
# Keep source and documentation consistent across Windows and macOS.
* text=auto eol=lf
*.bat text eol=crlf
````

### 3.14 `tools/check_docs.py`

````python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文檔一致性檢查（交接用）。verify_state.py 查「服務現況」，本腳本查「文件本身」。

用法（專案根目錄執行）：
  python -X utf8 tools/check_docs.py           # 全部檢查
  python -X utf8 tools/check_docs.py --quiet   # 只印問題與結論

檢查六項（都是實際發生過的腐化模式）：
  1. 死連結     ——markdown 相對連結指向不存在的檔案（整併文件時最常見）
  2. 過期字串   ——換了網址／改了名稱後殘留的舊值（見下方 STALE_PATTERNS，依專案調整）
  3. 缺日期標頭 ——DATED_DIRS 底下每份都要有「最後更新」，否則無法判斷可信度
  4. 硬編數量   ——「共 N 份」這類會自己過期的寫法
  5. 殘留佔位符 ——部署訪談沒換掉的洞（2026-08-05 加入：原本是部署自檢清單上一個要人工 grep
                  的核取方塊，而人工核取方塊遲早會有人跳過；改由工具擋才會自動發生。這一項掃
                  PLACEHOLDER_GLOBS 的所有檔案，不只 .md——佔位符也會留在 tools/verify_state.py
                  這種非文件檔裡；比對的是 PLACEHOLDER_NAMES 這份封閉清單，不是雙大括號語法）
  6. 工作中欄位 ——HANDOFF.md 的「工作中」標記不見了（2026-10-30 加入：這個欄位是跨機器誤接棒
                  防呆的唯一依據，掉了不會有任何徵兆——下一棒只會看到一切正常然後接棒，正是
                  這套骨架最怕的靜默失效。而「欄位缺席」與「沒人在做」分不開，所以不接受
                  「沒寫就是沒人」：必須明確寫「無（已交棒）」。沒有 HANDOFF.md 的 repo 整項跳過）

問題以結束碼 2 回報，乾淨為 0。本工具唯讀，絕不修改任何檔案。

source: PROJECT-BOOTSTRAP.md v2026-10-30 — 權威版在部署包，改這裡之前先改部署包再同步各專案。
「專案設定」區塊以外的內容應與權威版一致；副本落後時用這一行辨識。
"""
import argparse
import pathlib
import re
import subprocess
import sys

# ── 專案設定（部署後依實際情況調整）────────────────────────────
# 過期字串：搬遷／改名後不該再出現的東西。留空 list 就跳過這項檢查。
STALE_PATTERNS = [
    # ('localhost:8080', '已遷到正式網域，文件不該再出現本機位址'),
]
# 這些關鍵字出現在同一行時視為「刻意保留的歷史敘述」，不報錯。
STALE_OK = ('已停用', '已退役', '歷史', '勿再啟動', '~~')
# 這些路徑整份豁免（例如保存歷史決策的文件、已退役的部署設定）。
STALE_OK_PATHS = ()
# 這些路徑下的 .md 必須在前 8 行有「最後更新」。比對的是路徑前綴，所以單一檔案也放得進來。
# ARCHITECT.md 在列，是因為它會被拿來「找檔案」：沒有日期就無法判斷這份結構圖是哪一天的事實，
# 而過期的結構圖比沒有更糟——照著它找不到檔案的人，通常不會回頭修文件。
DATED_DIRS = ('docs/ai-notes/', 'ARCHITECT.md')
# 連結檢查的豁免路徑。部署包內嵌各檔範本，範本裡的相對路徑是照「該範本部署後的位置」寫的
# （例如 docs/ai-notes/ 或 .agents/skills/<slug>/），用部署包自己的位置去解析必然解不到——
# 那是假警報，不是死連結。沒有這條，自檢清單第 1 項在刪掉部署包之前永遠不可能通過，
# 而部署者只會學到「這支腳本的 FAIL 可以無視」，之後真的死連結也跟著被無視。
LINK_OK_PATHS = ('PROJECT-BOOTSTRAP.md',)
# 佔位符檢查掃哪些檔（不只 .md：訪談要填的值也會落在 .gitignore 與 verify_state.py 裡）。
PLACEHOLDER_GLOBS = ('*.md', '*.py', '*.sh', '*.json', '.gitignore', '.gitattributes')
# 豁免路徑。部署包本身整份都是佔位符，還沒刪掉時不該報錯（自檢清單最後一項會叫你刪它）。
# 專案若真的有檔案會用到上面那些名字當樣板變數，把該檔或該目錄加進來。
PLACEHOLDER_OK_PATHS = ('PROJECT-BOOTSTRAP.md',)
# ── 專案設定結束 ──────────────────────────────────────────────
# 以上依專案調整，以下與權威版一致。`tools/sync_project.py` 升級本檔時，會把上面這一段
# 原樣留下、只換掉其餘部分——沒有這個標記它就得用啟發式猜邊界，而猜錯就是把專案自己的
# 過期字串規則與豁免路徑默默洗掉，然後沒有人會發現。

COUNT_RE = re.compile(r'(共|計|全)\s*\d+\s*(份|個|支|條)|\d+\s*份(?!量)')
COUNT_CONTEXT = ('份', '個檔', '支腳本', '知識庫')
# 部署訪談會填的佔位符（第 1 節那張表）。這裡刻意用「名字的封閉清單」而不是「任何雙大括號」
# 或「雙大括號＋全大寫」：專案自己的樣板語法長得一模一樣——verify_state.py 範本裡有 docker 的
# --format '{{ .Names }}'，也遇過專案拿同樣的大寫雙大括號寫法產 HTML——用語法比對兩者都會中。
# 骨架只會留下下面這幾個洞，列舉它們就抓得完，而且不可能誤傷別人的樣板。
# 部署包新增佔位符時要同步這份清單（verify_bootstrap.py 會比對，漏了會 FAIL）。
PLACEHOLDER_NAMES = (
    'PROJECT_NAME', 'ONELINER', 'GH_OWNER', 'GH_REPO', 'GH_VISIBILITY', 'LANG',
    'TZ', 'TODAY', 'SECRETS', 'RUNTIME_DIRS', 'STACK_DIRS', 'VERIFY_TARGETS',
)
PLACEHOLDER_RE = re.compile(r'\{\{(?:' + '|'.join(PLACEHOLDER_NAMES) + r')\}\}')


def tracked(*globs):
    # -z 不能拿掉：git ls-files 預設 core.quotepath=true，會把非 ASCII 檔名輸出成加了
    # 雙引號的八進位跳脫（"\350\256\200..."）。那串原封不動包成 Path，開檔必炸——Windows
    # 是 OSError errno 22、macOS／Linux 是 FileNotFoundError，兩邊都是 traceback 而不是
    # FAIL，接手的人很容易判成「環境或 Python 版本問題」而跳過驗證，正好繞開這套骨架
    # 唯一的文檔關卡。2026-08-05 實際部署時踩到（中文檔名的專案會一直踩）。
    # -z 另外連「檔名含換行」也一起擋掉，比 -c core.quotepath=false 更完整。
    out = subprocess.run(['git', 'ls-files', '-z', *globs],
                         capture_output=True, text=True, encoding='utf-8').stdout
    return [pathlib.Path(p) for p in out.split('\0') if p]


def tracked_md():
    return tracked('*.md')


def check_links(files):
    bad, total = [], 0
    for md in files:
        posix = md.as_posix()
        if any(posix == p or posix.startswith(p) for p in LINK_OK_PATHS):
            continue
        for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', md.read_text(encoding='utf-8')):
            link = m.group(2).split('#')[0].strip()
            if not link or link.startswith(('http://', 'https://', 'mailto:')):
                continue
            total += 1
            if not (md.parent / link).resolve().exists():
                bad.append(f'{md.as_posix()} -> {link}')
    return total, bad


def check_stale(files):
    bad = []
    if not STALE_PATTERNS:
        return bad
    for md in files:
        posix = md.as_posix()
        if any(posix.startswith(p) or posix == p for p in STALE_OK_PATHS):
            continue
        for n, line in enumerate(md.read_text(encoding='utf-8').split('\n'), 1):
            for pat, why in STALE_PATTERNS:
                if pat in line and not any(ok in line for ok in STALE_OK):
                    bad.append(f'{posix}:{n}  「{pat}」（{why}）  {line.strip()[:70]}')
    return bad


def check_dates(files):
    bad = []
    for md in files:
        if not any(md.as_posix().startswith(d) for d in DATED_DIRS):
            continue
        head = '\n'.join(md.read_text(encoding='utf-8').split('\n')[:8])
        if '最後更新' not in head:
            bad.append(f'{md.as_posix()}  前 8 行沒有「最後更新：YYYY-MM-DD」')
    return bad


def check_placeholders(files):
    bad = []
    for md in files:
        posix = md.as_posix()
        if any(posix == p or posix.startswith(p) for p in PLACEHOLDER_OK_PATHS):
            continue
        for n, line in enumerate(md.read_text(encoding='utf-8').split('\n'), 1):
            for m in PLACEHOLDER_RE.finditer(line):
                bad.append(f'{posix}:{n}  「{m.group(0)}」  {line.strip()[:70]}')
    return bad


def check_busy_field(files):
    # 第 6 項：HANDOFF.md 的「工作中」欄位必須在。這一欄是 handoff skill A2.5 判斷
    # 「同一條分支有沒有別台機器在做」的唯一依據，而它掉了不會有任何徵兆——下一棒
    # 只會看到一切正常然後接棒。不接受「沒寫就是沒人在做」：那和「忘了寫」分不開。
    found, bad = False, []
    for md in files:
        if md.as_posix() != 'HANDOFF.md':
            continue
        found = True
        if '**工作中**' not in md.read_text(encoding='utf-8'):
            bad.append('HANDOFF.md  「Git 狀態」缺「- **工作中**：無（已交棒）」欄位'
                       '——跨機器誤接棒防呆靠它（見 handoff skill 的 A2.5／A5／B6）')
    return found, bad


def check_counts(files):
    bad = []
    for md in files:
        for n, line in enumerate(md.read_text(encoding='utf-8').split('\n'), 1):
            if line.lstrip().startswith('>') and '最後更新' in line:
                continue
            m = COUNT_RE.search(line)
            if m and any(w in line for w in COUNT_CONTEXT):
                bad.append(f'{md.as_posix()}:{n}  「{m.group(0)}」 {line.strip()[:70]}')
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    files = tracked_md()
    if not files:
        print('找不到 tracked markdown——請在專案根目錄執行，且檔案已 git add')
        return 2

    problems = 0
    total, dead = check_links(files)
    if not args.quiet:
        print(f'[links]   檢查 {total} 個相對連結')
    if dead:
        problems += len(dead)
        print(f'[links]   🔴 {len(dead)} 個死連結：')
        for b in dead:
            print(f'            {b}')

    stale = check_stale(files)
    if stale:
        problems += len(stale)
        print(f'[stale]   🔴 {len(stale)} 處過期字串：')
        for b in stale:
            print(f'            {b}')

    undated = check_dates(files)
    if undated:
        problems += len(undated)
        print(f'[dates]   🔴 {len(undated)} 份缺「最後更新」標頭：')
        for b in undated:
            print(f'            {b}')
    elif not args.quiet:
        print('[dates]   受管目錄全部有「最後更新」標頭')

    left = check_placeholders(tracked(*PLACEHOLDER_GLOBS))
    if left:
        problems += len(left)
        print(f'[holes]   🔴 {len(left)} 處殘留佔位符（部署訪談沒填完，照文件做會失敗）：')
        for b in left:
            print(f'            {b}')
    elif not args.quiet:
        print('[holes]   沒有殘留的佔位符')

    found_handoff, busy = check_busy_field(files)
    if busy:
        problems += len(busy)
        print(f'[busy]    🔴 {len(busy)} 處「工作中」欄位問題：')
        for b in busy:
            print(f'            {b}')
    elif not args.quiet:
        print('[busy]    HANDOFF.md 的「工作中」欄位在位' if found_handoff
              else '[busy]    沒有 HANDOFF.md，跳過這一項')

    counts = check_counts(files)
    if counts:
        print(f'[counts]  🟡 {len(counts)} 處硬編數量（會自己過期，建議改成不寫數字）：')
        for b in counts:
            print(f'            {b}')

    print()
    if problems:
        print(f'FAIL：{problems} 個問題需修正（硬編數量僅提醒，不計入）')
        return 2
    print('OK：文檔一致性檢查通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
````

### 3.15 `tools/verify_state.py`（骨架，部署後填 CHECKS）

````python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一鍵現況查證（交接用）。把接手查證從 5+ 個 AI 回合壓到 1 個回合（省 token）。

用法（專案根目錄執行）：
  python -X utf8 tools/verify_state.py

輸出＝緊湊 key=value 事實快照；與 HANDOFF.md「服務查證與期望快照」區塊比對即完成查證。
腳本只印事實、不做判斷——期望值放 HANDOFF（會隨進度變），避免兩處維護。
缺少某一層憑證時印 SKIPPED，仍繼續查證其他可用層級。

source: PROJECT-BOOTSTRAP.md v2026-08-05 — 權威版在部署包，改這裡之前先改部署包再同步各專案。
本檔的 CHECKS 區塊本來就該逐專案填寫；其餘內容應與權威版一致。
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

# ── 專案設定（部署後填這裡）──────────────────────────────────
BASE = os.environ.get('PROJECT_BASE_URL', '')   # 例：https://example.com
SECRET_FILE = '.env'                            # 憑證來源檔
SECRET_KEY = 'API_KEY'                          # 檔內的變數名

# (顯示名稱, 相對路徑或完整 URL, 是否需要憑證)
HTTP_CHECKS = [
    # ('health', '/api/health', False),
]
# (顯示名稱, 命令 list)
CMD_CHECKS = [
    # ('containers', ['docker', 'ps', '--format', '{{ .Names }}']),
]


def read_secret():
    """從 SECRET_FILE 讀憑證；讀不到回 None（呼叫端標 SKIPPED，不得自行找憑證）。"""
    try:
        for line in open(SECRET_FILE, encoding='utf-8'):
            if line.startswith(SECRET_KEY + '='):
                return line.split('=', 1)[1].strip()
    except OSError:
        pass
    return None


def http(name, path, key):
    url = path if path.startswith('http') else BASE.rstrip('/') + path
    req = urllib.request.Request(url)
    if key:
        req.add_header('Authorization', f'Bearer {key}')
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(4000).decode('utf-8', 'replace')
            try:
                data = json.loads(body)
                brief = str(len(data)) + ' items' if isinstance(data, list) else 'json ok'
            except json.JSONDecodeError:
                brief = f'{len(body)} bytes'
            print(f'{name}=OK http={r.status} {brief}')
    except urllib.error.HTTPError as e:
        print(f'{name}=FAIL http={e.code}')
    except Exception as e:                      # 連線層錯誤：印事實，不下「未配置」結論
        print(f'{name}=ERROR {type(e).__name__}: {e}')


def cmd(name, argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        out = ' | '.join(l.strip() for l in p.stdout.strip().split('\n') if l.strip())
        print(f'{name}=rc{p.returncode} {out[:300] or p.stderr.strip()[:200]}')
    except FileNotFoundError:
        print(f'{name}=SKIPPED（本機沒有 {argv[0]}）')
    except Exception as e:
        print(f'{name}=ERROR {type(e).__name__}: {e}')


def main():
    if not HTTP_CHECKS and not CMD_CHECKS:
        print('verify_state=NOT_CONFIGURED（尚未填 HTTP_CHECKS／CMD_CHECKS，見本檔頂端）')
        return 0

    key = read_secret()
    for name, path, need_key in HTTP_CHECKS:
        if need_key and not key:
            print(f'{name}=SKIPPED（{SECRET_FILE} 沒有 {SECRET_KEY}——先確認是不是設定沒帶到，再下結論）')
            continue
        if not BASE and not path.startswith('http'):
            print(f'{name}=SKIPPED（未設 PROJECT_BASE_URL）')
            continue
        http(name, path, key if need_key else None)

    for name, argv in CMD_CHECKS:
        cmd(name, argv)
    return 0


if __name__ == '__main__':
    sys.exit(main())
````

### 3.16 `.agents/skills/handoff/SKILL.md`（給 Antigravity 的指標）

> Antigravity 原生辨識專案根目錄的 `.agents/`（`.agents/skills/`、`.agents/workflows/`）。這裡放**指標**而不是內容——複製一份程序在這裡，兩份就會各自演化，最後一份說要先 fetch、另一份沒說。
> 只用得到 Claude Code 與 Codex 的專案可以不建這個檔；建了也不影響其他工具。

````markdown
---
name: handoff
description: Pointer to the authoritative handoff procedure in .claude/skills/. 接棒／交棒／跨機器同步的固定程序。
---

<!-- source: PROJECT-BOOTSTRAP.md v2026-08-05 — 本檔只是指標，改內容請改權威版 -->

# 本檔只是指標，請讀權威版

**權威版：[`.claude/skills/handoff/SKILL.md`](../../../.claude/skills/handoff/SKILL.md)**

那份是純 Markdown，路徑掛在 `.claude/` 下只是因為 Claude Code 會自動載入該位置，內容不限任何工具。

**請勿在此複製內容。** 兩份副本會各自演進並產生矛盾（曾發生：一份已更新成新流程、另一份停在舊版，而入口文件指向舊的那份，照做就失敗）。新知識一律寫進權威版。
````

### 3.17 `.codex/hooks.json`（給 Codex 的 hook 接線）

> **只有 Codex CLI 用得到這個檔；桌面 App 沒有 hooks**（2026-08-06 實測 App `26.721.41059`，`/hooks` 指令不存在）。App 請改走下一節的全域 skill。建了不會有害，但別以為 App 上會生效。
> CLI 的 hooks 與 Claude Code **同格式、同語意**：讀 `<repo>/.codex/hooks.json`，context 由 stdin 傳 JSON，exit 2 ＝擋下並把 stderr 交給模型。所以這裡掛的是**同樣那兩個 `.sh`**，不要另外複製一份到 `.codex/hooks/`。
> **路徑一律相對**——寫成 `C:\Users\...` 的絕對路徑，換到另一台機器或 macOS 必定失效，而且失效時是靜默的。
> 首次使用要在 CLI 打 `/hooks` 信任這份定義（Codex 用定義的雜湊記錄信任，改過內容要重新信任）。

````json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/git-freshness.sh",
            "timeout": 30,
            "statusMessage": "檢查 git 是否與 origin 同步…"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre-push-handoff.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
````

### 3.18 其他 skills 慣例（有需要時才建，不要空建）

當某個操作**做過兩次以上、而且有踩過坑**（API 呼叫順序、部署步驟、前端框架陷阱），就把它寫成 skill：

- **權威版放 `.claude/skills/<slug>/SKILL.md`**（Claude Code 會自動載入這個路徑，內容必須實體存在那裡）。
- 若也想讓其他工具找到，在 `.agents/skills/<slug>/SKILL.md` 放**指標**，不要複製內容。

SKILL.md 開頭固定 frontmatter：

````markdown
---
name: <slug>
description: <什麼情況該讀這份，寫清楚觸發時機——這行決定模型會不會載入它>
---

# <標題>

（實測過的步驟與指令，附日期與踩坑理由）
````

指標檔內容：

````markdown
---
name: <slug>
description: Pointer to the authoritative copy in .claude/skills/. <一句話說明用途>
---

# 本檔只是指標，請讀權威版

**權威版：[`.claude/skills/<slug>/SKILL.md`](../../../.claude/skills/<slug>/SKILL.md)**

**請勿在此複製內容。** 兩份副本會各自演進並產生矛盾（曾發生：一份已更新成新網址、另一份停在舊位址，而入口文件指向舊的那份，照抄就失敗）。新知識一律寫進權威版。
````

---

## 4. 上 GitHub

```bash
git init -b main
```

先確認 `.gitignore` 已就位再 `git add`（**順序不可反**，不然祕密會進第一個 commit）：

```bash
git status --porcelain
```

確認清單裡沒有憑證／運行資料後：

```bash
git add . && git diff --cached --name-only
```

再次確認清單乾淨，然後提交並建 repo（需先裝好 `gh` 並登入）：

```bash
git commit -m "chore: bootstrap project management skeleton"
```

```bash
gh repo create {{GH_OWNER}}/{{GH_REPO}} --{{GH_VISIBILITY}} --source=. --remote=origin --push
```

沒有 `gh` 就到 GitHub 網頁開一個空 repo，然後：

```bash
git remote add origin https://github.com/{{GH_OWNER}}/{{GH_REPO}}.git && git push -u origin main
```

最後確認 upstream 有對齊（hook 需要 upstream 才能比對）：

```bash
git status -sb
```

---

## 5. 部署後自檢清單

逐項確認，全過才算部署完成：

- [ ] `python -X utf8 tools/check_docs.py` → `OK`（一次涵蓋死連結與**殘留佔位符**；佔位符那一項掃 `.md`／`.py`／`.sh`／`.json`／`.gitignore`／`.gitattributes` 的 tracked 檔，所以要先 `git add`。本部署包自己被豁免——照最後一項刪掉它就好）
- [ ] `python -X utf8 tools/verify_state.py` → 可執行（尚未填檢查項時印 `NOT_CONFIGURED`，正常）
- [ ] `bash .claude/hooks/git-freshness.sh` → 印出 `✅ 本機沒落後 origin`，且最後一行有 `[handoff]` 提醒（沒有 upstream 會印警告，表示第 4 節沒做完）
- [ ] **工作中標記防呆**：把 `HANDOFF.md` 的「工作中」改成一個假的別台機器名，commit、push，再跑 `bash .claude/hooks/git-freshness.sh` → 要印 🔴 並叫你走 A2.5；改回「無（已交棒）」、commit、push 後再跑 → 不該再印。**驗完記得改回來**
- [ ] **骨架版本偵測**：`printf 1999-01-01 > .claude/.bootstrap-version && bash .claude/hooks/git-freshness.sh` → 要印 🟡「handoff 骨架落後」。**驗完刪掉那個快取檔**（`rm .claude/.bootstrap-version`），否則 12 小時內都會拿到假答案
- [ ] `.claude/skills/handoff/SKILL.md` 存在，前三行是 `---` / `name: handoff` / `description: ...`（frontmatter 壞掉 skill 就不會被載入）
- [ ] `ARCHITECT.md` 存在且有「最後更新」標頭（`check_docs.py` 會擋），「專案本體」那節寫的是**實況**——還沒有程式碼就照實寫，不要先畫一個想像中的架構
- [ ] 在 Claude Code 打 `/handoff` 看得到這個 skill
- [ ] pre-push hook 會放行無關指令：`echo '{"tool_input":{"command":"git status"}}' | bash .claude/hooks/pre-push-handoff.sh; echo $?` → `0`
- [ ] `git log --stat -1` 確認第一個 commit **沒有**含憑證或運行資料
- [ ] 關掉 session 重開一次，確認 hook 在對話開頭自動跑

**跨工具（只驗你真的會用的那幾個，用不到的不必建檔）**

- [ ] **可攜層**：`AGENTS.md` 開頭有「開工第一件事」那一段，而且指到的路徑存在——**這一項不能跳過**，它是唯一在所有工具上都成立的保證，其餘都只是輔助
- [ ] **Codex CLI**：`.codex/hooks.json` 存在且路徑全是相對路徑（`grep -n ':[\\/]' .codex/hooks.json` 應無輸出——絕對路徑在別台機器會靜默失效）；打 `/hooks` 信任該定義後，開一個 session 確認 `[git-check]` 有出現
- [ ] **Codex 桌面 App**：`/hooks` 打不出來是正常的（App 沒有 hooks）。改為把 `.claude/skills/handoff/SKILL.md` 複製到 `~/.codex/skills/handoff/SKILL.md`，重開 session 後問「你有哪些 skill 可以用」，看得到 `handoff` 就成了
- [ ] **Antigravity**：`.agents/skills/handoff/SKILL.md` 存在，且內容只有指標、沒有複製程序內容。它 2026-10-30 起也支援 `.agents/hooks.json` 的 `SessionStart`，但骨架**刻意沒附範本**（理由見開頭「跨工具與跨平台」）——要自己接就先實測相對路徑怎麼解析、以及 `echo` 的文字有沒有被顯示出來
- [ ] **共通的真正驗收**（不論哪個工具）：在專案裡講一句「我要接手這個專案」，agent 應該先 `git fetch`、讀 `AGENTS.md` ＋ `HANDOFF.md`，回報 3–5 行才動手。它直接開始翻程式碼就是沒接上——改用明講版：「請先讀 `.claude/skills/handoff/SKILL.md`，照 A 模式接棒」
- [ ] **另一台機器**：clone 後重跑上面「python 可執行」與「hook 自動跑」兩項。`python` 不存在就用 `python3`；Windows 需要 Git for Windows 附的 bash
- [ ] `HANDOFF.md` 的「本機能力」已填實際狀況
- [ ] 刪掉 `PROJECT-BOOTSTRAP.md`，以及用壓縮檔部署時附的 `讀我-先看這個.md`。前者的內容已分散進 AGENTS.md／handover-protocol.md，留著就是第二份會腐化的副本；後者的內容在部署完成的當下就是假的（它寫著「檔案都在，但裡面還有佔位符沒填」），下一棒讀到會以為部署沒做完而重跑一次訪談

---

## 6. 之後怎麼維持（一頁操作卡）

**每次開工／收工**：直接 `/handoff`（Claude Code），或用 README「換一個 AI 接手工作」的 prompt B（接棒）／A（交棒）指路給其他模型。順序永遠是先 A 後 B。

**改到 skill 或 hook 時**：權威版在本部署包 → 改這裡 → 覆蓋各專案 `.claude/skills/handoff/SKILL.md`（與選用的全域副本）→ 檔頭 `source:` 標記跳版。

標記的格式是 **`v<日期>`，同一天改第二次起在日期後面加序號**（`v2026-10-24.2`、`.3`），當天第一次不加。序號算的是**部署包當天的第幾次修改**（跟本檔開頭的「版本」行同一個號），不是單一檔案的——標記寫的本來就是「這份副本來自部署包的哪一版」。2026-10-24 那天這份 skill 改了三次，三次的標記卻都是 `v2026-10-24`——副本明明落後，標記顯示一樣新，於是把「舊版 session 名稱少一個全形空格」誤判成同步漏掉，白查一輪。日期粒度只能證明「不早於那一天」，證明不了最新。

沒改內容的檔案不要跟著跳版——謊報一次「副本落後」之後，這個標記就沒人再信。

**新知識該寫哪一份**：

| 你剛剛得到什麼 | 寫進 |
|---|---|
| 一條「以後都要這樣做」的規則、一次踩坑 | `AGENTS.md` 鐵律（重大）或 `docs/ai-notes/<主題>.md`（細節），**附絕對日期** |
| 某個操作的可重複步驟（做過兩次以上） | `.claude/skills/<slug>/SKILL.md` |
| 「東西搬家了」「多了一個元件」「權威版換位置了」 | `ARCHITECT.md`，**跟該變動同一個 commit** |
| 「還有哪些事沒做」「這件事被否決了」 | `docs/ai-notes/roadmap.md` |
| 「現在做到哪、下一步」 | `HANDOFF.md`（覆寫，不累積） |
| 給人看的入口、網址、怎麼跑起來 | `README.md` |

**開新的 ai-notes 檔案時**：回頭把 `AGENTS.md` 的「知識庫地圖」補上一列，否則沒人會找到它。

**已知的腐化模式與對策**：

| 症狀 | 對策 |
|---|---|
| HANDOFF 超過 80 行 | 把持久內容搬進 ai-notes，只留當下狀態 |
| 同一件事在兩份文件都寫了 | 留一份權威版，另一份改成指標並說明為什麼（避免下一棒又複製回去） |
| `ARCHITECT.md` 開始出現「正在做 X」「預計改成 Y」 | 那是 HANDOFF 與 roadmap 的內容，搬走；本檔只寫現在的結構 |
| 文件寫「共 N 份」「目前 12 個」 | `check_docs.py` 會提醒；改成不寫數字 |
| 換了網址／改了名稱 | 把舊值加進 `check_docs.py` 的 `STALE_PATTERNS`，讓工具替你抓殘留 |
| 兩台機器同時動 main | 恢復 single writer；分岔了就先整合，**禁止 force push** |
