# project-bootstrap 第三方視角查核與改善報告

查核日期：2026-11-02（Asia/Taipei）
基準：`main @ 313e7a529a095a3f671784452a2f284eee4cd3a7`；VERSION `2026-11-02`。
性質：本次對話中的獨立技術審閱，不是外部認證或安全保證。

## 1. 結論

**這套制度已具備可用的協作流程與有價值的回歸測試，但目前不足以支持「協作正確性會自動成立」的強主張。** 它適合有人監督、遵守程序的接力工作；尚不能當作可靠的互斥鎖、發布閘門、服務健康判定或全面的安全同步器。

本次接棒時，既有 `python -X utf8 tools/verify_bootstrap.py` 實跑 **37 項全過、exit 0、重生 22 檔**。其後在同一 commit 上加入獨立反例，仍然找到真實缺陷：占用誤報空閒、自訂 hook 被同步刪除、同步失敗仍 exit 0、服務檢查失敗仍 exit 0、push 漏判，以及子目錄啟動接線失效。這不是否定既有測試，而是證明測試的輸入空間與對外主張尚未對齊。

最優先應修的是**成功／失敗訊號與資料保全**，再處理發布版本、制度權威衝突與可重現驗收。繼續增加散文禁令，無法代替這些修正。

## 2. 範圍、方法與限制

檔案範圍涵蓋目前 17 個 tracked 檔：部署包、README、AGENTS、ARCHITECT、HANDOFF、CLAUDE/GEMINI 指標、VERSION、LICENSE、兩支 Python 工具、兩支本 repo hook／啟動器、兩份接線及 Git 設定。部署包涵蓋訪談、22 份生成檔案、A/B/C/0 程序、部署、同步與自檢；測試器另核對其生成、負向測試、平台接線與打包流程。

方法分為四層：

1. **實跑基準**：本次 session 已完成既有驗證；沙箱暫存區權限失敗後，以核准權限重跑成功。權限錯誤不當成產品缺陷。
2. **獨立反例**：在 repo 外建立生成骨架與本機 bare remote；不向 GitHub 推測試、不修改真專案。測試結果摘要保留於本報告；原始腳本與輸出位於原查核聊天產物，未隨 Git 發布。
3. **靜態控制流程與規則對照**：區分程式實作、程序要求、宣稱與測試真正證明的範圍。
4. **官方來源交叉查核**：Claude Code、Codex、Antigravity 與 Python 官方文件；官方文件支持不等於本機端到端實測。

**未執行**：新增模型呼叫、其他機器／macOS／Linux 實機測試、Claude／Antigravity 新 session 探針、六個既有專案的副本重查、歷史全部 commit 的祕密稽核。本 repo 明定模型探針需另行授權，這次沒有藉查核繞過。也未重啟已決定不追的 Antigravity IDE 調查。

報告中的「已重現」有本次輸出；「靜態確認」有明確程式分支或文件矛盾；「設計風險」是尚未透過並行／跨平台實驗證實的推論。不能用後兩者宣稱實際事故已經發生。

## 3. 主要主張核實

| 主張／功能 | 判定 | 查核理由 |
|---|---|---|
| 一份部署包可重生管理骨架 | 基本成立 | 現有抽取及填值測試成功，22 檔齊全；但人工部署的額外動作並非都由抽取器完成 |
| 持久知識／快照／Git 歷史分工 | 設計合理 | 能減少跨 session 的資訊遺失；內容正確性仍靠交棒者核對 |
| 每個事實只有一個家 | 部分成立 | 程式範本集中；程序摘要、權威規則、能力敘述仍有重複及實際矛盾 |
| 開場揭露其他 writer | 有缺陷 | 同步成功不代表空閒；含「無」的正常任務標題會造成明確的錯誤綠燈 |
| push 前防止漏交接 | 僅啟發式提醒 | 是 AI PreToolUse，不是 Git 原生 pre-push；指令字串、當前分支、工作樹特例均會漏判 |
| 同步保留專案設定 | 有缺陷 | 能保留另一組 hook；同一組內的自訂 handler 被整組替換 |
| 一鍵驗證服務現況 | 快照輸出成立，通過判定不足 | 能印 HTTP／命令結果，但命令失敗仍 return 0；不比對業務期望 |
| 文件一致性檢查 | 有限成立 | 能抓指定形式的本機連結、已知過期字串與佔位符；不是通用語意或網路連結驗證 |
| 跨工具支援 | 有條件成立 | 官方支持主要入口與 hook 契約；各版本、surface、信任設定仍需分別實測 |
| 版本落後偵測 | 範圍比名稱窄 | 只比較 SKILL 標記與 VERSION，不是整套部署完整性檢查 |
| 續聊改名與交棒計數 | 程序已寫入 | 18 個負向測試驗文字沒有消失，沒有量到各模型的實際遵循率 |
| 全過才打包 | 有缺陷 | SKIP 判斷在 build_zip 之後；有未驗證項仍進入打包 |

