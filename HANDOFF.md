# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 22:00（+08）
- **交棒者**：Codex 桌面 App／Mac（Codex 交接成本優化）
- **進度更新**：2026-11-15 08:21（+08）；可比較的純接棒／純交棒測試已完成離線設計與 fixture 核對，本聊天仍在工作中，未交棒。

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
- 第二階段首批 Codex：本版正常接棒與新建正常交棒 fixture 各 PASS、損害 0；權威版本提示前後探針確認舊版對上游版本答未知、本版收到新版 [facts] 並正確判本地落後。完整聚合用量及無效探針成本見 [PHASE2-RESULTS.md](experiments/handoff-ab/PHASE2-RESULTS.md)。
- 下一批可比較設計：`comparable.py` 用相同現行 full 骨架與每情境同一 master Git 快照，備好純接棒／純交棒 A/B 各 3 次、共 12 個交錯格；A 是一般依規則執行，B 多執行提示。接棒只到開工標記遠端確認，交棒從成果已完成且已推送起步；途中量測暫計提交排除於 A/B 外。起點污染、模型 exit 與人工待審有守門；`test_comparable.py` 的 2 項離線測試通過。正式模型批次未執行，詳見 [OPTIMIZATION-PLAN.md](experiments/handoff-ab/OPTIMIZATION-PLAN.md)。

## 未完成／下一步

1. 第二階段首批已執行；樣本每情境一次，不能推論效率改善。Codex 五小時用量到 84%，停止擴樣；本輪未找到 Claude Code CLI。純任務同版提示對照已離線備好 12 格，後續正式模型批次仍待執行；它只可估計提示落實的效果，不能當制度版本改善。每格需人工核對必要驗證與實際工作流，缺審查顯示 PENDING_REVIEW。
2. 本批實驗腳本與報告已由主代理審查；保留本聊天「工作中」。其他已部署專案同步仍須另行授權。
3. F50 桌面 App 完整互動驗收與第 3 期 Windows 尚未做；使用者先前決定不另建 F50 測試聊天。Windows 當地全域 skill 仍舊，先同步並核對 Git 殘留，不推舊 session 的未推 commit。

## 地雷與注意事項

- 制度權威在 `src/kit/`，副本與同步規則見 [AGENTS.md](AGENTS.md)；其他專案不同步也不代為釋出占用。
- 接棒及 staged 驗證都保留，可加 `--quiet`；Codex 用外層 60000 ms、內層最多兩段 30000 ms 等完，超過一分鐘才回報進度續等。
- 公開 repo 不放原始 rollout、憑證或本機絕對路徑。只記聚合數字與可重現口徑；腳本加速不代表完整交接或訂閱額度已同比改善。

## 服務查證與期望快照

- 前輪 handoff-ab 針對性測試 5 項、Codex 守門負向自檢 6 項、第二階段版本探針 OLD／NEW 各 7 項聚合核對通過。本輪 `test_comparable.py` 2 項離線測試通過；`python3 -X utf8 tools/verify_bootstrap.py --quiet` 66 項 exit 0。staged 驗證待主代理逐檔 stage 後執行。
- `uv run --locked pytest -q` 的 439 passed、376 subtests passed 是前輪歷史結果，本輪未重跑。Claude Code 等待行為未驗；本輪 Codex 訂閱用量讀值見第二階段結果，但不能精確分攤到個別格。
- 本 repo 沒有 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口；本輪未改 hook 接線，重新審核不適用。Windows 未驗；本版 fixture 接棒與交棒已有模型用量，真 repo 前後效率仍未驗。

## 懸置事項（AI 勿自行處理）

- 無。
