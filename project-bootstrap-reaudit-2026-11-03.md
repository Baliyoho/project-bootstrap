# project-bootstrap 第二輪第三方視角審查

日期：2026-11-03（Asia/Taipei）

基準：`main @ 4e92c25b2008cab785637103f5255ef89c000042`，VERSION `2026-11-02.8`。
性質：獨立反例與程式／程序審閱；不是外部認證。原查核報告與進度報告均視為待核對的主張。

本輪結論是：**修正有實質成效，但「已知問題都已完整修正」仍需縮小範圍。既有 50 項驗證全過，獨立反例仍找到 9 項可修正問題，其中同步資料保全、同步與占用程序的銜接、輸出遮罩應優先處理。** 沒有 P0 證據；這不等於保證不存在其他問題。

## 範圍與證據

涵蓋權威部署包的制度及生成程式、入口與結構文件、兩份既有報告、交接快照、同步工具、驗證器、兩個本 repo hook／啟動器、接線、Git 設定與生成骨架。以現行 22 檔骨架為基準，檢查部署→接棒→修改→驗證→同步→交棒鏈條。

- 同一聊天接棒階段已在上述相同 commit 實跑 `python -X utf8 tools/verify_bootstrap.py`：exit 0、50 項全過、無 skip。這次審查開始再 fetch，ahead／behind 均 0，工作樹乾淨；期間未修改受測 repo，因此沿用此基準，沒有把舊報告的執行結果冒充本次結果。
- 另執行 `review_probe.py`：生成範本，以真實函式、檢查器 CLI、同步 CLI、本機 bare remote 與 clone 驗證反例。測試程式 exit 0 表示探針成功執行，**不表示受測系統通過**；結果在 `review-results.json`。
- 原始探針與 JSON 保留在本次審查聊天產物，未納入 repo；換機器不能假設它們存在。取得原始探針後的執行方式：`python -X utf8 review_probe.py <權威repo路徑>`。每次另建隔離 fixture，保留供核對。用 `PYTHONDONTWRITEBYTECODE`／`sys.dont_write_bytecode` 避免 import 在受測 repo 寫入 bytecode。
- 沒有修改制度、正式測試、兩份舊報告或 HANDOFF；沒有 commit、向 GitHub push、同步真專案、呼叫額外模型或變更 hook 信任。
- 本輪沒有重新驗收六個既有專案、其他 OS、Python 3.8 或模型實際遵循；交接快照中的六專案結果是歷史記錄，不列為本輪獨立重現。原子 claim 與 Antigravity IDE 追查維持既定範圍，不自行重開。

嚴重度：P1＝可能丟失自訂保護、違反 writer 協調或洩出敏感輸出；P2＝可靠性／流程缺口；P3＝較低影響的誤報。以下行號均對上述基準。

## R01｜P1｜handler 所有權仍靠子字串，自訂命令仍會被靜默刪除

位置：`tools/sync_project.py:152–162`、`:187–205`。對應舊 F02，屬修正未涵蓋的輸入。

同組保留合法骨架 handler，再加專案 handler：

```json
{"type":"command","command":"python audit_hook.py --watch git-freshness.sh"}
```

`merge_wiring()` 回傳 error=null，自訂 handler 消失；說明卻是「換成權威版接線，專案其他設定原樣保留」。此命令只是把腳本檔名當監測參數，並沒有執行骨架 hook。

原因：`if s in cmd` 把「提到腳本名」當作「此 handler 歸骨架所有」，後續 `foreign` 排除它。舊版整組刪除已修，但所有權辨識仍可造成同樣結果。

建議：只自動替換能確認為既有骨架接線的 handler。用已知版本命令結構／指紋辨識；含額外邏輯、包裝或無法確認的命令保留並報 conflict，不以廣泛 shell 解析猜測。驗收需涵蓋參數、echo、同名專案腳本與複合命令，檢查實際保存內容而非只有 exit code。

證據：`handler_substring.custom_preserved=false`。

## R02｜P1｜未設 matcher 的同組自訂 handler 被悄悄限縮觸發範圍

位置：`tools/sync_project.py:191–203`。對應舊 F02 的 matcher 保全。

輸入：PreToolUse group 有正常骨架 handler 與 `echo all-tools-audit`，但沒有 matcher。合併後 error=null，整組被補成 `matcher: "Bash|PowerShell"`。

