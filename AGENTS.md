# AGENTS.md — 改這個 repo 之前先讀

> 最後更新：2026-10-31

## 這個 repo 是什麼

**AI 協作專案管理骨架的權威版。** 唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)——一份自帶所有檔案範本的部署包，複製到新專案資料夾就能生出整套制度。用法見 [README.md](README.md)。

**結構問題（有哪些檔、部署包各節產出什麼、副本存在於哪些地方）看 [ARCHITECT.md](ARCHITECT.md)**——動到結構就跟它同一個 commit 改；本檔只放規則。

**這裡不是知識庫。** 不要在本 repo 累積專案知識、踩坑紀錄或狀態；那些屬於各自的專案 repo。

唯一的例外是 `tools/verify_bootstrap.py`——它是**部署包的測試**，不是骨架的一部分，也不會被部署出去。

另一個例外是 [HANDOFF.md](HANDOFF.md)：2026-10-30 起這個 repo 多機維護，所以補上它當跨機器「工作中」標記的載體（`.claude/hooks/repo-git-check.sh` 開場讀 origin 那一份）。**它只有這個任務**——不要把狀態或知識寫進去，界線寫在它開頭那節。本 repo 依然刻意沒有 handoff skill、沒有 `pre-push-handoff.sh`、沒有 `check_docs.py`——它是制度的**來源**，不是一個交接中的工作專案（理由見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」）。

## 鐵律

1. **`PROJECT-BOOTSTRAP.md` 是權威版。** 制度要改就改它，再用 `python -X utf8 tools/sync_project.py <專案路徑> --write` 覆蓋到各專案（`--all` 可一次掃完；它會保留 `check_docs.py` 的專案設定區塊與兩份 hook 接線裡專案自己加的設定，而且只改檔案、不 commit）；**不要**在單一專案裡就地改 skill 或 hook——那正是「同一個事實有多個家」的失控起點。改完版本也要更新 `VERSION`，各專案的開場檢查靠它才知道自己落後。⚠️ **但只有在 `.claude/skills/handoff/SKILL.md` 真的改了內容時才跳 `VERSION`。** `VERSION` 實際上是「`SKILL.md` 的版本」：偵測器比的是該檔的 `source:` 標記與上游 `VERSION`（`git-freshness.sh` 的 `mine=`）。只改了不同步的範本（`sync_project.py` 的 `INSTANCE`，例如 `ARCHITECT.md`、`handover-protocol.md`）或部署包自己的敘述就跳版，每個專案會**永遠**印「骨架落後」，而且同步修不掉——同步回去的 `SKILL.md` 標記沒變。2026-10-30 修 Antigravity 那張表時踩到，被 `verify_bootstrap.py` 的「同版→閉嘴」擋下。
2. **改動 skill／hook 內容時，同步更新檔頭的 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->` 標記**，否則沒人分得出哪份副本落後。格式是 `v<日期>`，**同一天改第二次起在日期後面加序號**（`v2026-10-24.2`、`.3`），當天第一次不加；序號跟部署包開頭的「版本」行同一個號，算的是部署包當天的第幾次修改，不是單一檔案的——2026-10-24 當天改了三次而標記三次相同，副本落後卻顯示一樣新，誤判成同步漏掉白查一輪。
3. **保留每條規則的「為什麼」**。這份骨架的價值不在條文，在條文背後的事故；砍掉理由，下一棒就會繞過規則。
4. **改完要驗證**：跑 `python -X utf8 tools/verify_bootstrap.py`，**exit 0 才算改完**。它會重生骨架比對檔案清單、模擬部署填佔位符、跑 `check_docs.py`、負向測試佔位符檢查與 `ARCHITECT.md` 日期標頭檢查真的擋得住、掃絕對路徑與缺 `python3` 退路的跨平台地雷、測 pre-push hook 五情境、查全檔 LF 與兩份 JSON 設定，也查本 repo 自己的 `.md` 死連結、`.claude/settings.json` 與本 repo 那支 hook 的「工作中」判讀（這個 repo 沒有部署 `check_docs.py`，否則那就成了要跳版同步的副本）。2026-08-05 之前這段是要人照著手刻的敘述，每一棒都得重刻一次，於是實務上常被跳過——所以固化成一個指令。跳過的項目（例如機器上沒有 bash）腳本會印 `skip` 並回傳 1，回報時要照實寫。
5. **不要塞專案專屬內容**（網址、docId、憑證檔名、業務規則）。部署包只放通用制度與佔位符。
6. **這是公開 repo**（2026-09-07 起公開，MIT 授權）。任何人都看得到**全部 Git 歷史**，所以文件裡不要寫客戶／單位名稱、內部專案代號、本機絕對路徑——`README.md` 的「來源」那節就是為此改成不點名的中性描述。要補來源或舉例時照樣寫成中性描述；已經進歷史的東西刪不掉，所以是提交前擋，不是事後補救。

## 副本規則

**完整的副本拓撲（哪一份是權威、覆蓋到哪些地方）在 [ARCHITECT.md](ARCHITECT.md)**，這裡只放規則：

- **改完部署包，把所有副本一起覆蓋**，包括選用的全域 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/`（2026-10-30 實測 Codex CLI `0.164.0` 仍讀後者，雖然官方文件已經不列這個路徑）。漏掉一份，那台機器就繼續照舊制度做事。
- **Codex 的 hook 與 Claude Code 同格式同語意**，所以兩邊掛的是同樣那兩個 `.sh`——不要複製第二份腳本進 `.codex/`。兩份各自演化就會出現「Claude 端會擋、Codex 端不會擋」的不對稱。
- **Antigravity 的 hook 要分 surface 看，不要寫成整個產品的性質。** 它是四個獨立 surface（Antigravity 2.0 桌面 App／Antigravity CLI／Antigravity IDE／Python SDK，官方 blog 並排列出）。2026-10-31 實測：**CLI（`1.4.7`／`1.4.12`）與 2.0（`2.28.2`）都會讀專案層 `.agents/hooks.json` 並觸發**（CLI 靠 `agy -p` headless；2.0 沒有命令列入口，改成桌面自動化開 session ＋ 寫檔探針，再到真專案上確認注入進了 context），**接線已經端到端跑通並附進骨架**（3.18 轉接層 ＋ 3.19 Windows shim ＋ 3.20 接線）；**四個 surface 裡只剩 IDE `1.107.0` 沒觸發，原因仍未解釋**。**IDE 這一面 2026-10-31 決定不再追**（使用者不再用這個 surface，未解問題沒有讀者）——量到的事實照留，收掉的只是「去 IDE 重跑一次」那個下一步，掃到別再重提。改這三個檔之前先讀部署包「跨工具與跨平台」的 Antigravity 那一節——裡面有四個踩到才知道的約束：`.cmd` **必須全 ASCII**（中文註解會被 OEM code page 誤讀成指令執行）、**不能有多行括號區塊或 label**（LF 行末的 batch 會壞）、**路徑用 `%~dp0`／`$0` 推不靠 cwd**、**從 Windows 提交 `ag-wrap.sh` 要補 `git update-index --chmod=+x`**（Windows 不帶執行位元，而 Unix handler 直接跑這支 `.sh`，記成 `100644` 的話 Unix clone 上它靜默不動；2026-10-31 補裝六個專案時就是從 Windows 做的）。另外兩個反直覺的點：相對路徑可用而絕對路徑才脆弱（所以鐵律 5 跟它**沒有**衝突，在 Windows 上甚至是唯一寫得出來的形式）；`PreToolUse` 不明確回 `{"allow_tool": true}` 就等於**拒絕**，會擋掉使用者全部的工具呼叫——所以骨架**刻意只接 `SessionStart`**。
  要重開這個決定，門檻是比那次探針更強的證據——那次是讓 hook 自己寫檔，連 Hooks UI 自己列得出來的 `PreToolUse` 都沒觸發。
