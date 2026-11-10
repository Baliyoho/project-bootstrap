# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-10 20:20（+08）
- **交棒者**：Claude Code（Opus 5.5）／ `Mac`（Q5／Q6／Q7／Q11 照 AI 建議定案並推進；登記 Q12、Q13）

## 任務目標

依 [需求決策書](project-bootstrap-requirements-decision.md) 決策版本 2 與 [實現規劃](project-bootstrap-implementation-plan.md) 續作 v2；已授權分支實作，未授權部署或切換現行程序。
**51 ID 與 F11／F13／F43 子項的持續狀態唯一權威：[v2 現況索引](experiments/v2/status.json)**。索引不可讀就停止判定；本檔只留停點與行動。各模組用法與邊界見 [v2 說明](experiments/v2/README.md)。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`（從 `main @ 40a2d02` 建立）；main 尚未合入 v2。
- **工作中**：`Mac` ／ `Claude Code` ／ `㊣　26111018｜推Q5到Q11｜工作中｜交棒1次`，2026-11-10 20:28 (+08) 開工
- **骨架版本**：`2026-11-10`
- 本機能力：macOS 27.2／Apple silicon、Python 3.15.2、Swift 6.4.2、bash 3.2、Git 2.54；ad hoc virtualization entitlement 可啟 VM。Windows／Linux 未驗。現行部署包及程序未切換。

## 已完成

- v2 各原型（P0 管道分權／票據／受管 worker／VM 帳本與崩潰解除，M1–M4 偵測與合成阻擋，694 個 mutation 規格）都是合成 fixture 原型，索引結果仍是「未驗證」或「不通過」；逐模組與逐 ID 看 [v2 現況索引](experiments/v2/status.json)與 [v2 說明](experiments/v2/README.md)。
- 2026-11-10 稍早：Q1–Q4、Q8、Q9 已決；F22 第一階段（AGENTS 規則與理由分檔）；崩潰後解除 `crash_release.py`；handoff skill 拆成六檔進本分支部署包（`VERSION` `2026-11-10`，骨架 27 檔，設計與實測見 [skill 拆分設計](project-bootstrap-skill-split-design.md)）。
- 2026-11-10 本輪，使用者指示「照你的建議做」：Q5 (a)、Q6 (a)、Q7 (b)、Q11 (a) 已決，決策書第 6 節已記。
- Q11 (a)：這台 Mac 的 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/` 換成六檔版（與部署包產出逐位元相同；舊單檔只備份在當時 session 的暫存目錄）。試用第 1 筆記在設計稿第 10 節。
- Q6 (a)：本 repo 新增 `.claude/hooks/repo-action-rules.sh`，只接 Claude Code 的 PreToolUse／PostToolUse；`verify_bootstrap.py` 新增「動作當下送規則」（26 個實跑情境＋6 個接線負向測試），「本 repo 兩份接線」改成 Claude Code 可多接這支、Codex 仍只准 SessionStart。
- Q7 (b)：`trail_sources` 加 `questions_from_book`（第 6 節已決 Q 的採用理由／未選／暫緩子項）與 `nongoals_from_plan`（效率計畫 3.2）；決策書與效率計畫補了理由與出處。`contradictions.py` 的登記表改成只認頂層項目。
- Q5 (a)：真 VM `guest_runner_sigkill`（runner 被殺 → 退場與寫入拒絕、帳本阻擋、崩潰解除不開終端就拒絕）；舊共享 scratch 路徑定位為已被取代的實驗，不作寫入證據。

## 未完成／下一步

1. **P0 未退出**（決策書已定先收尾 P0 再進 P1）。退出門檻要 Windows／Mac 都驗受控寫入、完整歸因與執行中前提切換；這台只有 Mac，見 Q12。仍未驗：host 整機崩潰、通用工具進無共享 guest（屬 P3 的 M3 隔離）、兩 VM 的 virtiofs `flock` 不協調。
2. 可信真人核准、簽署金鑰發行／撤銷（Q1 (b) 日後另登）與額度來源；`release.py`／`publish.py` 的金鑰仍是測試替身。真實工具前補跨機通知／恢復、外部效果冪等及輸入裁剪。
3. **六檔版 skill 試用中**：多開幾個本 repo 的 session，看 A5／C／B 回報有沒有照模式檔走，記進設計稿第 10 節；之後另登新編號決定上 `main` 與同步專案（別台機器的全域副本、各專案、`main` 都還是舊版）。規則逐條連到 `reasons.md` 錨點排在試用之後，免得中途改動試用中的版本。本 repo 必讀約 16,100 仍超標，見 Q10。
4. **動作當下送規則試行中**：三種提醒都在真 session 進了 context。誤報兩種：指令裡寫到「&& git push」或字面 `\n` 後接 git push 的測試資料；另有約五次 PostToolUse 提醒出現在沒有 push 的指令後，離線重放、換 locale 都不觸發，擷取到的 hook 輸入也都不含 push，原因未查明。去留看試用結果。
5. trail：AGENTS 規則、第 6 節已決 Q、效率計畫非目標都已轉；多數採用理由只能寫「當時沒有記錄理由」，Q2 (b) 一條標為推論。Swift runner 與 guest 腳本沒有離線測試，未轉 mutation 規格；`guest_runner_sigkill` 只在真 VM 跑，沒有 mutation 規格。F14／F15 需另一個工具或 OS；F41 使用者已決定先不用雲端。
6. 需要先有決定才能做：Q10、Q12、Q13。Windows hook 同步也要 Windows 環境。

