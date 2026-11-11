# AGENTS.md — 改這個 repo 之前先讀

> 最後更新：2026-11-11（P1：原型程式搬到 src／tests，加 pyproject／uv.lock；前次 2026-11-10 本 repo 加動作當下送規則的 hook、全域副本換成六檔版）
> 本檔只放規則。每條規則的完整原文、理由與事故在 [AGENTS-reasons.md](AGENTS-reasons.md)，由規則後面的「為什麼」指過去；**要改、要質疑或想繞過某條規則之前，先讀它的理由**。（2026-11-10／F22：理由原本夾在規則裡，常態必讀量超標；搬家不刪。）

## 開工第一件事（任何工具、任何模型都適用）

**先走接棒程序的 A 模式，A 沒跑完之前不要改任何檔案**；收工走 B 模式，中途要拉最新或推一個安全點走 C 模式。

- 程序檔在**全域**副本 `~/.claude/skills/handoff/SKILL.md`（Codex 是 `~/.codex/skills/handoff/SKILL.md`）；這個 repo 刻意沒有專案層的那一份。工具不會自動載入 skill 就直接開那個檔讀。**這台機器沒有全域副本時，程序在 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的「3.8」節**；不要從別台機器搬檔或憑記憶重刻。
- 部署包 `2026-11-10` 起 skill 是一個目錄：`SKILL.md` 是入口，再照它讀同目錄的模式檔；這台 Mac 的全域副本 2026-11-10 已換成六檔版（決策書 Q11 (a) 試用）；**別台還沒換的仍是單檔**，照單檔走。本 repo 的「全綠」行由 `.claude/hooks/repo-git-check.sh` 印（前綴 `[repo-check]`），要重跑就跑它。
- **A4 改跑 `python -X utf8 tools/verify_bootstrap.py`**（不是 `verify_state.py`），**exit 0 才算改完**。
- 沒有 `check_docs.py`、沒有 pre-push 防呆，所以 B4 與擋 push 的關卡不存在；文件檢查由 `verify_bootstrap.py` 顧。
- **B7 先明確 stage，再跑 `python -X utf8 tools/verify_bootstrap.py --staged`。**
- **`HANDOFF.md` 是當下交接快照，也承載「工作中」標記**：A5 更新標記，B6 核對整份現況並覆寫，≤80 行、不累積歷史。

這些義務寫在這裡而不只放 hook，是因為有些工具不跑 hook。[為什麼](AGENTS-reasons.md#start)

**下列文件都不是每輪必讀，碰到那件事才讀：**

| 要做的事 | 先讀 |
|---|---|
| 討論需求、驗收、待決事項或替代工具 | [需求決策書](project-bootstrap-requirements-decision.md)：現行需求唯一權威（D1–D8、51 個穩定需求 ID）；待決唯一入口是第 6 節。決策定稿不等於實作完成 |
| 查某個需求 ID 做到哪 | [v2 現況索引](experiments/v2/status.json)；HANDOFF 只留停點與行動 |
| 動同步工具、驗證器、hook 或 R01–R09 相關的地方 | [第二輪複審快照](project-bootstrap-reaudit-2026-11-03.md)。2026-11-10 使用者同意從每輪必讀改成條件式；R01–R09 邊界的獨立複審還沒做，不要當成全部結案 |
| 動原查核報告那 16 條 | [查核進度](project-bootstrap-audit-progress.md) |
| 選型或架構實作 | [實現規劃](project-bootstrap-implementation-plan.md)；已授權 v2 分支實作，未部署，不授權略過現行程序 |
| 動 v2 原型 | [v2 原型說明](experiments/v2/README.md) |
| 效率改造 | [效率計畫](project-bootstrap-efficiency-plan.md)；尚未生效，不授權省略現行程序 |
| 追溯需求修訂理由 | [需求歷史原件](project-bootstrap-requirements-history.md)；其中的「權威版」「現在」「待決」不再指示現行操作 |
| 結構問題（有哪些檔、副本在哪） | [ARCHITECT.md](ARCHITECT.md)；動到結構就跟它同一個 commit 改 |

## 這個 repo 是什麼

- **AI 協作專案管理骨架的權威版。** 唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)：自帶所有檔案範本的部署包。用法見 [README.md](README.md)。
- **這裡不是知識庫**：不累積專案知識、踩坑紀錄或狀態，那些屬於各自的專案 repo。
- 不部署的例外：`tools/verify_bootstrap.py`（部署包的測試）；`src/project_bootstrap/`、`tests/`、`experiments/v2/`（說明與現況索引）與 `tools/verify_v2.py`（隔離原型，只用合成 fixture，不保存其他專案資料；**原型通過不授權切換程序或宣稱跨工具強保障**）；`pyproject.toml`／`uv.lock`（P1 開發骨架，A4 不需要）；[HANDOFF.md](HANDOFF.md)；本檔的理由檔。
- 刻意沒有 handoff skill、`pre-push-handoff.sh`、`check_docs.py`。這是**已宣告的例外**，不是空白；宣告不等於 F46 已達成；撤銷宣告改成補裝是使用者的決定。

