# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 11:19（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（實測本 repo 的 Claude Code push 前 hook）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)把 v2 的成果改成 v3 的形狀，分三期：第 1 期 Claude Code＋macOS（已完成並併回 `main`），第 2 期 Codex＋macOS，第 3 期兩個工具＋Windows；前一期驗過才開始下一期。Antigravity 放棄。v3 的一句話：制度只負責模型不會自己知道的事，不教模型怎麼做，也不自己造執行屏障。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：無（`feature/v3` 保留不刪，它那份 HANDOFF 指回 `main`）。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-14`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；沒有 `python` 指令，用 `python3`。桌面 App 內附 Claude Code 2.1.321。這台的全域 `~/.claude`、`~/.codex` handoff skill 已是 v2026-11-14。

## 已完成

2026-11-14 前一個 session，每項都經使用者在聊天中要求或決定（使用者問「交接制度有完全合乎 v3 嗎？沒有就先合規」，之後逐項回「裝」「拿掉」「改掉」）：

- **開場 hook**：`.claude/hooks/repo-git-check.sh` 從自己寫的判讀版（🔴／🟡、全綠行）換成 3.10 `git-freshness.sh` 的逐字副本，只印 `[facts]`。驗證項「本 repo 開場 hook」逐位元組比對；「本 repo 工作中判讀」「全綠行」退場。`.gitignore` 加 `.claude/.bootstrap-version`。
- **AGENTS.md 開工段**改名「跟部署出去的專案不同的地方」，只寫事實，不再要求先走 A 模式（v3 D12、第 5 節）。
- **補裝 push 前 hook**：`.claude/hooks/repo-pre-push.sh` 是 3.11 的逐字副本，兩份接線都接 PreToolUse。ARCHITECT 的已宣告例外剩 handoff skill 與 `check_docs.py` 兩項。驗證項「本 repo push 前 hook」含 7 個接線負向測試。
- **拿掉 `repo-action-rules.sh`** 與它的 PostToolUse 接線、驗證項「動作當下送規則」。
- **能力表** `loads-skill` 的替代做法不再指向已不存在的「開工第一件事」；`kit.md` 的 Codex 截斷提醒改指共用制度；部署包重生（`VERSION` 不動，skill 六檔沒改）。
- **Claude Code 的 push 前 hook 在本 repo 實測三條路**（本 session 11:1x，使用者回「做第 2 項」；開工標記上寫的 11:20 是誤植，實際約 11:14）：用本機暫時的空 commit 配 `git push --dry-run`，origin「工作中」為「無（已交棒）」時被擋（exit 2、訊息進 context）；推開工標記（差異含 `HANDOFF.md`）時放行；標記推上去後的 dry-run 也放行。兩個暫時 commit 都沒推，已用 `reset --soft` 拿掉。
- 同日稍早的 session：時間戳改 `MM.DD.HH`、`sync_project.py` 同步共用制度、四個專案與全域升 v2026-11-14、Q33／Q34／F10 定案（細節在 git log 與 ARCHITECT 表頭）。

## 未完成／下一步

1. **本 repo 的 Codex 接線改過（多了 PreToolUse），還沒重新審核與驗收**：在 Codex 互動 CLI 的 `/hooks` 審核 `.codex/hooks.json`，再開新 session 確認開場 `[facts]` 進 context、`git push` 時 `repo-pre-push.sh` 有跑。要呼叫模型，先問使用者。
2. 第 2 期 Codex＋macOS：同一套 handoff-ab 兩輪＋互動驗證，換 Codex 跑。要呼叫模型，開始前先問使用者；這個月的額外用量 2026-11-14 已到 94%（$7.54／$8）。
3. 別台機器的全域 `~/.claude`、`~/.codex` handoff skill 還是 v2：那台接棒時開場 hook 會印「家目錄與本專案不同」，從已同步的專案複製六個檔覆蓋。
4. NAS_MAINT 與鍵鼠同部署_mac 的 `AGENTS.md` 舊段落還提到 Antigravity（過時，但照原則沒動），清不清等使用者決定。

## 地雷與注意事項

- **本 repo 有三份手貼副本**：`AGENTS.md` 的共用制度（對 `AGENTS.md.tmpl`）、`repo-git-check.sh`（對 3.10）、`repo-pre-push.sh`（對 3.11）。改了範本要手動重貼（`sync_project.py` 拒絕本 repo），否則對應驗證項 FAIL。
- **本 repo 現在推 `main` 會被擋**：沒寫開工標記、這次推送又沒改 `HANDOFF.md` 時 exit 2。照共用制度條件 1 先推開工標記就不會撞到。
- 本 repo hook 不能改名成 `pre-push-handoff.sh`／`git-freshness.sh`：「本 repo 兩份接線」把指向這兩個名字當成被同步工具覆蓋過。
- **`approvals.py` 留在 `src/` 但沒有測試**：測試靠 `launcher`，跟著封存了；`release` 只用它的 `VERIFIER`。
- **一致性檢查對 v2 已決的題號很敏感**：在 `README`、`AGENTS`、`ARCHITECT`、`HANDOFF` 裡，提到 v2 題號的那一行不要同時出現「待決」兩個字，否則 `test_contradictions_repo` 會誤判。
- **待決登記處有兩個**：工具認得的是 v2 決策書第 6 節；v3 新增的題目在 v3 第 8 節。「懸置事項」只能寫 v2 已登記的題目；v3 的題目等使用者決定時寫在「未完成／下一步」。
- **共用制度的版本就是 `VERSION`**：共用制度、六個 skill 檔與 `VERSION` 要同版。改了共用制度卻不改 skill 時怎麼跳版還沒定案。
- **跨工具表**：README 那張是部署包能力矩陣（`src/kit/capabilities.json`）的轉述，一致性檢查綁住；有 `text` 的格一定要被渲染一次。
- 帳號允許超額，撞到訂閱上限會直接扣額外用量而不報錯。handoff-ab 的 `run.py` 有用量守門，不要拿掉；互動測試沒有守門。
- Claude Code 會用家目錄的 handoff skill 蓋掉專案那份；受測期間要把全域副本暫時換成受測版、跑完換回。
- 改這個 repo 的其他地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」，碰到對應的檔才讀。

## 服務查證與期望快照

- 2026-11-14 11:18 在 `main`（aca3ab8，本 session 只改 `HANDOFF.md`）：`verify_bootstrap.py` exit 0（66 項 ok、0 skip）；`uv run --locked pytest` 435 通過。`verify_v2.py` 本 session 沒重跑（上次 11:0x 通過）。
- B3：本 repo 沒有 `verify_state.py`，用 `verify_bootstrap.py`。B4：沒有 `check_docs.py`（已宣告例外）。B5：本 repo 的 Codex 接線**有改**，重新審核與實際執行驗收**沒做**（見下一步 1）。
- push 前 hook：Claude Code 這邊擋下與兩種放行都實測過（見已完成）；Codex 那邊沒測。
- 模型呼叫：本 session 沒有額外的模型呼叫。

## 懸置事項（AI 勿自行處理）

- 無。
