# HANDOFF — 工作交接狀態

- **交接時間**：2026-10-30 18:40（+08）
- **交棒者**：Claude Opus 5 ／ `DESKTOP-M8MRS05`（三平台能力重查，修掉四個過期斷言並加保鮮期檢查）

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

- 2026-10-30（本輪，`VERSION` 2026-10-30.3）：**三邊官方文件全部重查＋本機實測 Codex CLI `0.164.0`**，修掉
  四個過期斷言——Codex 桌面 App 其實有 hooks、`.agents/skills/` 連 Codex 也讀、`CLAUDE.md` 要改成只放
  `@AGENTS.md` import（有 `CLAUDE.md` 時 Claude Code 不原生讀 `AGENTS.md`）、`SessionEnd` 存在所以「關掉
  視窗沒有下一個動作」只對一半的工具成立（結論不變，理由換掉）。連帶改了 `extract()`、`sync_project.py`
  的 `CLAUDE.md` 歸類，並加上**跨工具表保鮮期**檢查（超過 90 天 fail，負向測試已驗）。逐項理由見部署包
  開頭的版本註與 [ARCHITECT.md](ARCHITECT.md)。
- 2026-10-30（同日早先）：補跨機器「工作中」標記；評估後**決定不裝** `pre-push-handoff.sh`；修正跨工具
  表的 Antigravity 一欄。理由在 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」。

## 未完成／下一步

1. 🔴 **骨架同步還沒落地**：`Grist_test`、`NAA_TR`、`NAS_MAINT`、`摘要skill設計`、`第三批56箱後檢查`
   已經跑過 `sync_project.py --write`，**各有 3 個未提交的檔**（兩份 `SKILL.md` ＋ `CLAUDE.md` 的 import）。
   要到各專案照 B 模式收尾：先跑 A2.5 確認沒有別台機器握著它的 main，而且它們的 pre-push hook 會要求
   那批 commit 動過自己的 `HANDOFF.md`。另兩個**刻意沒同步**，`SKILL.md` 還停在 `.2`：`序號卡`（已完結，
   不想在沒人會 commit 的 repo 留殘留）、`解決網路速度問題`（有別人未提交的工作）——這兩個會在下次開場
   自己報「骨架落後」，是自癒的，不急。
2. **兩件 Codex hook 行為還沒實測**：`.codex/hooks.json` 的 `PreToolUse` 沒 matcher 時會不會對每個工具都
   觸發、`statusMessage` 會不會被忽略。卡在互動式的 `/hooks` 信任（非互動只能用
   `--dangerously-bypass-hook-trust`，本輪刻意沒用）。
3. （可選，要實測）Antigravity `.agents/hooks.json`：設計已定——一支**只做管線**的 wrapper，讀 stdin 取
   `workspacePaths[0]`、`cd` 過去、跑同一支 `.sh`、stdout 包成 `injectSteps` 的 `ephemeralMessage`。
4. （可選）`SessionStart` 的 `sessionTitle` 自動寫 session 名稱（只固定得住開場那一半，狀態轉換仍靠模型）；
   `.codex/hooks.json` 接線本 repo 的 `repo-git-check.sh`（**不要**複製第二份腳本）；`AGENTS.md` 補一段
   「開工第一件事」——可攜層目前沒有一句叫 agent 先 `git fetch`、先看 origin 的「工作中」。

（「階段二 pre-push hook」2026-10-30 決定不裝，理由在 [ARCHITECT.md](ARCHITECT.md)，掃到別再重提。）

## 地雷與注意事項

- **single writer**：同一時間只有一台機器改 `main`。現在開工有標記了，但標記只告訴你「有東西在
  那台機器上」——**別台未提交的變更仍然只在那台的磁碟上**，得回去那台 push，這是標記機制的天花板。
- 改制度改 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)，改完 `verify_bootstrap.py` 要 exit 0（鐵律 4）。
- 本檔與 `.claude/hooks/repo-git-check.sh` 都不是部署包的一部分，**不要**用 `sync_project.py` 同步。
- 公開 repo：全部 Git 歷史人人看得到，不要寫單位名稱、內部代號、本機絕對路徑（鐵律 6）。

## 服務查證與期望快照

這個 repo 沒有 `tools/verify_state.py`——它是骨架的檔，不部署到自己身上。驗證指令是：

`python -X utf8 tools/verify_bootstrap.py`

目前：exit 0，**24 項全 `ok`**（`VERSION` 2026-10-30.3）。新增的那一項是「跨工具表保鮮期」。

## 懸置事項（AI 勿自行處理）

- 上面「未完成」第 2、3、4 項要不要做（都要花時間實測或設計，不是順手能完成的）。第 1 項不是懸置，是待收尾。
