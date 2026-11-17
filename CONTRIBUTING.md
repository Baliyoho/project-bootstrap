# 參與開發

> 最後更新：2026-11-17（建立：AGENTS.md 裡碰到才需要的規則、README.md 裡的開發流程與副本同步用法搬來這裡，需求決策書 v3 Q40）
> 這個 repo 由 AI session 輪流做。開工必守的規則在 [AGENTS.md](AGENTS.md)，AI 工具開工時會自動讀到；本檔是碰到才讀的流程與規則：改部署包、動副本或接線、寫本 repo 的交接快照、改兩支 hook 的訊息時才讀。每條的完整原文、理由與事故在 [AGENTS-reasons.md](AGENTS-reasons.md)。**要改、質疑或想繞過某條規則之前，先讀它的理由。**

## 改部署包的流程

規則在 AGENTS.md 的鐵律 1、4 與「跟部署出去的專案不同的地方」；這裡只補操作細節。[為什麼](AGENTS-reasons.md#rule-1)

- 動到結構（增刪檔案、部署包增刪一節範本、驗證項增減）就更新 [ARCHITECT.md](ARCHITECT.md)，跟該變動同一個 commit。
- 全套驗證在 macOS 約 35 秒，在原生 Windows 約 3–4 分鐘，超過指令工具預設的 120 秒上限，逾時不等於失敗。Windows 上 `python3` 是 WindowsApps 別名，要用 `python`。[為什麼](AGENTS-reasons.md#rule-4)
- 需要 ZIP 時跑 `python -X utf8 tools/verify_bootstrap.py --zip`（可在 `--zip` 後指定路徑）。只有全過才產出正式包；FAIL 回 2、SKIP 回 1，兩者預設都不產出或覆寫 ZIP。若確實需要未完整驗證的調試包，明確加 `--allow-unverified-zip`：僅容許 SKIP，仍回 1，包內附 `UNVERIFIED.json`（跳過項目與原因），「讀我」也會標示未驗證；FAIL 仍禁止。這避免「缺 bash 的檢查被跳過，卻產出看似驗證全過的 ZIP」（2026-11-02／F07）。

## 同步到已部署的專案

Codex 的 Windows 接線與 Git Bash 啟動器可用 `python -X utf8 tools/sync_project.py <專案路徑> --codex-only` 預演；實際寫入依下面的段落先接棒並加 `--owner`，不改專案的 SKILL 或其他設定。接線變更後要重新審核並驗收實際執行，條件與理由見部署包 3.17。[為什麼](AGENTS-reasons.md#copy-6)

`sync_project.py --all` 預設只掃 Desktop 下一層；可用 `--root <目錄>` 改掃描根目錄、`--exclude <目錄名>` 排除已完結專案。工具列出每個候選的納入／排除原因，透過 Git 的 git-dir／common-dir 排除 linked worktree，全域 skill 副本仍須另行同步。

固定範圍建議使用私人 inventory：`--inventory <清單.json>`，內容如 `[{"path":"../project-a","status":"active"},{"path":"../project-b","status":"archived"}]`；相對路徑以清單所在目錄為準，清單不要提交到公開骨架。預演與寫入都檢查 dirty、工作中標記、整份覆蓋檔與 `check_docs.py` 共用程式區的客製漂移。已檢視的 dirty 僅能在單一專案加 `--allow-dirty`；未知共用內容須人工比對後逐檔加 `--accept-drift <路徑>`，占用不能略過。不 stash、不 commit；這些檢查也不是並行鎖（2026-11-02／F13）。

**跨專案寫入先逐一 A1–A5 接棒**（2026-11-03／R03）：在目標專案推送本 session 的開工標記，再以 `--owner '<工作中欄位完整值>'` 聲明目前 writer。同步器會 fetch origin、確認 HEAD 與 `origin/<目前分支>` 完全一致，並核對本機與遠端的標記都精確等於 owner；套用前再查一次。離線、無 upstream、領先／落後／分岔、他人標記或本機標記漂移均拒絕，`--allow-dirty` 不豁免。owner 是呼叫者明確核對的協調證據，不是身分認證或原子鎖，仍須確認同工作樹只有一個 writer。

`--all`／inventory 僅供批次預演；`--write` 必須指定單一專案與 owner，空閒標記不能寫入。同步後留在該專案完成 B7 最終檔案檢查、B8 發布與清標記；若要中途安全點則走 C，保留占用。這修正了舊工具「正常 A5 writer 被拒絕、陳舊空閒 checkout 卻能寫」的矛盾。

handoff skill 目錄（七個檔）會同時存在於：**本 repo 的 `src/kit/files/.claude/skills/handoff/`**（權威來源，生成進部署包）、每個專案的 `.claude/skills/handoff/`、以及選用的全域 `~/.claude/skills/handoff/`。

- 要改就**改本 repo 的 `src/kit/files/.claude/skills/handoff/*.tmpl`**，跑 `tools/build_kit.py` 重生部署包，再覆蓋下去；不要在單一專案裡就地改，也不要手改 `PROJECT-BOOTSTRAP.md`。
- 每份副本檔頭有 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->`，用它辨識落後的副本（同一天改第二次起加序號，如 `v2026-10-24.2`）。

## 副本規則

拓撲在 [ARCHITECT.md](ARCHITECT.md)。動副本或接線之前，先讀對應理由段落的完整原文。

- 改完部署包，所有副本一起覆蓋，含選用的兩個全域 `skills/handoff/`。[為什麼](AGENTS-reasons.md#copy-1)
- Codex 與 Claude Code 掛同樣兩個 `.sh`，不在 `.codex/` 複製第二份；Windows 的 `codex-hook.cmd` 只做管線。[為什麼](AGENTS-reasons.md#copy-2)
- Antigravity 2026-11-13 起移出部署包（需求決策書 v3 D8）：舊 3.18–3.20 不再產出，已部署專案裡那三個檔不同步也不刪，清不清由使用者決定；要重新支援先讀理由裡的四個約束。[為什麼](AGENTS-reasons.md#copy-3)
- 接線路徑一律相對、不假設 cwd：前面掛 `$(git rev-parse --show-cdup)`；Antigravity 刻意不跟。[為什麼](AGENTS-reasons.md#copy-4)
- `.agents/` 只放指標與接線，skill 指標的 `description` 寫滿觸發詞。[為什麼](AGENTS-reasons.md#copy-5)
- Codex 啟動器也要同步（`sync_project.py --codex-only`）；接線改過要重新審核並驗收實際執行。[為什麼](AGENTS-reasons.md#copy-6)
- 本 repo 自己的 `HANDOFF.md`、兩支 `repo-*.sh`、`.claude/settings.json`、`.codex/hooks.json` 不在拓撲裡，`sync_project.py` 不碰；其中 `repo-git-check.sh`、`repo-pre-push.sh` 是 3.10、3.11 的手貼副本，改了範本要手動重貼，驗證器比對逐字相同。[為什麼](AGENTS-reasons.md#copy-7)

## 本 repo 的交接快照

B6 核對並覆寫整份 `HANDOFF.md`（≤80 行）：移除已完成待辦；未知分清現行故障與歷史無法歸因；版本與驗證照實際結果；沒做完寫明風險與續作步驟；收工清掉工作中標記。驗證器只守必要欄位，不判斷待辦是否真的完成。要額外模型呼叫的探針先取得授權、只用訂閱額度；新增守門要附負向測試。[為什麼](AGENTS-reasons.md#snapshot)

## 這個 repo 自己的指標檔

`CLAUDE.md` 只有一行 `@AGENTS.md`，不要改回「去讀 AGENTS.md」的句子；`GEMINI.md` 維持指標寫法。[為什麼](AGENTS-reasons.md#pointer)

## 行末

`.gitattributes` 強制 `eol=lf`；用 Python 改寫記得 `newline=''`。[為什麼](AGENTS-reasons.md#eol)

## 改兩支 hook 的訊息時

- 雙引號裡不寫反引號，欄位名用「」。[為什麼](AGENTS-reasons.md#hook-1)
- `$變數` 緊接中文或全形標點時寫成 `${變數}`。[為什麼](AGENTS-reasons.md#hook-2)
- 用腳本改時不把 patch 從 heredoc 餵進 `python -`。[為什麼](AGENTS-reasons.md#hook-3)
- 用腳本改 `.md` 不手寫 `\u` 轉義；patch 加「命中數 ≠ 1 就 abort」。[為什麼](AGENTS-reasons.md#hook-4)
