# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-23 16:20（+08）
- **交棒者**：Claude Code（桌面 App）／Mac mini（v4 重寫稿：目標定稿、八份文件成形）

## 任務目標

使用者在寫 v4 的需求與計畫，照[協作系統原則草稿](collaboration-system-principles-draft.md)重寫，目標是更簡潔、每個事實只有一個家。現行約束仍是需求決策書 v3 與實施計畫 v3；v4 整套取代 v3 時才生效。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：`v4_draft`（v4 草稿在 `v4_draft/`，重寫稿在 `v4_draft/new_draft/`）。
- **工作中**：Mac mini ／ Claude Code（桌面 App）／ ㊣　11.23.16｜待指派｜工作中｜交棒0次（開工 2026-11-23 16:20 +08）
- **骨架版本**：`2026-11-21.3`
- 本機能力：Mac mini；`git push` 可用；`.venv` 可跑外部套件測試（`.venv/bin/python -m pytest tests`）。`/usr/bin/python3` 是 3.9.6，低於全 repo 下限 3.12，要用另裝的 `python3`（3.15.2）。

## 目前進度

- `v4_draft/new_draft/` 八份：目標（已定稿，v4 最高層級規範）、需求、設計原則、理由與依據、實施計畫、進度、待決事項、歷史紀錄。目標以外都是初稿。
- 拆開的舊零件（需求書 v3、實施計畫 v3、原則草稿各段）與三份對照表留在 `v4_draft/` 根，索引見 [v4_draft/README.md](v4_draft/README.md)。
- 已照原則整理：`AGENTS.md`、驗證器、HANDOFF 格式（決策書 v3 Q59）。

## 未完成／下一步

1. **等使用者看 new_draft 的待決事項「還沒編號」各條**：強度定義、F43 子項、需求寫成可檢驗句子（AI 傾向）、名詞定義、放棄的路線放哪、設計原則是否列約束、條文附不附出處、第 2 期要不要重跑、設計原則與進度檔要不要部署到各專案、位元組上限、文件性質分類。逐條問，不要自己定。
2. **等使用者確認**實施計畫「v4 生效時要一起做的事」一節，以及三份對照表裡的建議刪除。
3. **部署目標形狀**（`v4_draft/target-shape.md`）還沒併進 new_draft：要先跟 `src/kit/kit.md` 比對。
4. **handoff skill 整理、`src/kit/kit.md` 對齊原則**：使用者排定之後做，沒說何時。兩份都混著「某天起……」的經過。做的時候一起處理驗證器 B 層的「skill 拆分」等項。
5. **這台 Mac 的全域 handoff skill 是 `2026-11-20.2`**，跟部署包不同版；使用者 2026-11-21 說先不要重裝。
6. **Windows 那台也在用的已部署專案**：還在 `2026-11-17.3`；等它交棒、且 Q60 有了做法再同步。Windows 那台的 Python 版本沒確認。

## 地雷與注意事項

- 使用者在 v4 重寫期間指示：`v4_draft/` 外的需求書 v3、實施計畫 v3、原則草稿只讀不改；草稿與分拆件一律放 `v4_draft/`。
- 根目錄的 `comparison-adr-memory-bank.md` 是使用者自己放的未追蹤檔，`--staged` 會因它回 exit 2：提交前暫移到 scratchpad、驗證後原樣移回；不要刪它或提交它。
- 共用規則與 HANDOFF 格式都沒經 handoff-ab 驗證；使用者要等規則全部定案再一次跑，不要每改一次就提。

## 服務查證與期望快照

- 2026-11-23 macOS Mac mini：`python3 -X utf8 tools/verify_bootstrap.py --staged` → exit 0，65 項全過（全域 skill 不同版只印提醒）。
- 這一輪只改文件，沒跑 pytest、變異測試與 handoff-ab；Windows 與已部署專案沒跑。

## 懸置事項（AI 勿自行處理）

- Q60：已部署專案的 `ARCHITECT.md` 怎麼改名成 `ARCHITECTURE.md`；定案前不要把任何專案同步到 `2026-11-20` 以後的版本。
- Q61：第 2 期（Codex＋macOS）與 Q49 在 Windows、Codex 上的實跑什麼時候續做。
