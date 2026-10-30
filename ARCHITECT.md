# ARCHITECT — 這個 repo 的結構

> **本檔＝結構的唯一權威**：`project-bootstrap` 由什麼組成、每樣東西的家在哪、改哪裡會影響到什麼。
> 最後更新：2026-10-30（同日第二次：三平台能力重查後，`extract()` 的抽取規則從「第一個區塊」改成「區塊依序對應檔名」、`sync_project.py` 把 `CLAUDE.md` 從 `INSTANCE` 搬到 `PARTIAL`、`verify_bootstrap.py` 加「跨工具表保鮮期」、副本拓撲裡 `.agents/skills/` 的角色改變。前一次是補上跨機器「工作中」標記並記下 `pre-push-handoff.sh` 決定不裝）
>
> **什麼時候改**：只有**結構**變動才改——根目錄多／少一個檔案、部署包增刪一節範本、`verify_bootstrap.py` 增減檢查項、副本拓撲改變。
> 制度內容本身怎麼寫（鐵律的措辭、skill 的步驟）**不要動這一份**，那些的家在 [AGENTS.md](AGENTS.md) 與部署包裡。

## 一句話

唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)——一份自帶所有檔案範本的部署包，複製到新專案資料夾就能生出整套制度。
其餘每個檔案都是它的**說明、指標或測試**，沒有第二個產出物（例外是下面那支本 repo 自己的開場檢查 hook——它誰的副本都不是——以及 `HANDOFF.md`，它是範本 3.3 的*實例*，只拿來當「工作中」標記的載體）。

## 根目錄

| 路徑 | 是什麼 | 什麼時候動 |
|---|---|---|
| [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) | **權威版部署包**：訪談表＋各檔範本＋上 GitHub＋自檢清單＋維持操作卡 | 制度要改就改它（鐵律第 1 條） |
| [README.md](README.md) | 人的入口：怎麼用、部署後長什麼樣、跨工具相容性、改這份骨架的開場 prompt | 用法或相容性改變 |
| [AGENTS.md](AGENTS.md) | AI 的入口：這個 repo 是什麼、鐵律、副本位置、行末規則 | 多一條鐵律、副本位置改變 |
| [CLAUDE.md](CLAUDE.md)、[GEMINI.md](GEMINI.md) | 指標，內容只有一句「去讀 AGENTS.md」 | 幾乎不動 |
| [HANDOFF.md](HANDOFF.md) | **只是跨機器「工作中」標記的載體**（2026-10-30 加）。範本 3.3 的*實例*，不是副本，不在副本拓撲裡、不要用 `sync_project.py` 同步。不是狀態日誌也不是知識庫，界線寫在它開頭那節 | 每輪開工／交棒改「工作中」與「待續分支」兩欄（skill 的 A5／B6），其餘段落幾乎不動 |
| 本檔 | 結構 | 只有結構變動 |
| [LICENSE](LICENSE) | MIT（2026-09-07 起公開） | 授權改變 |
| [tools/verify_bootstrap.py](tools/verify_bootstrap.py) | **部署包的測試**，不是骨架的一部分、也不會被部署出去 | 部署包多一種失效模式時 |
| [tools/sync_project.py](tools/sync_project.py) | **部署包的發佈工具**：把最新內容推到已部署的專案。`check_docs.py` 的專案設定區塊、兩份 hook 接線裡專案自己加的設定都會原樣保留。只改檔案，不 commit | 骨架多一個要同步的檔時（而且要同時歸類進 `WHOLE`／`WIRING`／`PARTIAL`／`INSTANCE`，否則驗證會 FAIL） |
| [VERSION](VERSION) | 一行版本號，與部署包開頭的版本行一致（`verify_bootstrap.py` 會擋不一致）。各專案的 `git-freshness.sh` 抓它判斷自己落後沒有 | 跟版本行一起改 |
| `.claude/settings.json`＋`.claude/hooks/repo-git-check.sh` | 本 repo 自己的 SessionStart 檢查：git 新鮮度＋`HANDOFF.md` 的「工作中」判讀。**不是部署包 3.9／3.10 的副本**，不在副本拓撲裡、不要用 `sync_project.py` 同步它（檔頭寫了為什麼不抄 3.10） | 幾乎不動 |
| `.gitignore`、`.gitattributes` | `dist/` 不進 Git；全檔強制 `eol=lf` | 幾乎不動 |
| `dist/` | 建置產物（`--zip` 產出的骨架壓縮檔），**不進 Git** | 要發佈就重跑一次，不要留在 repo 裡跟部署包唱反調 |

