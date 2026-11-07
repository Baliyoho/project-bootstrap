# v2 P0：可重跑的契約與架構門檻

> 最後更新：2026-11-07
> 範圍：v2 分支的合成實驗，沒有部署、模型呼叫、付費服務或正式制度切換。

需求以 [決策書](../../project-bootstrap-requirements-decision.md) 為準；[實現規劃](../../project-bootstrap-implementation-plan.md) 定義 P0–P5。現行部署包仍是 22 檔的唯一權威。本目錄不是第二份 handoff 制度，也不複製其他專案的檔案。

## 執行與結果語意

在來源 repo 根目錄執行（無 python 時用 python3；本機使用 python3）：

```sh
python3 -X utf8 tools/verify_v2.py
python3 -X utf8 tools/verify_v2.py --require-ready
python3 -X utf8 tools/verify_v2.py --baseline --json
python3 -X utf8 tools/verify_bootstrap.py
```

一般入口 exit 0 只表示契約測試與預期反例成功重現。`--require-ready` 在這個 P0 階段必須 exit 2：完整歸因、正在執行線的使用前通知、不可繞過入口仍未達標。測試／索引本身失敗則 exit 1，不能用它冒充「預期尚未就緒」。既有一鍵入口會執行 P0 回歸，但其綠燈也不表示全部需求通過。

`--baseline` 額外量一次完整舊驗證器的等待；JSON 包含 UTC 取得時間、OS／Python、候選內容 digest、各常態入口的字元與 hash。完整接棒含 Git、閱讀、判斷等時間，這裡沒有量到，不以驗證器時間代替。字元也不等於 token。報告可輸出到 gitignored `dist/`；下一棒可用相同命令重新取得，不能依賴聊天附件。

只使用 Python 標準庫與本機 Git，沒有安裝候選套件；外部套件版本／LICENSE／digest 鎖定仍在 P0 待辦。這是先驗架構契約的選擇，不代表放棄規劃的 pytest、JSON Schema、Gitleaks 或 sandbox-runtime。原型不宣稱 Python 下限或三 OS 驗收；現有部署工具的 Python 3.8 宣告沒有改動。

## 三個門檻與可失敗輸入

| 門檻 | 原型測什麼 | 還不能保證什麼 |
|---|---|---|
| F11(b) | SQLite 交易內保存完整前後文、事件 ID、指定測試身分、時間；錯誤 base／未知 capability 拒絕；日誌或內容寫入失敗整筆回滾，重啟保留事件 | 可信 launcher、跨程序身分隔離、實際檔案 materializer／crash recovery。相同 UID 可直接改 DB 而沒有對應事件，整項不通過 |
| F28 | pending revision 與持久通知同交易；所有已登記線（含未明確依賴者）失效；舊 ticket／重複完成拒絕；application ACK 與 transport ACK 分開；離線未確認線阻止啟用 | 即時 push、模型確實重建上下文、正在執行線的使用前得知。真子程序已載入舊前提後仍能繼續計算，拒絕其結果不是使用前保障 |
| F42／F43(a)／F48 | 合成動作按 actor／kind／resource／次數／額度來源授權，撤銷或耗盡拒絕；全部候選與訊息先掃才建立 immutable snapshot，再允許寫 Git object；無 ignore 亦拒絕合成禁入值 | 授權由受信人類入口簽發、所有 shell／GUI／MCP／Git／外連入口受控。普通 Git 可繞過掃描函式，完整強阻擋尚未成立 |

`contracts.py` 的 Lab 是可信代理內部資料模型，**不是可交給 agent 的安全 API**：register／grant 等管理方法仍在同一程序，capability 是測試身分。權限分離完成前不得保存真實原文或憑證。原文只留 TemporaryDirectory，實驗結束刪除；不進 Git。每個測試的正常與異常輸入即重建 fixture；沒有從歷史或其他主機取得祕密。

