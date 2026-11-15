# 交接棒執行與量測改進計劃

2026-11-15。使用者同意以「保證既有流程／規則正確執行，而不是繼續加長規則」為方針，並授權 Sol sub-agent 執行第一、二階段。第一階段離線改動見下；第二階段首批實測見 [PHASE2-RESULTS.md](PHASE2-RESULTS.md)。

## 開始位置與範圍

接棒依 AGENTS.md 與 HANDOFF.md 執行，接著讀本文。現行需求權威是根目錄的需求決策書 v3。碰到制度修改才讀相關理由與來源範本，避免為了解全貌展開歷史文件。先完成以下第一階段，再進入需要模型實測的第二階段。

第一階段在本聊天由 Sol sub-agent 實作。額外模型探針依 AGENTS.md 仍需取得授權、只用訂閱額度；其他已部署專案同步仍須另行授權。

## 已知證據與限制

- 詳細數字見 [CODEX-RESULTS.md](CODEX-RESULTS.md)。.3 完整接棒 147.103 秒、349,246 input、45,246 非快取 input；.4 完整回合 194.283 秒、444,536 input、46,200 非快取 input。
- .4 開工推送後的量測截點為 119.285 秒，後續記錄、驗證、推送與回覆增加 74.998 秒。兩次觀測的任務內容不同，無法由全程數字單獨推算優化效果。
- 單次驗證器串行／重疊對照為 52.72／34.28 秒，均 66 項通過。
- 本輪已看到執行落差：正常 Git 狀態仍讀整份異常參考；外層等待設成 1 秒，後續兩次 wait；量測中反覆讀 rollout，暫計提交增加一次完整驗證。
- 開場版本提示使用舊快取 2026-11-14，當時 origin/main 的 VERSION 已是 2026-11-14.4。需查清快取更新原因後再決定修法。

## 第一階段：離線驗證與最小改動

| 項目 | 已存在／執行落差／工具缺口 | 本輪處理 |
|---|---|---|
| 情境與評分 | `build.py`／`fixture.py` 建隔離 Git 情境；`score.py` 依 Git 結果評分。正常接棒仍曾展開異常參考、重複讀紀錄。 | 沿用既有情境與評分，不加守門；第二階段從完成後一次解析。 |
| 驗證與等待 | `verify_bootstrap.py --quiet` 和 handoff skill 已寫驗證沿用與 Codex 外層 60000 ms 等待。落差是受測回合用了 1 秒外層等待、提交前多驗一次。 | 沒有再加程序；按失效條件重用證據，等待由執行者依當前工具 schema 設定。Claude Code 的等待行為待模型實測。 |
| 用量 | `CODEX-RESULTS.md` 有手工觀測；沒有依指定 turn 解析兩種紀錄的工具。 | 新增只讀 `usage.py`。Codex 依 turn ID；Claude Code 依 user UUID，去重同 message ID 的串流。缺欄位或未完成回合輸出 `null`。原始紀錄與絕對路徑不入 repo。 |
| 版本快取 | 3.10 的 720 分鐘快取曾讓本 repo 在 fetch 到 .4 後仍提示舊版。 | 權威 repo 的 HTTPS／SSH origin 在成功 fetch 後直接讀 `origin/main:VERSION` 並更新快取；其他專案仍維持 12 小時 TTL。無效版本或 fetch 失敗不猜值。 |

離線核對：`usage.py` 對已記錄的 .4 Codex turn 重現 12 次模型回應、444,536 input、398,336 cached、46,200 noncached、3,368 output、194.283 秒；Claude Code 既有完整 turn 可解析出分列的 cache creation／read。共用欄位中 Claude cached 只計 cache read，noncached 計原始 input 加 cache creation；raw_usage 保留兩種快取原欄位，這些數字不換算訂閱額度。合成 fixture 覆蓋跨 turn、重複串流、未完成、缺欄位與 Codex 缺 response ID；hook fixture 覆蓋舊快取遇新版、有效快取、過期、無效回應、離線與 fetch 失敗。`usage.py` 用法：`python3 experiments/handoff-ab/usage.py codex <本機 rollout> <turn_id>` 或 `... claude <本機 session> <user_uuid>`；只回傳聚合 JSON。

