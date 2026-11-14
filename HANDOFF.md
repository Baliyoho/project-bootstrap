# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-14 22:00（+08）
- **交棒者**：Codex 桌面 App／Mac（Codex 交接成本優化）

## 任務目標

依[需求決策書 v3](project-bootstrap-requirements-decision-v3.md)驗收交接制度；本輪完成 Codex 等待與驗證器加速，下一棒依使用者要求順便量測接棒 token 花費。

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

## 未完成／下一步

1. **使用者已要求：下一次接棒順便測 token 花費。** 正常完成 `.4` 接棒，不另開測試聊天、不額外呼叫模型。從當前聊天的本機 rollout（`~/.codex/sessions/<日期>/rollout-*.jsonl`）只取該接棒 turn：數 `token_usage_record`，讀最後的 `turn_token_usage`，記 input、cached input、非快取 input（兩者相減）、output；以 `task_started`／`task_complete` 算耗時，另記空等工具呼叫次數。
2. 量測結果寫回 CODEX-RESULTS.md，對照 `.3` 的 11 次／349,246 input／147.103 秒及更早基準。當輪未結束時，最後回覆的用量尚未落盤：先標明截點與暫計，等下一則正常互動再補齊，不等待自己完成、不把暫計寫成完整總額；量測與記錄額外開銷另註。讀不到資料就明記未量，不能估算 token 或訂閱消耗。新版完整交棒用量仍未驗。
3. 已部署專案尚未同步到 `.4`，逐專案 `sync_project.py` 須另行授權。
4. 歷史開場訊息曾印本機版本比上游新（`.3` 對 `2026-11-14`）；當時未追查上游來源，`.4` 尚未重驗此提示，不當作已確認的現行故障。
5. F50 桌面 App：本聊天改名工具成功，但不等於完整互動驗收；使用者先前決定不另建測試聊天。第 3 期 Windows 未開始，新版 SessionStart 接線未實跑，當地全域 skill 仍舊；先同步並核對 Git 殘留，不推舊 session 的未推 commit。

## 地雷與注意事項

- 制度權威在 `src/kit/`，副本與同步規則見 [AGENTS.md](AGENTS.md)；其他專案不同步也不代為釋出占用。
- 接棒及 staged 驗證都保留，可加 `--quiet`；Codex 用外層 60000 ms、內層最多兩段 30000 ms 等完，超過一分鐘才回報進度續等。
- 公開 repo 不放原始 rollout、憑證或本機絕對路徑。只記聚合數字與可重現口徑；腳本加速不代表完整交接或訂閱額度已同比改善。

## 服務查證與期望快照

- `.4` 一般及 `--staged --quiet` 驗證均 66 項 exit 0（`470d34c` 提交前）；`uv run --locked pytest -q`：439 passed、376 subtests passed。
- 本次交棒只覆寫快照與量測待辦，程式未變，沿用上述 pytest 結果；提交前再跑 `python3 -X utf8 tools/verify_bootstrap.py --staged --quiet` 驗最終文件。
- 本 repo 沒有 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口；本輪未改 hook 接線，重新審核不適用。Windows 與新版完整交接模型用量未驗。

## 懸置事項（AI 勿自行處理）

- 無。
