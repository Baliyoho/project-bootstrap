# 封存索引

> 最後更新：2026-11-18（資料夾從 `docs/history/` 改名 `docs/archive/`，需求決策書 v3 Q44；`docs/history/` 改放可以自由查的熱歷史）；前次 2026-11-17（加 handoff-ab 的改進計畫與 ARCHITECT 的結構變更紀錄）；前次同日（建立：根目錄 19 份結案或被取代的需求與計畫類文件封存到這裡）
> **平常不讀，要回溯歷史先經使用者同意**（需求決策書 v3 Q39）。程式與測試不得引用這裡任何檔，`verify_bootstrap.py`「封存原件」會擋。現行權威是[需求決策書 v3](../../project-bootstrap-requirements-decision-v3.md)（要什麼）與[實施計畫 v3](../../project-bootstrap-implementation-plan-v3.md)（怎麼走過去）。
> 除了 v2 決策書逐位元組凍結，其餘檔搬來時只把連到根目錄的相對連結改成 `../../`，內文不改；檔內的「權威版」「待決」「未採納」都是當時的狀態。

## 決策書與需求定義

| 檔案 | 是什麼 | 何時結案 | 結論落在哪裡 |
|---|---|---|---|
| [requirements-decision-v2.md](requirements-decision-v2.md) | 需求決策書決策版本 2，含 Q1–Q31 與逐條否決理由 | 2026-11-17 退休，凍結原件（v3 Q39） | 51 個需求 ID 沿用到 v3 第 4 節 |
| [project-bootstrap-requirements-history.md](project-bootstrap-requirements-history.md) | 需求定義 v1 到 v3.10 的全文與修訂理由 | 2026-11-06 封存，由決策版本 2 取代 | 需求 ID 到 v3.10 為止的來歷；現行條文在 v3 第 4 節 |

## 需求來回討論（2026-11-04 到 11-06）

每一輪的結論都寫回了當時的需求定義，所以結論落在需求歷史原件的對應版本，ID 沿用到 v3。

| 檔案 | 是什麼 | 何時結案 | 結論落在哪裡 |
|---|---|---|---|
| [project-bootstrap-requirements-review-2026-11-04.md](project-bootstrap-requirements-review-2026-11-04.md) | Q1–Q7 審閱意見 | 2026-11-04 | 需求定義 v2 |
| [project-bootstrap-requirements-review-reply-2026-11-04.md](project-bootstrap-requirements-review-reply-2026-11-04.md) | 對 Q1–Q7 的逐項評估回覆 | 2026-11-04 全部採納 | 需求定義 v2 |
| [project-bootstrap-requirements-response-2026-11-04-2230.md](project-bootstrap-requirements-response-2026-11-04-2230.md) | 對 v2 修訂的再評估（S1–S6） | 2026-11-04 | 下一列的回覆 |
| [project-bootstrap-requirements-response-reply-2026-11-04-2310.md](project-bootstrap-requirements-response-reply-2026-11-04-2310.md) | 對 S1–S6 與六條校正的逐項回覆 | 2026-11-05 | 需求定義 v3 |
| [project-bootstrap-requirements-response-review-2026-11-05-0927.md](project-bootstrap-requirements-response-review-2026-11-05-0927.md) | 第三輪審閱 | 2026-11-05 | 下一列的回覆 |
| [project-bootstrap-requirements-response-review-reply-2026-11-05-1545.md](project-bootstrap-requirements-response-review-reply-2026-11-05-1545.md) | 對第三輪審閱的回覆與 v3 採納紀錄 | 2026-11-05 | 需求定義 v3 |
| [project-bootstrap-requirements-response-review-2026-11-05-1606.md](project-bootstrap-requirements-response-review-2026-11-05-1606.md) | 對需求 v3 的審閱 | 2026-11-05 | 下一列的回覆 |
| [project-bootstrap-requirements-response-review-reply-2026-11-05-1620.md](project-bootstrap-requirements-response-review-reply-2026-11-05-1620.md) | 對 1606 的回覆與 v3.1 採納紀錄 | 2026-11-05 | 需求定義 v3.1 |
| [project-bootstrap-requirements-response-review-2026-11-05-1632.md](project-bootstrap-requirements-response-review-2026-11-05-1632.md) | v3.1 的五項定向審閱 | 2026-11-05 採納 | 下一列的回覆 |
| [project-bootstrap-requirements-response-review-reply-2026-11-05-2150.md](project-bootstrap-requirements-response-review-reply-2026-11-05-2150.md) | 對 1632 的回覆與 v3.2 採納紀錄 | 2026-11-05 | 需求定義 v3.2 |
| [project-bootstrap-requirements-final-review-2026-11-05-2214.md](project-bootstrap-requirements-final-review-2026-11-05-2214.md) | v3.2 最後審閱與五項修改指令 | 2026-11-06 實作 | 需求定義 v3.3 |
| [project-bootstrap-requirements-completeness-audit-2026-11-06.md](project-bootstrap-requirements-completeness-audit-2026-11-06.md) | 功能完整性複查，八項候選缺口 C01–C08 | 2026-11-06 定案 | 需求定義 v3.10，見需求歷史原件「已定案（原待決）：功能完整性複查的八項候選缺口」 |

