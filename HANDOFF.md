# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-09 23:58（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `baliyohodeMini`（M2／M3 偵測原型批次：寫入前檢查、並行線、只讀、狀態、證據、待決、所有權、影響圖、mutation）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`baliyohodeMini` ／ `Claude Code` ／ `㊣　26111000｜續作v2偵測原型｜工作中｜交棒0次`，2026-11-10 10:05 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2、Git 2.54；ad hoc virtualization entitlement 可啟 VM。Windows／Linux 未驗。現行部署包及程序未切換。

## 已完成

- v2 P0 原型（管道分權、工作樹套用、票據簽核、受管 worker、outbox）與 Mac VM 無共享 guest 帳本 `guest_runs.py` 保留；三個原始繞過反例仍重現，嚴格模式未就緒。
- M3：`gitclaim.py` 開工／收尾閘門（F4／F9／F10／F19／F25）、`batch.py` 20 目標彙總（F30）；`preflight.py` 寫入時資格（遠端標記須正好是本 session、不得落後／分岔）＋發布確認，`batch` 可選逐目標發布確認。
- M1：`release.py` 整包 manifest 與逐次 nonce 簽章確認（F18／F32／F33）；`policy.py` 依所有權更新、只能加嚴的覆寫、空位 schema（F36／F37／F38）；`impact.py` 從索引證據推出改動影響（F31）。
- M2／M4 偵測：`lines.py` 並行線共用工作樹／index（F12）；`readonly.py` 只讀輪次快照比對（F23）；`state.py` 狀態模型與生成 HANDOFF 視圖（F1／F2／F5）；`evidence.py` 本輪／沿用／未驗證／不通過與依賴失效（F3／F40）；`facts.py` 文件命題對 Git／檔案實查（F20）；`decisions.py` 待決、委任與已宣告例外（F44／F34）；`doctor.py` 本機缺口（F16b）。
- **F45 跨文件矛盾**：`contradictions.py` 宣告式規則表＋決策書第 6 節登記列，報反向規則、節間／跨文件衝突、待決漏登、已決仍稱待決；`test_contradictions_repo.py` 對本 repo 文件要求未發現。首跑抓到 HANDOFF 懸置未登記，已補登決策書 Q1。
- **F6／F7／F8 留痕**：`trail.py` 決策紀錄（理由、基準、替代方案、雙向取代）、規則→理由、否決路線清單、舊快照比對抓刪改、路線圖里程碑。**F26 合流**：`confluence.py` 共同依據／帶條件結論／未確認／衝突分開，衝突整鍵擋用。**F24**：`campaign.py` 20 目標每列一動作，人工確認分組計數、超過 3 次照報。**F35**：`publish.py` 未本輪驗證、偽造結果、非 CI 簽章都拒絕且不寫檔。**F21**：`bypass.py` 讀 index 擋就地改 core／adapter；跳步紀錄雜湊鏈，無聲略過報出。
- **mutation 可重跑（F29／F49）**：`python3 -X utf8 experiments/v2/mutants.py` 跑 `mutants.json` 260 個守門刪改（2026-11-09 152 個全部 killed；2026-11-10 新增 contradictions 23、trail 24、confluence 15、campaign 14、publish 18、bypass 14 個，各以 `--only` 全 killed）（約 90 秒，不在 verify_v2 預設流程）。寫測試時抓到並修掉 `state.render` 兩個真錯；冗餘守門已刪而非保留。
- 以上全是合成 fixture 原型，索引結果仍是「未驗證」；未接進現行 A／B 程序、hook 或任何工具。現行 22 檔部署包、skill／hook 副本及 `VERSION` 未改，無同步債；未呼叫額外模型或真實服務。

## 未完成／下一步

1. **P0 未退出。** guest 父程序在退場前崩潰時帳本正確阻擋，但**沒有可信的解除路徑**：需「真人核准＋host 端獨立證據」的人工退場，牽涉可信真人核准來源，先和使用者確認方向（見懸置）。
2. 已寫效果冪等／回滾與跨 epoch 原子歸因未驗。舊 `managed_vm_switch` 仍借 host worker 並掛可寫 scratch；兩 VM 的 virtiofs `flock` 不協調。無共享路徑只涵蓋固定 shell 工具與 `note` 寫入。
3. 可信真人核准、簽署金鑰發行／撤銷與額度來源；`release.py` 可信端與金鑰仍是測試替身。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。
4. 不需使用者決定、可續做：仍無證據的 F45 擴充宣告表（版本號／序號規則等）、把決策書第 7 節等手寫理由轉成 `trail` 紀錄並建本 repo 路線圖檔、F14／F15／F16a／F17、F39、F41；把 `verify_bootstrap.py`／`verify_v2.py` 實際輸出轉成 `evidence.py` 紀錄；14 個較早 v2 檔（如 `broker.py`、`session.py`、`lifecycle.py`）沒被列為任何 ID 的證據，補對應前先讀懂各自支持哪條；較早模組的 mutation 轉進 `mutants.json`。
5. F46 仍須核對來源三項例外的替代保障與模型實際遵循（額外模型探針須先授權）。鎖定 runtime／候選版本／LICENSE／digest 後才做 P1。F22 常態必讀超過 12,000 字元，完整接棒時間與 token 未量。Windows hook 同步、Mac Codex 真實注入及 R01–R09 邊界獨立複審仍待做。

## 地雷與注意事項

- 本輪各原型都是**偵測**，不阻擋、不原子：`gitclaim`／`preflight` 判定到推送之間仍有時間窗；`lines` 擋不到沒登記就進同一資料夾的 agent；`readonly` 分不出遠端變動是本輪還是他人推送。不要把它們寫成保障。
- HANDOFF 懸置每條都要引用決策書第 6 節的 `Q` 編號（或寫 `- 無。`），否則 `test_contradictions_repo` 讓 verify 失敗。
- `release`／`policy` 的「效果」與依賴由宣告方填，宣告錯了或漏列，原型發現不了。`impact` 對沒進索引的檔一律回全驗，這是刻意的。
- 帳本「身分」是 parent 選定檔案的 digest，不是 VM 身分證明；`.host` 日誌與資料庫仍可被同 UID host 程序改寫。帳本列未 `retired` 時重啟一律阻擋；不要人工改列。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 2026-11-10 `python3 -X utf8 tools/verify_bootstrap.py --staged` exit 0，全部檢查通過，含 283 個 v2 契約／索引測試（verify_v2 由它帶跑）；提交候選另用 `--staged` 驗。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- mutation 全量未在 2026-11-10 重跑，見上方已完成那條。
- 2026-11-09 `vm_probe.py` exit 0（帳本與 channel 綁定版本）；本輪改動未碰 VM 程式。接線未改，信任重審不適用；無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 決策書第 6 節 Q1：崩潰後人工解除的可信真人核准來源（下一步 1／3）。下一步 4 不需決定，可直接續做。既有 v2 實作授權仍有效，P0 未驗收退出。
