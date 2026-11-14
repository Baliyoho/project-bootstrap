# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 10:35（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（session 名時間戳改 MM.DD.HH、四個專案與全域升到 v2026-11-14、ARCHITECT 四項與 Q33／Q34／F10 定案）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)把 v2 的成果改成 v3 的形狀，分三期：第 1 期 Claude Code＋macOS（已完成並併回 `main`），第 2 期 Codex＋macOS，第 3 期兩個工具＋Windows；前一期驗過才開始下一期。Antigravity 放棄。v3 的一句話：制度只負責模型不會自己知道的事，不教模型怎麼做，也不自己造執行屏障。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：無（`feature/v3` 保留不刪，它那份 HANDOFF 指回 `main`）。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-14`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；沒有 `python` 指令，用 `python3`。桌面 App 內附 Claude Code 2.1.321。這台的全域 `~/.claude`、`~/.codex` handoff skill 已是 v2026-11-14。

## 已完成

2026-11-14，每項都經使用者在聊天中決定或授權：

- **session 名稱時間戳 `YYMMDDHH` → `MM.DD.HH`**：共用制度、skill 六檔、開場 hook、本 repo 的 `repo-git-check.sh`、驗證器、v2 原型與測試一起改；`VERSION` 跳 `2026-11-14`。舊名字不必改，「工作中」判讀靠全形豎線。
- **`sync_project.py` 會同步 `AGENTS.md` 的共用制度**：只換標記之間，沒有就插在第一個「## 」前，標記外不動，舊交接段落列 MIGRATE；驗證項「同步共用制度」含負向測試。
- **四個專案升到 v2026-11-14**：NAA_TR（`feature/W15-research-shell`）、NAS_MAINT、grist-workflow、鍵鼠同部署_mac 各自開工→寫入→check_docs→push→清標記，origin 上都是 `無（已交棒）`。標記外的舊段落沒矛盾，照使用者原則保留。
- **全域 skill 換 v3**；本 repo `AGENTS.md` 貼入共用制度逐字副本（理由在 AGENTS-reasons 的 `shared`），驗證器要求它跟部署包逐字相同。
- **ARCHITECT 列給使用者的四項定案**：push hook 維持 exit 2（依 D13）、check_docs 壞格式 exit 2 保留、兩項 skill 句子契約保留；README 與部署包能力矩陣拿掉 Antigravity。
- **v3 第 8 節**：Q34 已決；Q33 封存——除了 `broker` 的執行屏障模組、VM 腳本與測試搬到 [archive/v2-barrier/](archive/v2-barrier/README.md)，`verify_v2` 不再跑探針與同 UID 反例。F10 強度改成「偵測＋阻擋（限 push 前 hook）」。

## 未完成／下一步

1. 第 2 期 Codex＋macOS：同一套 handoff-ab 兩輪＋互動驗證，換 Codex 跑。要呼叫模型，開始前先問使用者；這個月的額外用量 2026-11-14 已到 94%（$7.54／$8）。
2. 別台機器的全域 `~/.claude`、`~/.codex` handoff skill 還是 v2：那台接棒時開場 hook 會印「家目錄與本專案不同」，從已同步的專案複製六個檔覆蓋。
3. NAS_MAINT 與鍵鼠同部署_mac 的 `AGENTS.md` 舊段落還提到 Antigravity（過時，但照原則沒動），清不清等使用者決定。

## 地雷與注意事項

- **本 repo `AGENTS.md` 的共用制度是手貼副本**：改了 `src/kit/files/AGENTS.md.tmpl` 的共用制度要手動重貼（`sync_project.py` 拒絕本 repo），否則「規則理由連結」會 FAIL。
- **`approvals.py` 留在 `src/` 但沒有測試**：測試靠 `launcher`，跟著封存了；`release` 只用它的 `VERIFIER`。要動發布鏈時記得這點。
- **一致性檢查對 v2 已決的題號很敏感**：在 `README`、`AGENTS`、`ARCHITECT`、`HANDOFF` 裡，提到 v2 題號的那一行不要同時出現「待決」兩個字，否則 `test_contradictions_repo` 會誤判。
- **待決登記處有兩個**：工具認得的是 v2 決策書第 6 節；v3 新增的題目在 v3 第 8 節。「懸置事項」只能寫 v2 已登記的題目；v3 的題目等使用者決定時寫在「未完成／下一步」。
- **共用制度的版本就是 `VERSION`**：「AGENTS.md 共用制度」與「skill 拆分」要求共用制度、六個 skill 檔與 `VERSION` 同版。改了共用制度卻不改 skill 時怎麼跳版還沒定案。
- **跨工具表**：README 那張是部署包能力矩陣（`src/kit/capabilities.json`）的轉述，一致性檢查綁住；`capabilities.json` 裡有 `text` 的格一定要被渲染一次，不顯示的格要拿掉 `text`。
- 帳號允許超額，撞到訂閱上限會直接扣額外用量而不報錯。handoff-ab 的 `run.py` 有用量守門，不要拿掉；互動測試沒有守門。
- Claude Code 會用家目錄的 handoff skill 蓋掉專案那份；受測期間要把全域副本暫時換成受測版、跑完換回。
- 改這個 repo 的其他地雷在 [ARCHITECT.md](ARCHITECT.md)「開發注意事項」，碰到對應的檔才讀。

## 服務查證與期望快照

- 2026-11-14 10:3x 在 `main`：`verify_bootstrap.py --staged` exit 0（67 項 ok、0 skip）；`uv run --locked pytest` 435 通過（Q33 封存前 651）；`verify_v2.py` 428 個測試通過。mutation 只重跑 `tests.test_contracts`（19 全擋）與 `tests.test_broker`（20 全擋，2 個存活的移進封存）。
- B3：本 repo 沒有 `verify_state.py`，A4／B 用 `verify_bootstrap.py`。B4：沒有 `check_docs.py`（已宣告例外）。B5：本 repo 的 Codex 接線沒改，不適用；四個專案的 `.codex/hooks.json` 同步時是 ok（沒改），也不適用。
- 模型呼叫：本 session 沒有額外的模型呼叫。

## 懸置事項（AI 勿自行處理）

- 無。
