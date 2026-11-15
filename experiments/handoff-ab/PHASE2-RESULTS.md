# 第二階段模型實測：2026-11-15

## 測試範圍與版本

使用者授權 Sol sub-agent 執行第二階段，使用訂閱額度。前版 `d6d6218`、本版 `eae27b0`；兩版差異是離線用量解析 `usage.py` 與權威 repo 開場 hook 的版本快取處理。`gpt-6-sol`、`medium`、Codex CLI 0.169.0-alpha.11.1，macOS，ChatGPT Plus 登入；所有受測工作樹與 bare origin 留在 repo 外。Codex 5 小時窗由開始時 53% 到結束時 84%，七天窗 43% 到 47%；這是共用帳號讀值，不能把變化精確歸給單格。沒有使用 API key、額外點數或免費 reset。

本輪在 PATH、`~/.local`、`/opt/homebrew`、`/Applications` 未找到 Claude Code CLI，故未啟動 Claude 模型探針。這台機器無法驗證 Claude Code 的實際等待與本版用量。Codex 5 小時窗已達 84%，因此本批停在首批，不做擴樣；既有 runner 的 85% 是每格守門，並非新增普遍制度。

現有 handoff-ab 的 `build.py` 使用本機 bare origin，且 `run_env()` 設 `BOOTSTRAP_VERSION_CHECK=off`。所以原有 `clean`、`midway` 等情境的模型輸入不會因本輪 hook 改動而不同，`usage.py` 也只在模型回合後執行。不能把原有 fixture 的前後對照當成本輪效率改善。正常交棒另建已完工 fixture；`midway` 是半成品交棒，未拿來代替。

## 結果

| 測試 | 結果 | 完整 turn 秒數 | 模型回應 | input／cached／noncached／output |
|---|---|---:|---:|---:|
| 本版接棒並完成 `clean` fixture 任務 | PASS、損害 0、exit 0 | 82.181 | 16 | 445,951／423,808／22,143／3,011 |
| 前版權威版本提示 | 有效；答上游未知、無法判定落後 | 4.451 | 1 | 14,077／11,648／2,429／129 |
| 本版權威版本提示 | 有效；答上游 v2026-11-14.4、本地落後 | 3.590 | 1 | 14,109／11,648／2,461／33 |
| 本版正常交棒 | PASS、損害 0、exit 0 | 90.910 | 15 | 466,499／443,008／23,491／4,201 |

四個有效 session 各用獨立聊天。時間與 token 用 `usage.py` 在回合結束後依 turn ID 從本機 rollout 擷取；數字不等於訂閱額度。`clean` 的 82.181 秒包含接棒、完成 fixture 的程式任務、驗證與推送，不是純接棒時間，也不能和歷史 147 秒直接比較。此格沿用 `codex_run.py` 與 `score.py`：開工標記先推、程式成果推送、測試通過、標記保留、本機同步。正常交棒使用 `phase2_handoff_probe.py` 搭建完成 `celsius_to_kelvin` 並已推送的專案，初始占用是本機 `lab-mac ／ Codex CLI`；模型覆寫 HANDOFF、推交棒 commit、釋回標記，測試綠、本機與 origin 一致。此格 9 項機器檢查全過。

權威版本情境使用 `phase2_version_probe.py`：兩版工作樹的 AGENTS 標記都是 `2026-11-14`，`.claude/.bootstrap-version` 是仍有效的舊快取，origin 的 `VERSION` 已為 `2026-11-14.4`，本機尚落後 origin 一個 commit。只有 `git remote get-url origin` 回傳合成的權威 GitHub URL；其餘 `git fetch`、`git show` 走本機 bare origin，沒有連真 GitHub 或推真 repo。hook 舊版不印上游版本，本版印出落後提示；兩個回合的模型輸入均含 SessionStart hook 的 `[facts]`，rollout 均標 `gpt-6-sol`。模型僅根據該事實作答，沒有執行命令或改動已追蹤檔。這證實新版提示可到達模型且被正確理解；單次回答時間／token 差異無法作效率推論。

一個舊版探針首次建 fixture 時漏放 `.claude/settings.json`，模型沒有收到 `[facts]`，依預定有效性條件列 INVALID，耗時 4.838 秒、1 回應、13,968 input／11,648 cached／2,320 noncached／139 output。另一次執行因 `--trust` 與 `--ignore-user-config` 衝突，在啟動模型前 exit 1；修正隔離設定後前後版本各完成一次有效探針。有效格無模型失敗或重試。初次 INVALID 的成本已列入，沒有併入有效格統計。

## 重現與限制

只讀 fixture、hook 與評分方法在 `phase2_version_probe.py`、`phase2_handoff_probe.py`；原始事件、rollout、工作樹只留本機 `/tmp`，不進公開 repo。重現前先檢查 Codex ChatGPT 登入及訂閱用量，使用新的 repo 外目錄。版本探針依次 `prepare OLD ROOT`、`prepare NEW ROOT`、`run OLD ROOT --approved`、`run NEW ROOT --approved`，最後用 `assess OLD ROOT`、`assess NEW ROOT` 得到聚合評分；正常交棒以 `HANDOFF_AB_ROOT=ROOT` 執行 `phase2_handoff_probe.py prepare` 與 `run --approved`。正常接棒沿用 `codex_run.py one clean 1 --approved`。每次都需獨立 fixture 與可用額度；不能直接重跑已有事件的格子。

本批有效樣本數每情境 1，沒有計算中位數／範圍，也沒有前後正常接棒或正常交棒的可比差異。第二階段的效率改善尚未證實；已證實的是本版正常流程正確，以及權威版本提示能修正舊快取造成的資訊缺口。異常 busy、race、ahead、branch、drift、secret 未再跑：本輪改動不改它們的受測模型輸入，前期既有評分仍供背景，不宣稱本輪已驗。