`feasibility.py` 三個反例的預期結果是 `counterexample_observed=true`、`requirement_result=不通過`。移除拒絕、漏寫日誌或錯把 transport ACK 當 application ACK，契約測試應失敗；反例未能重現也不能安靜當成功，須重新判讀原因。

`isolation.py` 另外比較受 OS 約束的 macOS 子程序：檢查私有目錄讀取、直接寫檔、間接 shell 寫檔、Git object 寫入、網路被拒絕；scratch 正常可寫。只有啟動完成、正常操作成功且保護內容／object 集合不變才通過，不能把 Python 起不來算成阻擋。使用主機 `sandbox-exec`，本機 man page 已標 DEPRECATED；只作機制可行性探針，不採作正式 launcher、不宣稱逃逸審查或目前桌面工具已受它保護。非 macOS 明示未驗證。

`supervisor.py`（2026-11-07）將 F28 的改善方向做成真子程序實驗：兩條線持有各自程序，舊工作先停在執行中；前提變更寫 pending／通知，確認所有舊程序已退場，再啟動載入新上下文的替代程序。子程序自己回報 epoch／context digest 後才記 application ACK，全部確認後啟用新 epoch。舊 ticket 不可完成，失敗啟動或離線收件者都使新 epoch 保持未啟用。這只證明固定合成程式的可控介面，不證明任意模型已理解、現有 App 可被暫停或跨機通知已實作；F28 整項仍不通過。新增測試涵蓋正常替換、替代啟動失敗、離線線路、重複變更。

## 管道身分與管理分權（2026-11-07）

`broker.py` 把 agent 可呼叫的入口縮成有固定欄位的 write／effect，沒有 register、grant、revoke、shell 或任意命令。身分由父程序建立的獨立管道決定，不接受 JSON 裡的 actor 或 capability；管理操作只由父程序的合成授權 fixture 呼叫。資源逐管道限定，epoch 在 SQLite 寫入交易內重查，pending 前提不允許寫入或消耗授權。

請求以可信 principal＋整數序號識別，新增序號要求連續；收據與內容／合成效果在同一 SQLite 交易提交。相同原始請求重送回原收據、不重做效果，改內容重用序號及跳號拒絕。歷史收據也保留，重送舊事件不會恢復舊內容；被拒絕的請求同樣有收據，條件改變後須用新序號提出新請求。只有 parent 可指定恢復已知 principal、輪替 capability 並讀回其收據；agent 自填名稱不能恢復身分，舊 capability 會失效。未知例外只回固定錯誤並關閉管道，不把例外原文輸出。請求限制 8 KiB，重複 JSON 欄位、超大／畸形輸入皆拒絕。

`broker_fixture.py` 用實際 macOS sandbox 子程序測 11 次請求。與前面的 `isolation.py` 小範圍機制實驗不同，這個 profile 預設拒絕檔案讀取，只開 OS／Python 執行所需目錄、合成唯讀 repo 與自身 scratch；私有資料庫、另一線 scratch、連到私有庫的 symlink 都不可讀，正式視圖不可直接寫。Python 啟動器還需要逐層解析 runtime 祖先目錄，僅允許祖先目錄本身，不放開整棵樹；缺少它會在測安全邊界前就啟動失敗，不能當成功阻擋。繼承管道不傳 parent capability，其他描述符關閉，環境只留基本 PATH 與禁止 bytecode 寫入設定。

負向案例涵蓋冒名、自行授權、跨線資源、額度耗盡、重送、關閉／假造 channel、pending epoch、例外遮罩、重複 JSON key、深巢狀／過大輸入。整合探針再故意取消私有讀取保護、令子程序啟動失敗、送超大管道訊息，必須報不通過；合法 scratch 與代理寫入須能成功，避免把「整個程式跑不起來」當成保護。