1. 先盤點現有 handoff-ab 工具與測試，找可重用的紀錄解析及評分邏輯。交付簡短的「已存在／執行落差／工具缺口」對照，放在本文件更新即可。最小讀取、有效驗證沿用與 Codex 等待已寫入制度，優先處理落實方式。
2. 建立或延伸只讀用量解析工具，依明確指定的聊天／回合讀本機紀錄。Codex 以同 turn 的 token_usage_record 計數、最後 turn_token_usage 取累計、task_started/task_complete 算耗時。Claude Code 先查實際格式，處理串流、重複紀錄與快取欄位。缺欄位或未完成回合明記未知，不填零或猜值。
3. 用既有紀錄及去識別化合成 fixture 核對解析結果。輸出共用欄位、工具原始欄位與限制。正式量測等回合完成後一次擷取，省去受測回合中的暫計落檔。原始聊天與本機路徑不提交公開 repo。
4. 查版本快取的讀寫與同步路徑，針對已確認原因做最小修正，驗更新後、有效快取、過期、離線與無效回應情境。保持現有 hook 只報事實的契約。
5. 對照實際動作整理最小讀取、查核與等待的實現方式。獨立讀取可合併，相依修改及推送依序執行。Codex 沿用外層 60000 ms、內層最多兩段 30000 ms 的既有方式；Claude Code 依當前工具能力驗證等待行為。推送前遠端新鮮度與占用檢查仍需成立。
6. 依現有失效條件重用驗證結果，證據附對應版本與範圍。若需改參考文件，刪重複、改善定位並保留理由。先核對 v3 需求，避免把封存原型或額外守門帶回現行程序。

每項改動附能抓到具體回歸的測試；新增守門附負向測試。制度來源改 src/kit，再 build_kit.py 重生部署包，同步副本與版本依 AGENTS.md。本 repo 手貼 hook、共用制度與全域 skill 的同步範圍先讀對應理由。提交逐檔 stage，執行 python3 -X utf8 tools/verify_bootstrap.py --staged --quiet；必要的針對性測試另跑。第一階段交付可審查的改動、離線測試結果與第二階段的確切模型呼叫清單。

## 第二階段：取得授權後的模型實測

**原定候選清單與本批調整**：原擬正常接棒、正常交棒各做前版／本版、兩種工具、每格 3 次，共 24 個模型 session，另有六個異常候選。實際盤點後，本輪 hook 差異只在權威 repo 的版本提示，而既有 handoff-ab fixture 用本機 bare origin 且關閉版本查核；`usage.py` 是回合後解析，也不改模型輸入。直接跑 24 格不能量到本輪改善。因此首批改成 Codex 本版正常接棒、正常交棒各一次，加權威版本提示前後各一次。原有 `midway` 是半成品交棒，另建正常交棒 fixture。本輪未找到 Claude Code CLI；Codex 訂閱五小時窗於首批後已到 84%，停止擴樣。結果與限制見 [PHASE2-RESULTS.md](PHASE2-RESULTS.md)。後續若需量化變化，應先明確界定會改變受測模型輸入或工作流的版本，再安排重複樣本；不能用這批單次數據推算效率改善。

以下是原候選設計，僅供將來在可比版本與 fixture 上規劃對照，不是本輪未完成的必要 24 格：

- Claude Code 與 Codex 各自固定模型、推理設定、機器、起始 repo 及任務。使用獨立可拋棄 fixture，避免正式 repo 的占用影響比較。
- 若要比較每工具、每版本的正常接棒與正常交棒，可各做三次，前後版本與兩工具合計 24 個情境執行；是否共用聊天與實際呼叫數在執行前清單說明。採交錯順序，記首輪／後續輪與快取差異。既有歷史數據僅供背景。
- 接棒完成點包括開工標記推送及遠端核對、最終回覆完成。交棒完成點包括成果推送、占用釋回、本機乾淨且與遠端一致、最終回覆完成。
- 記全程秒數、模型回應數、input、cached input、非快取 input、output；另記驗證次數與耗時、Git 操作、僅回傳仍在執行的等待回合、異常查核及重試。不同供應商快取欄位保留原義，避免強行換算。
- 量測與記錄在受測回合完成後統一處理，另註開銷。訂閱額度只在有可比的實際讀值時報告。
- 沿用 handoff-ab 評分與受改動影響的異常案例，例如 busy、race、ahead、branch、drift、secret；額外執行數列入授權清單。必要行為全部通過、損害格 0 才接受改動。
- 時間與 token 各報中位數及範圍，檢查對應重複動作是否消除。樣本不足或改善落在波動範圍時明記未定；增加模型樣本需在授權額度內。

