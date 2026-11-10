# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-10 16:40（+08）
- **交棒者**：Claude Code（Fable 5.2）／ `baliyohodeMini`（F22 第一階段：AGENTS 規則與理由分檔、複審快照改條件式必讀、本檔已完成節縮短）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。各模組用法與邊界見 [v2 說明](experiments/v2/README.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`baliyohodeMini` ／ `Claude Code` ／ `㊣　26111010｜整理待決事項｜工作中｜交棒2次`，2026-11-10 15:41 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2、Git 2.54；ad hoc virtualization entitlement 可啟 VM。Windows／Linux 未驗。現行部署包及程序未切換。

## 已完成

- v2 各原型（P0 管道分權／票據／受管 worker／VM 帳本，M1–M4 偵測與合成阻擋，525 個 mutation 規格）都是合成 fixture 原型，索引結果仍是「未驗證」；逐模組與逐 ID 的內容看 [v2 現況索引](experiments/v2/status.json)與 [v2 說明](experiments/v2/README.md)，不在這裡重列。
- 2026-11-10 使用者裁定（決策書第 6 節）：崩潰解除採本機終端確認＋host 證據，拿不到證據就不解除，日後希望改成簽署金鑰；v2 偵測原型不接進現行程序，等 P1；F46 模型探針暫不授權。
- 2026-11-10 F22 第一階段（只動本 repo）：AGENTS.md 的事故與理由逐字搬到 [AGENTS-reasons.md](AGENTS-reasons.md)，入口每條規則留「為什麼」連結；`verify_bootstrap.py` 新增「規則理由連結」附 7 個負向測試；第二輪複審快照改成條件式必讀；`baseline.py` 的量測對象同步改成三份入口。必讀量 46,239 → 31,335 字元，仍不通過（上限 12,000，skill 一份約 22,000）。
- 現行 22 檔部署包、skill／hook 副本及 `VERSION` 未改，無同步債；未呼叫額外模型或真實服務。

## 未完成／下一步

1. **P0 未退出。** 依 Q1 (a) 實作崩潰後解除：host 本機終端互動確認＋host 端獨立停機證據，缺證據一律不解除（等同 (c)）；不得接受遠端或 agent 代按的確認。尚未動工。
2. 已寫效果冪等／回滾與跨 epoch 原子歸因未驗。舊 `managed_vm_switch` 仍借 host worker 並掛可寫 scratch；兩 VM 的 virtiofs `flock` 不協調。無共享路徑只涵蓋固定 shell 工具與 `note` 寫入。
3. 可信真人核准、簽署金鑰發行／撤銷與額度來源；`release.py`／`publish.py` 的金鑰仍是測試替身。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。
4. 不需使用者決定、可續做：lifecycle／supervisor／guardian 的 mutation 轉進 `mutants.json`（lifecycle 測試約 3 分鐘，群組要挑測試；先試跑，存活多半代表缺逐代碼測試）；F45 宣告表再擴充（版本號跟誰走、prompt 名稱；寬鬆樣式會把引述舊說法的句子當主張，要限定同一子句）；ARCHITECT 其他節與各報告的決策轉成 `trail` 可讀格式；F16a 對部署出去的專案入口同樣檢查。F14／F15 需另一個工具或 OS 才能驗；F41 使用者已決定先不用雲端。
5. 需要先有決定才能做：F22 第二階段與上限（見懸置；內容是 skill 依模式拆成獨立 skill、hook 在動作當下送規則、開場 hook 結論取代判讀表，全屬改現行程序，要跳 `VERSION` 並同步各專案）；P1 進場時機（見懸置）。偵測原型不接進現行程序、F46 探針不做，都已裁定。Windows hook 同步、Mac Codex 真實注入、R01–R09 邊界獨立複審仍待做。

## 地雷與注意事項

- 各原型都是**偵測**或合成阻擋，沒有接進任何工具：`publish`／`bypass.guard_commit` 未掛到實際發布或提交入口，`--no-verify` 之類繞法未處理。不要寫成保障。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件，失敗會讓 verify 失敗。HANDOFF 懸置每條要引用決策書第 6 節的 `Q` 編號（或 `- 無。`）；描述舊需求數時不要寫出那個數字（需求數規則會把它當反向說法）。決策書第 7 節每條要有 `理由：`。
- 提交指令要用 `&&` 綁住 verify 的結束碼，不要用 `;`（2026-11-10 曾因此把 exit 2 的提交推上 origin，數分鐘後修正）。
- AGENTS.md 現在只有規則；新增或改規則時，在 [AGENTS-reasons.md](AGENTS-reasons.md) 補對應段落與錨點，否則「規則理由連結」會擋。理由檔不是每輪必讀，**沒有量過模型在該讀的時候會不會真的去讀**；複審快照改條件式後也一樣。
- 讀 `tools/` 的測試不能放進 mutation 群組（`mutants.py` 只複製 `experiments/`，會假裝 killed），所以拆成 `*_repo.py`／`*_format.py`。改到既有守門的那一行時，`mutants.json` 對應原文會變 stale，要一起改（本輪 confluence 的 `whole =` 兩筆）。
- 帳本「身分」是 parent 選定檔案的 digest，不是 VM 身分證明；帳本列未 `retired` 時重啟一律阻擋，不要人工改列。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 2026-11-10 `python3 -X utf8 tools/verify_bootstrap.py --staged` exit 0，全部檢查通過（比上一輪多「規則理由連結」一項），含 352 個 v2 契約／索引測試（verify_v2 由它帶跑；F22 與三個預期反例照報不通過）。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-10 `python3 -X utf8 experiments/v2/mutants.py`：443 個全量實跑全部 killed（約 6 分鐘，不在 verify_v2 預設流程）；之後加入的 82 個（trail_sources／broker／launcher／materializer）以 `--spec` 試跑各自全部 killed，清單共 525 個，尚未再跑一次全量。
- `python3 -X utf8 experiments/v2/contradictions.py` 對本 repo：未發現（只比對宣告表）。
- VM 程式本輪未改（2026-11-09 `vm_probe.py` exit 0）。接線未改，Codex 信任重審不適用；無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 決策書第 6 節 Q4：F22 第二階段要不要做、上限要不要調（第一階段已完成；第二階段改現行程序，不要自行動手）。
- 決策書第 6 節 Q5：P1 進場時機（AI 建議先做完崩潰解除讓 P0 收尾）。下一步 1、4 不需決定，可直接續做。