**仍未交付的邊界**：父程序是可信測試 fixture，不是已驗收的人類授權服務。下節已補限期資格與 parent 請求保存，但正式 launcher、票據保管／遺失／更新流程及真正人類授權來源尚待整合。合成 effect 只改同一 SQLite 的事件與額度，不會刪真檔或呼叫付費 API，不能把交易收據外推成外部服務的 exactly-once 保證。尚未做 sandbox 逃逸審查、跨 OS／跨機或任何模型／桌面工具接線。原始同 UID 反例照留，完整需求判定不因本探針通過而改成通過。

## 限期資格與請求保存（2026-11-07）

`launcher.py` 的 LaunchAuthority 是可信 parent 的管理層：產生隨機 principal 與 256-bit 重連票據，私有 DB 只保存票據雜湊、資源範圍、授權來源標籤、有效期與撤銷狀態。重連必須持有票據，不能只報 principal 名稱，也不能要求較大的資源範圍；重連輪替 capability，舊管道失效。票據僅交給 parent 保管，沒有放進合成 agent 的 argv、環境或 RPC。Mac 管道探針已使用此層，正常寫入及合成授權效果仍須成功。

Broker 在受理新請求、讀回舊收據及恢復寫盤前重查資格；過期／撤銷時即使管道已建立仍拒絕。LaunchAuthority 簽發的合成動作授權必須有有效期，且不得超過管道資格；使用時再次核對期限與剩餘次數。舊 Lab.grant 的無期限形式只保留給低層合成契約，不代表人類授權，也不能作為正式入口。時間採 parent 時鐘並拒絕低於已提交 watermark 的倒退；沒有可信硬體時鐘，未提交的失敗檢查、DB 還原與未觀測的調時不受此判準保護，不能宣稱抗時鐘竄改。

RequestJournal 在可信 parent 的私有庫保存完整原始 bytes 與連續序號，再呼叫 broker；一次只容許一個 pending 請求。回應遺失或 parent 中斷後重送相同 bytes，收到最終持久收據才標 completed；materialization-pending 保持未完成。缺少原始請求、序號中斷、digest 不符或收據無對應日誌時停止，不生成新 principal／新序號猜測重送。此原型保留完整歷史，尚無裁剪、備份還原與跨機協定；DB 同時遺失或被可信 parent 篡改不在保證內。呼叫端的請求日誌尚未接入真實工具 adapter。

`test_launcher.py` 驗假造票據／principal、舊管道、期限邊界、撤銷、越權範圍、時鐘倒退、原始請求缺失／變更、日誌寫入失敗、回應遺失及過期後恢復寫盤。真正子程序分別在 outbox 提交後與 broker 效果提交後 `os._exit`，恢復後僅一筆效果。負向對照移除管道資格檢查或有效期記錄，重現舊邊界的錯誤放行；不是額外模型或外部服務測試。

此層的 `source` 是合成授權的來源標籤，非人類身分驗證或簽章。低層 Broker.attach／Lab 管理方法仍是 parent 內部 API，agent 隔離不能靠 Python 方法可見性成立。資格層本身不會終止已在運算的 child；下節的 parent 事件迴圈補直接子程序退場，F28 的前提切換與上下文重建仍需 supervisor 整合。這些限制未解決前不得部署真實資料。

## 固定啟動與直接子程序退場（2026-11-07）

`lifecycle.py` 的 ProcessLauncher 只接受可信 parent 提供的 LaunchPlan，不提供 agent 的任意命令 RPC。第一次啟動綁定 argv、入口 executable 的內容 digest 與 cwd 的實際位置／device／inode；替代啟動若改計畫會拒絕，不把原票據外推成另一個命令的授權。被入口讀入的其他腳本、import、設定與整個 runtime 尚未做完整 manifest 鎖定，仍須由可信 parent 保護。