## 部署包的內部結構

| 節 | 內容 | 誰會讀它 |
|---|---|---|
| 表頭 | 部署 prompt、版本日期、來源 | 拿到這份檔案的人 |
| 交接自動化怎麼運作 | 觸發（hook）／程序（skill）／防呆（hook）三層 | 想理解設計的人 |
| 跨工具與跨平台 | Claude Code／Codex CLI／Codex 桌面 App／Antigravity 的能力矩陣 | 要在別的工具上部署的人 |
| 0 | 這套骨架在解決什麼問題（失效模式 → 對策） | 想知道「為什麼要有這條規則」的人 |
| 1 | 部署前訪談：佔位符表 | 執行部署的 agent |
| 2 | 要建立的檔案結構 | 同上 |
| 3 | **各檔範本**（3.1–3.18），照抄只換佔位符 | 同上，改到哪份讀哪節 |
| 4 | 上 GitHub | 同上 |
| 5 | 部署後自檢清單 | 同上 |
| 6 | 之後怎麼維持（一頁操作卡） | 部署完的專案 |

第 3 節的範本清單就是 `verify_bootstrap.py` 裡 `EXPECTED` 的對照表：

| 節 | 產出 | 角色 |
|---|---|---|
| 3.1 | `AGENTS.md` | AI 入口、鐵律、知識庫地圖 |
| 3.2 | `CLAUDE.md`＋`GEMINI.md` | 指標（**一節產兩檔**，只有標題不同） |
| 3.3 | `HANDOFF.md` | 當下狀態（≤80 行、覆寫不累積） |
| 3.4 | `README.md` | 人的入口、交接 prompt A／B |
| 3.5 | `ARCHITECT.md` | 結構的唯一權威（2026-09-07 加入） |
| 3.6 | `docs/ai-notes/handover-protocol.md` | 交接的規則與理由 |
| 3.7 | `docs/ai-notes/roadmap.md` | 持久待辦與決策記錄 |
| 3.8 | `.claude/skills/handoff/SKILL.md` | **本骨架的核心**：0 建制／A 接棒／B 交棒／C 同步 |
| 3.9 | `.claude/settings.json` | 兩個 hook 的接線 |
| 3.10 | `.claude/hooks/git-freshness.sh` | SessionStart：git 新鮮度 |
| 3.11 | `.claude/hooks/pre-push-handoff.sh` | PreToolUse：push 前防呆 |
| 3.12 | `.gitignore` | 祕密與運行資料 |
| 3.13 | `.gitattributes` | 行末 LF |
| 3.14 | `tools/check_docs.py` | 文檔一致性檢查 |
| 3.15 | `tools/verify_state.py` | 一鍵現況查證（骨架） |
| 3.16 | `.agents/skills/handoff/SKILL.md` | Antigravity 的指標檔 |
| 3.17 | `.codex/hooks.json` | Codex CLI 的 hook 接線（掛 3.10／3.11 同樣那兩個 `.sh`） |
| 3.18 | —— | 其他 skills 的**慣例說明**，不產檔 |

## 部署包 → 骨架的抽取規則（改範本前先讀這段）

`verify_bootstrap.py` 的 `extract()` 就是「照著部署包生檔案」的機器版，規則只有四條：

1. **`### 3.x` 標題行裡的反引號路徑＝產出的檔名。** 改標題就是改檔名——3.2 的標題有兩個路徑，所以一節產兩檔。
2. **一節裡的 fence 依序對應標題上的檔名**；fence 比檔名少就全部沿用第一個（多數節是一檔一區塊）。fence 前的散文是給人看的說明，不會進檔案。
3. **標題行沒有路徑就不產檔**（3.18 是慣例說明）。

