# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-31 09:32（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（把 Antigravity 那輪探針的結論縮回它實際覆蓋的範圍）

## 這份檔案在這個 repo 的角色（跟其他專案不一樣，先讀這段）

**它只有一個任務：當跨機器「工作中」標記的載體。** 這個 repo 是制度的來源、刻意沒有 handoff
skill 也沒有知識庫（見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」），所以：

- **不要把這裡當狀態日誌或知識庫。** 鐵律「這裡不是知識庫」照舊；跨 session 的事實看 `git log`
  與各檔的 `source:` 版本標記。這一份要短，短到每輪交棒都願意維護它——會腐化的文件就是從
  「順手多寫兩段」開始的。
- **它是部署包範本 3.3 的*實例*，不是副本。** `sync_project.py` 的 `discover()` 靠 handoff skill
  認專案，掃不到這個 repo；`PARTIAL` 也只會在缺欄位時補欄位。所以它沒有同步義務，改它不必
  動 `VERSION`，也不要拿 `sync_project.py` 同步它。
- **每輪一定要維護的只有「待續分支」與「工作中」兩欄**：開工由 skill 的 A5 寫上機器、工具與
  session，交棒由 B6 改回「無（已交棒）」。其餘段落沒變就不用動。

## 任務目標

維護 AI 協作專案管理骨架的權威版 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　26103109｜重測AGY hook｜工作中`，2026-10-31 09:50 (+08) 開工
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。

## 已完成

- 2026-10-31（**刻意不跳版**，`SKILL.md` 一個字沒動）：**把前一輪 Antigravity 探針的結論縮回它實際
  覆蓋的範圍。只改敘述，接線／`verify_bootstrap.py`／`sync_project.py` 都沒動。** 起因是使用者指出
  **Antigravity 與 Antigravity IDE 是不同產品**——查證成立：官方 blog「Choosing your surface」並排列出
  **Antigravity 2.0（獨立桌面 App，無編輯器，官方稱 default recommendation）／Antigravity CLI（`agy`）／
  Antigravity IDE（VS Code fork）／Python SDK** 四個 surface，官方明講沒有 deprecate IDE、建議兩個都裝。
  而前一輪的探針**只跑在 IDE `1.107.0` 上**，結論卻寫成「Antigravity 沒有 hook 這一層」。
  四處斷言改掉（`AGENTS.md` 副本規則、`README.md` 跨工具表＋那段敘述、`ARCHITECT.md` 日期標頭＋拓撲圖、
  部署包的 Antigravity 整節＋跨工具表＋第 5 節驗收項＋`handover-protocol.md` 範本那句），
  → **`verify_bootstrap.py` exit 0，25 項全 ok（18 檔，與前一輪相同）**。
- **決定本身沒變（骨架仍不附 Antigravity 接線），變的是理由與重開它的門檻。** 舊版寫「門檻是比那次
  探針更強的證據」——**那句已取消**：探針測的是四個 surface 裡的一個，不構成要被超越的證據。
  新門檻只是「在你實際用的那個 surface 上，用絕對路徑的 `command` 再測一次」。
- 2026-10-31：前一輪（移除 Antigravity 接線）與更早的工具欄、三平台能力重查等，全部仍然有效，
  理由在部署包版本註與 [ARCHITECT.md](ARCHITECT.md)，這裡不複述。

## 未完成／下一步

1. **重測 Antigravity 的 hook（份量比前一輪記的重，而且現在知道怎麼測）。** 三個洞開著：①**2.0 與
   CLI 完全沒測**（本機三個 surface 都裝著，`~/.gemini/` 下 `antigravity`／`antigravity-cli`／
   `antigravity-ide` 並存，`agy 1.4.7` 在 PATH）；②**`command` 可能必須是絕對路徑**——第三方 CLI 指南
   這樣寫，而鐵律 5「接線路徑一律相對」＋`verify_bootstrap.py` 跨平台防呆**主動擋絕對路徑**，
   那輪還 exit 0 過，所以當時那份 `command` **必然是相對的**，症狀（log 檔沒產生）完全吻合；
   ③**有第三方可重現實測牴觸**（工作區 `.agents/hooks.json` 在三個 flavour 都觸發，log 路徑指向 IDE）。
   **從 CLI 測起**：它有 IDE 沒有的 `/hooks` 面板，分得開「設定沒被讀」與「讀了但沒跑」。
   一併確認 `~/.gemini/trustedFolders.json` 的涵蓋範圍（專案層 hook 要工作區被信任）。
   ⚠️ 若測出來會動，**鐵律 5 與 Antigravity 的絕對路徑要求就是真衝突**，要先決定怎麼解
   （例如接線層自己展開路徑），不要直接在部署包裡寫死絕對路徑。
2. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個工具都
   觸發、`statusMessage` 會不會被忽略。卡在互動式的 `/hooks` 信任（非互動只能用
   `--dangerously-bypass-hook-trust`，刻意沒用）。
3. （可選）`AGENTS.md` 補一段「開工第一件事」——可攜層目前沒有一句叫 agent 先 `git fetch`、先看
   origin 的「工作中」。**對 Antigravity 那一面，可攜層目前仍是唯一的防線。**
4. （可選）`SessionStart` 的 `sessionTitle` 自動寫 session 名稱；`.codex/hooks.json` 接線本 repo 的
   `repo-git-check.sh`（**不要**複製第二份腳本）。
5. **`README.md` 的跨工具表仍然沒有守門人**（`verify_bootstrap.py` 的「跨工具表保鮮期」只讀部署包
   那一張）。同一種「斷言過期／過度一般化」已經錯四次，這次是第四次。

（「階段二 pre-push hook」2026-10-30 決定不裝，理由在 [ARCHITECT.md](ARCHITECT.md)，掃到別再重提。）

## 地雷與注意事項

- **single writer**：同一時間只有一台機器＋一個工具改 `main`。
- 改制度改 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）。
- **只有 `SKILL.md` 真的改了才跳 `VERSION`**（鐵律 1）：這輪沒動它，所以沒跳。
- 🔴 **寫外部工具的能力時，先確認你講的是哪一個產品／surface。** 這輪的教訓不是「文件過期」，是
  **把一個 surface 的實測結果寫成整個產品的性質**。同名不同產品（Antigravity vs Antigravity IDE）
  在斷言裡沒有被區分，於是一次探針失敗被記成一整層能力不存在。
- 🔴 **骨架自己的不變量可能讓探針測不出東西。** 鐵律 5 擋絕對路徑，而被測的工具可能要求絕對路徑——
  驗證通過不代表探針有效。下次設計探針時先問：「這支探針有沒有被我們自己的規則綁住手腳？」
- 公開 repo：全部 Git 歷史人人看得到，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。
- 本檔與 `.claude/hooks/repo-git-check.sh` 都不是部署包的一部分，**不要**用 `sync_project.py` 同步。

## 服務查證與期望快照

這個 repo 沒有 `tools/verify_state.py`——它是骨架的檔，不部署到自己身上。驗證指令是：

`python -X utf8 tools/verify_bootstrap.py`

目前：exit 0，**25 項全 `ok`**，骨架 18 檔（與前一輪相同——這輪只改敘述，沒有增刪範本）。
`VERSION` 仍是 2026-10-31。跨工具表保鮮期的查證日期仍是 2026-10-30（這輪沒有重讀那六頁官方文件，
只查了 Antigravity 的 surface 區分與 hook 路徑，所以**刻意沒有把時鐘歸零**）。

## 懸置事項（AI 勿自行處理）

- 第 1 項要不要做（要在 Antigravity 的 2.0 或 CLI 上實際開 session 測，而且若測通會撞到鐵律 5）。
- 第 2、3、4、5 項要不要做。
