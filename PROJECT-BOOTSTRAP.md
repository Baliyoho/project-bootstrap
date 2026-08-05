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
> 版本：**2026-08-05**（加入 `handoff` skill——把交接協定變成 agent 會自己執行的程序，補 push 前防呆 hook，並把「殘留佔位符」從人工核取方塊改成 `check_docs.py` 的第 5 項檢查）。
> 萃取自「台大地理系案件審核工作流」與「NAA_TR」兩個專案實際運行的制度。

## 交接自動化怎麼運作（本骨架的核心）

制度寫成文件，agent 不一定會照做。本骨架用三層讓它**自動發生**：

| 層 | 檔案 | 什麼時候動 |
|---|---|---|
| **觸發** | `.claude/hooks/git-freshness.sh`（SessionStart hook） | 每次 session 開始自動 fetch、報告落後／分岔，並提醒「接棒先走 handoff skill」 |
| **程序** | `.claude/skills/handoff/SKILL.md` | agent 判斷要接棒／交棒／同步時自動載入；使用者也可打 `/handoff` 直接叫它 |
| **防呆** | `.claude/hooks/pre-push-handoff.sh`（PreToolUse hook） | 要推到權威分支、但這批 commit 沒更新 `HANDOFF.md` 時擋下，要求先走交棒程序 |

**分工**：`docs/ai-notes/handover-protocol.md`＝**規則與理由**（為什麼、什麼算對）；skill＝**怎麼做**（指令、判讀表、模板）。
兩者衝突以協定為準。這樣才不會變成「同一套程序有兩份會各自演化的副本」。

## 跨工具與跨平台（2026-08-05 查證）

**把三層拆成兩種可靠度**，不要假設哪個工具一定有自動化：

- **可攜層——到哪都成立**：`AGENTS.md`（Claude Code／Codex／Antigravity 都原生讀）＋ 純 Markdown 的程序檔。就算一個 hook 都沒掛，agent 讀 `AGENTS.md` 開頭那段就知道要先走交接程序。**正確性靠這一層，不靠 hook。**
- **工具層——有就更省事**：hooks。它只是讓人不必記得，不是制度成立的前提。

| | Claude Code | Codex | Antigravity |
|---|---|---|---|
| 讀 `AGENTS.md` | ✅ 經 `CLAUDE.md` 指標 | ✅ 原生 | ✅ 原生（`AGENTS.md` 優先於 `GEMINI.md`） |
| 自動載入程序檔 | ✅ `.claude/skills/`，可打 `/handoff` | ⬜ 無 skill 機制，靠 `AGENTS.md` 指路 | ✅ 原生讀 `.agents/skills/` |
| Hooks | ✅ `.claude/settings.json` | ✅ `<repo>/.codex/hooks.json`，**同格式、同語意**（stdin 收 JSON、exit 2 擋下並把 stderr 交給模型）；首次需在 CLI 打 `/hooks` 信任該定義 | ❌ 沒有 hook 機制 |
| Windows | ✅ | ✅（Codex 另支援 `commandWindows` 做平台覆寫） | ✅ |

因為 Codex 的 hook 格式與 Claude Code 相同，**兩邊掛的是同樣那兩個 `.sh` 檔**，不要各複製一份——那正是「同一個事實有多個家」的起點。

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
| 還有哪些事沒做（持久待辦、相依、優先序） | [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md) |
| <新主題> | <新增 docs/ai-notes/xxx.md 後，回來把這一列補上> |

`.claude/skills/` 資料夾雖然掛在 Claude 的路徑下，內容是純 Markdown，**任何模型都應直接讀取**。
`.agents/skills/` 下的同名檔案只是給 Antigravity 這類原生讀 `.agents/` 的工具用的**指標**，內容不重複——看到指標請回頭讀 `.claude/skills/` 的權威版。

## 跨模型／跨機器協作規範

1. **先同步 Git，再相信本機文件**：開工先 `git status -sb`、`git fetch origin`。異常（dirty／diverged／遠端意外前進）一律停在安全點，禁止 `reset --hard`、force push 或覆寫。
2. **single writer**：同一時間只讓一個 agent／一台機器修改 `main` 與 `HANDOFF.md`。非小型工作走 `feature/<ID>-<slug>`；未完成分支不得偷塞進 main。
3. **知識寫進 repo，不留在私有記憶。** 踩到新坑、確立新流程、改了 schema——當場更新 `docs/ai-notes/` 或對應 SKILL.md，並附**絕對日期**。私有記憶只放「先讀 AGENTS.md」這類指標與個人偏好。
4. **文件與現實衝突時，以實況為準**（安全唯讀查證），就地修正文件並註記日期。該機器缺憑證時只能明記 SKIPPED，**不得自行挖憑證**。
5. **不要重複造文件——每個事實只有一個家。** 設計與決策寫 `docs/ai-notes/`；操作步驟寫對應的部署／應用目錄；狀態寫 `roadmap.md`（持久）與 `HANDOFF.md`（當下）。其他地方只放指標。新知識歸入現有檔案，只有全新主題才開新檔並更新上方地圖。

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