第 2 條在 2026-10-30 從「只取第一個 fence，`GEMINI.md` 的標題再由腳本替換」改成現在這樣：3.2 的 `CLAUDE.md` 從此只有一行 `@AGENTS.md` import、`GEMINI.md` 維持指標寫法，兩份內容不同了。把其中一份合成在腳本裡，就等於讓範本內容有第二個家——部署包才是權威版。

所以：**新增一份範本＝新增一節＋把檔名加進 `EXPECTED`**。只做前者，驗證會 FAIL 說「多出」；只做後者會 FAIL 說「缺少」。

## `tools/verify_bootstrap.py` 守的東西

| 檢查 | 守什麼 | 失敗代表 |
|---|---|---|
| 重生骨架 | 範本清單與 `EXPECTED` 一致 | 有人刪了範本沒發現，或新增範本沒登記 |
| 填佔位符 | 模擬部署後不該有殘留 | 範本用了訪談表沒有的佔位符 |
| `check_docs` | 在填好的骨架跑要 exit 0 | 範本裡有死連結或缺日期標頭 |
| 佔位符清單 | `PLACEHOLDER_NAMES` 涵蓋範本真正用到的名字 | 有個洞永遠不會被檢查到，而且沒有跡象 |
| 佔位符檢查（負向） | 種一個佔位符回去必須被擋下 | 第 5 項檢查本身壞了 |
| 日期標頭（負向） | 拿掉 `ARCHITECT.md` 的「最後更新」必須被擋下 | `check_docs` 的 `DATED_DIRS` 漏了它 |
| 真實部署形狀 | 部署包在場＋非 ASCII 檔名時仍 exit 0 | 照說明部署的人一定會踩到 |
| 跨平台防呆 | 無絕對路徑、有 `python3` 退路 | 換一台機器會靜默失效 |
| pre-push hook 五情境 | 該擋的擋、該放的放 | 防呆變成誤擋或形同虛設 |
| 工作中標記 | 範本有欄位，且 git-freshness 讀 `origin` 後四種狀態各印對應結論（別台 🔴、自己這台 🟡、已交棒 ✅、欄位不存在 🟡） | 跨機器誤接棒防呆靜默失效——下一棒只會看到一切正常 |
| `VERSION` 檔 | 與部署包版本行一致 | 落後偵測會說謊，落後的專案以為自己最新 |
| 版本落後偵測 | 餵假版本要講、同版與 `BOOTSTRAP_VERSION_CHECK=off` 要閉嘴 | 專案不再自己回報落後，同步又回到靠人記得 |
| 本 repo 自己的文件 | 本 repo 的 `.md` 無死連結、`AGENTS.md`／`ARCHITECT.md` 有日期標頭 | 改檔名或搬段落留下死連結。部署包裡指向「部署後才存在的檔」的連結不算，判準是 `EXPECTED`，所以它指向本 repo 檔案的連結照樣會被抓 |
| 本 repo settings.json | 合法 JSON，且指向的 hook 真的在 | 開場檢查靜默不執行——看起來有防護、實際上沒有 |
| 本 repo 工作中判讀 | `repo-git-check.sh` 讀 `origin` 的 `HANDOFF.md` 後四種狀態各印對應結論，且跟 3.10 用同一個欄位字串 | 這個 repo 的跨機器防呆靜默失效，或兩支 hook 的欄位格式悄悄分岔 |
| 同步清單涵蓋骨架 | `sync_project.py` 的四份清單加起來要等於 `EXPECTED` | 新增範本沒歸類＝那個檔沒人同步，而且沒有徵兆。2026-10-30 就是這樣查出兩份 hook 接線從來沒被發下去 |
| 接線合併 | 餵一份「舊 matcher ＋ 專案自己加的 permissions 與 hook」進去，要換掉舊值、保住專案設定、已一致時不動 | 同步會洗掉專案設定，或落後的專案根本修不好 |
| 跨工具表保鮮期 | 「跨工具與跨平台」那節的「查證日期」不得超過 90 天（`BOOTSTRAP_FRESHNESS=off` 可跳過） | 對外部工具能力的斷言在無聲中過期。這一項只保證有人看過日期，**不保證有人真的重查**——買到的是「必須有意識地決定」。會做成 fail 而不是警告，是因為上一次的對策就是一句警告，而警告沒擋住第二次（Antigravity 的 hooks、Codex 桌面 App 的 hooks，兩次同一種錯） |
| 行末與雜項 | 全 LF、JSON 合法、腳本可執行 | Windows 寫出 CRLF、設定檔打錯字 |

