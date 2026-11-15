# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-15 08:43（+08）
- **交棒者**：Codex 桌面 App／Mac（交接棒效率驗證，交由 Claude Code 接續）

## 任務目標

使用者要求 Claude Code 接棒做驗證。方針是落實既有流程／規則。補 Claude 執行介面與離線驗證，再做可比較的純接棒／純交棒測試。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支 `main`。
- **待續分支**：無；`feature/v3` 保留但不是待續分支。
- **工作中**：Mac ／ Claude Code ／ ㊣　11.15.08｜Claude接棒驗證｜工作中｜交棒0次（開工 2026-11-15 08:55 +08）
- **骨架版本**：`2026-11-14.4`
- 3.10 hook source 已更新至 `2026-11-15`，skill 內容未改。
- 本機 Mac，使用 `python3`。前輪 Codex CLI 為 ChatGPT 訂閱登入；本輪未在常見位置找到 Claude CLI，下一棒需按當前環境重查。

## 已完成

- `eae27b0`：`usage.py` 支援指定 Codex turn／Claude user UUID 的離線解析，兩工具歷史完成紀錄已核對，缺欄位或未完成回合回報未知。
- 同批修正權威 repo 版本提示，成功 fetch 後讀 `origin/main:VERSION`；來源範本、部署包、本 repo hook 同步。其他專案仍用原 TTL，未同步。
- `0be5112`：Codex 接棒並完成 fixture 任務、正常交棒各 PASS；版本提示前後探針有效。每情境一次，效率改善未證實。見[第二階段結果](experiments/handoff-ab/PHASE2-RESULTS.md)。
- `25e3270`：純任務同版 A/B 設計與 Codex runner `comparable.py` 已離線驗證；正式 12 回合未執行。見[計劃](experiments/handoff-ab/OPTIMIZATION-PLAN.md)。

## 未完成／下一步

1. 依 AGENTS 接棒，再讀計劃末段與第二階段結果。下面直接列出 Claude 可共用部分與待補介面，避免重讀整份歷史。
2. **可共用設計**：現行 full 骨架、相同起始 Git 快照；純接棒停在開工標記推送與遠端核對，純交棒從成果已完成且已推送開始。兩組終點一致，必要驗證依既有規則。
3. **可共用對照**：A 一般依規則執行，B 多最小讀取、有效驗證沿用與適當等待提示。每工具每情境 A/B 各 3 次，共 12 回合，交錯順序；B 額外提示計入成本。只能估計提示落實效果，不能稱制度版本改善。
4. **可共用程式**：優先重用 `build.py`、`fixture.py`、`score.py`、`usage.py` 與 `comparable.py` 的起點雜湊、污染檢查及純任務條件。查看既有 Claude `run.py`、`selfcheck.py` 的登入、隔離與事件處理。`comparable.py` 直接依賴 `codex_run`，不能原樣跑 Claude。
5. **Claude 自行確認**：實際 CLI 入口、版本、訂閱登入、模型／推理設定、hook/skill 載入、等待行為與事件格式。本輪「未找到 CLI」只是歷史資訊，不能據此阻擋當前可用環境；跨工具 medium 不視為同義。
6. **Claude 補介面**：接上啟動、隔離設定、原始事件、唯一 user UUID、完成／失敗判定及回合後解析。重用 `usage.py` Claude 分支；快取讀取與建立分列，noncached 包含建立。以合成／既有紀錄驗串流去重、缺欄位、未完成及回合邊界。
7. **公平性與評分**：A/B 固定模型、設定、起始 HEAD/tree/refs 與占用值。非零 exit／timeout 為 INVALID，污染拒跑。必要驗證、own marker 遠端確認及任務範圍需人工核對命令與輸出，未審為 PENDING_REVIEW；事後測試綠不能證明模型做過驗證。
8. **執行與報告**：先離線驗 adapter 與負向案例，再每情境每組跑一格煙霧，有效後續三次配對。記 wall、回合秒數、模型回應、input/cached/noncached/output、可觀測動作及無效重試。回合後一次量測，記錄成本另列；缺等待／驗證耗時寫未知。Claude 與 Codex 各自比較。
9. 使用者已授權第二階段並要求 Claude 接棒驗證，可在此範圍接續，只用訂閱額度。每格重查用量；前輪 84% 是歷史快照。停止條件及順序見計劃，不重跑與本輪差異無關的原定 24 格。

## 地雷與注意事項

- 其他已部署專案同步仍需另行授權。Windows 舊 session 殘留先核對，不推來源不明的未推 commit。

- 既有 clean 包含程式任務，82.181 秒不能當純接棒；midway 是半成品交棒。純任務 fixture 與 Claude adapter 均需正式實跑。
- 共用制度權威是 `src/kit/`，修改及同步依 AGENTS 並保留理由。原始聊天、憑證、本機絕對路徑留 repo 外，報告只放聚合結果。
- 最小讀取、等待與驗證沿用已有規則，優先修執行與工具。原定 24 格已改列候選背景，非本輪必要待辦。

## 服務查證與期望快照

- `25e3270` 提交前純任務離線測試 2 項、`verify_bootstrap.py --staged --quiet` 66 項 exit 0。前輪 usage/cache 5 項、Codex validity 6 項通過。
- 本次只覆寫交接文件，提交前對最終 staged 快照跑 `python3 -X utf8 tools/verify_bootstrap.py --staged --quiet`；程式未改，沿用上述測試。
- 本 repo 無 `verify_state.py`／`check_docs.py`，使用 AGENTS 指定入口。此次未改 hook 接線，重新審核不適用。
- Claude 正式模型驗證、兩工具純任務 12 回合、真 repo 前後效率、Windows 尚未驗。F50 桌面完整互動未驗，使用者先前決定不另建 F50 測試聊天。

## 懸置事項（AI 勿自行處理）

- 無。