### 3.5 `docs/ai-notes/handover-protocol.md`

````markdown
# 交接協定（跨 session／agent／機器通用）

> 適用於同一模型換 session、跨模型、跨日及跨機器續作。
> 建立：{{TODAY}}。最後更新：{{TODAY}}。
>
> **本檔＝規則與判準**（為什麼這樣做、什麼算做對）。**可執行程序**（指令序列、Git 判讀表、HANDOFF 模板）在 [handoff skill](../../.claude/skills/handoff/SKILL.md)，不在此重複——那是唯一該照著做的一份。兩者衝突時**以本檔為準**，並就地修正 skill。

## 三層分工

| 層 | 放哪裡 | 性質 |
|---|---|---|
| 持久知識 | `AGENTS.md`、`docs/ai-notes/`、skills | 三個月後仍成立的鐵律、schema、流程、踩坑 |
| 當下狀態 | `HANDOFF.md` | 單一、精簡、只描述目前做到哪與下一步 |
| 傳輸／歷史 | {{GH_VISIBILITY}} GitHub `{{GH_OWNER}}/{{GH_REPO}}` | source/docs 的跨機器同步與版本史；**不是**資料備份 |

持久知識不要塞進 HANDOFF；HANDOFF 不累積歷史，舊版由 Git history 查。{{SECRETS}}、{{RUNTIME_DIRS}} 永遠不進 Git。

---

## 一、接棒（順序不可反）

> **自動防呆有兩層**（都只是保險，下面每一步仍必做——離線、非 Claude 端或設定沒載入時 hook 不會跑）：
> ① SessionStart hook（`.claude/hooks/git-freshness.sh`）：session 開始自動 fetch，注入落後／分岔／未推送警告，並提醒走 handoff skill。
> ② PreToolUse hook（`.claude/hooks/pre-push-handoff.sh`）：要推到權威分支、但這批 commit 沒更新 `HANDOFF.md` 時擋下（`HANDOFF_HOOK=off` 可停用）。

1. **先同步 Git**：**未同步前不要相信本機 HANDOFF。** 工作樹乾淨、有 upstream 且能 fast-forward 才可自行往下走（指令與完整判讀表見 skill A1）。
2. **確認你該站在哪條分支**：讀 HANDOFF 的「待續分支」。**若它指向 feature branch，該分支才是主幹**——`main` 可能明顯落後。不要因為 `main` 是預設分支就以為它最新。
3. **異常就停在安全點**：未知 dirty changes、diverged、遠端意外前進或 pull 不能 fast-forward 時，**禁止** `reset --hard`、force push、自動 stash 或覆寫。先辨認變更來源並回報。
4. **最小讀取**：只讀 `AGENTS.md` ＋ `HANDOFF.md`。其他知識庫依實際任務 lazy load。
5. **一鍵驗證**：有憑證就跑 `tools/verify_state.py`，與 HANDOFF 的期望快照比對；不一致以實況為準（見 skill A4）。
6. **3–5 行回報後動手**：Git 狀態、驗證結果、理解的現況與下一步。不要重述整份 HANDOFF。

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

## HANDOFF.md 模板

**模板在 [handoff skill](../../.claude/skills/handoff/SKILL.md) 的 B6**——模板是交棒時照填的東西＝程序，本檔只定義它必須包含什麼：
交接時間與交棒者、任務目標、Git 狀態（含待續分支與本機憑證能力）、已完成、未完成／下一步、地雷、服務查證快照、懸置事項。
≤80 行、覆寫不累積、**不寫自己的最終 commit hash**。

## 標準 prompt

**prompt A（交棒）／B（接棒）的正本在 [README.md](../../README.md)「換一個 AI 接手工作」**——那兩段是**人**要複製貼上的東西，家應該在人看的 README，不該在 AI 讀的協定裡各存一份。
本檔負責定義規則，README 負責提供可直接使用的指令。
````

### 3.6 `docs/ai-notes/roadmap.md`

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

### 3.7 `.claude/skills/handoff/SKILL.md`（交接程序，本骨架的核心）

