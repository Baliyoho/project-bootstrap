# project-bootstrap — AI 協作專案管理骨架

把「跨 session、跨模型、跨機器協作」需要的制度，打包成**一支安裝程式**：[bootstrap.py](bootstrap.py)。

這個 repo 唯一的產出物是安裝程式 `bootstrap.py`，由 `src/kit/` 以 `tools/build_kit.py` 生成；部署包的說明與每個範本在 [src/kit/](src/kit/kit.md)。其他檔案是它的來源、說明、指標或測試，退休的 v2 程式封存在 `archive/`；結構見 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 它在解決什麼

每條規則背後都有一次實際事故——移植時**不要把理由砍掉**，理由沒了，下一棒就會覺得規則多餘而繞過它。

| 失效模式 | 對策 |
|---|---|
| AI 對著過期的本機快照工作數小時，最後 commit 造成分岔 | SessionStart hook 自動 fetch，把落後、領先與「工作中」當事實放進 context |
| 交接文件愈寫愈長，接手者要讀 20 分鐘才知道現在做到哪 | 三層分工：持久知識／當下狀態（≤80 行）／Git 歷史 |
| 同一個事實散在三個檔案，各自演進到互相矛盾 | 每個事實只有一個家，其他地方只放指標 |
| 文件說 A、實際是 B，AI 照文件做就炸 | 以實況為準＋`verify_state.py`＋`check_docs.py` |
| 純文件修正被「等功能驗收」擋住，接手者拿到過期文檔集 | 兩類分支：功能分支需驗收；文件／基建分支驗證過即可併 |
| 連線失敗被誤判成「本機沒有憑證」，寫下錯誤結論 | SKIPPED 判準：先排除設定沒帶到；禁止自行挖憑證 |
| 祕密／運行資料被推上 GitHub | 規則＋`.gitignore`＋提交前固定檢查 staged 清單 |
| 交接品質看 agent 心情：漏驗證、忘了寫 HANDOFF 就 push | `handoff` skill＋pre-push hook |

## 怎麼用

需要 Python 3.12 以上（`bootstrap.py` 只用標準函式庫，macOS 與 Windows）。

1. 取得 `bootstrap.py`（本 repo 根目錄的單一檔），在終端機跑：

```bash
python3 bootstrap.py --target <新專案資料夾>
```

2. 程式一次問完訪談（專案名、GitHub owner/repo、憑證檔、運行目錄、時區…），把骨架寫進資料夾、逐檔比對雜湊；不在 Git 工作樹裡時 `git init`。它不碰網路、不 commit、不推送，**已存在的同名檔一律不覆寫**，新內容寫到旁邊的 `<路徑>.bootstrap-new`。不能互動時用 `--answers <檔案.json>`、`--set KEY=VALUE` 與 `--non-interactive`。
3. 在那個資料夾開 Claude Code 或 Codex，說「接棒」。安裝程式已把第一批工作寫進 `HANDOFF.md`：補寫需要理解專案的檔、合併 `.bootstrap-new`、回答留空的題目、先本機驗收再建 GitHub repo 首次推送、跑遠端與工具驗收。做法在 handoff skill 的 `mode-0.md`。

已部署的專案升級跑 `python3 bootstrap.py update --target <專案>`：先預演，加 `--write` 才寫入；只換骨架擁有的部分，專案自己的內容不動。

2026-11-18 以前的用法是把部署包 `PROJECT-BOOTSTRAP.md` 複製進資料夾，讓 AI 照抄二十幾個檔；那條路已拿掉（需求決策書 v3 Q49），`PROJECT-BOOTSTRAP.md` 也在同一天刪掉（Q50）。部署包的說明在 [src/kit/kit.md](src/kit/kit.md)，範本在 `src/kit/files/`。

## 部署後的專案長什麼樣

