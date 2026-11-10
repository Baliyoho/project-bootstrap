# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-10 21:35（+08）
- **交棒者**：Claude Code（Fable 5.2）／ `Mac`（依 HANDOFF 下一步逐項推進；剩下的項目都等使用者決定或屬後面階段）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。各模組用法與邊界見 [v2 說明](experiments/v2/README.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-10`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2、Git 2.54；ad hoc virtualization entitlement 可啟 VM；有 Secure Enclave 與 Touch ID。Windows／Linux 未驗。現行部署包及程序未切換。

## 已完成

- v2 各原型（P0 管道分權／票據／受管 worker／VM 帳本與崩潰解除，M1–M4 偵測與合成阻擋，720 個 mutation 規格）都是合成 fixture 原型，索引結果仍是「未驗證」或「不通過」；逐模組與逐 ID 看 [v2 現況索引](experiments/v2/status.json)與 [v2 說明](experiments/v2/README.md)。
- 決策書第 6 節 Q1–Q14 都有使用者裁定；六檔版 handoff skill 在本分支部署包與這台 Mac 的兩個全域副本（`VERSION` `2026-11-10`），不上 `main`、不同步專案。
- 2026-11-10 本輪（都在 v2 說明有對應段落）：
  - **動作提醒 hook 的誤報查明並修掉**：PostToolUse 的輸入含指令輸出，輸出裡換行後出現 git push 就觸發。`repo-action-rules.sh` 改成解析 JSON、只看 `tool_input`、照 shell 切詞；真 session 重測不再誤報；`verify_bootstrap.py` 的情境從 26 個加到 50 個，另有退回舊比對的負向測試。
  - **host 整機崩潰的離線盤點** `test_host_crash.py`：紀錄截斷或補零都不算停機證據；run 中途崩潰後永遠阻擋、沒有解除途徑；帳本檔截短不會讀成沒東西在跑；帳本檔遺失會讀成第一次啟動（已知缺口）。`crash_release` 對不存在的資料庫改成拒絕、不建檔。
  - **guest 殼層腳本離線測試** `test_vm_guest_scripts.py`，量到數字檢查有洞（`1-2`、`-`、`010` 會通過），兩支腳本已改嚴；真 VM 探針加 `runner_refusals`（runner 的拒絕路徑都不印停機行）。
  - **真人核准候選探針** `presence_probe.py`：本機可建立「本人在場才能簽」的 Secure Enclave 金鑰，不互動時簽不出來。沒有問過人，沒有接進任何路徑。

## 未完成／下一步

1. **清單上不用使用者決定的都做了**；接下來每一項都要先有懸置事項裡的裁定。下一棒先看使用者回了哪幾題，照裁定做；沒有新裁定就不要自己挑一題做。
2. P0 未退出。Mac 這半邊仍未驗：真的斷電與檔案系統耐久性、通用工具進無共享 guest（屬 P3 的 M3 隔離）、兩 VM 的 virtiofs `flock` 不協調（無共享路徑不用共享目錄，所以沒有後續動作）。帳本檔遺失讀成第一次啟動是已知缺口，沒有修。
3. 簽署金鑰發行／撤銷與額度來源沒做；`release.py`／`publish.py` 的金鑰仍是測試替身。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪（要先選定真實工具）。
4. 六檔版 skill：規則連到理由還沒做；本 repo 必讀約 16,100 仍超標，使用者說之後回頭修。
5. 動作提醒 hook 試行中。已知漏報：`bash -c "git push"` 這類包在引號裡的寫法；沒有 python 時退回舊的原始字串比對（會有先前那種誤報）。去留看試用結果。
6. Swift runner 沒有離線測試；guest 腳本的離線測試跑的是 host 的 dash／sh，不是 busybox ash；`guest_runner_sigkill` 與 `runner_refusals` 只在真 VM 跑，沒有 mutation 規格。trail 多數採用理由只能寫「當時沒有記錄理由」。F14／F15 需另一個工具或 OS；F41 使用者已決定先不用雲端。
7. Windows hook 同步、R01–R09 獨立複審、Mac Codex 真實注入、F28 模型探針都先不做（使用者 2026-11-10 裁定）。

## 地雷與注意事項

- handoff skill 的六個檔只在部署包 3.8 改，六個 `source:` 標記與 `VERSION` 要同版本。改到逐字搬來的行，「skill 拆分」會擋：要嘛還原，要嘛在 `tools/skill_split_baseline.json` 的 `rewritten` 寫明去處。改完要重新覆蓋這台的兩個全域目錄。
- 各原型都是**偵測**或合成阻擋，沒有接進任何工具。不要寫成保障。崩潰解除的終端確認只抬高 agent 代答門檻；`presence_probe` 的結果只是候選。
- 改 `vm_guest_init.sh`／`vm_managed_worker.sh` 之後要重跑真 VM `vm_probe.py`（離線測試不是 busybox）；`mutants.json` 對應原文也要一起改。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件。HANDOFF 的「下一步」與懸置裡**不要把已有裁定的 Q 編號跟等待決定的字樣寫在一起**；懸置每條要引用決策書第 6 節的 `Q` 編號（或 `- 無。`）。決策書第 7 節每條要有 `理由：`；第 6 節有裁定的項目底下子項格式是「採用理由／未選／暫緩」。
- 提交指令要用 `&&` 綁住 verify 的結束碼。這台的互動殼層是 zsh：管線的結束碼是 `${pipestatus[1]}`，不是 bash 的 `PIPESTATUS`。
- AGENTS.md 只有規則；新增或改規則時在 [AGENTS-reasons.md](AGENTS-reasons.md) 補段落與錨點。
- 讀 `tools/` 的測試不能放進 mutation 群組，所以拆成 `*_repo.py`。`mutants.py --only` 要給測試模組名（`experiments.v2.test_x`）；給錯會印「有存活或過期 {}」而不是全部擋下。新守門用 `denied(code, ...)` 寫法。
- 帳本列未 `retired` 時重啟一律阻擋，不要人工改列；解除走 `python3 -X utf8 -m experiments.v2.crash_release DB RUN_ID`，必須人在 host 本機終端。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。

## 服務查證與期望快照

- 2026-11-10 21:35 `python3 -X utf8 tools/verify_bootstrap.py --staged` exit 0，63 項全部通過（含 v2 的 433 個契約／索引測試；F22 與三個預期反例照報不通過）。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-10 `python3 -X utf8 experiments/v2/mutants.py` 全量 720 個全部 killed（含本輪新增：guest 腳本 18、真人核准探針判讀 7、崩潰解除缺資料庫 1）。
- 2026-11-10 `python3 -X utf8 experiments/v2/vm_probe.py` exit 0（約 40 秒，含新增的 `runner_refusals`；guest 腳本改嚴之後跑的）。`python3 -X utf8 -m experiments.v2.presence_probe` exit 0（候選可用但未驗收）。
- 本 repo 的 Claude Code 動作提醒 hook 已改；接線沒改；Codex 接線未改，Codex 信任重審不適用。無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- Q15：host 整機崩潰後要不要用開機階段識別當解除證據（決策書第 6 節）。
- Q16：真人核准來源要不要用「本人在場才能簽」的 Secure Enclave 金鑰做原型（驗收要使用者在場）。
- Q17：六檔版 skill 的規則怎麼連到理由（逐條連結或對照表）。
- Q18：Mac 這半邊之後怎麼走（先補 Q15／Q16、直接進 P1，或等 Windows）。
