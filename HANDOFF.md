# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-16 11:50（+08）
- **交棒者**：Codex 桌面 App／Windows（Windows 驗收與共用占用核對）

## 任務目標

完成 bootstrap v3 的跨平台驗收。Windows 原生 Codex CLI 已完成第一批真實情境及新版占用核對。下一棒使用同版在 macOS 複驗後，依 F15 對照結果。[通用改動及跨平台驗證清單](experiments/handoff-ab/CODEX-RESULTS.md#通用改動與跨平台驗證清單2026-11-16)

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　11.16.11｜待指派｜工作中｜交棒0次`，2026-11-16 11:57 (+08) 開工 [session-id=21ce82be-d8be-4ea6-8e4d-be0342978050]
- **骨架版本**：`2026-11-16.6`

## 已完成

- 共用開場 hook 以可執行的 Python 產生 UTF-8 JSON（Windows 依序試 `python3`、`python`）。`2026-11-16.2` 的 session ID 占用核對已在 `2026-11-16.3` 撤回：違反 D1、D14 與 3.11「判斷不了時放行」。
- Windows 原生 Codex CLI `0.166.0` 已驗開場、PreToolUse、異 session 攔截及同 session 正常釋回。工作區沙箱下的 Git 推送也已驗證單次核准可使測試遠端與本機追蹤參照同步。
- 十個 Windows 真實情境與兩個占用探針的結果已記錄。較早版本 `midway` 兩次誤釋回舊占用。新版 `2026-11-16.2` 依同一提示重跑 PASS，遠端 refs、標記、本機 HEAD 和工作樹全數保留，推送為零。舊評分保留供對照。[原生 Windows 結果](experiments/handoff-ab/CODEX-RESULTS.md#windows-離線驗證2026-11-16)
- 測試器已支援原生 Windows fixture、評分和 Codex developer 訊息中的開場 JSON。既有五個 OpenSSH 簽章 fixture 可在 Linux 實跑。

## 未完成／下一步

1. 已建 handoff skill 第七個檔 `env.md`（`2026-11-16.4`）：Codex／Claude Code、macOS／Windows 的差異碰到才讀，不改共用狀態判讀（Q35）。下次同步各專案與全域副本時要連同新檔一起覆蓋；Claude Code／Windows 尚無實測，該節目前空白。
2. macOS 同版 `midway` 已複驗：Codex 照 A2.5 選項 2 接手並交棒。使用者 2026-11-16 選 A2.5（Q36），`2026-11-16.5` 已把 B1 斷線例子改成一致；`midway` 回到原評分，格 3 照原評分為 PASS。[結果](experiments/handoff-ab/CODEX-RESULTS.md#macos-同版-midway-斷線複驗2026-11-16)
3. 2026-11-16 已同步到 `2026-11-16.6`：Mac 上六個專案（NAA_TR 在待續分支 `feature/W15-research-shell`，其 `main` 未動）與本機兩份全域 skill。待辦：`learn coding with ai agent` 當時被另一個 Claude Code session 占用，未同步；Windows 機器的專案與全域副本未同步；五個專案 `AGENTS.md` 標記外的舊交接段落（`sync_project.py` 列為 MIGRATE）待人工比對。grist-workflow 同步後 `verify_state.py` 仍是本機缺 `.env` 的 exit 2 基線。桌面 App 的 F50 五步互動沿用既有暫緩決定。

## 地雷與注意事項

- AI push hook 回到只擋「推權威分支、沒改 `HANDOFF.md`、origin 標記是無（已交棒）」一種情形。斷線 session 的舊標記只靠 B1 文字保護，Windows Codex 曾兩次誤釋回。
- Windows 的 HTTP push 可以送達遠端且 exit 0，本機追蹤參照卻仍因無法鎖定 `.git` 而停在舊 SHA。核對遠端和本機兩者，必要時用單次命令審核。
- 隔離倉庫、原始串流、模擬請求及登入配置留在本機。公開 repo 僅留聚合結果和復現條件。

## 服務查證與期望快照

- 來源 verifier 使用 `python -X utf8 tools/verify_bootstrap.py --staged --quiet`。Linux 容器以非 root 使用者測試，來源只讀，無外網。候選版 66 項全過，exit 0。
- 原生 Windows 已過開場與 push hook 情境。全套 Windows 驗證的既有 v2 P0 基線仍回傳 exit 2，含 POSIX mode、symlink、唯讀 Git 清理及殼層假設。完整交棒驗證在 Linux 執行。
- 本 repo 以來源 verifier 代替 `verify_state.py` 與 `check_docs.py`。版本與腳本副本已對齊。Codex 接線 JSON 無變更，Windows 隔離測試有實跑最新版腳本，macOS 實際信任與載入驗收列在下一步。

## 懸置事項（AI 勿自行處理）

- 無。
