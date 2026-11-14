# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 11:43（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（部署包範本與鍵鼠同部署_mac 拿掉已退場的 Antigravity）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)把 v2 的成果改成 v3 的形狀，分三期：第 1 期 Claude Code＋macOS（已完成並併回 `main`），第 2 期 Codex＋macOS，第 3 期兩個工具＋Windows；前一期驗過才開始下一期。Antigravity 放棄。v3 的一句話：制度只負責模型不會自己知道的事，不教模型怎麼做，也不自己造執行屏障。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：無（`feature/v3` 保留不刪，它那份 HANDOFF 指回 `main`）。
- **工作中**：Mac ／ Claude Code ／ 11.14.11｜Antigravity殘留（2026-11-14 11:5x 開工）
- **骨架版本**：`2026-11-14.2`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；沒有 `python` 指令，用 `python3`。桌面 App 內附 Claude Code 2.1.321。這台的全域 `~/.claude`、`~/.codex` handoff skill 已是 v2026-11-14。

## 已完成

2026-11-14 本 session（使用者依序回「清 Antigravity 舊段落」「先修部署包範本」「同步過去」「交棒鍵鼠」「也交棒」）：

- **部署包範本拿掉 Antigravity**（e7ddfb3）：`src/kit/files/` 的 `README.md.tmpl`、`ARCHITECT.md.tmpl`、`docs/ai-notes/handover-protocol.md.tmpl` 不再寫它會讀 `.agents/skills/`、hook 已接它、骨架附它的接線；部署包重生。skill 檔與 `kit.md` 的歷史紀錄沒動，`VERSION` 不跳。
- **鍵鼠同部署_mac**：`AGENTS.md` 三處（2db9297）；README、ARCHITECT、handover-protocol 照上面的範本手改（4f72d86）——這三個在 `owners.json` 是 `seed`，`sync_project.py` 預演確認不會更新它們，其他共用檔已是最新版。該專案已交棒（「工作中」無）。
- **NAS_MAINT 沒動**：當時 origin 上「工作中」是 `Mac mini` 11:13 開工的另一個 session（例行安全審查）。
- 同日稍早的 session：開場 hook 換成 3.10 逐字副本、補裝 push 前 hook 並在 Claude Code 實測三條路、拿掉動作提醒 hook、時間戳改 `MM.DD.HH`、四個專案與全域升 v2026-11-14（細節在 git log 與 ARCHITECT 表頭）。

## 未完成／下一步

1. **本 repo 的 Codex 接線改過（多了 PreToolUse），還沒重新審核與驗收**：在 Codex 互動 CLI 的 `/hooks` 審核 `.codex/hooks.json`，再開新 session 確認開場 `[facts]` 進 context、`git push` 時 `repo-pre-push.sh` 有跑。要呼叫模型，先問使用者。
2. 第 2 期 Codex＋macOS：同一套 handoff-ab 兩輪＋互動驗證，換 Codex 跑。要呼叫模型，開始前先問使用者；這個月的額外用量 2026-11-14 已到 94%（$7.54／$8）。
3. **NAS_MAINT 的 Antigravity 舊段落**：`AGENTS.md` 第 3、44、101 行，以及 README／ARCHITECT／handover-protocol（seed 檔，要照 e7ddfb3 手改）。等那邊的「工作中」清掉才能動。
4. **Antigravity 殘留等使用者決定**：①skill 的 `mode-a-stop.md.tmpl` 還有三處（舉例與「它沒有 SessionEnd」），要改就得跳 `VERSION`、六檔標記同版再同步；②已部署專案裡的 `.agents/ag-hook.cmd`、`.agents/hooks.json`、`.claude/hooks/ag-wrap.sh` 照原則不刪；③`kit.md` 第 191、307 行的工具名舉例與 `GEMINI.md` 理由還提到它（非歷史紀錄，但沒說它被支援）。
5. 別台機器的全域 `~/.claude`、`~/.codex` handoff skill 還是 v2：那台接棒時開場 hook 會印「家目錄與本專案不同」，從已同步的專案複製六個檔覆蓋。

## 地雷與注意事項

- **seed 檔不會被同步**：README、ARCHITECT、handover-protocol 等 `owners.json` 標 `seed` 的範本只在建制時發一次；改了範本，已部署專案要逐個手改。
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

- 2026-11-14 11:3x 在 `main`（範本修正 e7ddfb3 提交前的工作樹）：`verify_bootstrap.py` exit 0（66 項 ok、0 skip），逐檔 stage 後 `--staged` exit 0；`uv run --locked pytest` 435 通過。`verify_v2.py` 本 session 沒跑。
- B3：本 repo 沒有 `verify_state.py`，用 `verify_bootstrap.py`。B4：沒有 `check_docs.py`（已宣告例外）。B5：本 repo 的 Codex 接線**有改**（稍早 session），重新審核與實際執行驗收**沒做**（見下一步 1）。
- push 前 hook：Claude Code 這邊擋下與兩種放行都實測過；Codex 那邊沒測。
- 模型呼叫：本 session 沒有額外的模型呼叫。

## 懸置事項（AI 勿自行處理）

- 無。