[為什麼](AGENTS-reasons.md#what)

## 鐵律

1. **`PROJECT-BOOTSTRAP.md` 是權威版。** 制度要改就改它，再用 `python -X utf8 tools/sync_project.py <專案路徑> --owner '<本 session 工作中欄位完整值>' --write` 覆蓋到各專案（先在目標完成 A1–A5；`--all` 只能批次預演，寫入逐專案；它只改檔、不 commit）。**不要**在單一專案就地改 skill 或 hook。**只有 `.claude/skills/handoff/` 目錄裡的檔（入口 `SKILL.md` 與五個模式／理由檔）真的改了內容才跳 `VERSION`**，而且六個檔的 `source:` 標記要同一個版本；跳版後要某專案下一次開場就提示，刪掉它的 `.claude/.bootstrap-version`。[為什麼](AGENTS-reasons.md#rule-1)
2. **改 skill／hook 內容時，同步更新檔頭的 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->` 標記。** 同一天改第二次起在日期後面加序號（`.2`、`.3`）；序號算的是**當天第幾個帶 `source:` 標記的改動**。序號跟部署包開頭的「版本」行**不保證同號**：版本行與 `VERSION` 只跟著 handoff skill 目錄走。[為什麼](AGENTS-reasons.md#rule-2)
3. **保留每條規則的「為什麼」。** 理由可以搬到理由檔，不能刪；`verify_bootstrap.py` 的「規則理由連結」會擋沒有理由的規則。[為什麼](AGENTS-reasons.md#rule-3)
4. **改完要驗證**：跑 `python -X utf8 tools/verify_bootstrap.py`，**exit 0 才算改完**。印 `skip` 的項目會回傳 1，回報時照實寫。[為什麼](AGENTS-reasons.md#rule-4)
5. **不要塞專案專屬內容**（網址、docId、憑證檔名、業務規則）。部署包只放通用制度與佔位符。[為什麼](AGENTS-reasons.md#rule-5)
6. **這是公開 repo**（MIT）。不寫客戶／單位名稱、內部專案代號、本機絕對路徑；提交前擋，進了 Git 歷史刪不掉。[為什麼](AGENTS-reasons.md#rule-6)

## 副本規則

**完整的副本拓撲（哪一份是權威、覆蓋到哪些地方）在 [ARCHITECT.md](ARCHITECT.md)**，這裡只放規則：

- **改完部署包，把所有副本一起覆蓋**，包括選用的全域 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/`。[為什麼](AGENTS-reasons.md#copy-1)
- **Codex 與 Claude Code 掛同樣那兩個 `.sh`**，不要複製第二份腳本進 `.codex/`。Windows 的 Codex 接線用 `commandWindows` 經 3.17 的 `.claude/hooks/codex-hook.cmd` 找 Git Bash；它只做管線，沒有規則。[為什麼](AGENTS-reasons.md#copy-2)
- **Antigravity 只接 `SessionStart`；改 3.18–3.20 之前先讀部署包「跨工具與跨平台」的 Antigravity 那一節。** 四個約束：`.cmd` 全 ASCII；不能有多行括號區塊或 label；路徑用 `%~dp0`／`$0` 推、不靠 cwd；從 Windows 提交 `ag-wrap.sh` 要補 `git update-index --chmod=+x`。IDE 那一面已決定不再追，掃到別重提。[為什麼](AGENTS-reasons.md#copy-3)
- **接線路徑一律相對，但不能假設 cwd 是 repo 根目錄**：3.9／3.17 的路徑前面掛 `$(git rev-parse --show-cdup)`，Windows 那一欄再用 PowerShell 的 `-replace '/','\'` 正規化斜線；Antigravity（3.20）刻意不跟。[為什麼](AGENTS-reasons.md#copy-4)
- **`.agents/` 只放指標與接線**，不複製程序內容；那份 skill 指標的 `description` 必須寫滿觸發詞。[為什麼](AGENTS-reasons.md#copy-5)
- **Codex Windows 啟動器也要同步**：`sync_project.py --codex-only` 只更新各專案的 Codex 接線與啟動器。接線改過要重新審核並驗收實際執行（skill B5），不能只看檔案存在。[為什麼](AGENTS-reasons.md#copy-6)
- **本 repo 自己的 `HANDOFF.md`、`.claude/hooks/repo-git-check.sh`、`.claude/hooks/repo-action-rules.sh`、`.claude/settings.json`、`.codex/hooks.json` 不在副本拓撲裡**，`sync_project.py` 不要碰它們；它已明確拒絕把本 repo 當目標。[為什麼](AGENTS-reasons.md#copy-7)

## 本 repo 的交接快照

- **A5 寫工作中標記；B6 必須核對並覆寫整份 `HANDOFF.md`，≤80 行。** 已完成的待辦移除；保留的未知分清「現行故障」與「歷史無法歸因」；版本與驗證結果對實際執行結果，不抄上一輪；沒做完就明記風險與可續作步驟；收工清掉 origin 的工作中標記。
- `verify_bootstrap.py` 的「本 repo 交接狀態」只守必要欄位、80 行上限、`VERSION` 一致與已知過期待辦，**不能判斷任意待辦是否真的完成**；B6 仍須逐項核對證據。
- **需要額外模型呼叫的探針先取得使用者授權，且只用訂閱額度。**
- **新增守門檢查必須附負向測試**，否則永遠回 `ok` 也看不出來。

[為什麼](AGENTS-reasons.md#snapshot)

## 這個 repo 自己的指標檔

`CLAUDE.md` 只有一行 `@AGENTS.md` import，**不要改回「去讀 AGENTS.md」那種句子**；`GEMINI.md` 維持指標寫法。[為什麼](AGENTS-reasons.md#pointer)

## 行末

`.gitattributes` 強制 `eol=lf`。用 Python 改寫時記得 `newline=''` 或事後正規化。[為什麼](AGENTS-reasons.md#eol)

## 改兩支 hook 的訊息時

- **雙引號裡不要寫反引號**（那是命令替換）；欄位名用「」包，註解裡才能用。[為什麼](AGENTS-reasons.md#hook-1)
- **`$變數` 後面緊接中文或全形標點時一律寫成 `${變數}`**；macOS 的 bash 3.2 會吃掉緊接那個字的位元組。[為什麼](AGENTS-reasons.md#hook-2)
- **用腳本改這些檔時，不要把 patch 從 heredoc 餵進 `python -`**；把 patch 寫成檔案再執行，或用 `chr(10)` 組字串。[為什麼](AGENTS-reasons.md#hook-3)
- **用腳本改 `.md` 時不要手寫 `\u` 轉義**，直接寫中文字面；patch 腳本一律加「命中數 ≠ 1 就 abort」。[為什麼](AGENTS-reasons.md#hook-4)
