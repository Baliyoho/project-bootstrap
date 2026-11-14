# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 21:34（+08）
- **交棒者**：Claude Code 桌面 App／Mac（Codex 接棒成本優化）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)分期驗收交接制度：第 1 期 Claude Code＋macOS 已完成；第 2 期 Codex＋macOS 的 handoff-ab 已完成，桌面 App 標題項未驗；第 3 期兩工具＋Windows 尚未開始。本輪另外處理 Codex 接棒慢、耗量的問題。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支 `main`。
- **待續分支**：無；`feature/v3` 保留但不是待續分支。
- **工作中**：Mac ／ Codex 桌面 App ／ ㊣　11.14.21｜接棒成本驗收｜工作中｜交棒0次，2026-11-14 21:37 (+08) 開工
- **骨架版本**：`2026-11-14.3`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；無 `python` 指令，使用 `python3`。本機兩份全域 handoff skill（Claude Code、Codex）已覆蓋成 `v2026-11-14.3`，逐檔與範本相同。

## 已完成

- 2026-11-14 第 2 期 Codex＋macOS：handoff-ab 第一輪 12／12、第二輪 6／6 通過，損害格 0；F50 的 CLI 部分符合。詳見 [CODEX-RESULTS.md](experiments/handoff-ab/CODEX-RESULTS.md)。
- 查明上一次 Codex 桌面 App 接棒（21:02–21:05，累計輸入 1,119,828 tokens）的成本來源：28 次模型呼叫裡 15 次是在等 `verify_bootstrap.py`（每次約 54 秒，跑了兩次）時每 5 秒輪詢一次；每次呼叫重送約 35k–45k 上下文。
- `991baf3`：handoff skill 加「跑得久的指令」一節（工具先交回時一次把等待時間設到夠跑完，例如 `yield_time_ms` ≥ 60000），理由與數字寫在 `reasons.md`；`VERSION` 與標記跳到 `2026-11-14.3`。

## 未完成／下一步

1. **Codex 驗收這次優化（使用者正要做）**：使用者在新的 Codex 桌面 App 聊天說「接棒」。驗收看該次 rollout（`~/.codex/sessions/<日期>/rollout-*.jsonl`）：模型呼叫次數、`write_stdin` 空等次數、累計輸入，對照上次的 28 次／15 次／112 萬。結果記進 CODEX-RESULTS.md 的「sol 中 在codex的接棒花費」一節之後；未量到之前不得寫成已改善。
2. 已部署專案尚未同步到 `2026-11-14.3`，要逐專案跑 `sync_project.py`，須使用者另行授權。
3. 開場 hook 印「共用制度比上游新：本機 v2026-11-14.3，上游 v2026-11-14」；改版前就有同樣訊息（.2 對 v2026-11-14），「上游」取自哪裡尚未查。
4. 第 2 期 F50 桌面 App 標題項：使用者決定先不建測試聊天，CLI 的 `不適用` 不能代替。
5. 第 3 期在 Windows 驗兩工具；Windows Codex 的新版 SessionStart JSON 接線未實跑，當地全域 handoff skill 仍舊。先同步 skill、核對本機 Git 殘留，不要推舊 session 的未推 commit。

## 地雷與注意事項

- 制度權威在 `src/kit/`；改範本後重生部署包、同步所有副本並驗證實際 hook。本 repo 的手貼副本需另行同步，詳見 [AGENTS.md](AGENTS.md)。
- 推開工標記前的 `verify_bootstrap.py --staged` 本輪刻意保留：驗證器會檢查 HANDOFF 欄位，不是多餘的。
- 公開 repo 不放部署專案私有細節或憑證。`main` 測試須維持通過；功能分支合併仍要使用者驗收。

## 服務查證與期望快照

- 2026-11-14 21:32 Mac：`python3 -X utf8 tools/verify_bootstrap.py` 與 `--staged` 皆 exit 0；`uv run --locked pytest -q` 435 passed、369 subtests passed（`991baf3` 提交前）。交棒提交前再以 `--staged` 驗。
- `verify_bootstrap.py` 單次約 54 秒（本機實測）。

## 懸置事項（AI 勿自行處理）

- 無。