值得保留的部分：明確禁止破壞性 Git 操作、保留不確定性、不從別處挖憑證、B6 覆寫快照、預演同步、明確區分工具 surface，以及 Windows 完整啟動鏈與負向測試。這些不是只寫口號，已經有對應程序或可執行驗證。

## 4. 優先修正事項

嚴重度：P1＝可能誤導 writer／發布判定或損失專案設定，建議下一批先修；P2＝重要可靠性或維護缺口；P3＝可讀性與操作改善。未發現足以定為 P0 的證據。

### F01｜P1｜任務名稱含「無」，占用標記被誤判為已交棒【已重現】

位置：部署包 1425、1785 附近；本 repo `.claude/hooks/repo-git-check.sh:68`。

兩支 shell hook 都用 `*無*` 判斷整行，check_docs 亦以 `if '無' in value` 跳過後續格式驗證。測試標記：

```text
- **工作中**：`other-machine` ／ `Codex CLI` ／ `㊣　26110209｜修無效連結｜工作中｜交棒0次`
```

兩支 hook 都輸出「工作中是無（已交棒），沒有別台機器佔著 main」。正常任務名稱即可觸發，不需惡意輸入。這是本次最高優先的錯誤安全訊號。

**改善**：只解析唯一、格式正確的欄位；正規化後必須完整等於 `無（已交棒）` 才視為空閒。其餘值依欄位解析，缺欄、重複、空欄、非法格式均回 UNKNOWN。機器比對也要只比機器欄，而非整行包含本機名稱。

**驗收**：標題含「無／無效／無法」、機器名互為子字串、重複欄位、空工具欄等情境都不能產生錯誤綠燈；兩支 hook 與文件檢查器共用案例。

### F02｜P1｜同步會刪掉同組的專案自訂 hook【已重現】

位置：`tools/sync_project.py:175`，尤其 207 的 `cur[at] = copy.deepcopy(g)`；現有測試位於 `verify_bootstrap.py:1398` 附近。

將 `echo project-custom-check` 放在骨架 SessionStart 同一個 group 的 hooks 陣列中，呼叫 merge_wiring 後它消失，且沒有 error。現有測試只把自訂 hook 放在另一個 group，沒有覆蓋這個合法形狀。

**改善**：所有權應落在骨架 handler，不能將包含它的整個 group 視為全屬骨架。保留非骨架 handler 與相關 metadata；遇到無法安全拆分的 matcher，拒絕並提供 diff，不靜默猜測。腳本名稱 substring 比對也應改成可辨識的穩定 ID 或明確命令結構。

**驗收**：同組／異組／重複骨架 handler／只有 Windows command／自訂 matcher／hook metadata 的保留與衝突測試。

### F03｜P1｜同步報 FAIL 仍 exit 0，且可能已部分寫入【已重現＋靜態確認】

位置：`tools/sync_project.py:269`、421–444。

壞 JSON 的預演會印 FAIL，但程序 exit 0；不存在的目標也 exit 0，最後竟印「全部都已經是 v2026-11-02」。錯誤只存在 msgs，沒有彙總成失敗狀態。WHOLE 更新早於 JSON 驗證，`--write` 情境會先寫部分檔案再發現後續錯誤；此部分由程式順序確認，本次沒有對真專案測試。

