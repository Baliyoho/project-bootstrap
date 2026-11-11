# AGENTS.md — 改這個 repo 之前先讀

> 最後更新：2026-11-11（F22 第二輪：規則縮成短句，原文逐條留在理由檔；條件式文件表搬到 ARCHITECT）
> 本檔只放規則；每條的完整原文、理由與事故在 [AGENTS-reasons.md](AGENTS-reasons.md)。**要改、質疑或想繞過某條規則之前，先讀它的理由。**

## 開工第一件事

- **先走接棒程序 A 模式，A 沒跑完不改任何檔案**；收工走 B，中途同步走 C。程序在全域 `~/.claude/skills/handoff/SKILL.md`（Codex 是 `~/.codex/skills/handoff/`），本 repo 刻意沒有專案層那份；這台機器沒有全域副本就讀 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的「3.8」節，不要搬檔或憑記憶重刻。
- **A4 跑 `python -X utf8 tools/verify_bootstrap.py`，exit 0 才算改完**；B7 先明確 stage，再加 `--staged` 跑。沒有 `check_docs.py` 與 pre-push 防呆，B4 與擋 push 的關卡不存在。
- `HANDOFF.md` 是交接快照兼「工作中」標記：A5 寫標記，B6 核對並覆寫整份。
- 其他文件碰到那件事才讀，對照表在 [ARCHITECT.md](ARCHITECT.md) 的「碰到才讀的文件」。

這些寫在這裡而不只放 hook，是因為有些工具不跑 hook。[為什麼](AGENTS-reasons.md#start)

## 這個 repo 是什麼

AI 協作專案管理骨架的權威版，唯一產出物是部署包 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)（用法見 [README.md](README.md)）；不是知識庫，不存各專案的知識或狀態。現行需求權威是[需求決策書](project-bootstrap-requirements-decision.md)（51 個穩定需求 ID）。不部署的例外（測試、v2 原型、開發骨架、`HANDOFF.md`）與刻意沒有的 handoff skill、`pre-push-handoff.sh`、`check_docs.py` 列在 ARCHITECT：那是已宣告的例外，不是空白，改成補裝由使用者決定。原型通過不授權切換程序。[為什麼](AGENTS-reasons.md#what)

## 鐵律

1. **制度權威是 `src/kit/`**：改 `src/kit/kit.md` 或 `src/kit/files/<部署路徑>.tmpl`，跑 `python3 -X utf8 tools/build_kit.py` 重生 `PROJECT-BOOTSTRAP.md`，兩者同一個 commit；不要手改部署包，也不要在單一專案就地改 skill 或 hook。覆蓋到專案用 `tools/sync_project.py`，用法與前提先讀理由。只有 `.claude/skills/handoff/` 目錄裡的檔真的改了內容才跳 `VERSION`，六個檔的 `source:` 標記同版本。[為什麼](AGENTS-reasons.md#rule-1)
2. **改 skill／hook 內容時同步更新檔頭的 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->`**；同一天第二次起加 `.2`、`.3`，序號算的是當天第幾個帶 `source:` 標記的改動，跟部署包「版本」行不保證同號。[為什麼](AGENTS-reasons.md#rule-2)
3. **保留每條規則的「為什麼」**：可以搬到理由檔，不能刪；驗證器會擋。[為什麼](AGENTS-reasons.md#rule-3)
4. **改完跑 `verify_bootstrap.py`，exit 0 才算改完**；印 `skip` 的項目會回傳 1，照實回報。[為什麼](AGENTS-reasons.md#rule-4)
5. **不塞專案專屬內容**（網址、docId、憑證檔名、業務規則），部署包只放通用制度與佔位符。[為什麼](AGENTS-reasons.md#rule-5)
6. **這是公開 repo（MIT）**：不寫客戶／單位名稱、內部代號、本機絕對路徑，提交前擋。[為什麼](AGENTS-reasons.md#rule-6)

## 副本規則

拓撲在 [ARCHITECT.md](ARCHITECT.md)。動副本、接線或 Antigravity 之前，先讀對應理由段落的完整原文。

- 改完部署包，所有副本一起覆蓋，含選用的兩個全域 `skills/handoff/`。[為什麼](AGENTS-reasons.md#copy-1)
- Codex 與 Claude Code 掛同樣兩個 `.sh`，不在 `.codex/` 複製第二份；Windows 的 `codex-hook.cmd` 只做管線。[為什麼](AGENTS-reasons.md#copy-2)
- Antigravity 只接 `SessionStart`；改 3.18–3.20 前先讀部署包那一節與理由裡的四個約束。IDE 那面不再追。[為什麼](AGENTS-reasons.md#copy-3)
- 接線路徑一律相對、不假設 cwd：前面掛 `$(git rev-parse --show-cdup)`；Antigravity 刻意不跟。[為什麼](AGENTS-reasons.md#copy-4)
- `.agents/` 只放指標與接線，skill 指標的 `description` 寫滿觸發詞。[為什麼](AGENTS-reasons.md#copy-5)
- Codex 啟動器也要同步（`sync_project.py --codex-only`）；接線改過要重新審核並驗收實際執行。[為什麼](AGENTS-reasons.md#copy-6)
- 本 repo 自己的 `HANDOFF.md`、兩支 `repo-*.sh`、`.claude/settings.json`、`.codex/hooks.json` 不在拓撲裡，`sync_project.py` 不碰。[為什麼](AGENTS-reasons.md#copy-7)

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
