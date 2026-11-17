# project-bootstrap — AI 協作專案管理骨架

把「跨 session、跨模型、跨機器協作」需要的制度，打包成**一份可直接部署的檔案**：[PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

> 最後更新：2026-11-17（改成標準 README：開發流程與副本同步用法搬到 CONTRIBUTING.md；部署後的 README 也改成標準 README，連線資料從 AGENTS 搬進來，需求決策書 v3 Q40）；前次 2026-11-16（skill 七個檔；優先序改成 v3）。
> 這個 repo 只有一個產出物：上面那份部署包，由 `src/kit/` 以 `tools/build_kit.py` 生成。其他檔案是它的來源、說明、指標、測試或 v2 原型；結構見 [ARCHITECT.md](ARCHITECT.md)。

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
| 祕密／運行資料被推上 GitHub | 鐵律＋`.gitignore`＋提交前固定檢查 staged 清單 |
| 交接品質看 agent 心情：漏驗證、忘了寫 HANDOFF 就 push | `handoff` skill＋pre-push hook |

## 怎麼用

1. 把 `PROJECT-BOOTSTRAP.md` 複製到**新專案的空資料夾**。
2. 在該資料夾開一個 AI session，貼上：

```text
請完全依照本資料夾的 PROJECT-BOOTSTRAP.md 建立本專案的管理骨架：先做第 1 節訪談問我問題，
拿到答案後照第 3 節逐檔建立（內容照抄、只替換佔位符），依第 4 節先本機驗收再首次發布，最後跑第 5 節遠端與工具驗收並回報。
過程中不要自行增刪制度，也不要把佔位符留在檔案裡。
```

3. AI 會照第 1 節那張表一次問完（專案名、GitHub owner/repo、憑證檔、運行目錄、時區…），生出骨架、建 repo、跑自檢。
4. 骨架建好後**刪掉該專案裡的 `PROJECT-BOOTSTRAP.md`**——內容已分散進 `AGENTS.md`、`ARCHITECT.md` 與 `handoff` skill，留著就是第二份會腐化的副本。

也可以完全手動：照第 3 節自己把每個檔案建出來，效果一樣。

## 部署後的專案長什麼樣

```text
專案/
├─ README.md                        專案介紹：是什麼、為什麼做、怎麼連、怎麼跑
├─ AGENTS.md                        AI 開工時自動讀（標記之間是部署包管理的共用制度；其餘是專案鐵律）＝唯一權威
├─ CLAUDE.md / GEMINI.md            指標，指向 AGENTS.md
├─ HANDOFF.md                       當下工作狀態（≤80 行、覆寫不累積）
├─ ARCHITECT.md                     專案結構的唯一權威（只有結構變動才改）
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

## 核心：交接不靠人記，靠四層把漏做的機會壓低

| 層 | 檔案 | 什麼時候動 |
|---|---|---|
| **觸發** | `hooks/git-freshness.sh` | 每次 session 開始自動 fetch，只印 `[facts]`：時間戳（session 名用的 MM.DD.HH）、落後／領先、origin 的「工作中」。它只給事實，不下判斷（agent 自己推小時會寫出不存在的時刻，而那是靜默的） |
| **必守條件** | `AGENTS.md` 的共用制度一節 | 每次都適用，而且不必先讀別的檔：同步、「工作中」標記、交棒的定義、session 名稱（2026-11-13 起，需求決策書 v3 第 5 節） |
| **程序參考** | `skills/handoff/`（七個檔） | **碰到才讀，不是開工的前提**：逐步程序、Git 異常判讀、HANDOFF 模板、每條規則的理由；也可打 `/handoff`（建制走模式 0，見下節） |
| **AI push 提醒** | `hooks/pre-push-handoff.sh` | 只依字面命令、目前分支與 origin 檢查已提交 HANDOFF 差異；選項／refspec／其他 remote／GUI／script 不保證，純文字可能誤擋；見部署包 3.11 |

**分工**：`AGENTS.md` 的共用制度＝必守條件（衝突時以它為準）；`SKILL.md` 與同目錄的模式檔＝怎麼做（指令、判讀表、模板）與理由（`reasons.md`）；專案自己的 override 寫在 `AGENTS.md` 共用制度標記外的鐵律。
交接協定 `handover-protocol.md` 2026-11-17 起不再部署（需求決策書 v3 Q41）；舊專案留著的那一份是不同步的專案實例，在程序細節上**核心優先序：SKILL.md**，升級時須人工遷移。
override 只可加嚴或填補專案設定，使用者明確指示仍優先。權威程序只留一份，避免兩份副本各自演化（2026-11-03／複審 R06：人的入口曾保留相反優先序；2026-11-13／v3 第 5 節把「必守」這一層從 skill 移到 `AGENTS.md`，因為把參考檔當成前提，只讀一句話的 session 也得先讀完整份程序）。

## 完全空白的新專案：模式 0（建制）

上面那三層是**部署完成之後**才會動的；空白資料夾裡什麼都還沒有。所以同一支 skill 多了一個**模式 0**：
使用者講一句「幫我把交接機制建起來」，agent 就照部署包逐檔生成——訪談一次問完、照抄範本、上 GitHub、
跑自檢、寫第一份 `HANDOFF.md` 與 `ARCHITECT.md`，最後刪掉部署包（留著就是第二份會腐化的副本）。

**要讓它自動觸發，把 skill 裝成全域的**（一次就好，之後每個新專案都吃得到）：

```bash
mkdir -p ~/.claude/skills/handoff && cp <某個已部署專案>/.claude/skills/handoff/*.md ~/.claude/skills/handoff/
```

Codex 桌面 App 放 `~/.codex/skills/handoff/`，同樣那七個檔（2026-11-16.4 起多 `env.md`；2026-11-10 起 skill 是一個目錄，少複製一個，入口就會指向不存在的檔）。沒裝全域副本也可以——把 `PROJECT-BOOTSTRAP.md`
複製進資料夾，用最上面那段 prompt 手動指路，結果一樣。

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

**Antigravity 2026-11-13 起放棄**（需求決策書 v3 D8）：部署包不再產出它的接線與轉接層，已部署專案裡的舊檔不同步也不刪，清不清由使用者決定。之前的實測紀錄在 git 歷史與 [ARCHITECT.md](ARCHITECT.md)。

三個平面都接得上 hooks，但**都帶條件**：Codex 要專案被信任、而且每個專案各審一次。條件不成立時整層是**靜默**跳過的（2026-10-30 在未信任的資料夾實測，stderr 一個字都沒有），所以正確性押在可攜層、不押在 hook 上。共同前提：hook 需要 bash（macOS 內建，Windows 用 Git for Windows 附的，不是 WSL 那支）；hook 依序試 `python3`、`python`，Windows 的 WindowsApps `python3` 往往是個 PATH 找得到、執行卻失敗的別名（2026-11-16 實測 rc=49），要靠回退到 `python` 才拿得到 `[facts]`。

## 正式包的發布公鑰（v2 試行，2026-11-11）

v2 分支在試行「由 CI 簽章發布正式包、專案只留指標」（實現規劃 P2）。發布用的公鑰在 [src/kit/release-keys.txt](src/kit/release-keys.txt)，指紋：

```text
SHA256:FjVJTEPBuOaloJZV0GvtZiG3bXYJo68v+cTaVqs0JU0
```

第一次安裝時 `tools/install_package.py` 用這把公鑰驗簽；之後每一版只接受上一版列出的金鑰。私鑰只存在本 repo `release` environment 的 secret，每次發布都要 repo 擁有者核准。現行的部署方式（複製 `PROJECT-BOOTSTRAP.md`）不受影響。

## 參與開發

這個 repo 由 AI session 輪流做，開工時跟 AI 說「接棒」，收工時說「交棒」。

- 開工必守的規則在 [AGENTS.md](AGENTS.md)，AI 工具開工時會自動讀到。
- 改部署包的流程、同步到已部署專案的用法、碰到才需要的規則在 [CONTRIBUTING.md](CONTRIBUTING.md)。
- 目前做到哪在 [HANDOFF.md](HANDOFF.md)；需求的權威是[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)。

## 來源

從兩個實際運行的專案萃取：一個是表單資料庫＋NAS＋custom widget 的案件審核工作流，另一個是文本識別系統。兩個都是多模型（Claude／Gemini／Codex）、多機器（Windows↔macOS）協作。

骨架裡的每條規則都對應一次實際踩過的坑——所以規則旁邊一律附「為什麼」，砍掉理由，下一棒就會繞過規則。

## 授權

[MIT](LICENSE)
