# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-10 23:55（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（照使用者對 Q15–Q18 的裁定做完 Q15 與 Q17，登記 Q19）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。各模組用法與邊界見 [v2 說明](experiments/v2/README.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111108｜補帳本缺口｜工作中｜交棒0次`，2026-11-11 08:55 (+08) 開工
- **骨架版本**：`2026-11-10.2`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2、Git 2.54；ad hoc virtualization entitlement 可啟 VM；有 Secure Enclave 與 Touch ID。Windows／Linux 未驗。現行部署包及程序未切換。

## 已完成

- v2 各原型（P0 管道分權／票據／受管 worker／VM 帳本與崩潰解除，M1–M4 偵測與合成阻擋，mutation 規格）都是合成 fixture 原型，索引結果仍是「未驗證」或「不通過」；逐模組與逐 ID 看 [v2 現況索引](experiments/v2/status.json)與 [v2 說明](experiments/v2/README.md)。
- 決策書第 6 節 Q1–Q18 都有使用者裁定；六檔版 handoff skill 在本分支部署包與這台 Mac 的兩個全域副本，不上 `main`、不同步專案（Q14）。
- 2026-11-10 晚間本輪：
  - **Q15 (a) host 重開機當解除證據**：帳本開機前登記 `kern.bootsessionuuid`；runner 紀錄不合格時，現值跟登記值不同才算 host 端證據，仍要本機終端挑戰碼。紀錄合格就不讀開機識別。13 個新離線測試、13 個新 mutation；真 VM 探針驗登記值格式，以及同一次開機會被拒。細節在 v2 說明。
  - **Q16 (c)**：真人核准維持本機終端挑戰碼，`presence_probe` 不往下做。
  - **Q17 (b)**：部署包 3.8 的 `reasons.md` 末尾加「規則 → 理由在哪」對照表（40 列）；`verify_bootstrap.py` 新增「skill 規則對照表」與 8 個負向測試。六個 skill 檔與 `VERSION` 跳 `2026-11-10.2`，這台 Mac 的 `~/.claude/skills/handoff/`、`~/.codex/skills/handoff/` 已覆蓋且與重生骨架一致。
  - Q18 (b) 照做後登記 Q19（要不要進 P1）。

## 未完成／下一步

1. **等 Q19 的裁定**再決定 P0 收尾或進 P1；沒有新裁定就不要自己挑一題做。
2. P0 Mac 這半邊仍未驗：真的斷電與檔案系統耐久性、真的重開機（Q15 只有離線替身）、通用工具進無共享 guest（屬 P3 的 M3 隔離）。帳本檔遺失讀成第一次啟動是已知缺口，沒有修。
3. 簽署金鑰發行／撤銷與額度來源沒做；`release.py`／`publish.py` 的金鑰仍是測試替身。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪（要先選定真實工具）。
4. 六檔版 skill：本 repo 必讀約 15,600 仍超標，使用者說之後回頭修（Q10）。
5. 動作提醒 hook 試行中。已知漏報：`bash -c "git push"` 這類包在引號裡的寫法；沒有 python 時退回舊的原始字串比對（會誤報）。去留看試用結果。
6. Swift runner 沒有離線測試；guest 腳本的離線測試跑的是 host 的 dash／sh，不是 busybox ash；`guest_runner_sigkill` 與 `runner_refusals` 只在真 VM 跑，沒有 mutation 規格。trail 多數採用理由只能寫「當時沒有記錄理由」。F14／F15 需另一個工具或 OS；F41 使用者已決定先不用雲端。
7. Windows hook 同步、R01–R09 獨立複審、Mac Codex 真實注入、F28 模型探針都先不做（使用者 2026-11-10 裁定）。

## 地雷與注意事項

- handoff skill 的六個檔只在部署包 3.8 改，六個 `source:` 標記與 `VERSION` 要同版本；同一天再改要加序號（今天已到 `.2`）。改到逐字搬來的行，「skill 拆分」會擋：要嘛還原，要嘛在 `tools/skill_split_baseline.json` 的 `rewritten` 寫明去處。改了模式檔的段落標題，「skill 規則對照表」會擋，要一起改 `reasons.md` 對照表。改完要重新覆蓋這台的兩個全域目錄。
- 各原型都是**偵測**或合成阻擋，沒有接進任何工具。不要寫成保障。崩潰解除的終端確認只抬高 agent 代答門檻；開機識別的登記值存在同 UID 可寫的帳本裡。
- 改 `vm_guest_init.sh`／`vm_managed_worker.sh` 之後要重跑真 VM `vm_probe.py`（離線測試不是 busybox）；`mutants.json` 對應原文也要一起改（重構 `guest_runs.py`／`crash_release.py` 會讓舊原文失配，`mutants.py --only` 會報）。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件。HANDOFF 的「下一步」與懸置裡**不要把已有裁定的 Q 編號跟等待決定的字樣寫在一起**；懸置每條要引用決策書第 6 節的 `Q` 編號（或 `- 無。`）。決策書第 7 節每條要有 `理由：`；第 6 節有裁定的項目底下子項格式是「採用理由／未選／暫緩」。
- 提交指令要用 `&&` 綁住 verify 的結束碼。這台的互動殼層是 zsh：管線的結束碼是 `${pipestatus[1]}`，不是 bash 的 `PIPESTATUS`；`echo =====` 在 zsh 會被當成檔名展開而失敗。
- AGENTS.md 只有規則；新增或改規則時在 [AGENTS-reasons.md](AGENTS-reasons.md) 補段落與錨點。
- 讀 `tools/` 的測試不能放進 mutation 群組，所以拆成 `*_repo.py`。`mutants.py --only` 要給測試模組名（`experiments.v2.test_x`）。新守門用 `denied(code, ...)` 寫法。
- 帳本列未 `retired` 時重啟一律阻擋，不要人工改列；解除走 `python3 -X utf8 -m experiments.v2.crash_release DB RUN_ID`，必須人在 host 本機終端。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。

## 服務查證與期望快照

- 2026-11-10 23:55 `python3 -X utf8 tools/verify_bootstrap.py --staged` exit 0，64 項全部通過（含 v2 的 446 個契約／索引測試；F22 與三個預期反例照報不通過）。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-10 `python3 -X utf8 experiments/v2/mutants.py` 全量 733 個全部 killed（本輪新增 13 個崩潰解除刪改）。
- 2026-11-10 `python3 -X utf8 experiments/v2/vm_probe.py` exit 0（本輪改了 `guest_parent_sigkill` 之後跑的）。
- 本 repo 的 hook 與接線本輪沒改；Codex 接線未改，Codex 信任重審不適用。無額外模型呼叫、候選安裝或真實部署；沒有同步任何專案。

## 懸置事項（AI 勿自行處理）

- Q19：P0 Mac 這半邊收尾後要不要進 P1（決策書第 6 節）。