```text
專案/
├─ README.md                        專案介紹：是什麼、為什麼做、怎麼連、怎麼跑
├─ AGENTS.md                        AI 開工時自動讀（標記之間是部署包管理的共用制度；其餘是專案接著編號的規則）＝唯一權威
├─ CLAUDE.md                        指標，用 @AGENTS.md import
├─ HANDOFF.md                       當下工作狀態（≤80 行、覆寫不累積）
├─ ARCHITECTURE.md                     專案結構的唯一權威（只有結構變動才改）
├─ .bootstrap/answers.json          訪談答案（安裝程式寫、update 用；不含祕密）
├─ .claude/                         Claude Code
│   ├─ settings.json                hook 設定
│   ├─ hooks/git-freshness.sh       SessionStart：fetch 後只印 [facts]（時間與 session 名用的 MM.DD.HH、落後領先、origin 的「工作中」）
│   ├─ hooks/pre-push-handoff.sh    PreToolUse：AI push 提醒（有限覆蓋）
│   ├─ hooks/codex-hook.cmd         Codex 的 Windows 啟動器（Git Bash、純文字標頭、結束碼）
│   └─ skills/handoff/              碰到才讀的參考：入口 SKILL.md＋mode-a／mode-a-stop／mode-b／mode-0／reasons／env 共七個檔
├─ .codex/hooks.json                Codex：掛上面同樣那兩個腳本（同格式、同語意）
├─ .agents/skills/handoff/SKILL.md  Codex 讀 repo 的 .agents/skills/：指向權威版的指標
├─ docs/ai-notes/
│   └─ roadmap.md                   持久待辦總表
└─ tools/
    ├─ check_docs.py                死連結／過期字串／缺日期標頭／硬編數量／殘留佔位符
    └─ verify_state.py              一鍵現況查證（骨架，部署後填檢查項）
```

## 核心：交接不靠人記

制度寫成文件，agent 不一定會照做，所以交接靠幾層把漏做的機會壓低（不是保證發生）：開場 hook 自動 fetch、只印事實；`AGENTS.md` 的共用制度寫必守條件；`skills/handoff/` 是碰到才讀的程序參考；push 前 hook 在沒寫交接時提醒並阻擋。每一層做什麼、怎麼分工、限制在哪，見部署包說明 [src/kit/kit.md](src/kit/kit.md) 的「交接自動化怎麼運作」。

舊專案留著的交接協定 `handover-protocol.md`（2026-11-17 起不再部署，v3 Q41）跟 skill 衝突時，**核心優先序：SKILL.md**，升級時須人工遷移；使用者明確指示仍優先。

## 完全空白的新專案：模式 0（建制）

上面那三層是**部署完成之後**才會動的；空白資料夾裡什麼都還沒有。所以同一支 skill 多了一個**模式 0**：
使用者講一句「幫我把交接機制建起來」，agent 就跑 `bootstrap.py`，再做它寫進 `HANDOFF.md` 的第一批工作——
補寫專案本體、合併衝突檔、本機驗收後上 GitHub、跑遠端與工具驗收（2026-11-18 起，需求決策書 v3 Q49）。

**要讓它自動觸發，把 skill 裝成全域的**（一次就好，之後每個新專案都吃得到）：

```bash
mkdir -p ~/.claude/skills/handoff && cp <某個已部署專案>/.claude/skills/handoff/*.md ~/.claude/skills/handoff/
```

Codex 桌面 App 放 `~/.codex/skills/handoff/`，同樣那七個檔（2026-11-16.4 起多 `env.md`；2026-11-10 起 skill 是一個目錄，少複製一個，入口就會指向不存在的檔）。沒裝全域副本也可以——自己跑
`python3 bootstrap.py --target <資料夾>`，再開 session 說「接棒」，結果一樣。

模式 0 有兩條硬規定，都對應會實際發生的事：

- **沒拿到部署包就停下來要**，不要憑印象重刻。憑印象生出來的版本缺的永遠是最貴的那部分——每條規則後面的
  「為什麼」、hook 的邊界條件——看起來像那套制度，實際擋不住任何事，而且沒有任何跡象。