## 地雷與注意事項

- handoff skill 的六個檔只在部署包 3.8 改（六個區塊依序對應標題上的檔名），六個 `source:` 標記與 `VERSION` 要同版本。改到逐字搬來的行，「skill 拆分」會擋：要嘛還原，要嘛在 `tools/skill_split_baseline.json` 的 `rewritten` 寫明去處。改完要重新覆蓋這台的兩個全域目錄。
- 各原型都是**偵測**或合成阻擋，沒有接進任何工具：`publish`／`bypass.guard_commit` 未掛到實際發布或提交入口。不要寫成保障。崩潰解除的終端確認只抬高 agent 代答門檻。
- `test_contradictions_repo` 與 `test_trail_repo` 讀本 repo 真文件，失敗會讓 verify 失敗。HANDOFF 的「下一步」與懸置裡**不要把已決的 Q 編號跟「待決」字樣寫在一起**（會報 `decided-still-pending`）；懸置每條要引用決策書第 6 節的 `Q` 編號（或 `- 無。`）。決策書第 7 節每條要有 `理由：`；第 6 節已決項底下的子項格式是「採用理由／未選／暫緩」，沒選又沒寫的字母選項會被 trail 報出。
- 提交指令要用 `&&` 綁住 verify 的結束碼，不要用 `;`。
- AGENTS.md 只有規則；新增或改規則時在 [AGENTS-reasons.md](AGENTS-reasons.md) 補段落與錨點，否則「規則理由連結」會擋。
- 讀 `tools/` 的測試不能放進 mutation 群組（`mutants.py` 只複製 `experiments/`），所以拆成 `*_repo.py`。改到既有守門那一行時 `mutants.json` 對應原文會變 stale，要一起改。只驗「有拒絕」不驗代碼的測試殺不掉 mutant，新守門請用 `denied(code, ...)` 寫法。
- 帳本列未 `retired` 時重啟一律阻擋，不要人工改列；要解除走 `python3 -X utf8 -m experiments.v2.crash_release DB RUN_ID`，必須人在 host 本機終端。
- 僅合成暫存 fixture；原檔、票據、金鑰與合成 Git object 不進本 repo。

## 服務查證與期望快照

- 2026-11-10 20:20 `python3 -X utf8 tools/verify_bootstrap.py --staged` exit 0，63 項全部通過（含 v2 的 414 個契約／索引測試；F22 與三個預期反例照報不通過）。本 repo 無 `verify_state.py`／`check_docs.py`，依 AGENTS 使用替代入口。
- 2026-11-10 `python3 -X utf8 experiments/v2/mutants.py` 全量 694 個全部 killed（含本輪新增 trail 13、contradictions 1）。
- `python3 -X utf8 experiments/v2/contradictions.py` 對本 repo：未發現（只比對宣告表）。
- 2026-11-10 `python3 -X utf8 experiments/v2/vm_probe.py` exit 0（約 34 秒，含崩潰解除、崩潰後重送、未讀請求與 runner 被殺）。本 repo 的 Claude Code 接線已改（Q6 (a)）；Codex 接線未改，Codex 信任重審不適用。無額外模型呼叫、候選安裝或真實部署。

## 懸置事項（AI 勿自行處理）

- 決策書第 6 節 Q10：本 repo 拆完 skill 仍超標（約 16,100）怎麼處理；使用者已同意等全域副本的六檔版試用幾輪後再定。
- 決策書第 6 節 Q12：P0 的 Windows 半邊怎麼往下（AI 建議 (a)：先在 Windows 開 session 盤點能力，不改門檻）。
- 決策書第 6 節 Q13：要額外模型呼叫的三件事要不要授權（AI 建議 (c)：本週額度已用 73%，先不做）。