**exit 0 才算改完**（鐵律第 4 條）。印出 `skip` 的項目沒有被驗證，回報時要照實寫。

## 副本拓撲（同一份東西存在於多個地方的，只有這些）

```text
handoff SKILL.md
  部署包 3.8（權威）
    └─→ 各專案 .claude/skills/handoff/SKILL.md
          ├─→ （選用）~/.claude/skills/handoff/   ← 模式 0 建制真正會被載入的地方
          ├─→ （選用）~/.codex/skills/handoff/    ← Codex CLI 與桌面 App（2026-10-30 實測
          │                                          CLI 0.164.0 仍讀這個路徑，雖然官方
          │                                          文件已經不列它）
          └─→ .agents/skills/handoff/SKILL.md     ← 只放指標，不複製內容。2026-10-30 起
                                                     Antigravity 與 Codex 都把它當專案層
                                                     skill 來源，所以它的 description
                                                     必須寫滿觸發詞（那是它被發現的唯一依據）

兩個 hook .sh
  部署包 3.10／3.11（權威）
    └─→ 各專案 .claude/hooks/*.sh   ← 只有這一份腳本
          ├─← .claude/settings.json 指向它
          └─← .codex/hooks.json 指向同樣那兩個（不複製第二份）

check_docs.py
  部署包 3.14（權威，「專案設定」區塊除外——那塊本來就該依專案調）
    └─→ 各專案 tools/check_docs.py

兩份 hook 接線（JSON）
  部署包 3.9／3.17（權威，只管「指向骨架那兩個 .sh」的那幾組；
                   專案自己加的 permissions／env／額外 hook 原樣保留）
    ├─→ 各專案 .claude/settings.json
    └─→ 各專案 .codex/hooks.json
```

**JSON 沒辦法放 `source:` 標記**，所以上面那兩份接線在落後偵測裡是隱形的——它們唯一的守門人是 `sync_project.py` 的 `WIRING` 清單加上 `verify_bootstrap.py` 的「同步清單涵蓋骨架」。2026-10-30 把它們補進拓撲，是因為 2026-09-13 給 3.9 補的 `Bash|PowerShell` matcher 一直沒發下去：三個專案停在舊的 `Bash`，而那台機器的主 shell 正是 PowerShell，pre-push 防呆於是在那些專案等於沒裝，一個半月沒有任何徵兆。

