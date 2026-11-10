# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-10 18:35（+08）
- **交棒者**：Claude Code（Fable 5.2）／ `Mac`（handoff skill 拆成六檔的草稿寫進本分支部署包；Q9 已決，登記 Q11）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。各模組用法與邊界見 [v2 說明](experiments/v2/README.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111018｜推Q5到Q11｜工作中｜交棒0次`，2026-11-10 19:38 (+08) 開工
- **骨架版本**：`2026-11-10`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2、Git 2.54；ad hoc virtualization entitlement 可啟 VM。Windows／Linux 未驗。現行部署包及程序未切換。

## 已完成

- v2 各原型（P0 管道分權／票據／受管 worker／VM 帳本與崩潰解除，M1–M4 偵測與合成阻擋，680 個 mutation 規格）都是合成 fixture 原型，索引結果仍是「未驗證」；逐模組與逐 ID 看 [v2 現況索引](experiments/v2/status.json)與 [v2 說明](experiments/v2/README.md)。
- 2026-11-10 使用者裁定（決策書第 6 節 Q1–Q4）；F22 第一階段已完成（AGENTS 規則與理由分檔，必讀 46,239 → 31,335 字元，仍不通過上限 12,000）。
- 2026-11-10 崩潰後解除（Q1 (a)）：`crash_release.py`。`guest_runs` 開機前登記 runner `.host` 檔路徑；解除要那個檔逐行等於乾淨停機四行，再要 `/dev/tty` 照打挑戰碼（SSH／無終端拒絕；agent 殼層實測 `crash-release-no-terminal`），缺證據不問人、維持阻擋。真 VM `guest_parent_sigkill` 以真 runner 日誌走完解除、guest console 被拒；`guest_crash_replay` 在 outbox 已存未送時 SIGKILL，解除後重送只套用一次。同 UID 偽造 host 檔與偽終端不排除，不是真人證明。
- 2026-11-10 mutation 轉進：supervisor 11、guardian 10（新增 `test_guardian.py`）、lifecycle 26（補 `LifecycleCodeTests` 7 個逐代碼測試）、崩潰解除 23、F45 版本規則 3。lifecycle 整個模組實測約 5 秒（舊記 3 分鐘有誤）。
- 2026-11-10 F45 加「VERSION 只跟著 SKILL.md」規則（本 repo 未發現，反向句注入會報）；prompt 名稱已由 verify 的結構摘要一致性守，未重複加。F16a 對部署包生成的骨架以空家目錄跑通過，刪掉部署的 SKILL.md 即不通過。
- 2026-11-10（Mac 這輪）VM 探針相關 Python 檔轉成 mutation 規格：`vm_probe` 38、`managed_fixture` 37 個（首跑 26、30 個存活，補 10、9 個逐代碼測試）；`trail_sources.rules_from_agents` 讓 `why` 從 AGENTS 規則走到 AGENTS-reasons 段落（補 4 段 git 首次出現日期），7 個刪改。各組 `--spec` 單獨跑全部 killed。真 VM 新增 `guest_unread_request`：guest 已產生、parent 沒讀進 outbox 就被 SIGKILL 的請求，解除後不留任何效果（遺失、要重做）；parent 死後到 VM 停下之間的輸出未另量。
- 2026-11-10 skill 拆分（Q8、Q9 已決）：設計稿與實測在 [skill 拆分設計](project-bootstrap-skill-split-design.md)。部署包 3.8 現在產出六個檔（入口 `SKILL.md`＋`mode-a`／`mode-a-stop`／`mode-b`／`mode-0`／`reasons`），入口＋`mode-a.md` 5,380 字元（單檔 22,040）；拆分前 311 行有 300 行逐字留存、11 行列為已改寫。3.10 與本 repo 的開場 hook 全部條件成立才印「全綠」行。`VERSION` `2026-11-10`，骨架 27 檔。`sync_project.py` 會替舊專案補五個新檔；`verify_bootstrap.py` 新增「skill 拆分」「同步補齊模式檔」「全綠行」。
- 2026-11-10 Q5 (a)、Q6 (a)、Q7 (b)、Q11 (a) 已決。Q11 (a)：這台 Mac 的 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/` 已換成六檔版（與部署包產出逐位元相同）。**同步債**：`main` 沒有這一版、沒有同步任何專案、別台機器的全域副本未換；上 `main` 與同步專案等試用後另登新編號。

## 未完成／下一步

1. **P0 未退出。** 剩 2、3 兩項；崩潰解除已有合成原型。
2. 跨 epoch 原子歸因與舊路徑（`managed_vm_switch` 借 host worker、掛可寫 scratch）已寫效果回滾仍未驗；兩 VM 的 virtiofs `flock` 不協調；無共享路徑只涵蓋固定 shell 工具與 `note` 寫入。下一步是「隔離已寫效果」與擴到通用工具，屬 P0 下一階段範圍，跟 Q5 一起定。
3. 可信真人核准、簽署金鑰發行／撤銷（Q1 (b) 日後另登）與額度來源；`release.py`／`publish.py` 的金鑰仍是測試替身。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。
4. trail 來源：AGENTS 規則已轉；決策書第 6 節已決 Q 與效率計畫「非目標」沒有逐條否決理由，等 Q7；查核進度是修正紀錄、不是決策，不轉。Swift runner 與 guest 腳本沒有離線測試，未轉 mutation 規格。F14／F15 需另一個工具或 OS；F41 使用者已決定先不用雲端。
5. **F22 第二階段**：(1)(3) 已在本分支部署包，這台 Mac 的全域副本已換（Q11 (a) 試用中）。設計稿第 10 節列了沒做的：規則逐條連到 `reasons.md` 的錨點、任何工具上的實跑、Codex 重新審核。本 repo 合計約 16,100 仍超標，見 Q10。(2) 2026-11-10 起在本 repo 試行（Q6 (a)）：`.claude/hooks/repo-action-rules.sh` 只接 Claude Code，準備 push／push 後／改部署包／改 hook 時送規則摘要、不擋。本 session 實測三種提醒都進了 context；指令字串裡寫到「&& git push」或字面 `\n` 後接 git push 的測試資料仍會誤報。去留看試用結果。
6. 需要先有決定才能做：Q10。Windows hook 同步、Mac Codex 真實注入（要額外模型呼叫）、R01–R09 邊界獨立複審仍待做。

## 地雷與注意事項

- handoff skill 的六個檔只在部署包 3.8 改（六個區塊依序對應標題上的檔名），六個 `source:` 標記與 `VERSION` 要同版本。改到逐字搬來的行，「skill 拆分」會擋：要嘛還原，要嘛在 `tools/skill_split_baseline.json` 的 `rewritten` 寫明去處。
- 各原型都是**偵測**或合成阻擋，沒有接進任何工具：`publish`／`bypass.guard_commit` 未掛到實際發布或提交入口。不要寫成保障。崩潰解除的終端確認只抬高 agent 代答門檻。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件，失敗會讓 verify 失敗。HANDOFF 懸置每條要引用決策書第 6 節的 `Q` 編號（或 `- 無。`）；描述舊需求數時不要寫出那個數字。決策書第 7 節每條要有 `理由：`。
- 提交指令要用 `&&` 綁住 verify 的結束碼，不要用 `;`。
- AGENTS.md 只有規則；新增或改規則時在 [AGENTS-reasons.md](AGENTS-reasons.md) 補段落與錨點，否則「規則理由連結」會擋。
- 讀 `tools/` 的測試不能放進 mutation 群組（`mutants.py` 只複製 `experiments/`），所以拆成 `*_repo.py`。改到既有守門那一行時 `mutants.json` 對應原文會變 stale，要一起改。只驗「有拒絕」不驗代碼的測試殺不掉 mutant，新守門請用 `denied(code, ...)` 寫法。
- 帳本列未 `retired` 時重啟一律阻擋，不要人工改列；要解除走 `python3 -X utf8 -m experiments.v2.crash_release DB RUN_ID`，必須人在 host 本機終端。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。

## 服務查證與期望快照

- 2026-11-10 `python3 -X utf8 tools/verify_bootstrap.py --staged` exit 0，62 項全部通過（含 v2 的 407 個契約／索引測試；F22 與三個預期反例照報不通過）。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- `python3 -X utf8 experiments/v2/mutants.py`：2026-11-10 稍早全量 673 個全部 killed、其後 7 個以 `--spec` 單獨跑全部 killed，清單共 680 個。**本輪改了 `contradictions.py`（加兩條樣式）與 `baseline.py`，沒有重跑 mutation**；既有規格的原文行沒動。
- `python3 -X utf8 experiments/v2/contradictions.py` 對本 repo：未發現（只比對宣告表）。
- 2026-11-10 `python3 -X utf8 experiments/v2/vm_probe.py` exit 0（約 35 秒，含崩潰解除、崩潰後重送與未讀請求）。接線未改，Codex 信任重審不適用；無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 決策書第 6 節 Q10：本 repo 拆完 skill 仍超標（約 16,100）怎麼處理；使用者已同意等全域副本的六檔版試用幾輪後再定。
