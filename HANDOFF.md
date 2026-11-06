# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-06 17:31（+08）
- **交棒者**：Codex CLI ／ `baliyohodeMini`（需求實現與開源技術棧規劃）

## 任務目標

使用者要求依新決策書，公平比較現有 project-bootstrap 與開源工具，寫出需求實現及技術棧規劃；另授權恢復誤觸的決策書檔名。
交付：[實現規劃](project-bootstrap-implementation-plan.md)。它是提案，未部署、未取代現行程序；需求權威仍是 [決策書](project-bootstrap-requirements-decision.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-03`
- 本輪只新增規劃與更新入口／快照；未改部署包、skill、hook、接線、VERSION 或遠端保護設定。
- 本機能力：Mac、Python 3.15（用 python3）、bash 3.2；Windows／Linux 未在本輪重驗。

## 已完成

- 恢復決策書無引號檔名；與原提交內容逐位元組相同。
- 規劃涵蓋全部 50 ID、既有能力基準、開源候選與取捨、五模組架構、四個關鍵契約、P0–P5 分期與過渡保障。
- 推薦 Python 共用核心＋Git／結構化資料＋成熟檢查元件＋受控代理＋小型協調服務；不以規格框架、hooks 或訊息佇列冒充硬保障。
- 官方資料查證 2026-11-06：Gitleaks 維護方向、Beads Dolt、sandbox-runtime Windows alpha 與 Agent Mail 附加授權限制已列入選型；候選未安裝、未整合實測、未呼叫額外模型。
- 新增文件已登記 ARCHITECT／AGENTS；需求決策與歷史原件未修改。來源例外維持。

## 未完成／下一步

1. **把這次 hook 修正同步到各部署專案**（部署專案都在 Windows 那台，Mac 上一個都沒有）：在那台逐專案先完成 A1–A5，再跑 `python -X utf8 tools/sync_project.py <專案路徑> --owner '<工作中欄位完整值>' --write`。只有 `git-freshness.sh` 與 `ag-wrap.sh` 變、`SKILL.md` 沒變，所以**不會**印「骨架落後」，不同步也沒有任何提醒。
2. **Mac 的 Codex 開場 hook 驗收**（使用者自己做，會用到 Codex 額度）：在 Codex App 開啟本 repo 並信任 → Hooks 設定審核 SessionStart → 新 session 送一則短訊息，確認出現 `[repo-check]` 開場訊息（skill B5）。
3. **F42–F49 八條全部未實作、未驗收**。新規劃建議先 P0 驗證完整歸因、使用前通知與不可繞過授權，再分期；這是建議，不是已採納排程。
4. **F46 的偵測部分未實作**（宣告為例外已寫進 ARCHITECT）；`verify_bootstrap.py` 還不會把那三項列成已宣告的例外。
5. **F21 的阻擋層尚未實作**：要先指出擋在哪一層。
6. **F41 的七個缺口未修**（想要，不是排程），詳見 F41 驗收。
7. 依決策書第 5 節建立 **50 條持續維護的現況對照**；本輪規劃只有帶基準的能力快照，沒有移交狀態權威。
8. [第二輪複審快照](project-bootstrap-reaudit-2026-11-03.md) R01–R09 未逐項核對修正邊界。
9. [效率計畫](project-bootstrap-efficiency-plan.md) P0／P1 未實作；第 14 章 S1 仍待採納。

## 地雷與注意事項

- 規劃的 bootstrap CLI、代理與協調服務都尚不存在；不得照規劃跳過全域 handoff 或逐專案接棒。
- F11(b)、F28、F42／F43(a)／F48 是可行性門檻：工具若可繞過受控入口，必要強度不得報達標。
- 需求基準不等於驗收通過；來源三項例外仍有效，不得藉新架構偷偷補裝或撤銷。
- 額外模型探針須明確授權且只用訂閱額度；不因研究工具而取得安裝、付費或部署授權。
- 歷史需求只供追溯，待決唯一入口在決策書第 6 節；純實作待辦不列成需求待決。

## 服務查證與期望快照

本輪接棒與文件驗證均實跑 `python3 -X utf8 tools/verify_bootstrap.py`：exit 0、51 項全過、無 skip；最終提交快照按同一入口再驗。
本 repo 無 verify_state.py／check_docs.py，依 AGENTS 用上述替代入口；本輪接線未改，信任重審不適用。
外部候選只讀官方文件與 repo metadata，未作效能、隔離、通知或跨工具整合驗收。

## 懸置事項（AI 勿自行處理）

- 本輪交付規劃，不代表已採納或授權執行 P0–P5；後續依使用者選定範圍實作。
- 原子 claim 另案，Antigravity IDE 不重開；部署專案在 Windows 的同步仍需在該機器按程序處理。