啟動先持久記 `starting`，新 child 回固定 READY 後再重查資格、輪替 channel、記 `running` 並送 GO；合成 agent 在 GO 前不送請求。替換時先關舊 channel，TERM／必要時 KILL 並 wait 到直接 child 確實退出，記 `stopped` 後才能啟動替代者。握手錯誤、逾時、資格失效及日誌失敗都不交出可用的新管道；停止時即使日誌寫失敗仍嘗試終止 child，但保留未解狀態。parent 重啟只讀到 starting／running／stopping／unresolved 而沒有原程序物件時，拒絕替換；不憑 PID、經過時間或票據推定舊程序已退場，也不自行殺可能被重用的 PID。這是保守阻擋，尚無自動孤兒回收或人工解鎖程序。

TicketVault 使用已存在且屬於本 UID 的 0700 目錄；票據以隨機 handle 存成 0600 普通檔，O_EXCL／O_NOFOLLOW、單一 hardlink、內容長度與檔案／目錄 fsync 均檢查。讀取 FIFO 不等待，symlink、hardlink、錯誤權限與缺票據拒絕；不自動修權限、找歷史票據或重新發身分。資料只保存在合成暫存目錄，票據不進 agent 的 argv／環境／RPC；同 UID 的檔案權限不是隔離，仍由受驗的 OS profile 阻止 agent 讀私有目錄。

Mac `broker_fixture.py` 已用此生命週期與票據庫執行原有 11 次請求，正常私有票據讀回、管道效果、寫盤及程序退場都要成功。parent 的有界管道迴圈在閒置時每次等待最多 0.1 秒再重查資格，失效後結束 transport 並終止直接 child；這不是所有 OS／阻塞操作的即時停止承諾。`ProcessLauncher.check()` 本身需由事件迴圈呼叫，不是常駐背景 watchdog。

`test_lifecycle.py` 驗替換順序、舊 channel 失效、固定計畫拒絕變更、parent 重啟未解、啟動途中撤銷、握手失敗、忽略 TERM、停止／日誌故障、閒置過期及票據檔案反例；移除停止檢查的負向對照重現兩個 child 同時存活。沿用單一 parent writer 前提，不宣稱跨 parent 的原子 claim。只驗受追蹤的直接子程序，沒有驗任意後代／逃離程序樹、parent 崩潰後孤兒回收、票據遺失／更新、過期後延續授權、Windows 或真正人類授權入口。舊 supervisor 仍是獨立合成上下文實驗，尚未與此生命週期合成一個正式執行面。

## POSIX 工作樹套用與中斷恢復（2026-11-07）

`materializer.py` 將受理的內容事件套用到 parent 預先指定的合成工作樹：既有內容先由可信 parent seed；事件保存前後文與 epoch，寫盤前另提交 prepared 意圖，暫存檔寫完並 fsync 後同目錄 replace，再 fsync 目錄並記 applied。Broker 在這條鏈完成前只回 materialization-pending，不以「內容庫已受理」冒充檔案已完成。同資源前一筆未套用時拒絕新變更，避免計畫內容繼續往前而磁碟落後。

資源對路徑的映射由 parent 提供，不接受 agent 任意路徑。只支援已存在目錄下的普通檔案；使用 dir_fd／O_NOFOLLOW 拒絕 symlink、拒絕 hardlink、父層跳脫與 .git，保留普通檔案 mode。映射以 NFC＋casefold 保守拒絕可能的同檔別名（即使某個大小寫敏感檔案系統能分開，這個原型也不接受），避免兩個 resource 其實指向同一個檔案。暫存名依事件保留在受保護目錄；中斷後可以重建暫存內容。恢復時磁碟仍是 before 才繼續替換，已是 after 則完成收據；內容／mode 不符、epoch 已失效或恢復 phase 不明都停止。已 applied 的舊收據只表示過去那筆已完成，不把較新內容改回舊版。