## 下一棒回報

## 可比較的純任務設計（2026-11-15，離線準備完成，模型尚未執行）

`comparable.py` 延用現行 `build.py`、`phase2_handoff_probe.py`、`score.py`、`codex_run.py` 與 `usage.py`。這是**同一版本的執行提示對照**，不能稱為制度版本或 hook 版本優化。A 是同一任務只按現有規則完成；B 另明示最小讀取、有效驗證沿用、等待及回合外量測。B 多出的提示字數進入實際 input 成本。若兩組實際讀取／驗證／等待行為相同，不能把時間差歸給提示。

兩個任務分開：純接棒從無人占用、乾淨且同步的 repo 起步，執行 A4 等必要驗證、推自己的開工標記、從遠端確認、回覆後停住；HANDOFF 的下一項等後續指令，不開發。只讀或只回答的 session 本來不 claim；本 fixture 明確要求接棒並推開工標記，所以適用 A5。純交棒從 `celsius_to_kelvin` 已完成、已推送且本 session 占用的 repo 起步，只做 B3／B4／B6／B7／B8 等必要查核、快照、釋回與回覆，不再開發。兩組均不得省略必要驗證。

每情境 A/B 各 3 次，共 **12 個獨立 Codex turn／12 次預計模型呼叫**；沒有額外版本探針或 Claude Code 格。每個情境只建立一份 master Git 狀態，再複製成 6 格；同情境六格的起始 HEAD、tree、refs SHA-256 完全相同。模型固定 `gpt-6-sol`、`medium`，Codex CLI 走同一隔離設定，兩組使用同一份現行 full 骨架、hook、環境與任務終點。交錯順序記在 `paired-plan.json`：第 1 輪接棒 A/B、交棒 B/A；第 2 輪反向；第 3 輪同第 1 輪。各格獨立 bare origin 與 work，不共享執行後 Git 狀態。原始紀錄、工作樹及認證連結只在 repo 外的 `HANDOFF_AB_ROOT`。

離線準備：`HANDOFF_AB_ROOT=<repo 外新目錄> python3 -X utf8 experiments/handoff-ab/comparable.py prepare`；`plan` 列狀態；正式執行才用 `run <CELL> --approved`，完成後可用 `assess <CELL>` 重算。每格啟動前比對 origin snapshot、work HEAD、remote tracking ref、工作樹乾淨與占用值；任何差異拒跑。先各情境各組 1 格作煙霧測試；任一 INVALID、FAIL、損害、fixture 污染、CLI 非零退出或 timeout 即停，查明後才決定是否繼續。所有 12 格完成或既有訂閱用量守門觸發時停止；不自動補跑無效格，也不增加任意授權門檻。本輪只做設計與離線測試，正式 12 次**尚未啟動**。

每格保留 CLI 外層完整 wall 秒數、CLI exit、完成後 `usage.py` 依唯一 turn 算的模型秒數、回應數與 input／cached／noncached／output 及原始欄位；無 rollout、未完成或缺欄位寫 `null`，不填零。CLI JSON 只能可靠計數可見的讀取、驗證、Git 命令；各項耗時、工具等待回合及重試若無可靠事件維持 `null`。回合結束後一次讀紀錄並評分，解析與寫報告的成本另外以離線計時記錄，不混進受測 wall 秒數；不在受測回合中做「途中量測暫計提交」。那個舊觀察是測量行為本身造成的開銷，不能作公平 A 組；如要估計，另用本地無模型的解析／記錄計時，沒有遞迴量測尾巴。

機器評分檢查開工標記先推、末態占用、沒有開發、交棒釋回、成果不變、main 綠、本機同步與禁止操作。遠端確認是否真正比對 own marker、必要驗證是否按順序且有效、實際讀取範圍／等待及是否有多做任務，需看每格原始命令與輸出人工判定。每格 `review.json` 由審查者填 `subject_verification`、`task_scope`、`remote_confirmation` 的布林值或 `null`；審查說明另記於 repo 外，交棒的遠端確認項由 runner 內部標不適用。缺人工核對時總判定是 `PENDING_REVIEW`，不能宣稱全程 PASS；任何人工項 false 是 FAIL。CLI exit 非 0／timeout 一律 INVALID。每格 `run-config.json` 記實際 CLI 版本、模型與推理參數、JSON 事件格式、提示與起點雜湊；rollout 的模型另由有效性檢查。報告先列每格正確性與實際動作，再以配對的全程秒數、token 中位數與範圍及快取比例描述；樣本不足、動作未分化或差異落在波動範圍，寫未定，不推算訂閱額度收益。

