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

## Claude Code 純任務煙霧四格：2026-11-15

使用者要求 Claude Code 接棒驗證並自行登入受測設定目錄。Claude Code 2.1.325（桌面 App 內建），`claude-opus-5-5`、`--effort medium`，訂閱登入（Pro），macOS。設計與提示見 [OPTIMIZATION-PLAN.md](OPTIMIZATION-PLAN.md) 的純任務設計與 Claude Code 介面兩節。每格一個獨立 `claude -p` session，共 4 次模型呼叫，其餘 8 格未跑。

隔離方式與計劃不同的一點：假家目錄下 macOS 存不了登入憑證，改用真家目錄模式（`HANDOFF_AB_HOME=real`）加隔離設定目錄；skill、設定與 git 設定仍是隔離的，碰到真家目錄制度檔會判 INVALID，四格都沒有碰。登入憑證依設定目錄的路徑字串存放，`HANDOFF_AB_CONFIG` 改成不解析符號連結。

| 格 | 判定 | wall 秒 | 回合秒 | 模型回應 | input／cached／noncached／output | 工具呼叫 |
|---|---|---:|---:|---:|---:|---:|
| takeover-A-1 | PASS | 27.525 | 25.199 | 7 | 202,347／182,015／20,332／1,688 | 8 |
| takeover-B-1 | PASS | 21.807 | 20.925 | 5 | 142,186／121,625／20,561／1,610 | 5 |
| handoff-B-1 | PASS | 36.588 | 35.770 | 9 | 278,517／254,908／23,609／2,830 | 9 |
| handoff-A-1 | FAIL（fixture 造成，見下） | 26.573 | 25.935 | 5 | 166,159／137,732／28,427／1,912 | 5 |

四格 exit 0、有效性檢查全過、損害 0。cached 只計 cache read；noncached 幾乎全是 cache creation（每格 20,316–28,417）。`usage.py` 的回合秒數與 CLI 自報的 `duration_ms` 每格相差不到 0.04 秒。回合後解析加評分每格 0.08–0.17 秒，不在受測秒數內。三個 PASS 格的人工審查項（必要驗證、任務範圍、接棒的遠端確認）由本 session 看每格的命令與輸出後填 true。

**handoff-A-1 沒有交棒，原因是 fixture，不是模型做錯。** 交棒起點的占用標記寫的是 08 時開工的 session；受測者是 09 時才開的新 session，照規則核對「同機器、同工具，但 session 名與開工時間對不上」，當成別人占用而停下，沒有改檔也沒有推送，回覆列出三個選項。B 組那一格沒有做這個核對，直接完成交棒。所以這個情境現在量到的是「有沒有核對占用者」，不是交棒效率；A/B 的差異不能歸給 B 的執行提示。Codex 的同一個起點只跑過一次（當時通過），同樣的問題在 Codex 上有沒有還不知道。純交棒要先改起點或提示（讓占用者確實是受測 session，或在提示明講標記是誰的），才有可比的格子。

**接棒兩格**都跑了 `verify_state.py` 與測試、只推開工標記、從 origin 重讀確認。A 用 Skill 工具載入 handoff 再讀 `mode-a.md`；B 直接用 Bash 讀 `SKILL.md` 與 `mode-a.md`，少兩次模型回應。A 的開工標記沒帶 session 名，B 有帶。每組一格，時間與 token 的差異不能作結論。

**量測介面**：這是 Claude adapter 第一次對到真實 `-p` 串流與 session 紀錄，init、hook 輸出、工具呼叫、result、唯一 user UUID 都解析成功。第一格的機器評分一度是 FAIL，原因是 `comparable.py` 比對原始碼時一邊去掉了尾端換行；已改成比 git blob 並補正反測試，重新評分後 PASS。這個錯在 Codex 路徑上也存在，只是那 12 格從沒跑過。

**用量**：四格期間五小時窗 43% → 50%，七天窗 75% → 76%，七天窗已出現接近上限的預告（`allowed_warning`）；沒有用到超額。這是共用帳號讀值，不能精確歸給單格。守門門檻 85%。
