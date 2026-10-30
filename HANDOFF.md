# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-30 17:25（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（修正跨工具表的 Antigravity 一欄）

## 這份檔案在這個 repo 的角色（跟其他專案不一樣，先讀這段）

**它只有一個任務：當跨機器「工作中」標記的載體。** 這個 repo 是制度的來源、刻意沒有 handoff
skill 也沒有知識庫（見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」），所以：

- **不要把這裡當狀態日誌或知識庫。** 鐵律「這裡不是知識庫」照舊；跨 session 的事實看 `git log`
  與各檔的 `source:` 版本標記。這一份要短，短到每輪交棒都願意維護它——會腐化的文件就是從
  「順手多寫兩段」開始的。
- **它是部署包範本 3.3 的*實例*，不是副本。** `sync_project.py` 的 `discover()` 靠 handoff skill
  認專案，掃不到這個 repo；`PARTIAL` 也只會在缺欄位時補欄位。所以它沒有同步義務，改它不必
  動 `VERSION`，也不要拿 `sync_project.py` 同步它。
- **每輪一定要維護的只有「待續分支」與「工作中」兩欄**：開工由 skill 的 A5 寫上機器與 session，
  交棒由 B6 改回「無（已交棒）」。其餘段落沒變就不用動。

## 任務目標

維護 AI 協作專案管理骨架的權威版 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- 本機能力：Windows 11 ＋ Git for Windows 的 bash；有 push 權限（不寫祕密值）。

## 已完成

- 2026-10-30：補上跨機器「工作中」標記。本檔當載體、`.claude/hooks/repo-git-check.sh` 加判讀段
  （🔴 別台／🟡 同台／✅ 已交棒／🟡 欄位不存在）、`tools/verify_bootstrap.py` 加一項測這支 hook
  的四情境。在此之前這個 repo 的 single writer 完全靠人顧，取捨記在 [ARCHITECT.md](ARCHITECT.md)。

- 2026-10-30：評估「階段二」`pre-push-handoff.sh`，**決定這個 repo 不裝**。否決理由（含「加計數器
  欄位讓 bump 它就能過」這個變通為什麼更糟）寫進 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有
  的東西」，連同它失效的條件。部署包本身沒動，`verify_bootstrap.py` exit 0。

- 2026-10-30：**修正「跨工具與跨平台」表的 Antigravity 一欄**——它現在有 `.agents/hooks.json`
  ＋ `SessionStart`，舊表的「❌ 沒有 hook 機制」是 2026-08-05 的事實。連同 `ARCHITECT.md` 與
  `handover-protocol.md` 兩份範本裡跟著錯的句子。**刻意沒附 `.agents/hooks.json` 範本**（相對路徑
  解析與 stdout 格式官方沒寫，猜錯是靜默失效），也**刻意沒跳 `VERSION`**——理由寫進 AGENTS.md
  鐵律 1：`VERSION` 實際上是 `SKILL.md` 的版本，這次沒動 `SKILL.md`，跳版會讓每個專案永遠印
  「骨架落後」且同步修不掉。

## 未完成／下一步

1. （可選）`.codex/hooks.json` 接線同一支 `repo-git-check.sh`，讓 Codex 開場也看得到這個檢查
   （**不要**複製第二份腳本）。目前只有 Claude Code 的 SessionStart 會跑它。
2. （可選，要實測）Antigravity 的 `.agents/hooks.json` 同樣可以接 `repo-git-check.sh`，但先在機器上
   確認兩件事：相對路徑對著哪個 cwd 解析、`echo` 出來的文字會不會被顯示（它的 stdout 是
   `injectSteps` JSON 契約）。兩件事任一不成立就別接——不會觸發的 hook 比沒有更糟。
3. （可選）`AGENTS.md` 補一段「開工第一件事」。這個 repo 的可攜層目前沒有任何一句叫 agent 先
   `git fetch`、先看 origin 的「工作中」——接棒程序在全域 skill，只有 Claude Code 會自動載入，
   所以 Codex 桌面 App 與沒接線的 Antigravity 開這個 repo 時完全沒有提醒。

（原本的「階段二 pre-push hook」2026-10-30 決定不裝，理由寫在 [ARCHITECT.md](ARCHITECT.md)
「這個 repo 刻意沒有的東西」，掃到別再重提。）

## 地雷與注意事項

- **single writer**：同一時間只有一台機器改 `main`。現在開工有標記了，但標記只告訴你「有東西在
  那台機器上」——**別台未提交的變更仍然只在那台的磁碟上**，得回去那台 push，這是標記機制的天花板。
- 改制度改 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）。
- 本檔與 `.claude/hooks/repo-git-check.sh` 都不是部署包的一部分，**不要**用 `sync_project.py` 同步。
- 公開 repo：全部 Git 歷史人人看得到，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。

## 服務查證與期望快照

這個 repo 沒有 `tools/verify_state.py`——它是骨架的檔，不部署到自己身上。驗證指令是：

`python -X utf8 tools/verify_bootstrap.py`

目前：exit 0，23 項全 `ok`（`VERSION` 2026-10-30.2）。

## 懸置事項（AI 勿自行處理）

- 上面「未完成」那一項（Codex 接線）要不要做。