> **這一份就是「教 agent 自動交接同步」的東西。** 內容照抄不要改，包含檔頭的 `source:` 版本標記——它讓你日後能一眼看出某個專案的副本是不是落後了。
> 檔案裡的 `docs/ai-notes/handover-protocol.md` 刻意寫成純路徑而非連結，這樣同一份文字放進全域 `~/.claude/skills/` 也不會產生死連結。

````markdown
---
name: handoff
description: 接棒／交棒／跨機器同步的固定程序（Git 同步判讀、站對分支、驗證、寫 HANDOFF、安全提交與 push）。Use at the start of a work session in a repo that has AGENTS.md/HANDOFF.md, when picking up where a previous session, model, or machine left off, when wrapping up or handing work over, when syncing mid-session, and before any git push. Triggers on 接手、接棒、交棒、收工、換機器、換模型、同步進度、繼續上次的工作、handoff、hand off、pick up where we left off、resume work。
---

<!-- source: PROJECT-BOOTSTRAP.md v2026-08-05 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 交接與同步程序（可執行）

> **本檔＝程序**：做什麼、下哪些指令、什麼時候必須停下來問人。
> **規則與理由**（三層分工、分支模型、SKIPPED 判準、事故史）在 `docs/ai-notes/handover-protocol.md`。兩者衝突時**以協定為準**，並就地修正本檔。
> 純 Markdown，任何模型（Claude／Gemini／Codex）都應直接讀取，不限某一家工具。

## 適用判斷（先做這一步）

專案根目錄有 `AGENTS.md` 與 `HANDOFF.md` → 適用，往下走。
**沒有** → 本程序不適用，不要憑空建立交接檔案；直接做使用者要的事，或問他要不要導入這套制度。

專案沒有 `tools/verify_state.py`／`tools/check_docs.py` 也能用：對應步驟改為「跳過並在回報寫明沒有該工具」，**不要自己發明驗證**。

## 0. 判斷模式

| 情況 | 模式 |
|---|---|
| session 剛開始／要續作／換機器／換模型 | **A 接棒** |
| 工作告一段落、要收工或換人接手 | **B 交棒** |
| 工作中想拉最新或推一個安全點，還沒要交棒 | **C 同步** |
| 準備 `git push` | 先做 **B**——push 是交棒的最後一步，不是獨立動作 |

不確定就走 A。**A 沒跑完之前不要修改任何檔案。**

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

---

## C. 中途同步（還沒要交棒）

- 拉最新：照 A1 判讀表走，異常一樣停。
- 推安全點：B7 → B8（可略過 B6；但這批 commit 若會被別人或別台機器看到，仍要在 HANDOFF 補一句現況）。
- **換機器前一定要 push，下一台機器一定要先 fetch。**
- **single writer**：同一時間只有一個 agent／一台機器可以改 `main` 與 `HANDOFF.md`。要換手就先交棒。

---

## 必須停下來問使用者（不得自行決定）

- Git 異常：dirty 來源不明、diverged、不能 fast-forward、遠端意外前進、沒有 upstream
- `push --force`、`reset --hard`、刪分支、改寫歷史
- 功能分支要併進 `main`（需使用者驗收；文件／基建分支驗證過可自己併）
- 憑證缺失，或需要跨機器搬憑證
- HANDOFF 沒授權的破壞性操作（刪檔、批次改資料、改 schema）

## 反例（真的發生過，別重演）

- ❌ 開工沒 fetch，對著落後數十個 commit 的本機 HANDOFF 工作數小時 → 分岔，收拾一整天。
- ❌ 連線失敗直接寫「本機未配置」→ 其實只是金鑰環境變數沒設，結論全錯。
- ❌ 純文件修正卡在功能分支等驗收 → 接手者同步 `main` 拿到過期文檔集。
- ❌ 知識寫在對話裡或私有記憶 → 換模型、換機器後全部消失。
- ❌ HANDOFF 愈疊愈長變成日誌 → 接手者要讀 20 分鐘才知道現在做到哪。
- ❌ push 完才想起沒更新 HANDOFF → 下一棒拿到過期狀態（pre-push hook 會擋，但別靠它）。
````

**同步規則（重要）**：這份 SKILL.md 會同時存在於 ①本部署包 ②每個專案的 `.claude/skills/handoff/` ③（選用）全域 `~/.claude/skills/handoff/`。
**權威版是本部署包**；要改就改這裡，再覆蓋下去，不要在單一專案裡就地改——那正是「同一個事實有多個家」的典型失控起點。

### 3.8 `.claude/settings.json`

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
        "matcher": "Bash",
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