原本未設 matcher 代表每次該事件都觸發；同步後專案的 Edit／Write／MCP 等檢查不再觸發。這是合法設定的語意改變，不是壞 JSON。該預設語意有 [Claude 官方 hooks 文件](https://code.claude.com/docs/en/hooks#how-a-hook-resolves) 支持；本輪實測的是合併輸出，沒有呼叫模型量測 runtime。

原因：`clash` 只檢查 `k in meta_now`；缺鍵帶有預設語意，卻被當成無衝突。

建議：比較正規化後的實際 matcher 語意，包含缺省值；若同組有自訂 handler，拒絕改觸發條件或安全拆成不同 group。驗收包括缺 matcher、空字串、萬用 matcher、明確 matcher 與其他組層欄位。

證據：`matcher_absent.result.matcher="Bash|PowerShell"`。

## R03｜P1｜同步 preflight 與 A 模式占用規則沒有接合

位置：`tools/sync_project.py:598–611`；部署包 skill A1、A2.5、A5。

獨立 fixture 已 fetch 遠端，`origin/main:HANDOFF.md` 明確為 other-machine 工作中，本機 HANDOFF 仍為空閒，工作樹乾淨、分支計數為 ahead=1／behind=1。對此目標跑 `--codex-only --write`，同步器仍改了接線並 exit 0。

反方向也測了：本機寫入並 commit 本 session 的工作中標記後，同步器 exit 1、拒絕占用。這表示依 A5 先寫標記的正常 writer 也不能使用同步器，而沒完成 A1 的陳舊 checkout 反而可以。

原因：preflight 只看本機 HANDOFF 且只接受「無（已交棒）」；不驗 upstream 對齊、遠端標記與目前已授權 session 的關係。這不是要求實作原子鎖，也不是尚未做的並行實驗；是單一呼叫中已知資訊沒被採用，以及兩條現行規則無法同時遵守。

建議：明定跨專案同步的接棒流程與 owner 證據，讓同步器接受已核對的當前 writer，拒絕其他 writer、過期／分岔／未知 upstream。若要把 Git 同步責任留給呼叫者，也須有可驗證前提與一致程序，不應同時要求 A5 又只接受空閒。驗收至少涵蓋已授權自身占用、其他人占用、已 fetch 但未 pull、分岔、離線與無 upstream；不以 `--allow-dirty` 當占用豁免。

證據：`stale_busy_sync.exit=0`、`updated=true`、`counts="1\t1"`；`own_claim_sync.exit=1`。

## R04｜P1｜先截斷再遮罩，會洩出已知憑證的部分字元

位置：部署包 `PROJECT-BOOTSTRAP.md:2238–2247`、`:2290–2298`（生成 `verify_state.py`）。對應舊 F04 新增遮罩的邊界。

使用完全假的 `_SECRET='SYNTHETIC_SECRET_abcdefghijklmnop'`，子命令印出 290 個 x 後接完整假憑證。實得輸出尾端含 `SYNTHETIC_`，沒有 `***`。

原因：`out[:300]`／stderr `[:200]` 在 `say()` 的整字串替換之前執行。憑證被切斷後不再匹配 `_SECRET`，已知敏感字串仍有部分出現在結果中。此結果只證明部分洩出，沒有把它誇大成已取得完整真憑證。

建議：先對完整 stdout／stderr 做遮罩，再摘要、換行整理與截斷；例外與標籤輸出也一致處理。驗收涵蓋兩個長度邊界、完整值、跨行與不同輸出來源；只有已知的單一 `_SECRET` 能遮，不應宣稱通用祕密偵測。

證據：`redaction_truncation.partial_secret_leaked=true`。

## R05｜P2｜inventory 中 active 目標失效，被當正常排除且 exit 0

位置：`tools/sync_project.py:545–560`、`:657–660`、最終摘要。涉及舊 F03／F13。

inventory 放一個有效且已一致的 active 目標，另放不存在的 active 路徑。CLI 印 EXCLUDE「沒有 handoff skill」，最後卻印「全部都已經是 v2026-11-02.8」，exit 0。

使用者明列 active 的目標失效，與主動標 archived 的正常排除不同。路徑搬動、掛載失敗或技能檔遺失時，一部分維護目標被漏掉，呼叫端仍得到全成功。

建議：區分「刻意排除」與「要求同步但無法處理」。active 驗證失敗應列入 failures，非零退出，摘要限定實際處理成功的目標。`--all` 的一般非專案目錄不必因此報失敗。測一好一壞、一好一 archived、全失敗與重複路徑。

證據：`missing_active_inventory.exit=0` 及 stdout。

## R06｜P2｜人的入口仍教相反的規則優先序

位置：`README.md:60–61`，對照部署包 `:686`、`:894`；驗證器 `tools/verify_bootstrap.py:2975–3016`。對應舊 F10／F15。

README 現行敘述是「兩者衝突以協定為準」，不是歷史引用。新版 skill／協定則明確以同步 SKILL 核心優先。README 是人使用與複製程序的入口，這仍會把讀者帶回舊規則。

目前核心優先序測試只驗 skill 與協定，沒有驗 README，故 50 項全過可與此矛盾並存。

建議：README 改為指向單一權威，或與新版一致的短摘要；把人的入口納入語意／結構比對。驗收應故意在 README 放回反向優先序並確認失敗，而不是只測 skill／協定。

## R07｜P2｜B7 驗證先於 stage，新增文件會漏驗

位置：部署包 `:1302–1311`（B7）、`:1854–1867`（檔案列舉）；協定摘要 `:770`。

fixture 新增未追蹤 `new-note.md`，含 `[x](missing-target.md)`。依現行順序先跑 `check_docs.py`：exit 0。再 `git add new-note.md` 後跑同一指令：exit 2，抓到同一個死連結。

原因：檢查器只用 `git ls-files`，而 B7 明文先驗最終文件、再 stage。新增檔尚不在輸入集合，驗證結果不能證明本次待提交文件全數通過。這不是要求通用 Markdown 語意檢查，是現有檢查能力未作用在將提交的檔案上。

建議：先檢視並明確 stage 本次檔案，再驗最終提交集合；或讓驗證器明確接收本次候選集合。後續 stage 若改變文件集合必須重驗，部分 stage 還要釐清驗工作樹或 index 內容。不要為解此問題使用不加選擇的 `git add -A`。

證據：`untracked_doc.before_add_exit=0`、`after_add_exit=2`。

## R08｜P2｜工具欄為空仍通過欄位與快照驗證

位置：部署包 `:2006–2014`。對應舊 F01／F08。

標記為：

```text
- **工作中**：`machine` ／ `` ／ `session`
```

`check_busy_field()` 回 `(True, [])`，`check_snapshot()` 也沒有問題。判斷只驗欄位數與第二欄有沒有全形豎線，沒有驗第二欄是否空白。

影響：文件可被驗成合格但缺少規則明訂的工具身分；hook 對缺工具的分支另有提醒，所以此項不宣稱直接變成錯誤綠燈，仍屬應被擋下的資料完整性缺口。

建議：機器與工具兩欄均需 trim 後非空；把空字串、純空白、純反引號、缺欄位納入共用案例，同時驗 hook 與文件檢查器的預期。

證據：`empty_tool.busy=[true,[]]`、`snapshot=[]`。

## R09｜P3｜角括號路徑與 title 合用時，合法連結被報死連結

位置：部署包 `:1897–1907`。對應舊 F08。

檔案 `existing file.md` 真實存在，Markdown 為 `[x](<existing file.md> "title")`。檢查器卻回 `link.md -> <existing file.md>` 不存在。

原因：先判斷整段是否以 `>` 結尾，帶 title 時不符合；去掉 title 後沒有再去角括號。兩種修正各別通過，組合仍失效。

建議：先解析 destination／title，再處理角括號，或用合適 Markdown parser；保留真死連結的反向案例。這是有限 parser 的常見合法輸入誤報，不要求一次涵蓋所有 Markdown 方言。

證據：`angle_title_link`。

## 額外的靜態風險與維護觀察

以下不混入上述九項已確認問題的計數，也不聲稱做過未做的跨平台實驗。

1. **原子替換沒有保留檔案 mode**：`sync_project.py:373–377` 新建 `.sync-tmp` 後直接 replace，沒有從原檔複製 mode。POSIX 新檔通常不帶執行位元，若 `ag-wrap.sh` 內容需要更新，可能使原本可直接執行的 wrapper 失去 x bit。現有「部署生命週期」測的是首次部署／clone，沒有涵蓋既有可執行檔同步升級。建議 POSIX fixture 從 0755 升級後檢查 mode、直接執行並驗 Git diff；本輪 Windows 未量此結果。這與 Windows index mode 指令是不同路徑。
2. **既存 `verify_state.py` 是 INSTANCE**：F04 範本修正不會透過 `sync_project.py` 自動遷移到舊專案。這是已宣告的所有權選擇；應有逐專案人工遷移證據，不能只從「六專案同步完成」推定服務檢查器也升級。本輪不檢查私人專案，因此不把它寫成既有部署仍故障。
3. **摘要仍有細節漂移**：ARCHITECT 表格仍稱 CLAUDE／GEMINI 只有標題不同、交接 prompt A/B；生成的 ARCHITECT 仍稱兩指標只有「去讀 AGENTS.md」。部署範本實際已不同，且 README prompt 已改用收工／開工。屬可合併整理的低影響文件債。
4. **測試證據應分層**：部分文字契約測試只證明 token 未消失，不能證明規則互相相容；R03、R06、R07 正是跨元件矛盾。行為測試應增加輸入組合與流程順序，不以更多固定字串負向測試取代。
5. **沒有 package manifest／跨 OS CI 仍是界線**：VERSION 只代表 skill、新版 Python 以外的下限仍是靜態檢查；已被文件承認。本輪不以這些已知限制否定已完成的版本方向修正，也不要求重新啟動原子 claim。

## 舊 F01–F16 的複審判定

「可維持」只表示原修正的約定範圍有相應程式與基準驗證支持，不是沒有任何相鄰缺陷。

| 舊項 | 本輪判定 |
|---|---|
| F01 占用子字串 | 原始錯誤綠燈已有修正；空工具欄仍需 R08 補強 |
| F02 自訂 hook 保全 | **不可廣義結案**：R01、R02 仍可刪除或改變自訂保護 |
| F03 同步失敗訊號 | 壞 JSON／直接不存在目標已修；inventory 路徑仍有 R05 |
| F04 服務失敗 exit | 原始 FAIL／ERROR 訊號可維持；新遮罩有 R04；舊實例遷移另驗 |
| F05 子目錄接線 | 可維持；基準含原始命令與 Windows 啟動鏈，官方亦支持 cwd 原因 |
| F06 AI push 提醒 | 可維持明確縮限後範圍；不重新要求它成為原生發布閘門 |
| F07 ZIP SKIP | 可維持；控制流程已在打包之前拒絕 FAIL／未允許的 SKIP |
| F08 文件／快照 | 原缺檔與結構問題已有修正；R07、R08、R09 仍需處理 |
| F09 版本方向 | 可維持；不將 skill 版本等同整包完整性 |
| F10 核心優先序 | 核心兩份已統一，人的入口仍相反，見 R06 |
| F11 協作狀態 | 多數舊順序矛盾已修；同步占用銜接 R03、提交輸入集合 R07 未閉合 |
| F12 非互斥鎖 | 約定的邊界文件可維持；原子 claim 仍另案，未宣稱實作 |
| F13 同步範圍 | worktree／dirty／漂移已有守門；R03、R05 使「安全同步」仍需縮限 |
| F14 Python 下限 | 原 API 問題已修；3.8／其他 OS 未實跑，維持已揭露界線 |
| F15 敘述復活 | 原五處修正成立，但 R06 與其他摘要殘留證明仍有文件分岔 |
| F16 部署生命週期 | 首次發布順序與本機測試可維持；不是同步升級或跨 OS 實測 |

## 官方文件交叉核對

- [Codex Hooks](https://learn.chatgpt.com/docs/hooks)：支持專案層 hooks、commandWindows、session cwd 與 Git root 定位建議；也明列審核與信任。這支持現行接線方向，不代表本輪已重做 CLI／App 注入驗收。
- [Claude Hooks](https://code.claude.com/docs/en/hooks)：支持未設 matcher 觸發所有該事件的語意，直接支撐 R02 的影響。沒有藉這次文件核對宣稱所有 Claude 版本的行為均實測。
- [Antigravity Hooks](https://antigravity.google/docs/hooks)：目前有 injectSteps／ephemeralMessage 契約。歷史指定版本的啟動、cwd、shim 與 IDE 結果仍以歷史實測記錄為界；本輪沒有額外模型探針或重開 IDE 調查。

## 建議修正順序與驗收

第一批處理 R01–R04：先保住專案設定、可執行保護、writer 協調與敏感輸出。每個修正要讓本報告的獨立反例先失敗、修後通過，再跑既有驗證；同步器除函式層外需補實際 CLI 零寫入／正確拒絕測試。

第二批處理 R05–R08，修正 inventory 失敗彙總、單一規則入口、B7 最終輸入集合及工具欄檢查；R09 可併入文件檢查器修正。同步流程的測試至少要走一次「A1→A5→同步→B7→B8」，只在空閒 fixture 呼叫同步不夠。

跨平台 mode 風險應補 POSIX 升級實驗。正式修正後再依既有制度更新權威版、元件標記、必要的 VERSION、回歸測試與各專案遷移證據；本輪僅提供審查，不替使用者修改制度或舊報告的結案狀態。

## 保存與交接說明（2026-11-03）

使用者要求下一輪接棒先讀本報告，因此在審查結束後將本快照保存到 repo，並更新 AGENTS、ARCHITECT 與 HANDOFF。上文「未修改／未提交」描述的是審查階段，不是後續的保存交棒。R01–R09 的查核結論仍對應本文基準 commit；本輪沒有實作修正。後續處理狀態寫 HANDOFF，不把這份報告累積成日誌。原始探針／JSON 未隨 Git 發布；下一手可依各節的輸入與實得結果建立最小反例，不可宣稱已取得或重跑未取得的聊天產物。
