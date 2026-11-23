# 進度

> 最後更新：2026-11-23
> v4 重寫稿，不是約束文件。回答「各期走到哪、靠什麼證據、還差什麼」。各期的範圍與退出條件在[需求](requirements.md)「分期」與「驗收」，路線與暫緩項目在[實施計畫](roadmap.md)；當下這一棒做到哪在 `HANDOFF.md`，逐條需求的實作狀態在[現況索引](../../docs/status.json)。期別狀態變了才改本檔，只寫現況，經過進[歷史紀錄](history.md)。
> v4 生效前，期別進度以[實施計畫 v3](../../project-bootstrap-implementation-plan-v3.md)為準；本檔是 2026-11-23 照它整理的快照。

| 期 | 狀態 | 證據 | 還差什麼 |
|---|---|---|---|
| 第 1 期 | 已結案（2026-11-17） | handoff-ab 兩輪見 [RESULTS](../../experiments/handoff-ab/RESULTS.md)「v3 第 1 期」，F50 見 [F50.md](../../experiments/handoff-ab/F50.md)，都跑在部署包 `2026-11-13`；macOS 的安裝、更新、換行與兩支 hook 在 `tests/test_bootstrap_repo.py` 實跑 | 無 |
| 第 2 期 | 進行中 | handoff-ab 兩輪見 [CODEX-RESULTS](../../experiments/handoff-ab/CODEX-RESULTS.md)（2026-11-14） | Codex 桌面 App 的 F50 標題項判定；在 Codex 上照 HANDOFF 接手的安裝程式實跑。續做時機見[待決事項](open-questions.md) Q61 |
| 第 3 期 | 有部分紀錄 | Codex＋原生 Windows 見 CODEX-RESULTS 的 Windows 各節（2026-11-16） | `midway` 斷線情境的失敗在 B1 改了之後重跑；Claude Code＋Windows；Windows 的安裝、`.gitattributes` 換行與 hook 實跑 |
