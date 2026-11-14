# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 22:00（+08）
- **交棒者**：Codex 桌面 App／Mac（Codex 交接成本優化）
- **進度更新**：2026-11-15 07:29（+08）；本聊天仍在工作中，未交棒。

## 任務目標

依需求決策書 v3 改善交接棒執行效率，方針是落實既有流程與規則。本聊天已授權 Sol sub-agent 執行[改進與驗證計劃](experiments/handoff-ab/OPTIMIZATION-PLAN.md)第一階段。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支 `main`。
- **待續分支**：無；`feature/v3` 保留但不是待續分支。
- **工作中**：`Mac` ／ `Codex 桌面 App` ／ `㊣ 11.14.22｜接棒用量量測｜工作中｜交棒0次`，2026-11-14 22:03 (+08) 開工
- **骨架版本**：`2026-11-14.4`
- 本機：macOS 27.2、Python 3.15.2、uv 0.13.7；無 `python`，用 `python3`。兩份全域 handoff skill（Claude Code、Codex）12 檔與 `.4` 範本逐位元組相同。

## 已完成

- 第 1 期 Claude Code＋macOS 完成；第 2 期 Codex handoff-ab 12／12 與 6／6 通過，損害格 0；F50 CLI 部分符合，桌面 App 項尚未完整驗收。
- `470d34c`：來源驗證器保留全部檢查，以子程序重疊獨立回歸；同內容串行 52.72 秒、重疊 34.28 秒，均 66 項 exit 0。新增 `--quiet`，skill 補 Codex 外層等待及最小讀取用法。
- `.3` 接棒已量：11 次模型回應、349,246 input（304,000 cached）、1,028 output、147.103 秒。相較前次 28 次／1,119,828 input，累計輸入下降，但非快取輸入增加，不能等同比例換算訂閱額度。
- 證據、量測口徑與限制集中在 [CODEX-RESULTS.md](experiments/handoff-ab/CODEX-RESULTS.md)。
- 第一階段離線改動：新增 handoff-ab `usage.py`，依指定 Codex turn／Claude user UUID 只讀解析，未完成或缺欄位明記未知；.4 歷史 Codex turn 重現已記數字，Claude Code 完整 turn 解析出快取建立與讀取分列。
- 3.10 開場 hook 修正本 repo 的舊快取提示：權威 repo 成功 fetch 後讀 `origin/main:VERSION`；來源範本、部署包、本 repo 手貼 hook 同步。其他專案維持 12 小時 TTL，尚未同步。skill 內容未動，`VERSION` 仍為 `.4`。

## 未完成／下一步

1. 第一階段實作與主代理審查完成；第二階段依下列計劃取得模型探針授權後進行。
2. [OPTIMIZATION-PLAN.md](experiments/handoff-ab/OPTIMIZATION-PLAN.md)列出第二階段可分批核准的煙霧測試、完整對照與異常候選；正常交棒 fixture 尚需建立。額外模型探針仍需另行授權、只用訂閱額度。其他已部署專案同步仍須另行授權。
3. F50 桌面 App 完整互動驗收與第 3 期 Windows 尚未做；使用者先前決定不另建 F50 測試聊天。Windows 當地全域 skill 仍舊，先同步並核對 Git 殘留，不推舊 session 的未推 commit。

## 地雷與注意事項

- 制度權威在 `src/kit/`，副本與同步規則見 [AGENTS.md](AGENTS.md)；其他專案不同步也不代為釋出占用。
- 接棒及 staged 驗證都保留，可加 `--quiet`；Codex 用外層 60000 ms、內層最多兩段 30000 ms 等完，超過一分鐘才回報進度續等。
- 公開 repo 不放原始 rollout、憑證或本機絕對路徑。只記聚合數字與可重現口徑；腳本加速不代表完整交接或訂閱額度已同比改善。

## 服務查證與期望快照

- 本輪 handoff-ab 針對性測試 5 項通過；`python3 -X utf8 tools/verify_bootstrap.py --quiet` 66 項 exit 0。staged 驗證待主代理 stage 後執行。
- `uv run --locked pytest -q` 的 439 passed、376 subtests passed 是前輪歷史結果，本輪未重跑。第二階段模型對照、Claude Code 等待行為與訂閱額度變化尚未驗證。
- 本 repo 沒有 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口；本輪未改 hook 接線，重新審核不適用。Windows 與新版完整交接模型用量未驗。

## 懸置事項（AI 勿自行處理）

- 無。