## 結構紀錄

| 檔案 | 是什麼 | 何時結案 | 結論落在哪裡 |
|---|---|---|---|
| [architect-log.md](architect-log.md) | ARCHITECT.md 開頭原本的逐次結構變更紀錄（2026-08-05 到 2026-11-17） | 2026-11-17 搬出，ARCHITECT 改成只寫現況 | 現況在 ARCHITECT.md；之後的變更看 Git 歷史 |

## 查核、計畫與設計

| 檔案 | 是什麼 | 何時結案 | 結論落在哪裡 |
|---|---|---|---|
| [project-bootstrap-audit.md](project-bootstrap-audit.md) | 第三方查核 F01–F16（查核編號，不是需求 ID） | 2026-11-03：15 條修正，F12 完成協調邊界 | 唯一沒做的原子 claim 在實施計畫 v3 第 4 節（F12、F25） |
| [project-bootstrap-audit-progress.md](project-bootstrap-audit-progress.md) | 上一列 16 條的處理進度 | 2026-11-03 | 同上 |
| [project-bootstrap-reaudit-2026-11-03.md](project-bootstrap-reaudit-2026-11-03.md) | 第二輪複審 R01–R09 | 2026-11-03 修完（`4cd9262`、`a762ad1`） | 修正在程式與驗證器裡，沒有留下待辦 |
| [project-bootstrap-skill-split-design.md](project-bootstrap-skill-split-design.md) | handoff skill 依模式拆分的設計與實測 | 2026-11-10 寫進部署包（當時的 Q9 (a)） | F22；字元上限後來由 v3 的 D11 行數預算取代 |
| [project-bootstrap-efficiency-plan.md](project-bootstrap-efficiency-plan.md) | 效率改進提案：接棒分流、驗證分層、必讀精簡、來源與產物分離 | 2026-11-17 由實施計畫 v3 取代 | 驗證分層與沿用結果在實施計畫 v3 第 4 節（F22、F24），還成立的非目標在第 5 節；「接棒 5 分鐘內」使用者不再要（F22 只照 D11） |
| [project-bootstrap-implementation-plan.md](project-bootstrap-implementation-plan.md) | v2 時代的實現規劃：技術棧、51 項映射、P0–P5 | 2026-11-17 使用者判定 P0–P5 不算數 | 實施計畫 v3 第 2 節的否決路線 |
| [handoff-ab-optimization-plan.md](handoff-ab-optimization-plan.md) | handoff-ab 的交接棒執行與量測改進計畫（原 `experiments/handoff-ab/OPTIMIZATION-PLAN.md`） | 2026-11-15 兩階段做完，結果在 `experiments/handoff-ab/PHASE2-RESULTS.md`；2026-11-17 封存 | 怎麼跑搬進 `experiments/handoff-ab/README.md`「純任務 A/B 與後續探針」；量測對應 F22、F24 |