> Codex 的接線見 3.16——它掛的是**同樣這兩個 `.sh`**，不要複製第二份腳本進 `.codex/`。兩份各自演化就會出現「Claude 端會擋、Codex 端不會擋」的不對稱。

### 3.9 `.claude/hooks/git-freshness.sh`

> Windows 需要 Git for Windows 附的 bash（Claude Code 內建可用）。建立後在 macOS／Linux 上加執行權限：`chmod +x .claude/hooks/git-freshness.sh`。

````bash
#!/usr/bin/env bash
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
  echo "[git-check] ✅ 與 origin 同步（branch=$branch）。"
fi
if [ "$dirty" -gt 0 ]; then
  echo "[git-check] 🟡 工作區有 $dirty 個未提交變更（可能是上一棒未收斂，先辨認來源再動）。"
fi
if [ -f .claude/skills/handoff/SKILL.md ]; then
  echo "[handoff] 本專案有交接制度：接棒先走 handoff skill 的 A 模式（.claude/skills/handoff/SKILL.md）——同步 Git、站對分支、只讀 AGENTS.md＋HANDOFF.md，回報 3–5 行後再動手；收工走 B 模式。"
fi
exit 0
````

### 3.10 `.claude/hooks/pre-push-handoff.sh`（push 前防呆）

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
# 權威版在 PROJECT-BOOTSTRAP.md，改這裡之前先改部署包。

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

### 3.11 `.gitignore`

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
__pycache__/
*.py[cod]
*.log

# Operating-system metadata
.DS_Store
Thumbs.db
````

> 依訪談把 `{{SECRETS}}`／`{{RUNTIME_DIRS}}` 補進去，再加語言／框架專屬項目（`node_modules/`、`.venv/`、`dist/`、`.build/` …）。**寧可多擋不要少擋。**

### 3.12 `.gitattributes`

````gitattributes
# Keep source and documentation consistent across Windows and macOS.
* text=auto eol=lf
*.bat text eol=crlf
````

### 3.13 `tools/check_docs.py`

````python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文檔一致性檢查（交接用）。verify_state.py 查「服務現況」，本腳本查「文件本身」。

用法（專案根目錄執行）：
  python -X utf8 tools/check_docs.py           # 全部檢查
  python -X utf8 tools/check_docs.py --quiet   # 只印問題與結論

檢查五項（都是實際發生過的腐化模式）：
  1. 死連結     ——markdown 相對連結指向不存在的檔案（整併文件時最常見）
  2. 過期字串   ——換了網址／改了名稱後殘留的舊值（見下方 STALE_PATTERNS，依專案調整）
  3. 缺日期標頭 ——DATED_DIRS 底下每份都要有「最後更新」，否則無法判斷可信度
  4. 硬編數量   ——「共 N 份」這類會自己過期的寫法
  5. 殘留佔位符 ——部署訪談沒換掉的洞（2026-08-05 加入：原本是部署自檢清單上一個要人工 grep
                  的核取方塊，而人工核取方塊遲早會有人跳過；改由工具擋才會自動發生。這一項掃
                  PLACEHOLDER_GLOBS 的所有檔案，不只 .md——佔位符也會留在 tools/verify_state.py
                  這種非文件檔裡；比對的是 PLACEHOLDER_NAMES 這份封閉清單，不是雙大括號語法）

問題以結束碼 2 回報，乾淨為 0。本工具唯讀，絕不修改任何檔案。

source: PROJECT-BOOTSTRAP.md v2026-08-05 — 權威版在部署包，改這裡之前先改部署包再同步各專案。
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
# 這些目錄下的 .md 必須在前 8 行有「最後更新」。
DATED_DIRS = ('docs/ai-notes/',)
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

### 3.14 `tools/verify_state.py`（骨架，部署後填 CHECKS）

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

### 3.15 `.agents/skills/handoff/SKILL.md`（給 Antigravity 的指標）

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

### 3.16 `.codex/hooks.json`（給 Codex 的 hook 接線）

> Codex 的 hooks 與 Claude Code **同格式、同語意**：讀 `<repo>/.codex/hooks.json`，context 由 stdin 傳 JSON，exit 2 ＝擋下並把 stderr 交給模型。所以這裡掛的是**同樣那兩個 `.sh`**，不要另外複製一份到 `.codex/hooks/`。
> **路徑一律相對**——寫成 `C:\Users\...` 的絕對路徑，換到另一台機器或 macOS 必定失效，而且失效時是靜默的。
> 首次使用要在 Codex CLI 打 `/hooks` 信任這份定義（Codex 用定義的雜湊記錄信任，改過內容要重新信任）。沒有用 Codex 的專案不建這個檔即可。

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

