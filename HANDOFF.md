# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-10 13:20（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `baliyohodeMini`（v2 偵測原型第二批：F45／F6–F8／F26／F24／F35／F21／F17／F39／F3–F40 ingest）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。各模組用法與邊界見 [v2 說明](experiments/v2/README.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`baliyohodeMini` ／ `Claude Code` ／ `㊣　26111007｜第二機接續偵測｜工作中｜交棒0次`，2026-11-10 07:50 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2、Git 2.54；ad hoc virtualization entitlement 可啟 VM。Windows／Linux 未驗。現行部署包及程序未切換。

## 已完成

- v2 P0 原型（管道分權、工作樹套用、票據簽核、受管 worker、outbox、Mac VM 無共享 guest 帳本）保留；三個原始繞過反例仍重現，嚴格模式未就緒。
- M1／M3：`gitclaim`、`batch`、`preflight`、`release`、`policy`、`impact`（F4／F9／F10／F18／F19／F25／F30／F31–F33／F36–F38）。
- M2／M4 偵測（2026-11-09）：`lines`、`readonly`、`state`、`evidence`、`facts`、`decisions`、`doctor`（F1／F2／F3／F5／F12／F16b／F20／F23／F34／F40／F44）。
- 2026-11-10 新增（全是合成 fixture 原型，索引結果仍「未驗證」）：
  - F45 `contradictions.py`：宣告式規則表＋決策書第 6 節登記列。對本 repo 首跑抓到兩處真矛盾並已修：HANDOFF 懸置未登記（補登決策書 Q1）、ARCHITECT 根目錄表需求數是舊值（改 51）。
  - F6／F7／F8 `trail.py`＋`trail_sources.py`：直接讀決策書第 7 節、實現規劃 3.4 路線表與第 7 節分期表；抓到第 7 節第 7 條缺 `理由：` 標記，已補（未改字句）。
  - F26 `confluence.py`、F24 `campaign.py`、F35 `publish.py`（阻擋）、F21 `bypass.py`（index 擋就地改 core＋跳步雜湊鏈）、F17 `install.py`、F39 `inventory.py`、F3／F40 `ingest.py`（實跑輸出轉成 59 筆全 PASS）。
  - 較早 14 個 v2 檔對應到 ID；測試守住新增檔必須被某 ID 認領（只剩 `__init__.py`、`status.json` 刻意回全驗）。
- 現行 22 檔部署包、skill／hook 副本及 `VERSION` 未改，無同步債；未呼叫額外模型或真實服務。

## 未完成／下一步

1. **P0 未退出。** guest 父程序崩潰後帳本正確阻擋，但沒有可信解除路徑，等決策書 Q1（見懸置）。
2. 已寫效果冪等／回滾與跨 epoch 原子歸因未驗。舊 `managed_vm_switch` 仍借 host worker 並掛可寫 scratch；兩 VM 的 virtiofs `flock` 不協調。無共享路徑只涵蓋固定 shell 工具與 `note` 寫入。
3. 可信真人核准、簽署金鑰發行／撤銷與額度來源；`release.py`／`publish.py` 的金鑰仍是測試替身。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。
4. 不需使用者決定、可續做：F14／F15／F16a（乾淨第二機接續：先查 AGENTS 指向的全域 skill 在新機不存在時，repo 內能否取得程序）、F41；較早模組（broker／launcher／lifecycle 等）的 mutation 轉進 `mutants.json`；F45 宣告表再擴充（序號規則、prompt 名稱；部分已由 verify_bootstrap「主張沒復活」守）；ARCHITECT 與各報告的決策轉成 `trail` 可讀格式；F26 衝突處置驗收。
5. 需要先有決定或授權才能做：把 `ingest`／`bypass`／`contradictions` 接進現行 A4／B7 或 hook（＝切換現行程序）；F46 模型實際遵循探針（額外模型呼叫）；鎖定 runtime／候選版本／LICENSE／digest 後做 P1。F22 常態必讀 46,239 字元（上限 12,000），不通過照報。Windows hook 同步、Mac Codex 真實注入、R01–R09 邊界獨立複審仍待做。

## 地雷與注意事項

- 各原型都是**偵測**或合成阻擋，沒有接進任何工具：`publish`／`bypass.guard_commit` 未掛到實際發布或提交入口，`--no-verify` 之類繞法未處理。不要寫成保障。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件，失敗會讓 verify 失敗。HANDOFF 懸置每條要引用決策書第 6 節的 `Q` 編號（或 `- 無。`）；描述舊需求數時不要寫出那個數字（需求數規則會把它當反向說法）。決策書第 7 節每條要有 `理由：`。
- 2026-11-10 本 session 曾把 verify exit 2 的提交推上 origin（`28a6aaf`，原因就是上一條的數字句），數分鐘後以 `2ae0271` 修正。提交指令要用 `&&` 綁住 verify 的結束碼，不要用 `;`。
- 讀 `tools/` 的測試不能放進 mutation 群組（`mutants.py` 只複製 `experiments/`，會假裝 killed），所以拆成 `*_repo.py`／`*_format.py`。
- 帳本「身分」是 parent 選定檔案的 digest，不是 VM 身分證明；帳本列未 `retired` 時重啟一律阻擋，不要人工改列。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 2026-11-10 `python3 -X utf8 tools/verify_bootstrap.py --staged` exit 0，全部檢查通過，含 312 個 v2 契約／索引測試（verify_v2 由它帶跑；F22 與三個預期反例照報不通過）。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-10 `python3 -X utf8 experiments/v2/mutants.py`：313 個全量實跑，全部 killed，exit 0（約 3 分鐘，不在 verify_v2 預設流程）。
- `python3 -X utf8 experiments/v2/contradictions.py` 對本 repo：未發現（只比對宣告表）。
- VM 程式本輪未改（2026-11-09 `vm_probe.py` exit 0）。接線未改，Codex 信任重審不適用；無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 決策書第 6 節 Q1：崩潰後人工解除的可信真人核准來源（下一步 1／3）。下一步 4 不需決定，可直接續做。既有 v2 實作授權仍有效，P0 未驗收退出。
