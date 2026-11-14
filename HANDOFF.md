# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 12:3x（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（清掉 NAS_MAINT 與 NAA_TR 的 Antigravity 殘留）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)把 v2 的成果改成 v3 的形狀，分三期：第 1 期 Claude Code＋macOS（已完成並併回 `main`），第 2 期 Codex＋macOS，第 3 期兩個工具＋Windows；前一期驗過才開始下一期。Antigravity 放棄。v3 的一句話：制度只負責模型不會自己知道的事，不教模型怎麼做，也不自己造執行屏障。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：無（`feature/v3` 保留不刪，它那份 HANDOFF 指回 `main`）。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　11.14.12｜接棒善後｜工作中｜交棒0次`，2026-11-14 12:32 (+08) 開工
- **骨架版本**：`2026-11-14.2`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；沒有 `python` 指令，用 `python3`。桌面 App 內附 Claude Code 2.1.321。這台的全域 `~/.claude`、`~/.codex` handoff skill 已是 v2026-11-14.2。

## 已完成

2026-11-14 兩個 session：11.14.11（使用者選「Antigravity 殘留」，依序回「改，並同步」「刪掉」「兩處都改」，最後「五個都交棒」）與 11.14.12（使用者依序選「清 NAS_MAINT 殘留」「NAA_TR 規則檔：刪檔＋改 README」「三邊都交棒」）：

- **部署包 v2026-11-14.2**（d35c36f）：skill `mode-a-stop.md` 三處、`kit.md` 工具名舉例拿掉 Antigravity；`GEMINI.md` 指標寫法的理由改寫成不依賴它。`VERSION`、六個 skill 檔、共用制度標記一起跳版（共用制度內文沒動，但開場 hook 拿那個標記比上游 `VERSION`）；本 repo `AGENTS.md` 副本重貼；`tools/skill_split_baseline.json` 的 `rewritten` 登記三行改寫。
- **四個專案同步並刪接線檔**：鍵鼠同部署_mac、NAS_MAINT、grist-workflow、NAA_TR（在 `feature/W15-research-shell`）都跑了 `sync_project.py`（7 項），刪掉 `.agents/ag-hook.cmd`、`.agents/hooks.json`、`.claude/hooks/ag-wrap.sh`（刪前確認只互相引用），check_docs exit 0，四個都已交棒。
- **全域 skill**：`~/.claude`、`~/.codex` 六個檔覆蓋成 v2026-11-14.2（覆蓋前比對過與舊版逐位元組相同）。
- **NAS_MAINT 殘留**（12dd01e，已交棒）：`AGENTS.md` 三處、`ARCHITECT.md` 兩處照 e7ddfb3 手改；README、handover-protocol 本來就沒有殘留；check_docs exit 0。
- **NAA_TR 規則檔**（6963f21，在 `feature/W15-research-shell`，已交棒）：使用者決定刪掉 `.agents/rules/handoff.md`，README 指路句一併拿掉；pre-push、AGENTS、handover-protocol 的歷史性提及保留；check_docs exit 0。
- 同日稍早的 session：部署包範本拿掉 Antigravity（e7ddfb3）、開場 hook 換成 3.10 逐字副本、補裝 push 前 hook、時間戳改 `MM.DD.HH`（細節在 git log）。

## 未完成／下一步

1. **本 repo 的 Codex 接線改過（多了 PreToolUse），還沒重新審核與驗收**：在 Codex 互動 CLI 的 `/hooks` 審核 `.codex/hooks.json`，再開新 session 確認開場 `[facts]` 進 context、`git push` 時 `repo-pre-push.sh` 有跑。要呼叫模型，先問使用者。
2. 第 2 期 Codex＋macOS：同一套 handoff-ab 兩輪＋互動驗證，換 Codex 跑。要呼叫模型，開始前先問使用者；這個月的額外用量 2026-11-14 已到 94%（$7.54／$8）。
3. 別台機器的全域 `~/.claude`、`~/.codex` handoff skill 還是舊版：從已同步的專案複製六個檔覆蓋。
4. 各專案開場可能印「共用制度比上游新：本機 v2026-11-14.2，上游 v2026-11-14」：上游版本快取 720 分鐘，最晚 12 小時自己消失；要立刻消就由使用者刪該專案的 `.claude/.bootstrap-version`。

