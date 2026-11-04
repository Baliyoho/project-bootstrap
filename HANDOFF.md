# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-04 10:08（+08）
- **交棒者**：Codex ／ `DESKTOP-M8MRS05`（GitHub 文件架構調研與規劃增補）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)；本輪依使用者要求在[效率計畫](project-bootstrap-efficiency-plan.md)新增獨立的 AI 專案檔案架構章節，只規劃、不實作。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-03`
- 本機能力：Windows、Python 3.13、Git Bash、PowerShell；驗證 fixture 需沙箱外執行。

## 已完成

- 效率計畫第 14 章：五個 GitHub／官方來源比較、部署後專案與來源 repo 兩種目錄樹、文件責任、遷移表、S1–S3 批次與負向驗收。
- 研究 AGENTS.md、Spec Kit、OpenSpec、Anthropic skills、Superpowers；來源與查閱日期放計畫。未安裝或執行外部框架，未呼叫額外模型。
- 計畫註明原基準與現在的差異，修正 R01–R09 與 POSIX mode 的過期時態；不把提案當現行制度。
- 前輪 R01–R09、同步 copymode 與結構摘要漂移均已修；Windows 52 項驗證，前輪另有 WSL Linux mode 隔離實測。
- 前輪六個維護專案及兩份全域 skill 已同步；四份通用 verify_state 人工遷移、兩份自訂保留。此次未重新驗收私人專案。
- 本輪只改計畫與本快照，無實際結構變動；部署包、skill、hook、接線、VERSION 皆未變，不需要同步副本或重審信任。

## 未完成／下一步

1. 使用者審閱第 14 章，決定是否採納 S1 文件責任整理；未授權實施搬檔或制度變更。
2. P0 量測、P1 程序分流及後續效率改造仍未實作；不以新提案省略現行程序。
3. 新 session 先 A 模式並讀第二輪複審；凍結報告不是即時待辦。

## 地雷與注意事項

- 新目錄樹皆為提案；本 repo 不可套用部署後專案整棵樹或安裝自身 handoff 副本。
- 拆 references 前須補齊生成、同步、ZIP 與全域依賴；不能只搬 SKILL 而留下缺檔。
- --write 必須單一專案搭配 --owner 且先推 A5；協調證據不是原子鎖。
- 原 review_probe.py／review-results.json 未隨 Git 發布；未取得或重跑原始聊天探針。
- 外部 main 連結會變動；實作採用前固定 commit、再驗相容性。私人資料不進公開 repo。

## 服務查證與期望快照

本輪 A4：`python -u -X utf8 tools/verify_bootstrap.py` exit 0、52 項全過、無 skip；22 個生成檔、本 repo 11 份 Markdown。
最終候選內容再跑完整驗證 exit 0、52 項全過、無 skip；補填結果後重驗本 repo 文件與交接快照，index 與工作樹一致。
前輪 Linux mode fixture 為隔離測試，不是完整跨 OS suite；Python 3.8 仍僅靜態擔保。此次不重跑業務服務／私人專案、不驗模型遵循。

## 懸置事項（AI 勿自行處理）

- 效率與文件架構提案尚未採納；原子 claim 另案，Antigravity IDE 不再追查。
- 額外模型探針須另行授權且只用訂閱額度。
