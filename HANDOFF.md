# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-15 14:32（+08）
- **交棒者**：Claude Code 桌面 App／Mac（Claude 端交接棒驗證全部做完，交回 Codex 做優化）

## 任務目標

使用者決定：**Claude Code 這邊不用再測**，接下來在 Codex 那邊做優化。方針不變：落實既有流程／規則，不靠加長規則。本輪 Claude 的結果是 Codex 優化的參考依據，完整數字在 [PHASE2-RESULTS.md](experiments/handoff-ab/PHASE2-RESULTS.md) 後半（三節 Claude 結果）。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支 `main`。
- **待續分支**：無；`feature/v3` 保留但不是待續分支。
- **工作中**：`Mac` ／ `Codex` ／ `㊣ 11.15.14｜交接流程優化｜工作中｜交棒0次`，2026-11-15 14:38 (+08) 開工
- **骨架版本**：`2026-11-14.4`
- 本輪沒有動 `src/kit/`、部署包、hook、skill。
- 本機 Mac，使用 `python3`。Claude CLI 是桌面 App 內建的 2.1.325，不在 PATH，用 `CLAUDE_CODE_EXECPATH`／`CLAUDE_BIN` 指定。

## 已完成

本輪全部在 `experiments/handoff-ab/`。

- **Claude 受測介面**：`comparable.py` 以 `HANDOFF_AB_TOOL=claude` 切到 `claude_pair.py`；不設就是原本的 Codex 路徑。另有 `relay.py`（同 session 先接棒再交棒）與 `HANDOFF_AB_VARIANT=occupant`／`slow` 兩個探針。用法在 [OPTIMIZATION-PLAN.md](experiments/handoff-ab/OPTIMIZATION-PLAN.md) 末兩節。
- **修掉三個量測／評分問題**（Codex 路徑也受益）：`usage.py` 把載入 skill 時插入的 `isMeta` 訊息當成下一輪；純接棒的「沒有多做開發」因尾端換行永遠不過（Codex 那 12 格沒跑過所以沒發現）；登入憑證依設定目錄路徑字串存放。
- **交棒提示改了一句**（Codex 共用）：明講 origin 上的「工作中」標記是受測 session 自己的。不講的話新開的受測 session 會把標記當成別人占用而停下。
- **Claude 實測共 66 次模型呼叫，全部有效、損害 0**（`claude-opus-5-5`、`--effort medium`）：
  - 純接棒／純交棒 A/B 各 6 格共 24 格全 PASS。A 只給任務，B 加執行提示。
  - 現行版本異常情境 10 格全 PASS（busy、ahead、race 正確停下）。
  - 150 秒驗證 4 格：都一次把 timeout 設成 600 秒等到結果，沒有輪詢或重試。
  - 同 session 先接棒再交棒 4 格、8 回合全過。
  - 占用者核對探針 6 格、舊提示煙霧 4 格（其中 2 格交棒不併入比較）。

## 給 Codex 優化的結論

1. **執行提示的效果小**：接棒 B 中位數 24.6 秒對 A 27.5 秒（6 對裡快 5 對，範圍重疊）；交棒 37.8 對 38.5 秒，看不出差異。正確性都不受影響。
2. **提示實際改變的行為**：B 不用 Skill 工具、直接讀參考檔（交棒非快取 input 少約 3,000–4,700）；交棒少跑一次未 stage 的文件檢查；同 session 交棒時沿用接棒的服務驗證、不重跑。
3. **時間幾乎都是模型回應**：接棒一格 25 秒裡工具執行只占 0.8 秒。要省時間得減少模型回應次數，不是加快命令。
4. **同 session 交棒比新 session 便宜**：非快取 input 約 11,000 對 23,000–27,000。

## 未完成／下一步

1. Codex 的純任務 12 格從沒正式跑過（含新交棒提示）：`comparable.py prepare` 後 `run <CELL> --approved`，先四格煙霧。每格前查訂閱用量。
2. 兩個制度問題，**本輪沒有改；改不改、怎麼改由使用者決定，AI 不自行處理**：
   - 交棒前沒有要求核對占用者。新 session 被要求交棒、標記對不上自己時，6 格裡 3 格直接清掉；停下的 3 格都讀了 `mode-a-stop.md`，清掉的都沒讀，`mode-b.md` 沒有這一步。每組 3 格，是觀察不是因果。
   - 開工標記第三欄：`AGENTS.md` 寫三欄，`mode-a.md` 寫「第三欄可省」；省掉後占用判讀只剩開工時間可對。
3. 要改制度就改 `src/kit/`、重生部署包、同步副本，依 AGENTS 鐵律並保留理由。

## 地雷與注意事項

- 帳號有開超額：五小時窗用滿會直接轉成超額計費，串流不報錯。`run.py` 的門檻預設 85%，`HANDOFF_AB_LIMIT` 可調；本輪經使用者同意用到 95%，結束時五小時窗 82%、七天窗 90%，沒有用到超額。
- macOS 的假家目錄存不了 Claude 登入憑證，Claude 實跑用 `HANDOFF_AB_HOME=real` 加 `HANDOFF_AB_CONFIG`。Codex 路徑不受影響。
- 受測工作區、原始串流、session 紀錄都在 repo 外的系統暫存目錄，重開機會清掉；報告只放聚合結果，不需要保留。
- Claude 與 Codex 的數字不互相比較；跨工具 medium 不同義。
- 其他已部署專案同步仍需另行授權。Windows 舊 session 殘留先核對，不推來源不明的未推 commit。
- 原始聊天、憑證、本機絕對路徑留 repo 外。

## 服務查證與期望快照

- 本輪最後一次程式改動後：離線測試 16 項通過（`test_claude_pair` 7、`test_comparable` 2、`test_usage` 2、`test_relay` 2、`test_version_cache` 3），`codex_selfcheck.py` 通過，`selfcheck.py` 兩輪通過。
- 每次提交前 `python3 -X utf8 tools/verify_bootstrap.py --staged --quiet` 66 項 exit 0；本次交棒只覆寫本檔，同樣跑過。
- 本 repo 無 `verify_state.py`／`check_docs.py`，使用 AGENTS 指定入口。本輪未改 hook 接線，重新審核不適用。
- **未驗**：Codex 純任務 12 格與各探針的 Codex 對應、真 repo 前後效率、Windows、超過 600 秒的驗證。F50 桌面完整互動未驗，使用者先前決定不另建測試聊天。

## 懸置事項（AI 勿自行處理）

- 無。