### 3.17 其他 skills 慣例（有需要時才建，不要空建）

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
- [ ] `bash .claude/hooks/git-freshness.sh` → 印出 `✅ 與 origin 同步`，且第二行有 `[handoff]` 提醒（沒有 upstream 會印警告，表示第 4 節沒做完）
- [ ] `.claude/skills/handoff/SKILL.md` 存在，前三行是 `---` / `name: handoff` / `description: ...`（frontmatter 壞掉 skill 就不會被載入）
- [ ] 在 Claude Code 打 `/handoff` 看得到這個 skill
- [ ] pre-push hook 會放行無關指令：`echo '{"tool_input":{"command":"git status"}}' | bash .claude/hooks/pre-push-handoff.sh; echo $?` → `0`
- [ ] `git log --stat -1` 確認第一個 commit **沒有**含憑證或運行資料
- [ ] 關掉 session 重開一次，確認 hook 在對話開頭自動跑

**跨工具（只驗你真的會用的那幾個，用不到的不必建檔）**

- [ ] **可攜層**：`AGENTS.md` 開頭有「開工第一件事」那一段，而且指到的路徑存在——**這一項不能跳過**，它是唯一在所有工具上都成立的保證，其餘都只是輔助
- [ ] **Codex**：`.codex/hooks.json` 存在且路徑全是相對路徑（`grep -n ':[\\/]' .codex/hooks.json` 應無輸出——絕對路徑在別台機器會靜默失效）；在 Codex CLI 打 `/hooks` 信任該定義後，開一個 session 確認 `[git-check]` 有出現
- [ ] **Antigravity**：`.agents/skills/handoff/SKILL.md` 存在，且內容只有指標、沒有複製程序內容
- [ ] **另一台機器**：clone 後重跑上面「python 可執行」與「hook 自動跑」兩項。`python` 不存在就用 `python3`；Windows 需要 Git for Windows 附的 bash
- [ ] `HANDOFF.md` 的「本機能力」已填實際狀況
- [ ] 刪掉 `PROJECT-BOOTSTRAP.md`，以及用壓縮檔部署時附的 `讀我-先看這個.md`。前者的內容已分散進 AGENTS.md／handover-protocol.md，留著就是第二份會腐化的副本；後者的內容在部署完成的當下就是假的（它寫著「檔案都在，但裡面還有佔位符沒填」），下一棒讀到會以為部署沒做完而重跑一次訪談

---

## 6. 之後怎麼維持（一頁操作卡）

**每次開工／收工**：直接 `/handoff`（Claude Code），或用 README「換一個 AI 接手工作」的 prompt B（接棒）／A（交棒）指路給其他模型。順序永遠是先 A 後 B。

**改到 skill 或 hook 時**：權威版在本部署包 → 改這裡 → 覆蓋各專案 `.claude/skills/handoff/SKILL.md`（與選用的全域副本）→ 檔頭 `source:` 標記換版本日期。副本落後時用標記就能認出來。

**新知識該寫哪一份**：

| 你剛剛得到什麼 | 寫進 |
|---|---|
| 一條「以後都要這樣做」的規則、一次踩坑 | `AGENTS.md` 鐵律（重大）或 `docs/ai-notes/<主題>.md`（細節），**附絕對日期** |
| 某個操作的可重複步驟（做過兩次以上） | `.claude/skills/<slug>/SKILL.md` |
| 「還有哪些事沒做」「這件事被否決了」 | `docs/ai-notes/roadmap.md` |
| 「現在做到哪、下一步」 | `HANDOFF.md`（覆寫，不累積） |
| 給人看的入口、網址、怎麼跑起來 | `README.md` |

**開新的 ai-notes 檔案時**：回頭把 `AGENTS.md` 的「知識庫地圖」補上一列，否則沒人會找到它。

**已知的腐化模式與對策**：

| 症狀 | 對策 |
|---|---|
| HANDOFF 超過 80 行 | 把持久內容搬進 ai-notes，只留當下狀態 |
| 同一件事在兩份文件都寫了 | 留一份權威版，另一份改成指標並說明為什麼（避免下一棒又複製回去） |
| 文件寫「共 N 份」「目前 12 個」 | `check_docs.py` 會提醒；改成不寫數字 |
| 換了網址／改了名稱 | 把舊值加進 `check_docs.py` 的 `STALE_PATTERNS`，讓工具替你抓殘留 |
| 兩台機器同時動 main | 恢復 single writer；分岔了就先整合，**禁止 force push** |