恢復邊界覆核補強（2026-11-07）：重送已受理的寫入仍須符合當前 channel 的資源範圍；parent 重連時縮權，不能靠舊收據繼續寫盤。拒絕不改原收據，恢復授權後可用同一請求完成。資料庫在首次綁定時保存 root 的 device／inode 與完整資源映射，重啟改映射或換工作樹會拒絕；每次開 root 也核對身分。已有事件但沒有綁定的舊實驗庫不自動收編；尚無搬機、換根目錄或增減映射的遷移程序，需另行設計。恢復看到 after 內容後仍須 fsync 目錄，成功才記 applied；否則維持 pending，不能把可見內容當成已耐久套用。

`test_recovery.py` 用真正的獨立子程序 `os._exit`，分別在 prepared、暫存檔同步、replace、applied 提交後終止，再開資料庫／新管道恢復同一請求；檢查一筆事件、一份收據、正確內容、mode 與無殘留 staging。另驗效果在收據前終止會回滾、丟失回應後不重扣合成額度、收據或 commit 失敗不留下可晚點誤提交的交易、外部變更不覆蓋、失效 epoch 不寫盤與 symlink／hardlink／未知 phase 拒絕。受隔離 agent 整合探針也已接上 materializer：可經代理更新 managed 檔，直接寫仍被拒絕。

**適用邊界**：只在 POSIX 合成且由 broker 獨占的工作樹驗收，不是多 writer 的原子 CAS。外部程序若能在檢查與 rename 間改目錄／檔案，仍超出此保障，必須由 OS 隔離排除；不宣稱能歸因外部寫入恰好與 after 相同的內容。不支援自動建立目錄、刪除、整批檔案交易、真實專案遷移或 Windows。SQLite FULL 與 fsync 加上程序終止測試不是實測斷電；磁碟毀損／設備遺失仍未驗。尚未接 Gitleaks 或完整提交／發布代理，不能把可套用檔案等同敏感資料不進 Git。

## F50 與索引權威

`session.py` 實作狀態轉移及改名 adapter 契約；接棒／續聊、等待、交棒、重試、下限次數、缺工具、讀回不符都有測試。handoff receipt 的真實來源尚須工具 adapter 驗證，呼叫端自己填四個 True 不是可信交棒證據。returned state 要先耐久保存再重試外部改名；目前尚無正式持久儲存與工具事件接線，不能宣稱自動改名完整交付。`from_title` 只能恢復顯示欄位；事件去重須保存整份 state，不能只靠標題復原。

全部 51 ID 與 F11／F13／F43 子項的**持續實作狀態唯一權威**已從 `fdc0bbd:HANDOFF.md` 移交 [status.json](status.json)。欄位保留原狀態來源、範圍、重跑入口、未知與下一個驗收點；未驗證不是待決。`registry.py` 直接從決策書第 3 節核對 ID，測缺漏、重複、子項遺失、證據不存在與憑空成功。P0 不接受任何整項「通過」宣稱；日後正式驗收須改驗收證據模型與負向案例，不能只改狀態字串。

HANDOFF 保留 writer、目前行動與此索引的指標；若索引不可讀就停止判定，不從舊摘要恢復權威。原查核報告 F01–F16 是另一組編號，不與需求 ID 混用。

## 接下來的架構工作

1. 管道分權、POSIX 套用、限期資格、請求保存及直接 child 生命週期已有合成證據；下一批處理後代程序／parent 中斷的控制邊界、人類授權與票據更新／過期後續作。將請求 outbox、管道生命週期與 supervisor 接成同一執行面；逐 surface 列繞過入口，不把 fixture 當真實部署。
2. 將合成 supervisor 的停止／排空／重建上下文協定接到實際可控執行介面；不能把程式裡 application=True 當作模型已理解，也不能把 outbox 當即時通知。真實模型探針仍需另行明確授權。
3. 再鎖定需實際採用的外部元件、驗 Windows／Mac 門檻。未通過前不開始全面搬來源、改現行 A4 或部署專案。
4. 接棒成本已能逐次量測；短入口及證據失效機制需配套驗收後才切換。常態必讀超額照實報不通過，不藉此省略檢查。
