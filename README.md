# project-bootstrap — AI 協作專案管理骨架

把「跨 session、跨模型、跨機器協作」需要的制度，打包成**一份可直接部署的檔案**：[PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

> 最後更新：2026-08-05。這個 repo 只有一個產出物：上面那份部署包。其他檔案都是說明或指標。

## 怎麼用

1. 把 `PROJECT-BOOTSTRAP.md` 複製到**新專案的空資料夾**。
2. 在該資料夾開一個 AI session，貼上：

```text
請完全依照本資料夾的 PROJECT-BOOTSTRAP.md 建立本專案的管理骨架：先做第 1 節訪談問我問題，
拿到答案後照第 3 節逐檔建立（內容照抄、只替換佔位符），再依第 4 節上 GitHub，最後跑第 5 節自檢並回報。
過程中不要自行增刪制度，也不要把佔位符留在檔案裡。
```

3. AI 會問 11 個佔位符（專案名、GitHub owner/repo、憑證檔、運行目錄、時區…），生出骨架、建 repo、跑自檢。
4. 骨架建好後**刪掉該專案裡的 `PROJECT-BOOTSTRAP.md`**——內容已分散進 `AGENTS.md`／`handover-protocol.md`／`handoff` skill，留著就是第二份會腐化的副本。

也可以完全手動：照第 3 節自己把每個檔案建出來，效果一樣。

## 部署後的專案長什麼樣

```text
專案/
├─ README.md                        人的入口（系統是什麼、怎麼連）
├─ AGENTS.md                        AI 的入口（鐵律、連線資料、知識庫地圖）＝唯一權威
├─ CLAUDE.md / GEMINI.md            指標，指向 AGENTS.md
├─ HANDOFF.md                       當下工作狀態（≤80 行、覆寫不累積）
├─ .claude/                         Claude Code
│   ├─ settings.json                hook 設定
│   ├─ hooks/git-freshness.sh       SessionStart：git 新鮮度檢查＋提醒走交接程序
│   ├─ hooks/pre-push-handoff.sh    PreToolUse：沒更新 HANDOFF 就想 push 時擋下
│   └─ skills/handoff/SKILL.md      交接與同步的可執行程序（A 接棒／B 交棒／C 同步）＝權威版
├─ .codex/hooks.json                Codex：掛上面同樣那兩個腳本（同格式、同語意）
├─ .agents/skills/handoff/SKILL.md  Antigravity 原生讀 .agents/：指向權威版的指標
├─ docs/ai-notes/
│   ├─ handover-protocol.md         交接協定（規則與判準）
│   └─ roadmap.md                   持久待辦總表
└─ tools/
    ├─ check_docs.py                死連結／過期字串／缺日期標頭／硬編數量／殘留佔位符
    └─ verify_state.py              一鍵現況查證（骨架，部署後填檢查項）
```

## 核心：交接不靠人記，靠三層自動發生

| 層 | 檔案 | 什麼時候動 |
|---|---|---|
| **觸發** | `hooks/git-freshness.sh` | 每次 session 開始自動 fetch，報告落後／分岔，並提醒「接棒先走 handoff skill」 |
| **程序** | `skills/handoff/SKILL.md` | agent 判斷要接棒／交棒／同步時自動載入；也可打 `/handoff` |
| **防呆** | `hooks/pre-push-handoff.sh` | 要推到權威分支、但這批 commit 沒更新 `HANDOFF.md` → 擋下並要求先走交棒程序 |

**分工**：`handover-protocol.md`＝規則與理由（為什麼、什麼算對）；`SKILL.md`＝怎麼做（指令、判讀表、模板）。
兩者衝突以協定為準。這樣才不會變成「同一套程序有兩份會各自演化的副本」。

## 跨工具與跨平台

正確性放在**可攜層**（`AGENTS.md` 開頭那段＋純 Markdown 的程序檔），三個工具都原生讀得到；hooks 只是讓人不必記得，不是制度成立的前提。

| | Claude Code | Codex CLI | Codex 桌面 App | Antigravity |
|---|---|---|---|---|
| 讀 `AGENTS.md` | ✅ 經 `CLAUDE.md` 指標 | ✅ 原生 | ✅ 原生 | ✅ 原生 |
| 自動載入程序檔 | ✅ `.claude/skills/`、`/handoff` | ⬜ 靠 `AGENTS.md` 指路 | ✅ `~/.codex/skills/`，也讀專案的 `.agents/skills/` | ✅ 原生讀 `.agents/skills/` |
| Hooks | ✅ `.claude/settings.json` | ✅ `<repo>/.codex/hooks.json`，同格式同語意，首次需 `/hooks` 信任 | ❌ 沒有 | ❌ 沒有 |

**Codex 要分 CLI 與桌面 App**（2026-08-06 實測 App `26.721.41059`）：CLI 有 hooks 且與 Claude Code 同格式，兩邊掛**同樣那兩個 `.sh`**、不各留一份；桌面 App 沒有 hooks，但有原生 skill 系統，把 `SKILL.md` 複製到 `~/.codex/skills/handoff/` 即可。

只有 Claude Code 與 Codex CLI 有自動關卡，**其餘兩者要靠可攜層**——這就是正確性不押在 hook 上的理由。共同前提：hook 需要 bash（macOS 內建，Windows 用 Git for Windows 附的）；`python` 不存在的機器改用 `python3`。

## 它在解決什麼

每條規則背後都有一次實際事故——移植時**不要把理由砍掉**，理由沒了，下一棒就會覺得規則多餘而繞過它。

| 失效模式 | 對策 |
|---|---|
| AI 對著過期的本機快照工作數小時，最後 commit 造成分岔 | SessionStart hook 自動 fetch 並注入警告 |
| 交接文件愈寫愈長，接手者要讀 20 分鐘才知道現在做到哪 | 三層分工：持久知識／當下狀態（≤80 行）／Git 歷史 |
| 同一個事實散在三個檔案，各自演進到互相矛盾 | 每個事實只有一個家，其他地方只放指標 |
| 文件說 A、實際是 B，AI 照文件做就炸 | 以實況為準＋`verify_state.py`＋`check_docs.py` |
| 純文件修正被「等功能驗收」擋住，接手者拿到過期文檔集 | 兩類分支：功能分支需驗收；文件／基建分支驗證過即可併 |
| 連線失敗被誤判成「本機沒有憑證」，寫下錯誤結論 | SKIPPED 判準：先排除設定沒帶到；禁止自行挖憑證 |
| 祕密／運行資料被推上 GitHub | 鐵律＋`.gitignore`＋提交前固定檢查 staged 清單 |
| 交接品質看 agent 心情：漏驗證、忘了寫 HANDOFF 就 push | `handoff` skill＋pre-push hook |

## 要改這份骨架時：開 session 貼這段

在本 repo 開新的 AI session 時整段複製貼上。**這不是接棒 prompt**——本 repo 沒有 `HANDOFF.md`，也沒有骨架那套 hooks，見下方說明。
改完部署包一律用 `python -X utf8 tools/verify_bootstrap.py` 驗證（重生骨架＋跑完所有檢查，**exit 0 才算完成**）。

```text
這個 repo 是「AI 協作專案管理骨架」的權威版，唯一產出物是 PROJECT-BOOTSTRAP.md：一份自帶所有檔案範本的
部署包，複製到新專案資料夾就能生出整套制度（三個入口、交接協定、handoff skill、兩個 git hook、兩支驗證腳本）。

先讀 AGENTS.md 與 README.md，再讀 PROJECT-BOOTSTRAP.md 的第 0–2 節建立全貌。
第 3 節是各檔範本，改到哪一份才讀那一段——不要整份讀完，那是 1000 多行。

工作時遵守：
1. 權威版是 PROJECT-BOOTSTRAP.md。制度要改就改它，不要去改各專案裡的副本；改完把副本一起覆蓋
   （位置見 AGENTS.md「已知的副本位置」）。
2. 只放通用制度與 {{佔位符}}，不要塞專案專屬內容（網址、docId、憑證檔名、業務規則）。
3. 每條規則都要保留「為什麼」與絕對日期。砍掉理由，下一棒就會覺得規則多餘而繞過它。
4. 動到 skill／hook 內容時，同步更新檔頭的 source 版本標記，否則沒人分得出哪份副本落後。
5. 全檔 LF。用 Python 改寫要 newline='' 或事後正規化，否則 Windows 會把整份寫成 CRLF。
6. 本 repo 刻意沒有 HANDOFF.md 與 hooks——它是制度的來源，不是一個交接中的工作專案。
   不要「順手」把骨架套到它自己身上。跨 session 狀態看 git log 與 source 版本標記。
   tools/ 底下只有 verify_bootstrap.py，那是部署包的測試，不是骨架的一部分。

改完必須驗證，沒驗證不算完成：

    python -X utf8 tools/verify_bootstrap.py

要 exit 0。它會重生骨架比對檔案清單、模擬部署填佔位符、跑 check_docs.py、負向測試佔位符
檢查擋不擋得住、測 pre-push hook 五情境、查全檔 LF。印出 skip 的項目代表沒被驗證，要照實回報。

先用 3–5 行回報現況與你打算做什麼，再動手。破壞性操作、commit 或 push 之前先問我。
```

## handoff skill 的副本同步規則

`SKILL.md` 會同時存在於：**本 repo 的部署包內**（權威版）、每個專案的 `.claude/skills/handoff/`、以及選用的全域 `~/.claude/skills/handoff/`。

- 要改就**改本 repo 的 `PROJECT-BOOTSTRAP.md`**，再覆蓋下去；不要在單一專案裡就地改。
- 每份副本檔頭有 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->`，用它辨識落後的副本。

## 來源

從兩個實際運行的專案萃取：台大地理系案件審核工作流（Grist＋NAS＋custom widget，repo `grist-workflow`）、NAA_TR（檔案管理局文本識別）。兩個都是多模型（Claude／Gemini／Codex）、多機器（Windows↔macOS）協作。

repo 名寫在這裡是因為本機資料夾名稱和專案名對不上（`grist-workflow` 的工作目錄叫 `Grist_test`），沒有這行就會有人以為這個專案不存在。