**改善**：先建完整 plan，所有目標／JSON／設定區塊通過 preflight 後才套用。回傳 changed、failed、skipped、conflicts 等結構化結果；任何失敗非零退出。拒絕自身 repo、目標不存在、根目錄不是有效部署均不可宣稱最新版。逐檔原子替換並保留可回復方案；多檔失敗必須明記哪些已套用。

**驗收**：任一檔案解析失敗時零寫入；寫入途中失敗有一致復原或完整清單；exit status 與摘要一致。

### F04｜P1｜服務失敗仍回傳成功碼【已重現】

位置：部署包 1933–1981。

在生成的 verify_state 加入會 exit 7 的命令，輸出 `deliberate-failure=rc7`，但 main() 仍回傳 0。HTTP FAIL、ERROR 也只印字；沒有結果彙總。這使以 exit 0 判斷服務驗收的下游流程誤過關。NOT_CONFIGURED 回 0 是既有明示選擇，不能與真正失敗混為一談。

**改善**：每項檢查回傳結構化 PASS／FAIL／ERROR／SKIP／NOT_CONFIGURED；非零程序碼不得被吞掉。宣告哪些檢查必需、允許哪些缺配置；服務健康另外定義 HTTP status、JSON 欄位或業務 predicate，不能只把有回應當作正常。祕密內容與命令輸出要有遮罩界線。

**驗收**：rc7、HTTP 500、timeout、錯誤回應內容都讓 strict 模式非零；可選項缺配置有獨立報告，不能當通過。

### F05｜P1｜子目錄啟動時，hook 根本找不到【已重現＋官方支持】

位置：部署包 3.9／3.17；本 repo 兩份接線。