## 地雷與注意事項

- **seed 檔不會被同步**：README、ARCHITECT、handover-protocol 等 `owners.json` 標 `seed` 的範本只在建制時發一次；改了範本，已部署專案要逐個手改。
- **本 repo 有三份手貼副本**：`AGENTS.md` 的共用制度（對 `AGENTS.md.tmpl`）、`repo-git-check.sh`（對 3.10）、`repo-pre-push.sh`（對 3.11）。改了範本要手動重貼（`sync_project.py` 拒絕本 repo），否則對應驗證項 FAIL。
- **改 skill 檔的既有行要登記 `tools/skill_split_baseline.json`**：拆分前的舊行不在任何檔、也不在 `rewritten`，「skill 拆分」就 FAIL。
- **跳 `VERSION` 時共用制度標記也要跳**：開場 hook 拿 `AGENTS.md` 共用制度標記比上游 `VERSION`，只跳 skill 會讓每個專案一直印落後。
- **本 repo 現在推 `main` 會被擋**：沒寫開工標記、這次推送又沒改 `HANDOFF.md` 時 exit 2。照共用制度條件 1 先推開工標記就不會撞到。
- 本 repo hook 不能改名成 `pre-push-handoff.sh`／`git-freshness.sh`：「本 repo 兩份接線」把指向這兩個名字當成被同步工具覆蓋過。
- **`approvals.py` 留在 `src/` 但沒有測試**：測試靠 `launcher`，跟著封存了；`release` 只用它的 `VERIFIER`。
- **一致性檢查對 v2 已決的題號很敏感**：在 `README`、`AGENTS`、`ARCHITECT`、`HANDOFF` 裡，提到 v2 題號的那一行不要同時出現「待決」兩個字，否則 `test_contradictions_repo` 會誤判。
- **待決登記處有兩個**：工具認得的是 v2 決策書第 6 節；v3 新增的題目在 v3 第 8 節。「懸置事項」只能寫 v2 已登記的題目；v3 的題目等使用者決定時寫在「未完成／下一步」。
- **跨工具表**：README 那張是部署包能力矩陣（`src/kit/capabilities.json`）的轉述，一致性檢查綁住；有 `text` 的格一定要被渲染一次。
- 帳號允許超額，撞到訂閱上限會直接扣額外用量而不報錯。handoff-ab 的 `run.py` 有用量守門，不要拿掉；互動測試沒有守門。
- Claude Code 會用家目錄的 handoff skill 蓋掉專案那份；受測期間要把全域副本暫時換成受測版、跑完換回。
- 改這個 repo 的其他地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」，碰到對應的檔才讀。

## 服務查證與期望快照

- 2026-11-14 12:3x（11.14.12 session，本 repo 只改 `HANDOFF.md`）：逐檔 stage 後 `verify_bootstrap.py --staged` exit 0；pytest 沒重跑。NAS_MAINT、NAA_TR 各自 check_docs exit 0，接線沒動。
- 2026-11-14 11:5x 在 `main`（d35c36f 提交前的工作樹）：`verify_bootstrap.py` exit 0（0 skip），逐檔 stage 後 `--staged` exit 0；`uv run --locked pytest` 435 通過。`verify_v2.py` 本 session 沒跑。
- B3：本 repo 沒有 `verify_state.py`，用 `verify_bootstrap.py`。B4：沒有 `check_docs.py`（已宣告例外）。B5：本 repo 的 Codex 接線**有改**（稍早 session），重新審核與實際執行驗收**沒做**（見下一步 1）。四個專案的接線（`.claude/settings.json`、`.codex/hooks.json`）本 session 沒動，同步器報 ok。
- push 前 hook：Claude Code 這邊擋下與兩種放行都實測過；Codex 那邊沒測。
- 模型呼叫：兩個 session 都沒有額外的模型呼叫。

## 懸置事項（AI 勿自行處理）

- 無。