## Claude Code 介面（2026-11-15，離線驗證完成，模型尚未執行）

`comparable.py` 以 `HANDOFF_AB_TOOL=claude` 切到 `claude_pair.py`；不設就是原本的 Codex 路徑，行為不變。兩個工具各用自己的 `HANDOFF_AB_ROOT`，`paired-plan.json` 記工具名，拿錯工作區會在啟動模型前拒跑。設計、提示、交錯順序、起點雜湊與污染檢查同上一節，結果只在 Claude 內部比較。

- **環境**：這台機器的 CLI 是桌面 App 內建的 Claude Code 2.1.325，不在 PATH，由 `CLAUDE_CODE_EXECPATH` 或 `CLAUDE_BIN` 指定。受測用隔離設定目錄需使用者自己登入一次（不搬憑證）；`run.py preflight` 會印出登入指令並檢查訂閱登入。
- **固定設定**：模型 `claude-opus-5-5`（沿用前兩輪 Claude 受測）、`--effort medium`；跟 Codex 的 medium 不同義。工具清單與權限模式同 `run.py`，拿掉 `--no-session-persistence` 並指定 `--session-id`，回合後才有唯一的 session 紀錄。
- **交棒起點**：占用標記的工具名改成 `Claude Code`。沿用 Codex fixture 的話，受測者會把它當成別人的占用而依規則停下。
- **有效性**：沿用 `score.validity` 的串流檢查（模型、handoff skill、第一則回覆前的 `[facts]`、沒碰測試 repo 外的制度檔、正常結束），再加 init 剛好一個且 session id 相符、result 剛好一個 success、唯一 session 紀錄、紀錄裡剛好一則人類訊息。任一不成立即 INVALID。
- **用量**：`usage.py claude` 依唯一 user UUID 解析。本輪修了一個邊界：載入 skill 時 harness 會插一則 `isMeta` 文字訊息，舊判定把它當成下一輪，整個回合會回報未完成（全部未知）；真實紀錄已確認有這種列。現在略過 `isMeta`。CLI 在 result 事件自報的 `duration_ms`／`num_turns` 另存 `cli_reported` 當對照。
- **用量守門**：每格前後讀串流最後一筆 `rate_limit_event`；超額、被限流或五小時窗到 85% 就不跑下一格，`score.json` 的 `limit` 會有字。
- **可觀測動作**：Read／Grep／Glob 與 Bash 讀取、驗證命令、git 命令、Skill 呼叫與工具呼叫總數，同一個 tool_use id 只算一次；耗時、等待回合與重試沒有可靠事件，維持 `null`。

離線測試 `test_claude_pair.py` 5 項：合成串流與 session 紀錄的有效格、重複串流去重、`isMeta` 不切斷回合、模型不符／缺 `[facts]`／session id 不符／錯誤結束／缺 result／碰 repo 外制度檔各自 INVALID、多一則人類訊息／未完成／缺紀錄／紀錄不唯一時用量為未知、指令保留 session 紀錄、Claude fixture 的占用標記與拿錯工作區拒跑。拿掉 `isMeta` 修正時測試會失敗（已實際試過）。串流與 session 紀錄的實際欄位只對過既有真實 session 紀錄與前兩輪的解析碼，2.1.325 的 `-p` 串流要等第一格煙霧才算驗過。

執行：`HANDOFF_AB_TOOL=claude HANDOFF_AB_ROOT=<repo 外新目錄> python3 -X utf8 experiments/handoff-ab/comparable.py prepare`，登入後 `run <CELL> --approved`。先跑 `takeover-A-1`、`takeover-B-1`、`handoff-B-1`、`handoff-A-1` 四格煙霧，有效才續跑其餘八格。

回報已完成項目、實際改動、驗證結果與仍未驗證事項。第一階段完成即可提供具體第二階段測試清單供使用者授權。使用者要求交棒時再覆寫 HANDOFF 並釋回占用。
