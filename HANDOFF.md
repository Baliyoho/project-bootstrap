# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-11 09:15（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（照 Q19 補帳本錨點，P0 Mac 這半邊收尾）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。各模組用法與邊界見 [v2 說明](experiments/v2/README.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111109｜開工P1｜工作中｜交棒0次`，2026-11-11 09:26 (+08) 開工
- **骨架版本**：`2026-11-10.2`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2、Git 2.54；ad hoc virtualization entitlement 可啟 VM；有 Secure Enclave 與 Touch ID。Windows／Linux 未驗。現行部署包及程序未切換。

## 已完成

- v2 各原型（P0 管道分權／票據／受管 worker／VM 帳本與崩潰解除，M1–M4 偵測與合成阻擋，mutation 規格）都是合成 fixture 原型，索引結果仍是「未驗證」或「不通過」；逐模組與逐 ID 看 [v2 現況索引](experiments/v2/status.json)與 [v2 說明](experiments/v2/README.md)。
- 決策書第 6 節 Q1–Q19 都有使用者裁定；六檔版 handoff skill 在本分支部署包與這台 Mac 的兩個全域副本，不上 `main`、不同步專案（Q14）。
- 2026-11-11 本輪（Q19 採 (b)，使用者原話「先補缺口，然後p0就可以先收尾了」）：
  - **帳本錨點**：`GuestRunLedger(lab, anchor=...)` 第一次開啟先把隨機帳本 id 寫進資料庫以外的錨點檔（fsync 檔與目錄、不覆蓋），再存進資料庫；之後帳本被刪、清空或換掉而錨點還在就拒絕（`ledger-lost`／`ledger-replaced`），錨點不見是 `ledger-anchor-missing`。不給 `anchor=` 行為不變。`test_guest_runs.py` 加 9 個、`test_host_crash.py` 加 1 個離線測試；新增 15 個 mutation。真 VM `guest_parent_sigkill` 的 parent 帶錨點，探針移走帳本檔後重開得到 `ledger-lost`。
  - **P0 Mac 這半邊收尾**：已知缺口清單寫在 v2 說明（錨點那段之後）；實現規劃第 7 節加一段說明 Mac 部分依 Q19 收尾，Windows 照 Q12 留到之後。
- 2026-11-11 **P1 第一片（開發骨架）**：使用者說「Start P1」，選了四片切法的第一片並授權 `brew install uv` 與下載依賴。新增 `pyproject.toml`（最低 3.12、`package = false`、授權表）、`uv.lock`（14 個外部套件含 sha256）、`src/project_bootstrap/`（空套件）、`tests/test_layout.py`；`verify_bootstrap.py` 新增「P1 開發骨架」附 7 個負向測試。`broker_fixture.sandbox_plan` 改啟動解析後的基底 Python（venv 的連結會被 sandbox 擋）。
- 2026-11-11 **P1 第二片（搬家）**：使用者說「Do slice 2」。`experiments/v2` 的程式 `git mv` 到 `src/project_bootstrap/`、測試到 `tests/`，模組名改 `project_bootstrap.x`／`tests.test_x`；`status.json` 證據路徑、`mutants.json` 檔案與測試名一起改；`experiments/v2/` 只留說明與索引。邏輯沒動，只改 import、路徑、`-c` 子程序的 `cwd`（改成 `src`）與 `mutants.py` 的複製範圍。歷史文件（決策書 Q 條目、設計稿、ARCHITECT 舊登記）的舊路徑照原樣留著。
- 2026-11-11 **P1 第三片（來源權威切換）**：使用者說「Start slice 3」。部署包拆成 `src/kit/kit.md`＋27 個 `src/kit/files/<部署路徑>.tmpl`，`tools/build_kit.py` 生成 `PROJECT-BOOTSTRAP.md`（仍提交），逐位元組重建、`extract()` 27 檔相同。AGENTS 鐵律 1 改寫並在理由檔補日期理由；README、ARCHITECT、本 repo 兩支 hook 的提醒改指 `src/kit`；`verify_bootstrap.py` 新增「部署包由來源生成」附 9 個負向測試。部署內容沒變，`VERSION` 不跳、不同步。

## 未完成／下一步

1. P1 切成四片（1 開發骨架 → 2 把 `experiments/v2` 模組與測試搬進 `src`／`tests` → 3 來源權威切換：部署包由來源生成、骨架檔等價重建、同批改 AGENTS 鐵律 1 → 4 JSON Schema、Markdown parser、快速只讀入口與 F22 實測）。第一到三片已做完；第四片等使用者說再開工。模組分組（目前 50 個模組平放在一個套件）沒做，留到真的要用時。
2. P0 Mac 的已知缺口（不再在 P0 補）：真的斷電與檔案系統耐久性、真的重開機、錨點只擋意外遺失、通用工具進無共享 guest（屬 P3）；清單在 v2 說明。
3. 簽署金鑰發行／撤銷與額度來源沒做；`release.py`／`publish.py` 的金鑰仍是測試替身。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪（要先選定真實工具）。
4. 六檔版 skill：本 repo 必讀約 15,300 仍超標，使用者說之後回頭修（Q10）。
5. 動作提醒 hook 試行中。已知漏報：`bash -c "git push"` 這類包在引號裡的寫法；沒有 python 時退回舊的原始字串比對（會誤報）。去留看試用結果。
6. Swift runner 沒有離線測試；guest 腳本的離線測試跑的是 host 的 dash／sh，不是 busybox ash；`guest_runner_sigkill` 與 `runner_refusals` 只在真 VM 跑，沒有 mutation 規格。trail 多數採用理由只能寫「當時沒有記錄理由」。F14／F15 需另一個工具或 OS；F41 使用者已決定先不用雲端。
7. Windows hook 同步、R01–R09 獨立複審、Mac Codex 真實注入、F28 模型探針都先不做（使用者 2026-11-10 裁定）。