- **使用者沒明講要導入就不要建。** 這支 skill 會在他只想改一行程式時被載入；未經同意在別人的 repo 裡灑出
  十幾個檔案，最後會留下半套沒人維護的制度，比沒有更糟。

## 跨工具與跨平台

正確性放在**可攜層**（`AGENTS.md` 開頭那段＋純 Markdown 的程序檔），下面三個平面都原生讀得到；hooks 只是讓人不必記得，不是制度成立的前提。**「讀得到」不等於「照做」**：這張表量的是載入，不是遵循（2026-11-02／F15；遵循那一種唯一的量測是 2026-11-01 的六個收尾 session，git 全對、兩個漏改 session 名稱）。

| | Claude Code | Codex CLI | Codex 桌面 App |
|---|---|---|---|
| 讀 `AGENTS.md` | ✅ 經 `CLAUDE.md` 指標 | ✅ 原生 | ✅ 原生 |
| 自動載入程序檔 | ✅ `.claude/skills/`、`/handoff` | ✅ `~/.codex/skills/` ＋ repo 的 `.agents/skills/`（2026-10-30 實測） | ✅ 同 CLI |
| Hooks | ✅ `.claude/settings.json` | ✅ `<repo>/.codex/hooks.json`，同格式同語意；要專案被信任＋**每個專案各審一次**（信任綁絕對路徑；互動模式開場會自己問） | ✅ 有（App `26.506` 起，Settings 裡審核） |

**Codex 要分 CLI 與桌面 App**：CLI 有 hooks 且與 Claude Code 同格式，兩邊掛**同樣那兩個 `.sh`**、不各留一份；桌面 App 也有 hooks（2026-10-30 重查：App `26.506` 起有 in-app 信任審核，與 CLI 共用 `~/.codex`；舊版這裡寫「沒有」是 2026-08-06 的實測，已過期），全域 skill 一樣放 `~/.codex/skills/handoff/`。

**Antigravity 2026-11-13 起放棄**（需求決策書 v3 D8）：部署包不再產出它的接線與轉接層，已部署專案裡的舊檔不同步也不刪，清不清由使用者決定。之前的實測紀錄在 git 歷史與 [ARCHITECTURE.md](ARCHITECTURE.md)。

三個平面都接得上 hooks，但**都帶條件**：Codex 要專案被信任、而且每個專案各審一次。條件不成立時整層是**靜默**跳過的（2026-10-30 在未信任的資料夾實測，stderr 一個字都沒有），所以正確性押在可攜層、不押在 hook 上。共同前提：hook 需要 bash（macOS 內建，Windows 用 Git for Windows 附的，不是 WSL 那支）；hook 依序試 `python3`、`python`，Windows 的 WindowsApps `python3` 往往是個 PATH 找得到、執行卻失敗的別名（2026-11-16 實測 rc=49），要靠回退到 `python` 才拿得到 `[facts]`。

## 參與開發

這個 repo 由 AI session 輪流做，開工時跟 AI 說「接棒」，收工時說「交棒」。

- 規則在 [AGENTS.md](AGENTS.md)，AI 工具開工時會自動讀到；每條規則的理由在[理由檔](docs/rationale.md)。
- 改部署包的流程、同步到已部署專案的用法與其他做法在 [AI 維護手冊](docs/maintenance.md)。
- 目前做到哪在 [HANDOFF.md](HANDOFF.md)；需求的權威是[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)；部署包的逐版變更在 [CHANGELOG.md](CHANGELOG.md)。

## 來源

從兩個實際運行的專案萃取：一個是表單資料庫＋NAS＋custom widget 的案件審核工作流，另一個是文本識別系統。兩個都是多模型、多機器（Windows↔macOS）協作。本專案只支援 Claude Code 與 Codex，明確不支援 Gemini。

骨架裡的每條規則都對應一次實際踩過的坑——所以規則旁邊一律附「為什麼」，砍掉理由，下一棒就會繞過規則。

## 授權

[MIT](LICENSE)
