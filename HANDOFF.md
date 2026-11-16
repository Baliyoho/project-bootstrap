# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-16 11:50（+08）
- **交棒者**：Codex 桌面 App／Windows（Windows 驗收與共用占用核對）

## 任務目標

完成 bootstrap v3 的跨平台驗收。Windows 原生 Codex CLI 已完成第一批真實情境及新版占用核對。下一棒使用同版在 macOS 複驗後，依 F15 對照結果。[通用改動及跨平台驗證清單](experiments/handoff-ab/CODEX-RESULTS.md#通用改動與跨平台驗證清單2026-11-16)

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-16.2`

## 已完成

- 共用開場 hook 以可執行的 Python 產生 UTF-8 JSON，並從工具 payload 取得 session ID。開工標記留存 ID。AI push hook 釋回、替換或刪除已占用標記時，核對原標記與工具 ID。缺 ID 的舊標記先由使用者核對遷移。既有開工提醒保留。
- Windows 原生 Codex CLI `0.166.0` 已驗開場、PreToolUse、異 session 攔截及同 session 正常釋回。工作區沙箱下的 Git 推送也已驗證單次核准可使測試遠端與本機追蹤參照同步。
- 十個 Windows 真實情境與兩個占用探針的結果已記錄。較早版本 `midway` 兩次誤釋回舊占用。新版 `2026-11-16.2` 依同一提示重跑 PASS，遠端 refs、標記、本機 HEAD 和工作樹全數保留，推送為零。舊評分保留供對照。[原生 Windows 結果](experiments/handoff-ab/CODEX-RESULTS.md#windows-離線驗證2026-11-16)
- 測試器已支援原生 Windows fixture、評分和 Codex developer 訊息中的開場 JSON。既有五個 OpenSSH 簽章 fixture 可在 Linux 實跑。

## 未完成／下一步

1. 在 macOS 取用 `2026-11-16.2`，按[跨平台驗證清單](experiments/handoff-ab/CODEX-RESULTS.md#通用改動與跨平台驗證清單2026-11-16)先跑完整驗證，再用兩個隔離的 CLI session 檢查異 session 拒絕、同 session 放行、舊標記與待續分支。實際審核 hook 信任後再判讀。
2. macOS 以相同版本、相同 `midway` 提示和 B1 保全判準與 Windows 對照。先前 macOS 規則複驗是 `2026-11-15.2`。[macOS 歷史結果](experiments/handoff-ab/PHASE2-RESULTS.md#codex-占用者核對複驗2026-11-15) 額外模型呼叫按訂閱與使用者授權執行。
3. 其他已部署專案與選用的全域 skill 副本仍待同步。先核對現有占用，再依 `AGENTS-reasons.md` 的副本規則與 `tools/sync_project.py` 處理。桌面 App 的 F50 五步互動沿用既有暫緩決定。

## 地雷與注意事項

- 本版 hook 比對目前分支的已提交內容與本機追蹤參照。覆蓋範圍是可辨識的 AI 殼層推送。交棒前仍要 fetch 核對。舊標記缺 ID 時由使用者處理遷移。
- Windows 的 HTTP push 可以送達遠端且 exit 0，本機追蹤參照卻仍因無法鎖定 `.git` 而停在舊 SHA。核對遠端和本機兩者，必要時用單次命令審核。
- 隔離倉庫、原始串流、模擬請求及登入配置留在本機。公開 repo 僅留聚合結果和復現條件。

## 服務查證與期望快照

- 來源 verifier 使用 `python -X utf8 tools/verify_bootstrap.py --staged --quiet`。Linux 容器以非 root 使用者測試，來源只讀，無外網。候選版 66 項全過，exit 0。
- 原生 Windows 已過開場與 push hook 情境。全套 Windows 驗證的既有 v2 P0 基線仍回傳 exit 2，含 POSIX mode、symlink、唯讀 Git 清理及殼層假設。完整交棒驗證在 Linux 執行。
- 本 repo 以來源 verifier 代替 `verify_state.py` 與 `check_docs.py`。版本與腳本副本已對齊。Codex 接線 JSON 無變更，Windows 隔離測試有實跑最新版腳本，macOS 實際信任與載入驗收列在下一步。

## 懸置事項（AI 勿自行處理）

- 無。