## 地雷與注意事項

- 錨點拒絕的解除是人工步驟：確認那份帳本沒有 guest 還可能在跑，再手動刪錨點檔；沒有做成工具，agent 不要自己刪。
- 制度只改 `src/kit/`，改完跑 `python3 -X utf8 tools/build_kit.py` 重生 `PROJECT-BOOTSTRAP.md`，同一個 commit；手改部署包會被「部署包由來源生成」擋。handoff skill 的六個檔改 `src/kit/files/.claude/skills/handoff/*.tmpl`，六個 `source:` 標記與 `VERSION` 要同版本；同一天再改要加序號。改到逐字搬來的行，「skill 拆分」會擋：要嘛還原，要嘛在 `tools/skill_split_baseline.json` 的 `rewritten` 寫明去處。改了模式檔的段落標題，「skill 規則對照表」會擋，要一起改 `reasons.md` 對照表。改完要重新覆蓋這台的兩個全域目錄。
- 各原型都是**偵測**或合成阻擋，沒有接進任何工具。不要寫成保障。崩潰解除的終端確認只抬高 agent 代答門檻；開機識別登記值與錨點都在同 UID 可寫的地方。
- 改 `vm_guest_init.sh`／`vm_managed_worker.sh` 之後要重跑真 VM `vm_probe.py`（離線測試不是 busybox）；`mutants.json` 對應原文也要一起改（重構 `guest_runs.py`／`crash_release.py` 會讓舊原文失配，`mutants.py --only` 會報）。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件。HANDOFF 的「下一步」與懸置裡**不要把已有裁定的 Q 編號跟等待決定的字樣寫在一起**；懸置每條要引用決策書第 6 節的 `Q` 編號（或 `- 無。`）。決策書第 7 節每條要有 `理由：`；第 6 節有裁定的項目底下子項格式是「採用理由／未選／暫緩」。
- 提交指令要用 `&&` 綁住 verify 的結束碼。這台的互動殼層是 zsh：管線的結束碼是 `${pipestatus[1]}`，不是 bash 的 `PIPESTATUS`；`echo =====` 在 zsh 會被當成檔名展開而失敗。
- AGENTS.md 只有規則；新增或改規則時在 [AGENTS-reasons.md](AGENTS-reasons.md) 補段落與錨點。
- 讀 `tools/` 的測試不能放進 mutation 群組，所以拆成 `*_repo.py`。`mutants.py --only` 要給測試模組名（`tests.test_x`）。從 repo 根目錄跑模組要 `PYTHONPATH=src`；測試裡用 `-c` 起、要 import 本套件的子程序，`cwd` 要給 `src`。新守門用 `denied(code, ...)` 寫法。
- 帳本列未 `retired` 時重啟一律阻擋，不要人工改列；解除走 `PYTHONPATH=src python3 -X utf8 -m project_bootstrap.crash_release DB RUN_ID`，必須人在 host 本機終端。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。

## 服務查證與期望快照

- 2026-11-11 `python3 -X utf8 tools/verify_bootstrap.py --staged`：exit 0，66 項全部通過（含「部署包由來源生成」；`verify_v2` 跑 `tests/` 的 461 個；F22 與三個預期反例照報不通過）。`python3 -X utf8 tools/build_kit.py --check` 一致。
- 2026-11-11 `uv run --locked pytest`：搬家後 Python 3.15 與 uv 下載的 CPython 3.12.16（scratch venv）都是 461 個通過；`PYTHONPATH=src python3 -m unittest discover -s tests -t .` 也是 461 個。`uv lock --check` 一致。Windows／Linux 未跑。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-11 `python3 -X utf8 src/project_bootstrap/mutants.py`：搬家後全量 748 個全部 killed，沒有 stale。
- 2026-11-11 `python3 -X utf8 src/project_bootstrap/vm_probe.py` exit 0（搬家後重跑，`VM_PROBE_OK`，含錨點那一步）。
- 本 repo 的 hook 與接線、handoff skill 本輪沒改；Codex 接線未改，Codex 信任重審不適用。無額外模型呼叫或真實部署；本機用 Homebrew 裝了 uv 0.13.7，依賴只進專案 `.venv` 與 uv 快取；沒有同步任何專案。

## 懸置事項（AI 勿自行處理）

- 無。