每份副本檔頭有 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->`，**改內容就要跳版**，否則沒人分得出哪份落後（鐵律第 2 條）。同一天改第二次起要在日期後面加序號（`v2026-10-24.2`）——日期粒度只能證明「不早於那一天」，2026-10-24 就因此誤判過一次。
沒改內容的檔案不要跟著跳版——謊報「副本落後」之後，這個標記就沒人再信。

## 這個 repo 刻意沒有的東西

- **沒有 handoff skill、沒有 `pre-push-handoff.sh`、沒有 `check_docs.py`。** 它是制度的**來源**，不是一個交接中的工作專案；把骨架的這幾份套到它自己身上，就會出現「權威版與它的副本互相同步」的迴圈。跨 session 狀態看 `git log` 與各檔的 `source:` 版本標記；接棒程序讀全域副本 `~/.claude/skills/handoff/`。**`HANDOFF.md` 是 2026-10-30 補回來的例外**，見下一條；`pre-push-handoff.sh` 同一天重新評估過，結論仍是不裝，但理由已經換成另一個，見下面那條。
- **跨機器「工作中」標記：2026-10-30 先是接受這個缺口，同一天決定多機維護就補上了。** 當初不裝的理由是它需要 `HANDOFF.md` 當載體，而那一份得每輪交棒維護——只為防呆而裝，就是多一份沒人讀、然後開始腐化的文件；那時 single writer 靠人顧。改成多機維護之後這個理由不成立了：`git log` 與 `git fetch` **看不到別台機器未提交的變更**，而開場那個 ✅ 只證明「本機沒落後 origin」，誤接棒就會整批繞過那些變更。所以補上 `HANDOFF.md`（範本 3.3 的*實例*，不是副本，沒有同步義務），並在 `repo-git-check.sh` 加判讀段——**沿用 3.10 的同一個載體與同一個欄位，沒有發明第二種標記**，那會變成「這裡會擋、別處不會擋」的不對稱。為了讓這份文件不腐化，它開頭明寫「只當標記載體」，每輪只維護兩欄。**天花板要講明白**：標記只告訴你「東西在那台機器上」，東西本身仍得回那台 push，這不是實作缺漏。
- **`pre-push-handoff.sh`：2026-10-30 評估過，決定不裝。** 第一條那個「套到自己身上會變成同步迴圈」的理由，在 `HANDOFF.md` 以*實例*身分補回來之後就不夠用了——同一招對這支 hook 也成立——所以這次是另一個理由。它擋的是「推到權威分支、但這批 commit 沒更新 `HANDOFF.md`」，而這裡的 `HANDOFF.md` 刻意只剩「待續分支」與「工作中」兩欄：**中途推進度的當下，交接狀態真的沒有變**，沒有東西可寫。於是每次誤報只剩兩條路——編一行不成立的更動，或 `HANDOFF_HOOK=off`——實際上一定是後者，而「看到 handoff-check 就 off」一旦變成反射，哪天它為了真正的理由擋下來也會被順手關掉；防呆的價值全在那一次。**同時否決了「加一個計數器／時間戳欄位、bump 它就能過」的變通**：那會讓這支 hook 從此擋不下任何東西，卻比 `off` 更糟——`off` 是看得見的、每次都是有意識的決定，bump 過的時間戳卻長得像合規，下一棒會以為這份檔案一直有在維護；而「最後 push 時間」`git log` 已經有了，手動維護的第二份只會漂移（[AGENTS.md](AGENTS.md) 「每個事實只有一個家」）。**這個判斷綁在「這裡的 HANDOFF 只是標記載體」上**：哪天它恢復成真的狀態文件，或這個 repo 改成以 feature 分支為主（那時 hook 根本不會擋），理由就不成立，要重新評估。
- **但有一支自己的 SessionStart hook**（`.claude/hooks/repo-git-check.sh`，2026-10-30 加）：做 git 新鮮度比對與「工作中」判讀（後者 2026-10-30 加），檔頭明寫**不是 3.10 的副本、不要同步**。在此之前這個 repo 開場完全沒有提醒，A1 的 fetch 全靠使用者記得打「接棒」把全域 skill 載進來。為什麼不直接抄 3.10——`sync_project.py` 的 `discover()` 靠 handoff skill 發現專案，這個 repo 沒有 skill，`--all` 永遠掃不到它，抄過來就會變成「所有專案都同步了、只有來源自己落後」而且毫無跡象的那一份副本。
- **沒有 CI。** 驗證是一個指令（`python -X utf8 tools/verify_bootstrap.py`），跑它是鐵律第 4 條的義務。
- `tools/` 底下只有部署包自己的工具——`verify_bootstrap.py` 測試它、`sync_project.py` 發佈它，兩支都不是骨架的一部分，也都不會被部署出去。

## 全域約束（誰強制什麼）

| 約束 | 由誰強制 | 理由與做法 |
|---|---|---|
| 全檔 LF | `.gitattributes` 的 `eol=lf`＋`verify_bootstrap.py` 的行末檢查 | [AGENTS.md 行末那節](AGENTS.md) |
| 不寫單位名／內部代號／本機絕對路徑 | 人（提交前擋）＋骨架端的跨平台防呆檢查 | [AGENTS.md 鐵律第 6 條](AGENTS.md) |
| 只放通用制度與 `{{佔位符}}` | `verify_bootstrap.py` 的佔位符清單比對 | [AGENTS.md 鐵律第 5 條](AGENTS.md) |
| 副本改內容就跳 `source:` 版本 | 人 | [AGENTS.md 鐵律第 2 條](AGENTS.md) |

## 改本檔的時機

根目錄多／少一個檔案、部署包增刪一節範本（記得同步 `EXPECTED` 與上面的 3.x 對照表）、`verify_bootstrap.py` 增減檢查項、副本拓撲改變。
**跟該變動同一個 commit**，並更新檔頭的「最後更新」。
