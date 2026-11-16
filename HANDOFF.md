# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-16 13:30（+08）
- **交棒者**：Claude Code 桌面 App／Mac（審查 Codex 的 Windows 改動、撤回衝突、加 `env.md`、macOS `midway` 複驗、同步各專案）

## 任務目標

完成 bootstrap v3 的跨平台驗收。Codex 在 macOS 與 Windows 都驗過；下一棒在 **Windows 上用 Claude Code** 驗第一次，這是四種組合裡唯一還沒實測的。制度方向依需求決策書 v3 Q35：一套共用規則，工具與平台的差異只寫在碰到才讀的 `.claude/skills/handoff/env.md`，不改變共用狀態的判讀。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-16.6`

## 已完成

- `2026-11-16.3`：撤回 Codex 加的 session ID 占用核對（缺資訊就擋，把標記變成鎖，違反 D1、D14 與 3.11「判斷不了時放行」，也沒有使用者定案；Q35）。保留 Windows 的 `python3`／`python` 回退。
- `2026-11-16.4`：handoff skill 改成七個檔，新增 `env.md`（Codex／Claude Code／Windows／macOS 各一節）。Codex 長指令與 hook 驗收逐字搬入；Windows 沙箱鎖 `.git` 的提醒原本只在部署包，現在會部署到專案。
- `2026-11-16.5`：`mode-b.md` B1 的斷線例子改成跟 `mode-a-stop.md` A2.5 選項 2 一致：使用者明確確認舊標記與工作屬於自己時可接手；只說「請交棒」或同機器同工具不算（Q36，使用者選 A2.5）。
- `2026-11-16.6`：`env.md` 開頭加「開場沒有 [facts] 時依序查」，出現症狀才查。測試器 `codex_run.py` 每格記錄 CLI 路徑與版本，並用 `--trust` 讓專案 hook 載入。
- macOS `midway` 同版複驗：有效 1 格，Codex 照 A2.5 接手並交棒，照原評分 PASS；失敗與平台無關。[結果](experiments/handoff-ab/CODEX-RESULTS.md#macos-同版-midway-斷線複驗2026-11-16)
- Mac 上六個專案與本機 `~/.claude`、`~/.codex` 兩份全域 skill 已同步到 `2026-11-16.6`，各專案標記已釋回。

## 未完成／下一步

1. **Claude Code／Windows 首次實測**（下一棒）。先 `git pull` 到 `2026-11-16.6`，確認開場 `[facts]` 有進 context；沒有就照 `env.md`「開場沒有 [facts] 時依序查」（重點：Claude Code 用的 `bash` 是不是 Git for Windows 那支、`python3` 是否為失效別名）。再驗 push 前 hook 的 exit 2 真的擋下（推 `main`、沒改 `HANDOFF.md`、origin 標記是無（已交棒））。有差異就照 `env.md` 開頭的條件寫進「Claude Code」或「Windows」一節，寫明版本與日期；會改變交接結果的規則不放 `env.md`，先問使用者（Q35）。
2. Windows 機器上的全域 `~/.claude/skills/handoff/`、`~/.codex/skills/handoff/` 與該機的專案同步到 `2026-11-16.6`（`tools/sync_project.py`，七個檔，覆蓋前先看現況）。
3. `learn coding with ai agent` 未同步：同步時另一個 Claude Code session 持有標記（2026-11-16 10:20 開工）。標記釋回後再同步。
4. 五個專案 `AGENTS.md` 標記外的舊交接段落待人工比對（`sync_project.py` 列 MIGRATE：NAA_TR、NAS_MAINT、academic-summary-skill、grist-workflow、鍵鼠同部署_mac）。NAA_TR 只同步了待續分支 `feature/W15-research-shell`，其 `main` 未動。
5. 桌面 App 的 F50 五步互動沿用既有暫緩決定。

## 地雷與注意事項

- 跑 Codex 實驗前先看 CLI 版本：2026-11-16 的 Mac 上 Codex App 外掛內附 `0.167.0-alpha.3.2`、ChatGPT App 內附 `0.169.0-alpha.11.1`，`PATH` 上沒有 `codex`；未信任專案不載入專案 hook。讀 Codex 用量可用 `codex app-server` 的 `account/rateLimits/read`，不呼叫模型。
- AI push hook 只擋「推權威分支、沒改 `HANDOFF.md`、origin 標記是無（已交棒）」一種情形。斷線 session 的舊標記靠 B1／A2.5 文字，使用者明確確認歸屬才可接手。
- Windows 的 HTTP push 可能送達遠端且 exit 0，本機追蹤參照卻停在舊 SHA（`env.md` Windows 節）。推送後核對兩者。
- grist-workflow 在這台 Mac 的 `verify_state.py` 是 exit 2（缺 `.env`，errors=0 skipped=2），不是同步造成。
- 隔離倉庫、原始串流與登入配置留在本機；公開 repo 只留聚合結果與復現條件。

## 服務查證與期望快照

- 2026-11-16 13:30 Mac：`python3 -X utf8 tools/verify_bootstrap.py --staged --quiet` 66 項全過，exit 0；`experiments/handoff-ab/codex_selfcheck.py` 通過。
- 原生 Windows 全套驗證的既有 v2 P0 基線仍回傳 exit 2（POSIX mode、symlink、唯讀 Git 清理、殼層假設），在 Windows 上跑驗證器要分清這個基線與新問題。
- 本 repo 以來源 verifier 代替 `verify_state.py` 與 `check_docs.py`；兩支 `repo-*.sh` 與共用制度副本已和範本逐字對齊。

## 懸置事項（AI 勿自行處理）

- 無。
