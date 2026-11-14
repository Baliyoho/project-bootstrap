# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 20:57（+08）
- **交棒者**：Codex／Mac（Codex 接線與第 2 期 macOS 制度驗收）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)分期驗收交接制度：第 1 期 Claude Code＋macOS 已完成；第 2 期 Codex＋macOS 的 handoff-ab 已完成，桌面 App 標題項未驗；第 3 期兩工具＋Windows 尚未開始。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支 `main`。
- **待續分支**：無；`feature/v3` 保留但不是待續分支。
- **工作中**：`Mac` ／ `Codex 桌面 App` ／ `㊣　11.14.21｜接棒｜工作中｜交棒0次`，2026-11-14 21:04 (+08) 開工
- **骨架版本**：`2026-11-14.2`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；無 `python` 指令，使用 `python3`。本機兩份全域 handoff skill 與部署包相同。

## 已完成

- Codex SessionStart hook 修正為 `hookSpecificOutput.additionalContext` JSON（`46f4a26`），本 repo 與四個已部署專案的開場事實已在 Codex CLI 互動驗收；PreToolUse 放行路徑與隔離 repo 的阻擋路徑也已實測。詳見 [CODEX-RESULTS.md](experiments/handoff-ab/CODEX-RESULTS.md) 與 Git 歷史。
- 2026-11-14 第 2 期 Codex＋macOS：handoff-ab 完整組第一輪 12／12、第二輪 6／6 通過，損害格 0；18 份 rollout 都是 `gpt-6-sol`、收到 `[facts]` 並載入專案 skill。F50 在同一個 CLI 聊天跑完五輪：Git 接棒、兩次交棒、只讀續聊、等決定與要求的 `session：` 行符合。CLI 無改名工具，桌面 App 標題項沒有宣稱通過。方法、原始資料位置與限制在 [CODEX-RESULTS.md](experiments/handoff-ab/CODEX-RESULTS.md)。
- 新增 `codex_run.py` 與六項正負向探針 `codex_selfcheck.py`；原始受測 repo 與 JSONL 留在系統暫存目錄，未進公開 repo。使用者授權用訂閱額度，逐格查用量；沒有使用額外點數。

## 未完成／下一步

1. 使用者已決定先記錄 CLI 結果，不建立桌面 App 測試聊天。之後若要完成第 2 期 F50，須在獨立 Codex 桌面 App 聊天驗標題符號、固定起始時間、狀態與交棒累計；CLI 的 `不適用` 不能代替此項。
2. 第 3 期在 Windows 驗兩工具；Windows Codex 的新版 SessionStart JSON 接線尚未實跑，當地全域 handoff skill 仍舊。先同步 skill，核對本機 Git 殘留，不要推舊 session 的未推 commit。

## 地雷與注意事項

- 制度權威在 `src/kit/`；改範本後重生部署包、同步所有副本，並驗證實際 hook。這個 repo 的三份手貼副本不由 `sync_project.py` 更新，詳見 [AGENTS.md](AGENTS.md)。
- 公開 repo 不放部署專案的私有細節或憑證。`main` 測試須維持通過；功能分支合併仍要使用者驗收。
- 初次 Codex 煙霧測試的 `workspace-write` 沙箱擋 `.git/FETCH_HEAD`，屬測試環境限制；另建乾淨 fixture 用可寫 Git 的模式重跑，18 個有效結果未計該次。

## 服務查證與期望快照

- 2026-11-14 20:53 Mac：`python3 -X utf8 tools/verify_bootstrap.py` exit 0；本次只改 `HANDOFF.md`，提交前仍須逐檔 stage 後跑 `--staged`。本輪未改程式／hook，故無需重跑互動驗收。
- 2026-11-14 第 2 期提交前：`uv run --locked pytest -q` 435 passed、369 subtests passed；本次只覆寫交接快照，pytest 未重跑。

## 懸置事項（AI 勿自行處理）

- 無。