- **接線路徑一律相對**：寫死絕對路徑換機器就靜默失效（真的發生過），`verify_bootstrap.py` 的「跨平台防呆」會擋。
- **`.agents/` 只放指標與接線**，不複製程序內容。2026-10-31 起它有 `hooks.json`（接線）與 `ag-hook.cmd`（Windows shim）——兩者都**不含任何判斷規則**，規則只在被包的那支 `.sh` 裡（權威版只有一份），所以它們跟「複製第二份腳本」不是同一種風險：裡面沒有東西可以跟權威版分岔，只會在管線上壞掉，而管線由 `verify_bootstrap.py` 的「Antigravity 接線」守著。2026-10-30 起它不只給 Antigravity——`codex debug prompt-input` 的 Skill roots 表證實 Codex 也把 repo 的 `.agents/skills/` 當 skill 來源。既然會被自動發現，**那份指標的 `description` 就必須寫滿觸發詞**：agent 是靠它決定要不要開檔的，寫短等於無聲地關掉一個入口。
- **本 repo 自己的 `HANDOFF.md` 與 `.claude/hooks/repo-git-check.sh` 不在副本拓撲裡**，`sync_project.py` 不要碰它們：前者是範本 3.3 的*實例*，後者誰的副本都不是（檔頭寫了為什麼不抄 3.10）。它們的檢查由 `verify_bootstrap.py` 顧。

## 這個 repo 自己的指標檔

`CLAUDE.md` 2026-10-30 改成只有一行 `@AGENTS.md` import。**不要改回「去讀 AGENTS.md」那種句子**：Claude Code 有 `CLAUDE.md` 就不原生讀 `AGENTS.md`，用文字請它去讀不保證它真的開檔（當天在這個 repo 上驗證過：session 開場只拿到 `CLAUDE.md` 那三行）。`GEMINI.md` 維持指標寫法——Antigravity 原生讀 `AGENTS.md`，而它支不支援 `@` import 沒有文件可查。

## 行末

`.gitattributes` 強制 `eol=lf`。部署包全檔是 LF；用 Python 改寫時記得 `newline=''` 或事後正規化，否則 Windows 會把整份寫成 CRLF。