從測試 repo 的 subdir 執行接線使用的 `bash .claude/hooks/git-freshness.sh`，exit 127、No such file。shim 內的 `%~dp0` 只能在 shim 已經被找到後生效，無法修復呼叫它的相對路徑。Codex 官方文件確認 command 以 session cwd 執行，且直接建議從 Git root 解析 repo hook。[Codex Hooks](https://learn.chatgpt.com/docs/hooks)

**改善**：「不得硬編特定機器的絕對路徑」與「執行時由 Git root 算出絕對路徑」應分清；後者是可攜解法。依工具提供的根目錄變數或 Git root 定位，維持 quoting、stdin 與退出碼。Antigravity 的解析基準須獨立保留，不能直接照搬。

**驗收**：用 JSON 接線中的原始 command，分別從 repo root、子目錄、空白／中文目錄執行；測到入口，不只用完整路徑直接測 shim。

### F06｜P2｜push 防呆會放過未提交交接與常見指令形狀【已重現】

位置：部署包 1546–1565；`verify_bootstrap.py:488`。

在存在未推送 commit、且該批 commit 沒改 HANDOFF 的 fixture 中：

| 輸入／狀態 | 本次退出碼 |
|---|---:|
| `git push origin main`，HANDOFF 乾淨 | 2，正確阻擋 |
| `git -c color.ui=false push origin main` | 0，漏判 |
| `git push origin main`，HANDOFF 僅有未提交修改 | 0，放行；該修改根本不會隨 push 上傳 |

另外，當前分支不是實際 refspec 目的分支、command 只是提到 git push、外部 Git GUI 等都不在可靠覆蓋內。程式已註明「寧可漏擋」，因此不應把它描述成完整發布保證。

**改善**：先移除未提交修改放行的錯誤假設；明確命名為「AI push 提醒」。若需要硬發布閘門，另評估 Git 原生 pre-push 對 ref/SHA 的檢查與伺服器保護，並保留合法的開工／中途同步狀態。不要企圖以更多 substring 規則解析所有 shell。

**驗收**：命令選項、refspec、不同 remote、staged／unstaged HANDOFF、GUI／script 路徑、開工與交棒各有明確期望。

### F07｜P2｜有 SKIP 仍進入 ZIP 打包【控制流程重現】

位置：`tools/verify_bootstrap.py:1884`–1888。

以 stub 代替檢查與 build_zip，注入一個 SKIP 後執行 main：**build_zip 仍被呼叫，最後才 return 1**。本次未真的生成或發布該 ZIP；測的是可重現的控制流程，不冒充完整發布實驗。這與「全過才輸出」不一致。

**改善**：在 build_zip 前判定 FAIL 與 SKIP；預設只允許完全通過時發布。若保留未驗證產物的調試選項，必須顯式啟用並附未驗證 manifest。

### F08｜P2｜文件檢查器的保障範圍不足【靜態確認＋函式測試】

位置：部署包 1693–1876。

HANDOFF 不在輸入清單時 check_busy_field 回 `(False, [])`，主程式跳過；部署後刪掉整份 HANDOFF 並不被這項強制擋住。它也不驗 80 行、必要章節與欄位唯一性；本 repo 有較強版本，但沒有部署給使用者。日期檢查只找「最後更新」文字，不驗日期。連結檢查跳過外部 URL、去掉 anchor，且是簡單 regex，不等同完整 Markdown 驗證。

**改善**：區分「一般文件檢查」與「已部署制度檢查」模式；後者必須要求 HANDOFF、必要欄位及行數。文件對外名稱改成實際範圍；語意與任務完成證據仍由 B6 負責。新增 Markdown 語法測試，避免程式碼範例、帶 title／空白的連結誤報。

### F09｜P2｜VERSION 無法代表整個制度包，且比較方向錯置【靜態確認】

位置：部署包 1497–1510；`verify_bootstrap.py:714`；AGENTS 鐵律 1。

VERSION 只跟 SKILL 的 source 比較，因此 hook、JSON、檢查器變動可能永遠不提示；此限制已被文件承認。比較使用不相等而非版本大小，連上游較舊也稱本機落後；既有測試把快取「最新」設成 1999，反而把錯方向的情境命名為落後。source 標記相等亦不代表內容相等。

**改善**：將 package release、個別 component 版本與專案 migration 狀態分開；生成含路徑／hash／所有權的 manifest。先稱「版本不同」而非「落後」，再以版本規則判方向；保留離線與快取狀態的可觀測性。JSON 納入 manifest，不必硬塞註解。

### F10｜P2｜同步的新程序可能被不同步的舊協定推翻【設計衝突】

位置：`sync_project.py:84` 的 INSTANCE；部署包 655、851 附近。

handover-protocol 是不同步的專案實例，卻規定與 SKILL 衝突時以協定為準，甚至就地修 SKILL；而權威 repo 又禁止在單一專案就地改共用 SKILL。升級後不能只憑 SKILL 已同步就斷言制度一致。

**改善**：共用規範採版本化核心，專案差異用明確 override；同步前列出核心版本與需人工遷移的實例，不直接整份覆蓋專案規則。指定單一衝突優先序，避免要求接手者修改應保持同源的檔案。

### F11｜P2｜A/B/C 仍有未定義或互相牴觸的狀態【靜態確認】

位置：部署包 1007–1124、1154–1289、1396。

- A1 未明確處理「乾淨但 ahead-only」與 fetch 失敗；只有前兩列可自行繼續，卻沒有完整的異常處置表。
- A2 切到待續分支後，沒有明確再跑 A1 的同步與 divergence 檢查。
- A4 說現況不一致就地修文件；A5 又要求先回報、寫標記後才改檔，順序應釐清。
- hook 的分岔提示直接建議 `git pull --rebase`，與 A1「分岔停下等指示」不一致。
- B3/B4 在 B6 覆寫 HANDOFF 之前，最後產出的快照沒有明確再驗一次。
- 「準備 push 先 B」與 A5 開工 push、C 安全點 push 同時存在；應列出明確例外。

**改善**：建立小型狀態轉移表，每列含前提、允許操作、成功證據與失敗處理；A4 只收集差異，取得寫入權後才修文件；B6 後驗最終待提交狀態。不要讓規則的解讀順序決定結果。

### F12｜P2｜工作中標記是協調訊號，尚非互斥鎖【設計風險，未做並行實驗】

A2.5 讀取與 A5 寫入間有時間窗；跨 clone 同時 push 通常會由 Git 非 fast-forward 拒絕其中一方，但同一工作樹的兩個 session 仍可能在 commit/index 操作時互相干擾。hostname／工具名／可變標題也不是穩定 owner token。

**改善**：先寫清支援的是接力 single-writer；同機寫入增加本地原子 claim，跨機 claim 綁定觀測到的 remote SHA，push 成功後重讀確認 owner。不要讓到期時間自動奪走 writer；未知是否仍工作時保留人工確認。失敗的 claim 不可直接當一般 merge 衝突合併。

### F13｜P2｜--all 的「所有」有隱藏範圍，worktree 判斷不可靠【靜態確認】

位置：`sync_project.py:43`、378。

只掃 Desktop 下一層、有特定 SKILL 路徑的專案；用路徑是否含 `worktrees` 排除，任意名稱的 Git worktree 仍可被掃入，普通目錄名稱含該字則被排除。全域副本不在自動掃描中。寫入亦未自動確認 dirty、占用與當地客製差異。

**改善**：支援明確 inventory 或 `--root`；用 Git 自己的 worktree/common-dir 資訊辨認；輸出目標及排除原因。preflight 檢查占用、dirty 與檔案內容漂移；不自行 stash／commit。全域副本另列明確的同步目標。

### F14｜P2｜Python 相容性前提未宣告【官方 API＋程式確認】

位置：`verify_bootstrap.py:206`；sync_project 共用該 extract。

使用 `Path.read_text(..., newline='')`，官方標示此參數自 **Python 3.13** 才加入；因此維護／同步工具並非任何 python3 都能跑。文件主要只說 python 不存在改用 python3。本機是 Python 3.13，基準成功不涵蓋舊版本。[Python pathlib](https://docs.python.org/3/library/pathlib.html#pathlib.Path.read_text)

**改善**：明確標出維護工具與部署後工具各自的最低版本；或改用較早已支援 newline 的 open。啟動先檢查版本並清楚報錯，CI 測最低支援版本。

### F15｜P2｜已修正的主張仍在範本／操作卡復活【靜態確認】

- 部署包 504 仍說「其他工具（Gemini／Codex）沒有 skill 機制」，與現行能力表相反；新部署 README 會直接帶出這句。
- 第 6 節 2302 說版本序號算當天第幾次修改，AGENTS 則說算帶 source 標記的修改，兩者不是同一規則。
- 協定 685 與接棒 prompt 仍以「有憑證才跑」描述 verify_state，會漏掉不需憑證的本機／公開檢查。
- README 的 prompt A/B 命名是 A 交棒、B 接棒，與 skill 模式相反；它雖有定義，仍是可避免的操作負擔。
- 「可攜層到哪都成立」「三層自動發生」過度保證；載入、遵循與執行是三種不同證據。

**改善**：先修已知矛盾，再以共用資料生成摘要／能力表。不要只增加特定舊句的禁止 regex，因為新的措辭會再次繞過。保留事故理由，但將大段年代記移到部署包附錄，以短 reason ID 指向；維持單一可攜產出，不必新增第二份權威。

### F16｜P2｜發布測試與實際部署流程尚未閉環【靜態確認】

測試器 extract 的是圍欄內範本；例如 .gitignore 需依訪談追加 SECRETS／RUNTIME_DIRS 的指令在圍欄外，基準答案又只用已有的 `.env`／`data/`，所以測試沒有證明自訂憑證路徑真的被忽略。Windows 初次建立 ag-wrap.sh 的 Git executable bit，也仰賴人工指令。第 4 節先 push，完整第 5 節驗收才在其後執行；初次發布可能早於完整驗收。

**改善**：將訪談答案轉為部署 manifest；加入不同憑證檔名的 `git check-ignore` 測試、索引 mode／clone 後可執行測試、空白專案完整生命週期測試。先做不依賴 remote 的檢查，再首次發布，接著驗遠端及 runtime。祕密掃描關鍵字與檔案清單只降低風險，不能宣稱涵蓋所有祕密格式。

## 5. 外部工具查證結果

**Claude Code**：官方目前支持 v2.1.277 起原生 AGENTS、預設 CLAUDE 優先、`@AGENTS.md` import，以及 import 不重複載入的主要說明。這部分核心方向成立；「保證到哪都注入」仍應受設定、版本與權限限制。[Claude memory](https://code.claude.com/docs/en/memory)

**Codex**：官方支持 repo hooks、commandWindows、Bash 工具別名、PreToolUse exit 2，以及 repo `.agents/skills`。官方同時明列 session cwd 與 Git root 定位建議，支持 F05。`~/.codex/skills` 在本次提供的技能清單中確實存在，但不把此單一環境觀察擴張成未來所有版本契約。也不把 CLI runtime TUI 測試當成 App UI 驗收。[Codex Hooks](https://learn.chatgpt.com/docs/hooks)、[Build skills](https://learn.chatgpt.com/docs/build-skills)

**Antigravity**：官方支持 workspace `.agents/hooks.json` 與 SessionStart `injectSteps`，與目前使用方向一致。但當前 PreToolUse 文件使用 `decision: "allow"` 等欄位，並非 repo 歷史實測描述的 `allow_tool`。這是版本／契約差異，需要把歷史觀察明確限定版本；不據此宣稱舊實驗造假，也不因此擅自接上目前刻意未使用的 PreToolUse。IDE 不再追查的既有決定維持。[Antigravity Hooks](https://antigravity.google/docs/hooks)

各版本的「已端到端實測」目前主要是 repo 敘述；本次沒有重做模型探針。未提供可核對的原始紀錄時，只能標為歷史紀錄，不能冒充本次獨立重現。未來保存去識別化 fixture、版本、OS、命令、退出碼、最小輸出與 hash，即可提高證據強度，不需要保存私人對話全文。

## 6. 改善路線與驗收門檻

| 階段 | 工作 | 完成標準 |
|---|---|---|
| 第一批：修錯誤成功訊號 | F01–F07：占用 parser、handler 保全、同步與服務 exit、cwd 定位、push dirty 漏判、SKIP 打包 | 本次反例轉成負向測試；既有 37 項仍過；錯誤狀態不能綠燈或產出正式包 |
| 第二批：釐清協作契約 | F08–F12：部署後 HANDOFF schema、package manifest、核心與 override、A/B/C 狀態表、claim 邊界 | 換分支、續聊、未推送、失敗 claim、交棒最終快照均有明確驗收；不靠語意猜測 |
| 第三批：建立發行可信度 | F13–F16：inventory、最低版本、文件去重、部署整合測試與跨平台 CI | Windows/macOS/Linux 適用測試全過，skip 明列且不可當 release pass；產物帶 commit/hash |

每批都依 repo 規則先改部署包權威內容，再更新標記、必要的 VERSION 與測試，驗證後才同步副本。**在版本設計正式遷移以前，仍遵守目前「只有 SKILL 改動才跳 VERSION」規則**，不要因本報告建議而直接製造永久落後提醒。

建議建立三種測試標籤：`text-contract`（文字存在）、`script-behavior`（函式／程序）、`runtime-e2e`（真工具注入／阻擋）。報告分別顯示，避免用一個「37 項全過」讓讀者誤以為模型遵循也被量過。新增 CI 前需處理版本保鮮檢查的時間依賴、子程序 timeout、網路隔離與 fixture 命令退出碼檢查。

建議量測的是跨 session 接手是否先同步、改檔前是否取得 writer、交棒是否上傳最終快照、續聊是否保留次數，以及不同工具的漏步率。模型行為評測需另行授權並使用訂閱額度；不要把字串負向測試的數量當遵循率。

## 7. 查核產物與後續使用

原查核階段的報告與反例均在 repo 外，當時未修改制度檔、未 commit、未 push、未同步既有專案。2026-11-02 使用者要求交棒時讓下一手閱讀本報告，因此將本報告保存於 repo；這是對上述基準 commit 的查核快照，不代表問題已修正，也不是新的制度權威。

原查核聊天產物包含 `audit_probe.py`、`audit-results.json`、`audit_supplement.py`、`audit-supplement.json`，未納入本 repo，換機器不能假設它們仍可存取。主測試使用 local bare remote，補充測試以 stub 確認 ZIP 控制流程；它們不是正式回歸測試套件。下一手依本報告的輸入與實得結果重建最小反例，再修正權威版與補正式測試；不要把未取得的原始產物宣稱為已核對。

建議下一個實作任務直接從 F01／F02／F03 開始：它們分別關乎 writer 誤判、專案設定保存與同步結果可信度，也是其餘制度能否安全推廣的前提。
