# v2 P0：可重跑的契約與架構門檻

> 最後更新：2026-11-12（P2 第 5 片，加 Q26 行末）
> 2026-11-11 P1 第二片：本目錄的程式已搬到 [src/project_bootstrap](../../src/project_bootstrap/__init__.py)、測試搬到 [tests](../../tests/__init__.py)；這裡只留本說明與 [現況索引](status.json)。下文提到的檔名是同一份程式，指令已改成新位置；各節日期的歷史敘述不改。
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

`--baseline` 額外量一次完整舊驗證器的等待；JSON 包含 UTC 取得時間、OS／Python、候選內容 digest、各常態入口的字元與 hash，及本次 Python executable、guardian、sandbox-exec、ssh-keygen 的檔案 SHA-256。讀不到的元件明示未驗證。完整接棒含 Git、閱讀、判斷等時間，這裡沒有量到；字元也不等於 token。報告可輸出到 gitignored `dist/`；下一棒可用相同命令重新取得。

使用 Python 標準庫、本機 Git、macOS sandbox-exec 與 OpenSSH 簽章驗證器，沒有安裝候選套件。外部候選與完整 runtime 的版本／LICENSE／digest 清單仍在 P0 待辦。原型尚未驗 Python 下限或三 OS，現有部署工具的 Python 3.8 宣告沒有改動。

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

原始 `source` 是合成來源標籤，簽核模式另見下節。低層 Broker.attach／Lab 管理方法仍是 parent 內部 API，agent 隔離由 OS profile 負責。受管執行面的退場與前提切換見後文。原型限合成資料。

## 合成動作簽核（2026-11-08）

`approvals.py` 用 [OpenSSH 的分離簽章介面](https://man.openbsd.org/ssh-keygen.1) 驗 Ed25519 文件。驗證端接收公開金鑰；測試簽署端用獨立的暫存私鑰。每個實驗資料庫固定 audience、公開金鑰與驗證器 digest；無法驗證或任一項改變就停止。已存在低層授權的實驗庫不能直接切成簽核模式。簽核綁定資料庫、principal、前提 epoch、動作、資源、次數、期限與適用的額度來源；合成額外模型僅接受訂閱標籤。所有效果只記錄在合成資料庫。

授權與原始簽核收據在同一交易落地。精確重播只回原授權 ID，換內容重用 ID、遺失收據、受眾或範圍不符皆拒絕。切換中的 epoch 不收簽核；舊 epoch 的未用次數不會轉到新前提。簽核模式下既有 launcher 標籤入口拒絕發放，低層缺簽核收據的授權也無法消耗。`test_approvals.py` 另用原有 macOS 隔離 worker 的 broker 管道實測合成 paid-api。這台 Mac 的 OpenSSH 套件回報 10.5p1；測試外未部署簽核元件。真人身分／明示同意的 UI、簽署金鑰的發行與撤銷、受信服務部署、資料庫備份回滾、票據續期的人類證據與真實效果均另驗。

## 固定啟動與監護退場（2026-11-08）

`lifecycle.py` 的 ProcessLauncher 只接受可信 parent 提供的 LaunchPlan，不提供 agent 的任意命令 RPC。第一次啟動綁定 argv、入口 executable、guardian 所用 Python executable 和 guardian 腳本的 digest，以及 cwd 的實際位置／device／inode；任何一項變動都拒絕替換或重啟續接。其他腳本、import、動態函式庫與設定仍須由可信 parent 保護。舊 fixture 若缺新計畫指紋會拒絕重啟，沒有自動遷移。

啟動先持久記 `starting`，新 worker 回固定 READY 後再重查資格、輪替 channel、記 `running` 並送 GO；合成 agent 在 GO 前不送請求。`guardian.py` 是可信 parent 啟動的獨立監護程序，持有 worker 的 Popen。parent 獨占生命管道寫端，關閉或被終止造成 EOF；監護程序收到後 TERM／必要時 KILL 並 wait worker，再把回收紀錄寫入這次啟動專用的私有檔案並 fsync。生命管道與紀錄 FD 均不傳給 worker，監護不拿票據或資料庫管理能力。替換先關舊 channel，再關生命管道，確認監護結束及回收紀錄後才記 `stopped`。只看監護程序結束會把監護被殺、worker 仍存活誤判為成功。

握手錯誤、逾時、資格失效及日誌失敗都不交出可用的新管道；停止時即使日誌寫失敗仍嘗試回收 worker，但保留未解狀態。慢監護不被 launcher 強殺，停止逾時保持阻擋。重啟後普通 `start` 仍拒絕未知狀態；明確呼叫 `reconcile` 要核對有效票據、固定計畫及本次啟動的回收紀錄，包含原目錄／檔案的 device 和 inode、權限、單一連結與完整內容。缺檔、空檔、替換、舊次啟動紀錄或監護來不及寫入都保持阻擋。這條路徑不讀 PID、不掃描程序表。監護僅在仍存活且得到排程時提供直接 worker 回收。紀錄目前留在暫存 fixture，未設長期清理、人工解鎖或遷移。

TicketVault 使用已存在且屬於本 UID 的 0700 目錄；票據以隨機 handle 存成 0600 普通檔，O_EXCL／O_NOFOLLOW、單一 hardlink、內容長度與檔案／目錄 fsync 均檢查。讀取 FIFO 不等待，symlink、hardlink、錯誤權限與缺票據拒絕。可信 parent 的 `renew` 要求現有票據、同一啟動計畫和回收證據，接受已到期但未撤銷的票據；新票據先寫入私有檔，再以同一交易更新票據雜湊、原定位符指向和續期記錄。交易失敗仍以原票據為準；成功後舊票據失效，同一定位符與 principal 可續接原 outbox。動作授權的個別到期日不延長。缺現行票據不回退舊檔或重新發身分。合成來源標籤仍由可信 parent 提供，沒有真人身份查證；同 UID 的權限由受驗的 OS profile 補隔離。

Mac `broker_fixture.py` 已用此生命週期與票據庫執行原有 11 次請求，正常私有票據讀回、管道效果、寫盤及程序退場都要成功。OS profile 拒絕 process-fork／signal，實測 fork、subprocess、posix_spawn 與向監護送訊號遭拒，避免 agent 再生後代或自行終止監護；這是目前單程序合成 agent 的限制，不是通用 shell／任意程序樹控制。parent 的有界管道迴圈在閒置時每次等待最多 0.1 秒再重查資格。`ProcessLauncher.check()` 仍需事件迴圈呼叫才能及時反映撤銷；啟動時也把剩餘租期換成同機 monotonic 截止點，監護即使收不到 EOF，仍會在截止時停止 worker。SIGSTOP 凍結父程序的負向情境已實跑；凍結期間未到期的即時撤銷、監護失效、整機暫停及跨機時鐘未驗收。

`test_lifecycle.py` 除既有啟停、資格、日誌與票據反例，另用真正被 SIGKILL 的 parent 測握手中／執行中的回收；固定 worker 全生命週期持有檔案鎖，以鎖釋放證明退場，沒有用 PID 消失推定。移除監護後重現孤兒仍持鎖；殺監護後 worker 仍持鎖且替換拒絕；控制 FD 不繼承、啟動失敗釋放 FD、未解狀態不對無關活程序送訊號也有測試。票據更新另驗舊票據失效、撤銷後拒絕、交易失敗及現行檔案遺失。未隔離 worker 產生後代的反例會在直接 worker 已 stopped 後繼續持鎖。`test_broker_fixture.py` 移除 fork／signal 防護各會使探針失敗。沿用單一 parent writer 前提；任意後代、監護被殺、票據遺失後重新驗身分、Windows 與真正人類授權未完成。

2026-11-08 程序樹候選探針：`tree_probe.py` 在本機合成程序群組中，對仍持有的群組送 TERM，一般後代的檔案鎖會釋放；後代若呼叫 `setsid` 建立新 session，群組 leader 已退場，後代仍持鎖。`test_tree_probe.py` 驗正反例，移除脫離行為時反例檢查會失敗。這說明程序群組不能作為任意後代的退場證明；探針沒有接入可信 launcher，也不能用群組 ID 做重啟認領。依 [Apple setpgid](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setpgid.2.html)／[killpg](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/killpg.2.html) 文件，群組只能對仍屬於該群組的程序送訊號。[Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) 具備關閉最後 handle 時終止關聯程序的候選機制，但 breakaway 設定、建立時加入與實際退場證據須在 Windows 另驗。Mac 的多程序及 guardian 被殺仍維持阻擋；尚未選定真實 surface。

2026-11-08 Mac 後代事件候選探針：macOS 27 SDK 的 [`es_new_descendants_client`](https://developer.apple.com/documentation/endpointsecurity/es_new_descendants_client(_:_:)) 宣稱可接收呼叫程序整棵後代樹的事件；依該定義推論，`setsid` 不會因改變程序群組而移出後代樹，此點尚未實測。同一份 SDK header 明定需要 `com.apple.developer.endpoint-security.client` entitlement。這台 macOS 27.2 的未簽署合成 helper 成功編譯，API 回傳 3（`ERR_NOT_ENTITLED`），因此本機沒有可用事件客戶端。`tree_probe.py` 的可重跑前置探針只測 API 准入，沒有訂閱事件或操作真實程序。即使有 entitlement，通知本身也不會在 guardian 被殺時自動終止已存活後代；仍需獨立驗證事件遺失、程序身分、結束確認、重啟恢復與撤銷時的 fail closed 行為。此候選目前不提供 Mac 多程序退場保障，亦不改變 P0 未退出。

2026-11-08 Mac VM 候選已從支援查詢推進到合成 guest。`python3 -X utf8 src/project_bootstrap/vm_probe.py`（2026-11-11 前是 `experiments/v2/vm_probe.py`）在這台 Apple silicon／macOS 27.2 下載並核對 [Alpine 3.24.4 aarch64 netboot](https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/aarch64/netboot/) 的固定 SHA-256，從壓縮的 `vmlinuz-virt` 解出 ARM64 Image，替換 initramfs 的 `/init`，編譯並 ad hoc 簽署帶 [`com.apple.security.virtualization` entitlement](https://developer.apple.com/documentation/virtualization/adding-the-virtualization-entitlement-to-your-project) 的 Swift runner。原壓縮 kernel 使 VM start 回 `VZErrorDomain Code=1`；解壓後啟動成功。影像只快取於本機暫存目錄，repo 不保存下載的二進位。探針建立一個無網路裝置、只共享新暫存目錄的 VM；guest 以 `setsid` 啟動持 guest 檔案鎖、每 0.2 秒寫一次共享 heartbeat 的後代。guest 自查鎖被占用與子程序另有 session，host 另查 heartbeat 在運行中增加。這是有限的合成執行面，沒有測真實工具或任意命令。

同輪實測 [`stop`](https://developer.apple.com/documentation/virtualization/vzvirtualmachine/stop(completionhandler:)) 回呼成功且 VM state=0 後，heartbeat 停止；直接 SIGKILL host runner 後 heartbeat 也停止，重新啟動 VM 才恢復增加，舊 guest 的獨立 heartbeat 檔保持不變。**host 的 `flock` 對同一 virtiofs 檔案在 guest 持鎖期間仍可取得鎖**；再同時啟動兩台 VM 共用同一目錄與鎖檔，兩個 guest 都回報持鎖且各自的 heartbeat 增加。這個鎖不能跨 host／VM 協調單 writer，也不能用 host 鎖取得當作退場證據。

2026-11-08 的後續整合：runner 增加父程序獨占的控制管道，收到停止命令或父端消失時呼叫 VM stop，避免用舊 PID 發訊號。`vm_probe.py` 實跑控制管道 EOF 後的停止，並把一台仍寫 heartbeat 的合成 VM 接到 `managed_fixture.py` 的切換：先在私有資料庫記錄未確認 VM，再封住 epoch 0、回收單 worker、要求 VM stop、核對回呼及 heartbeat 穩定並保存證據，最後才啟用 epoch 1。若退場失敗或證據未保存，切換維持 pending；重啟拒絕把未知 VM 當成已退場。真 VM 探針另以 SIGKILL 父程序實測 guest 因管道 EOF 退場、但新父程序因無持久退場證據而拒絕恢復。

2026-11-09 再接一項固定合成操作：epoch 0／1 的整數乘法各由一台 guest 執行，結果經既有 outbox／broker 寫入合成工作樹。VM 退場紀錄改按 actor＋epoch 保存，兩筆退場證據都保留；舊 epoch 未送出的請求在退場後被拒。首次連續啟兩台的反例抓到啟動狀態只按 actor 更新、使舊列從 retired 倒退為 running；現改按 actor＋epoch 且只許 unconfirmed→running。

同日後續把這項合成操作的請求及結果移出 virtiofs 共享 scratch，改走 runner 配給該 VM 的第二個雙向 virtio console（`/dev/hvc1`）；parent 持有獨立管道端點，guest 不接觸正式工作樹。host 對回覆限制 128 bytes、核對請求 ID／epoch，逾時、截斷、錯 epoch 均拒絕。實跑第一次發現 TTY 回顯把請求當成回覆；guest 須在已開啟的 fd 上設 `raw -echo` 才能收到有效結果。真 VM 探針再次量到兩個 epoch 的結果經 broker 套用。離線負向測試在共享 scratch 放同名 symlink／hardlink 結果，確認 host 的算術結果只讀專用通道；這不證明同 UID host 不能干擾 runner 或 parent。VM 的正式寫入能力仍只有 parent broker，沒有直接掛載合成 repo。[Apple virtio console 文件](https://developer.apple.com/documentation/virtualization/vzvirtioconsoledeviceserialportconfiguration)說明雙向 file handle attachment 的介面。

2026-11-09 再加一條固定合成寫入路徑：parent 對同一 VM 的專用 serial 發出有 nonce／epoch／序號的算術命令，guest 執行後自己格式化受限的 `note` broker 請求。parent 限長 256 bytes 並核對 nonce、epoch、序號及固定 schema，將 guest 原始請求 bytes 寫入獨立 principal 的 `RequestJournal` 後才送 broker；channel 的資格與 `note` 範圍由可信 parent 簽發，票據不交給 guest。真 VM 探針在同一合成資料庫啟動 host worker 及另一 guest principal，確認寫入事件的 actor 是 guest 而非 host worker、檔案內容為 guest 計算的 `10`；前提進入 pending 後仍在運行的 guest 再送舊 epoch 請求，broker 留下拒絕收據且檔案不變。離線測試另驗額外 actor 欄位、錯 epoch、截斷回覆及 outbox 的原 bytes／重啟後重送。這是**單一固定 shell 操作**的管道歸因，不代表 guest 已持有通用工具或可信身分證明；parent 直接提供 guest 的計算輸入，沒有把模型上下文或受管工具搬入 VM。

2026-11-09 後續將固定 guest broker 寫入路徑改成無共享目錄模式：runner 不配置 virtiofs 裝置，guest 反向嘗試 mount `probe` 並要求失敗，也不啟 heartbeat 子程序；雙方啟動標記與專用 serial 就緒後才受理請求。真 VM 再跑 `guest_broker`，合成寫入與 pending epoch 拒絕仍通過；離線負向測試驗缺任一標記、guest 宣稱已 mount 或意外取得共享目錄會阻擋。其他 VM 退場、兩 epoch 與跨 VM `flock` 反例仍刻意掛可寫 scratch，用來量測原邊界；不能把固定 broker 路徑的無共享配置外推到它們。

2026-11-09 再將**固定合成受管程式**拆成 `vm_managed_worker.sh` 並封入 initramfs。無共享 guest 的 `/init` 設好 console 後執行它；worker 一次載入 epoch／factor，之後 parent 只送 value／序號／base，乘法與 broker 請求由 guest worker 完成。`guest_broker` 探針不啟 host worker，在 epoch 0 啟 guest、記原始請求、完成寫入；建立 pending 後，仍在運行的舊 guest 請求遭拒，未完成操作失效。確認舊 VM stop 後啟另一台無共享 VM，載入 epoch 1 的 factor，取得載入確認、application ACK 並啟用新前提；新 guest 寫入 `21`，私有日誌保留兩筆寫入的同一 principal、各自 epoch 及三筆原始請求。真 VM 探針 exit 0；離線負向測試另驗 context ACK 與 base 不符。這只把**固定 shell 工具**放進 VM，沒有模型或通用桌面工具，也沒有讓 guest 取得 broker 管理權或票據。

專用 console 讓請求與同一台 VM 的裝置連接，但不是防同 UID host 程序偽造的身分證明；可信 parent 仍可代送，故 actor 只能代表本合成管道的授權歸屬，**不是對任意實際操作者的完整歸因**。舊 `managed_vm_switch` 路徑仍借 host worker channel 並掛共享 scratch；新 `guest_broker` 是獨立的無共享 guest worker 路徑，不能把兩條路徑的證據拼成完整保障。新路徑的 VM stop 證據已由 `guest_runs.py` 持久記錄（見下段）；掛共享 scratch 的舊路徑仍有 guest 可直接改檔及已寫效果不回滾的問題。正式工作樹、外部網路／效果、host／hypervisor 崩潰、其他 OS、真實工具及成本尚未驗。父程序在保存證據前中斷時故意保持阻擋，尚無安全解除途徑。舊實驗庫的單鍵 VM 紀錄不自動遷移，應使用新合成 fixture 重跑。`VM_PROBE_OK` 只表示本機合成觀察完成，不解除 Mac 多程序工具的阻擋。

2026-11-08：`managed_fixture.py` 將 supervisor 的固定 worker 協定、guardian 和父程序 outbox 接到同一個 macOS 合成執行面。一鍵入口的 `managed_probe` 先在 epoch 0 留下一筆未送出的結果與一件執行中的工作，再寫入通知並封住 epoch 0。舊 worker 確認退場後，替代 worker 沿用固定啟動計畫，從管道讀取新前提並回報摘要；確認與啟用在同一交易完成。重送舊請求保留原始 bytes 並被拒，只有 epoch 1 的新結果寫到合成工作樹。`test_managed_fixture.py` 另驗停止未確認、載入舊前提、離線收件者與回應遺失。

2026-11-09 晚間補上無共享路徑的**持久 run 帳本** `guest_runs.py`。parent 在開機**前**於同一私有資料庫寫入 `starting` 列：parent 自訂 run id、probe id，以及實際交給 runner 的 runner 二進位、kernel、initramfs、`/init` 與工具腳本 SHA-256；host 確認無共享開機後轉 `running`，退場只接受 host 停機標記、相同 probe id 與 runner 結束碼 0，額外欄位一律拒絕。actor 只要有未退場列，就不能再開新 guest；application ACK 只接受 pending epoch 的唯一存活 run，寫入前也要該 run 是當前 epoch 唯一存活者。重開資料庫只讀帳本，未退場就 `vm-retirement-unconfirmed`，不看 PID、時間或 guest 日誌推定。真 VM `guest_broker` 改經帳本完成兩 epoch，關閉再重開資料庫核對兩筆退場與身分；新增 `guest_parent_sigkill` 在 guest 運行中 SIGKILL 父程序，VM 因控制管道 EOF 停止，但重開帳本仍保持 `running` 並阻擋重啟。`test_guest_runs.py` 的 6 個離線測試在 scratch 副本逐一移除 6 個守門條件，都會失敗。同輪發現 runner 的 stderr（host 標記）與 guest console 原本合寫同一日誌，guest 印出 `HOST_STOPPED state=0` 就能混進停機判讀；已改成 `launch()` 把 stderr 寫到另一個 `.host` 檔，所有 VM 探針的 host 啟動／停機判讀只讀該檔且要求整行相符，離線測試驗 guest console 的偽造行不被採用（移除分離後測試失敗）。再把 channel 與 run 生存期綁定：`mark_running` 要求該 run 的 actor 持有的 capability，帳本只存其 SHA-256；`require_live`／ACK 必須出示同一個 capability。退場在同一交易呼叫 `Lab.resume` 輪換 capability，所以舊 guest 的 channel 不只靠 parent 記得查帳本，而是 broker 本身以 `unknown-session` 拒絕；真 VM 在舊 guest 退場後用舊 journal 再送寫入，被拒且檔案不變，替代 guest 由 parent 重新 `connect` 取得新 channel。邊界：身分是 parent 選定檔案的 digest，不是 guest 實際執行內容的證明；host 檔仍由同 UID 可寫，不防 host 程序偽造；父程序在退場前崩潰時 capability 不會輪換（但持有它的 parent 已死，重開帳本仍阻擋），崩潰後的人工解除見下段。

2026-11-10 依決策書 Q1 (a) 補上**崩潰後人工解除** `crash_release.py`。parent 在開機前把 runner stderr 檔的絕對路徑寫進帳本（`open_run(..., host_log=...)`，舊帳本自動補欄位但沒有路徑，永遠不能解除）。解除工具先自己讀那個登記過的檔，不跟符號連結、只收一般檔、上限 64 KiB、純 ASCII，內容必須逐行等於乾淨無共享停機的四行（`HOST_NO_SHARED_DIRECTORY`、`HOST_CONFIG_VALID`、`HOST_STARTED`、`HOST_STOPPED state=0`）；不合格就 `crash-release-unconfirmed`，**根本不開終端問人**。有證據才開 `/dev/tty`（不讀 stdin，piped agent 答不到），有 `SSH_CONNECTION`／`SSH_CLIENT`／`SSH_TTY` 就拒絕，先清掉終端裡預先排隊的輸入，列出 run、actor、epoch、probe、日誌路徑與 SHA-256，要人照打一次新產生的 `release <run 前 8 碼> <挑戰碼>`。兩者都過，帳本 `release_crashed` 在同一交易把列改成 `retired`（證據記 `kind: crash-release`、host 證據與確認的 tty／時間）並輪換 capability；帳本自己再核一次欄位集合、probe、登記路徑、方法與 run id。用法：`python3 -X utf8 -m experiments.v2.crash_release DB RUN_ID`，exit 0 解除、1 拒絕且不變、2 用法錯。本 session 在 agent 殼層直接呼叫 `open_local_terminal()` 得到 `crash-release-no-terminal`。真 VM `guest_parent_sigkill` 在 SIGKILL 父程序、確認重開仍阻擋後，以真 runner 的 `.host` 檔加合成終端替身走完解除，並確認 guest console 日誌被拒；真 runner 輸出正好是那四行。另加真 VM `guest_crash_replay`：父程序在 guest 寫入請求已存進 outbox、還沒送出時被 SIGKILL，工作樹不變、重開帳本阻擋；解除後替代 parent 以同一 ticket `connect`、送出原 bytes，套用一次並歸到 epoch 0，第二次送是 `no-pending-request`。broker 本身不查帳本：重送的是 guest 存活時已持久化的原請求，舊 channel 已隨父程序消失；這不涵蓋 guest 在 parent 死後才產生的效果（無共享路徑沒有其他效果出口）。同日再加真 VM `guest_unread_request`：parent 對 guest 送出寫入命令，等 guest console 出現 `GUEST_TOOL_WRITE_REQUEST=<nonce>`（請求已產生）才 SIGKILL parent，此時請求 bytes 還在 parent 那端沒讀的管道裡；解除後替代 parent 以同一 ticket `connect`，送出得到 `no-pending-request`，`client_requests` 與 `writes` 都是 0、工作樹沒有檔案。也就是 parent 沒讀進 outbox 的 guest 輸出會遺失、不會被套用，代價是那筆工作要重做。parent 死後到 VM 停下之間 guest 若再產生輸出，出口是同一條已失去讀端的管道，這段時間沒有另外量測。`test_crash_release.py` 10 個離線測試；`mutants.json` 新群組 23 個刪改（含 `guest_runs` 既有 6 個守門）全部 killed。邊界：host 檔同 UID 可寫，同 UID 程式也能自己開偽終端並答題，所以這只抬高 agent 代答的門檻，**不是真人證明**；runner 在印停機行之前就被殺、或父程序在開機前崩潰而沒有 host 檔時，照 Q1 退回 (c) 維持阻擋；舊共享 scratch 路徑沒有解除；使用者日後要改成簽署金鑰（Q1 (b)），屆時另登新編號。

2026-11-10 補 hypervisor 程序異常：真 VM `guest_runner_sigkill` 在父程序**活著**時直接 SIGKILL VM runner（Virtualization.framework 跑在 runner 程序裡，殺它就是 VM 當場消失）。runner 來不及印 `HOST_STOPPED`，所以沒有 host 停機證據：`retire()` 與再送寫入都失敗，帳本留在 `running`，重開資料庫後 `require_quiescent` 與重開新 run 都是 `vm-retirement-unconfirmed`；`crash_release.release` 在讀 host 檔時就以 `crash-release-unconfirmed` 拒絕，**終端開啟函式一次都沒被呼叫**，帳本不變。這是 Q1 (a)「拿不到 host 證據就不放行、退回 (c)」的實測。沒有驗：host 整機崩潰或斷電（帳本與 host 檔可能一起停在任意狀態）、runner 印出停機行之後才被殺。

2026-11-10 再補 **host 整機崩潰的離線盤點** `test_host_crash.py`（7 個測試，沒有真的讓機器崩潰，也沒有新增守門；每個測試造出一種崩潰可能留在磁碟上的狀態，記錄現有帳本與崩潰解除怎麼處理）。量到的：(1) runner 紀錄在任一位元組截斷都不被當成停機證據，只有完整四行或只缺最後一個換行才收；整段補零、乾淨紀錄後面補零、停機行位置是零都拒絕，而且不開終端。(2) **host 在 run 中途死掉時，run 永遠阻擋、沒有任何解除途徑**：runner 跟 host 一起死，停機行從來沒寫出去，崩潰解除在讀 host 檔時就拒絕；開機確認前死掉也一樣。重開機後那台 VM 實體上一定不在了，但帳本裡沒有任何東西能證明這件事。要不要把「開機階段識別改變」當成 host 端證據，是決策書 Q15（2026-11-10 採 (a)，見下段）。(3) 停機行已寫出、runner 卻不是以 0 結束（印完才被殺）時，`retire` 拒絕，要走崩潰解除加本機終端確認；這只模擬帳本那一面，真 VM 上沒有量。(4) 帳本檔被截短（每 512 bytes 試一次）不是 SQLite 讀不了，就是仍讀到未退場而阻擋，沒有一種長度讀成「沒有東西在跑」。(5) **反例：帳本檔被刪或變成空檔時，讀起來跟第一次啟動一樣**，`require_quiescent` 通過；舊 principal 也不在了，所以要 parent 重新 `register` 才開得了 guest，但重新註冊後就回到 epoch 0。資料庫以外沒有任何東西記著「這裡曾經有一份帳本」，這是已知缺口，不是保障。同輪順手修：`crash_release.release` 對不存在的資料庫路徑原本會讓 `Lab()` 悄悄建一個空帳本，現在先拒絕（`unknown-guest-run`）、不建檔。沒有驗：真的斷電（SQLite `synchronous=FULL` 與檔案系統的耐久性是相信來的）、檔案大小不變的磁碟毀損。

2026-11-10 依決策書 Q15 (a) 補上 **host 重開機當解除證據**。parent 開機前除了 runner 紀錄路徑，也把這台 host 的開機識別（macOS `kern.bootsessionuuid`，用絕對路徑 `/usr/sbin/sysctl` 讀，只收大寫 UUID 格式）寫進帳本（`open_run(..., boot_session=read_boot_session())`；舊帳本自動補欄位但沒有值，就跟以前一樣沒有這條路）。`crash_release.release` 先照舊讀 runner 紀錄，**紀錄合格就用紀錄、不讀開機識別**；紀錄不合格而且有登記開機識別時，才讀現值：讀不到、格式不對或跟登記的一樣（同一次開機，VM 可能還在跑）都拒絕、不開終端；不一樣才算 host 端證據，照樣要 host 本機終端打挑戰碼，畫面列出登記值與現值。帳本 `release_crashed` 另核一次：`basis: host-reboot`、欄位集合、probe、登記值相同、現值是合格 UUID 且不同。`test_crash_release.py` 加 12 個離線測試（重開機解除、沒有紀錄也能解除、同一次開機或讀不到不問人、紀錄合格時不讀開機識別、沒登記就不看開機識別、只登記開機識別的 run、偽造證據、格式、舊帳本補欄位、讀取函式的失敗情況），`test_host_crash.py` 加 1 個（同樣的半截紀錄，有登記開機識別時同一次開機仍阻擋、重開機後可解除）；`mutants.json` 該群組 37 個刪改全部 killed（新增 13 個，另把因改寫而過期的 5 個對應原文更新）。真 VM `guest_parent_sigkill` 的 parent 現在會登記開機識別，探針確認登記值格式正確、而且同一次開機下用現值當重開機證據會被拒。邊界：**沒有真的重開機驗過**（現值不同只在離線測試裡用替身造出來）；開機識別本身同 UID 改不了，但登記值存在同 UID 可寫的帳本裡，能改帳本的程序本來就能直接把列改成已退場，所以這不比原有的崩潰解除更弱，也不更強；只證明「那個 VM 程序已不在」，不證明它停下前沒有產生效果（無共享路徑的效果出口只有 parent 的 outbox）。真人核准來源維持本機終端挑戰碼（Q16 (c)）。

2026-11-11 依決策書 Q19 (b) 補上**帳本錨點**。`GuestRunLedger(lab, anchor=<絕對路徑>)`：第一次開啟時先產生隨機帳本 id，寫進錨點檔（暫存檔 `O_EXCL`、0600、fsync，再用 `link` 放到目標名稱，已存在就 `ledger-anchor-conflict`、不覆蓋，最後 fsync 目錄），再在同一交易把同一個 id 存進資料庫。之後只有兩邊都在且相同才開：錨點在、資料庫沒有 id（檔案被刪、清空或換成新檔）是 `ledger-lost`；id 不同是 `ledger-replaced`；資料庫有 id 但錨點不見是 `ledger-anchor-missing`；錨點是符號連結、目錄、超長或格式不是整行 `GUEST_LEDGER <32 位小寫十六進位>` 是 `ledger-anchor-unreadable`；路徑非絕對或非正規是 `invalid-ledger-anchor`。拒絕時都不補寫任何一邊。沒給 `anchor=` 的行為不變（`test_host_crash.py` 保留原反例）；已有資料的舊帳本第一次帶錨點開啟時直接採用。`test_guest_runs.py` 加 9 個離線測試，`test_host_crash.py` 加 1 個（同樣的刪檔／清空，帶錨點時被拒，崩潰解除也不問人）；`mutants.json` 該群組新增 15 個刪改，52 個全部 killed。真 VM `guest_parent_sigkill` 的 parent 現在帶錨點（放在跟資料庫不同的目錄），探針在崩潰解除之後把帳本檔改名移走，重開得到 `ledger-lost`。解除拒絕是人工步驟：確認那份帳本沒有 guest 還可能在跑之後，手動刪錨點檔；沒有做成工具。邊界：錨點跟資料庫一樣是同 UID 可寫的檔，能同時刪兩者的程序照樣回到第一次啟動，所以這只擋**意外遺失**，不擋刻意刪除；錨點與資料庫在同一個檔案系統時，整個目錄樹一起不見也擋不住；耐久性靠 fsync，跟帳本一樣沒有真的斷電驗過。

**P0 Mac 這半邊在 2026-11-11 依 Q19 收尾**，以合成原型加下列已知缺口清單作結，不是全部退出條件都達成：真的斷電與檔案系統耐久性沒驗；真的重開機沒驗（Q15 只有離線替身）；帳本錨點只擋意外遺失；通用工具進無共享 guest 屬 P3 的 M3 隔離；簽署金鑰發行／撤銷與額度來源沒做；Swift runner 沒有離線測試、guest 腳本離線測試不是 busybox ash；真人核准只是本機終端挑戰碼，不是真人證明。Windows 那半邊照 Q12 留到之後。

**舊共享 scratch 路徑的定位（2026-11-10 決定，依 Q5 (a) 收尾 P0 時做的取捨）**：`managed_vm_switch` 那條路徑（host worker 經 serial 請 guest 計算、guest 另掛可寫 virtiofs 寫 heartbeat）**不修、不冪等化**，定位為已被取代的退場閘門實驗，只證明「舊 guest 停下才啟用新 epoch」，**不作 F11 寫入或歸因證據**。理由：它要驗的兩 epoch、退場證據與舊 channel 拒絕，`guest_broker`＋`guest_runs` 已在無共享模式驗過；把它改成無共享，等於在 `managed_fixture` 裡重做一次同樣的路徑，而且 heartbeat 證據本來就需要共享目錄。它仍留在一鍵探針裡，作為 supervisor 與 VM 閘門整合的回歸。

同一 fixture 的 `resume` 在持久退場證據通過後，從持久初始前提或同一 principal 的通知重建上下文。若切換尚未提交，仍用原 pending epoch 與通知完成切換；若前提已生效，恢復該 epoch 並作廢中斷的計算，已保存的請求仍按原 bytes 送出。測試用真正的 SIGKILL 在初始／新 epoch 執行中、切換後舊 worker 尚未停、替代 worker 已載入但啟用交易尚未提交四處中止。只有既有資料庫、計畫、票據與原目錄的回收紀錄都可核對時才恢復；多程序工具、跨機推送、裝置遺失與真實 surface 另驗。

## POSIX 工作樹套用與中斷恢復（2026-11-07）

`materializer.py` 將受理的內容事件套用到 parent 預先指定的合成工作樹：既有內容先由可信 parent seed；事件保存前後文與 epoch，寫盤前另提交 prepared 意圖，暫存檔寫完並 fsync 後同目錄 replace，再 fsync 目錄並記 applied。Broker 在這條鏈完成前只回 materialization-pending，不以「內容庫已受理」冒充檔案已完成。同資源前一筆未套用時拒絕新變更，避免計畫內容繼續往前而磁碟落後。

資源對路徑的映射由 parent 提供，不接受 agent 任意路徑。只支援已存在目錄下的普通檔案；使用 dir_fd／O_NOFOLLOW 拒絕 symlink、拒絕 hardlink、父層跳脫與 .git，保留普通檔案 mode。映射以 NFC＋casefold 保守拒絕可能的同檔別名（即使某個大小寫敏感檔案系統能分開，這個原型也不接受），避免兩個 resource 其實指向同一個檔案。暫存名依事件保留在受保護目錄；中斷後可以重建暫存內容。恢復時磁碟仍是 before 才繼續替換，已是 after 則完成收據；內容／mode 不符、epoch 已失效或恢復 phase 不明都停止。已 applied 的舊收據只表示過去那筆已完成，不把較新內容改回舊版。

恢復邊界覆核補強（2026-11-07）：重送已受理的寫入仍須符合當前 channel 的資源範圍；parent 重連時縮權，不能靠舊收據繼續寫盤。拒絕不改原收據，恢復授權後可用同一請求完成。資料庫在首次綁定時保存 root 的 device／inode 與完整資源映射，重啟改映射或換工作樹會拒絕；每次開 root 也核對身分。已有事件但沒有綁定的舊實驗庫不自動收編；尚無搬機、換根目錄或增減映射的遷移程序，需另行設計。恢復看到 after 內容後仍須 fsync 目錄，成功才記 applied；否則維持 pending，不能把可見內容當成已耐久套用。

`test_recovery.py` 用真正的獨立子程序 `os._exit`，分別在 prepared、暫存檔同步、replace、applied 提交後終止，再開資料庫／新管道恢復同一請求；檢查一筆事件、一份收據、正確內容、mode 與無殘留 staging。另驗效果在收據前終止會回滾、丟失回應後不重扣合成額度、收據或 commit 失敗不留下可晚點誤提交的交易、外部變更不覆蓋、失效 epoch 不寫盤與 symlink／hardlink／未知 phase 拒絕。受隔離 agent 整合探針也已接上 materializer：可經代理更新 managed 檔，直接寫仍被拒絕。

**適用邊界**：只在 POSIX 合成且由 broker 獨占的工作樹驗收，不是多 writer 的原子 CAS。外部程序若能在檢查與 rename 間改目錄／檔案，仍超出此保障，必須由 OS 隔離排除；不宣稱能歸因外部寫入恰好與 after 相同的內容。不支援自動建立目錄、刪除、整批檔案交易、真實專案遷移或 Windows。SQLite FULL 與 fsync 加上程序終止測試不是實測斷電；磁碟毀損／設備遺失仍未驗。尚未接 Gitleaks 或完整提交／發布代理，不能把可套用檔案等同敏感資料不進 Git。

## M3 開工／收尾閘門（2026-11-09）

`gitclaim.py` 是 F9／F10 的原型，對真 Git 判定，不讀聊天或本機 HANDOFF。`assess_start` 先確認站在追蹤自己遠端同名分支的分支上，再 fetch；fetch 失敗一律 `fetch-failed`，即使舊 tracking ref 看起來對齊且空閒。之後依序拒絕未知 dirty（含未追蹤檔）、分岔、ahead-only、落後（要先 ff pull 再重判）；占用只看遠端那一份 HANDOFF 的「工作中」欄位，缺欄、重複或空值算 `owner-unknown`，不當成空閒；只有空閒或完全等於本 session 的標記才放行。被占用時把標記拆成機器／工具／session 三欄，分別回報別台機器、同機別工具、同工具別 session（含缺 session）與無法辨識工具的兩欄舊格式；空白欄、缺反引號或欄位後有雜訊算 `owner-unknown`，遠端查不到則是 `fetch-failed`（F4）。自己要寫的標記也必須是完整三欄，否則 `invalid-owner`。`finish` 不收布林值，只收 `run_check` 的檢查收據：在乾淨工作樹上執行驗證，記結束碼、行首 `skip` 行數與當時的 HEAD tree，執行中改動工作樹就不給收據；收據為空、非零、有 SKIP 或 tree 不是現在的 HEAD tree（驗證後又 commit）都拒絕（F19）。另要求工作樹乾淨、HEAD 的標記已釋出，fetch 後遠端不能有 HEAD 沒有的 commit，push 不 force；推送後再 fetch，遠端等於 HEAD 且標記已釋出才回傳 `session.py` 的 `HandoffReceipt`，F50 計數因此只在真的交棒成功時加一。

`test_gitclaim.py` 用本機 bare origin 與多個 clone 實測 16 個情境（含檢查收據與占用代碼）：乾淨對齊、ahead-only／分岔／落後、離線（搬走 origin 而 tracking ref 仍在）、未追蹤與已追蹤變更、無 upstream／追錯分支／detached、本機空閒而遠端他人占用、自己的標記、缺／重複／空的欄位、兩條分支各自占用互不阻擋而同一分支第二個 writer 停止（標記再舊也不當租約到期，F25）；收尾端測成功（收據只計一次）、遠端前進時不推、pre-receive 拒絕、離線、推送後被另一 writer 搶占。scratch 副本逐一移除 22 個守門，21 個讓測試失敗；剩下的推送後「標記已釋出」再查在邏輯上由推送前的 HEAD 檢查蘊含，沒有輸入能單獨觸發，已在程式註明。邊界：這是協調檢查不是原子 claim，判定到推送之間仍有時間窗；只在 macOS 本機 Git 跑過，未接進現行 A／B 程序或任何工具。

`batch.py` 在其上做 F30 的批次彙總：每個輸入目標恰好列一次，archived 列為 excluded，重複、缺失、未知狀態、被拒或非預期例外都算失敗且不中斷其他目標；有失敗或一個都沒處理就不是 ok。`test_batch.py` 用 20 個真 Git 目標（14 正常與 6 種例外／失效）實測，摘要為 `NOT OK: 14 eligible, 5 failed, 1 excluded of 20 listed`；移除 8 個守門都會讓測試失敗。它只彙總開工資格，不取代 `sync_project.py` 的同步批次。

## M1 整包 manifest 與逐次寫入確認（2026-11-09）

`release.py` 是 F18／F32／F33 的原型。`build_manifest` 對一份來源樹列出每個元件的 SHA-256（路徑不得逃逸、不得是 symlink），整包 digest 取 canonical JSON；所以只改 hook 或 schema 時，版本字串不變也會得到不同 digest。`WriteGate.confirm` 在**每次**受管寫入前產生新 nonce，向可信端要一份用 ssh-keygen 簽的 channel 聲明（channel、epoch、manifest digest、nonce、簽發與到期時間），依序驗簽章與 namespace、channel 名、nonce、時效、epoch 不倒退、manifest 與本機一致、正式版，最後重算本機元件 digest。程式沒有任何快取路徑：拿不到聲明就 `channel-unreachable`，重播先前合法的聲明因 nonce 不符而 `stale-confirmation`。

`test_release.py` 7 個測試用拋棄式 ed25519 金鑰實測：每次寫入都重新確認；離線與重播；就地改元件（F32）；只改 hook 或 schema 的新 release 讓舊客戶停止（F18）；他人金鑰、錯 namespace、竄改、錯 channel、過期、未來簽發、型別錯、epoch 倒退、調試版。scratch 副本逐一移除 12 個守門都會讓測試失敗；原本的「開頭為 `/`」檢查被空片段檢查涵蓋而無法單獨測，已刪除。邊界：可信端與金鑰是測試替身，沒有 CI 身分、金鑰治理、網路傳輸或原子安裝；沒有接進現行 `git-freshness.sh`、`sync_project.py` 或任何工具，現行 720 分鐘快取照舊。

## 受管寫入前檢查（2026-11-09）

`preflight.py` 把上面兩個原型組成一次寫入前的檢查。`assess_start` 問的是「能不能開工」，要求乾淨工作樹；寫入卻發生在開工之後、工作還沒提交時，所以另有 `assess_write`：每次都先 fetch，遠端標記必須**正好**是本 session（空閒回 `not-claimed`，他人照 F4 的占用代碼），落後回 `behind-pull-required`、分岔回 `diverged`；未提交與尚未推送的本機工作是預期狀態，不擋。`ManagedWrite.check(operation)` 先跑 Git 再跑 `WriteGate.confirm`，拒絕代碼帶 `git:` 或 `release:` 前綴標明是哪一層；Git 已拒絕時不消耗發布確認。兩層每次都重查，沒有快取。`batch.assess_many` 多一個可選的 `confirm(path)`：Git 乾淨對齊但套件漂移的目標記為 `failed`／`release:<代碼>`，不算 eligible。

`test_preflight.py` 8 個測試用真 Git 與拋棄式 ed25519 金鑰：持有者帶未提交／未推送工作可寫；空閒、他人、同工具別 session、標記不可讀、無效 owner 都拒絕；開工後被他人搶占時本機 HANDOFF 仍寫著自己，寫入檢查以落後／分岔擋下；離線不用舊 tracking ref；每次寫入都要新確認；通道離線、元件就地改動在 Git 通過時以 `release:` 拒絕；批次的漂移目標與 confirm 例外。scratch 副本逐一移除 11 個守門，10 個讓測試失敗；剩下的是批次失敗列的 `pop('manifest')`，manifest 只在確認成功後才寫入，那兩行是死碼，已刪除。邊界：仍是協調檢查不是原子 claim，檢查到寫入之間有時間窗；簽章端與金鑰仍是測試替身；沒有接進任何工具的寫入入口。

## F12 並行線不共用工作樹（2026-11-09）

`lines.py` 的 `assess_lines` 檢查一份登記的並行線（線 ID、checkout 路徑、宣告分支）。判定靠 Git 自己回報的 toplevel、index 路徑與目前分支，不比路徑字串，所以子目錄、symlink、複製過去指向別線 git dir 的 `.git` 檔都會被認成同一棵樹或同一個 index。同工作樹（`shared-worktree`）、同 index（`shared-index`）、同分支（`shared-branch`）的每條線都標記；宣告分支與實際不符（含 detached）是 `branch-mismatch`；非 checkout、重複或空線 ID 也各有代碼；每條線恰列一次，有任何代碼或沒有線就不是 ok。不同分支不是豁免：在同一棵樹裡切分支，另一條線的未提交檔與 staged 內容會被一起帶走。

`test_lines.py` 5 個測試用真 Git：`git worktree` 與獨立 clone 是合格的獨立線（一邊 stage 後另一邊 `status` 仍為空）；同樹換分支、子目錄、symlink、複製 `.git` 檔、detached、不存在、非 repo、重複 ID。scratch 副本逐一移除 9 個守門，7 個讓測試失敗；另兩個（路徑 realpath、先檢查目錄存在）由 Git 本身涵蓋，已刪除，並另以未解析的 `/var` 暫存路徑確認 symlink 仍判同樹。邊界：只偵測不鎖；登記表由呼叫端提供，沒經過登記直接進同一資料夾的 agent 擋不到；未接進任何工具。

## F23 只讀輪次不留狀態（2026-11-09）

`readonly.py` 的 `read_only(repo, action)` 在回答前後各取一次快照比對：本機 branch／tag ref 與 HEAD、index 檔的 SHA-256、每個變更或未追蹤檔的內容 hash、遠端 `ls-remote`。回答可以 fetch，所以 remote-tracking ref 不比。快照全程用 `git --no-optional-locks`，否則 stat 過期時光是 `status` 就會改寫 index，造成假的 `index-changed`。遠端列不出來（離線、無 upstream）記 `unverified`，不當成沒變；遠端變了只報 `remote-changed`，分不出是本輪推送還是別人並行推送。回答拋例外時報告掛在例外的 `read_report` 上。

`test_readonly.py` 5 個測試用真 Git：讀檔／log／fetch 乾淨、stat 過期不誤報；寫標記、對已改檔再改、stage、commit、push、新增檔、開分支、只建 ref、只 detach 各被指出；離線、無 upstream、非 repo 都是未驗證。scratch 副本逐一移除 12 個守門都讓測試失敗。邊界：只偵測不阻擋，session 改名、Git config 與 repo 外的檔案不在比對範圍；未接進任何工具。

## M2 狀態模型與 HANDOFF 視圖（2026-11-09）

`state.py` 是 F1／F2／F5 的原型：目標（需求 ID、決策版本、人類決策來源）、任務（狀態、證據、卡點）、有序下一步與風險（已知壞掉／未知／風險／已知正常）存成資料。`check` 回傳 `(位置, 代碼)`：目標缺、空白、無 ID、ID 不在決策書、決策版本不是現行版、來源不存在都讓目標「未驗證」——非空不等於正確；完成無證據、證據不存在、卡住無原因、已完成卻列在下一步、開放任務沒排入、下一步引用不存在的任務都會被指出；宣稱已知正常或已知壞掉卻沒有證據時改顯示為「未知」。`render` 從同一份資料生成 HANDOFF 的目標、已完成、下一步、地雷四節，代碼標在對應項目旁；已完成的任務不論 `next` 怎麼寫都不會出現在下一步，沒排入的開放任務另列不消失。

`test_state.py` 4 個測試用合成決策書；寫測試時抓到視圖兩個真錯（開放任務沒排入時從視圖消失、重複 ID 讓後者蓋掉已完成的前者），已修。scratch 副本逐一移除 29 個守門都讓測試失敗。邊界：只用標準函式庫、未選 schema 函式庫；證據檔存在不等於命題為真；現行 HANDOFF 仍是手寫，沒有從模型生成或回頭核對；未接進任何工具。

## M2 證據帳與事實 adapter（2026-11-09）

`evidence.py` 是 F3／F40 的原型。每個要宣稱的項目由證據紀錄決定，報告固定分成本輪實查、沿用、未驗證、不通過四組。本輪紀錄直接採用；沿用紀錄必須有來源、取得時間、範圍，以及它依賴的每個輸入（`file:<相對路徑>`、`env:<名稱>`）當時的 digest，現在算出來不同就 `expired`、讀不到就 `dependency-unreadable`；使用者可撤銷。依賴以名稱加內容 digest 記錄，改名無關檔案不會誤失效。SKIP／NOT_CONFIGURED／無紀錄是未驗證，FAIL／ERROR 是不通過；只要有一個宣稱不是本輪實查或有效沿用，整體就不是通過。較新的紀錄無效時照實報原因，不退回較舊的通過。

`facts.py` 是 F20 的原型。宣稱帶文件、命題文字、adapter 與預期值；adapter 對真 Git 與檔案唯讀實查（目前分支、工作樹乾淨、檔案存在、檔案內容），結果為一致、不一致（列出文件、命題、預期與實際值）或未知。沒授權、沒有 adapter、查詢失敗都是未知，不算一致；repo 外的路徑即使檔案存在且內容相符也拒絕。`handoff_claims` 從 HANDOFF 的實際欄位格式取出骨架版本與待續分支。

`test_evidence.py` 5 個、`test_facts.py` 5 個測試；scratch 副本逐一移除守門，證據帳 19 個、事實 adapter 10 個都讓測試失敗（補強過的兩處：逃逸路徑改指向真實存在的檔案、補 index 不被改寫的測試）。邊界：依賴清單由產生證據的一方宣告，漏列的輸入改變不會失效；撤銷清單的保存未實作；adapter 只有四個本機查詢，服務與遠端狀態未涵蓋；不保證識破偽造紀錄；未接進任何工具。

## 待決事項與已宣告例外（2026-11-09）

`decisions.py` 是 F44／F34 的原型。`check_decisions`：待決事項要有問題、影響的需求 ID 與選項；AI 只能在使用者授予、有來源、範圍涵蓋全部影響 ID 的委任內定案，而且要記理由，否則 `ai-decided-without-delegation` 或 `delegated-without-rationale`；反過來，委任範圍內的事項不能掛成待使用者決定（`delegated-but-waiting-for-user`）。任務標了 `waits_for_decision` 就必須指向已登記且仍待決的事項，問題不能只藏在任務欄位裡。`check_exceptions`：例外要有內容、授權者、來源、範圍、理由與重檢條件，日期型重檢到期就標出。`render` 生成「懸置事項」與「已宣告例外（宣告不等於通過）」兩節。

`test_decisions.py` 6 個測試；scratch 副本逐一移除 25 個守門都讓測試失敗。邊界：只能檢查已登記的內容，完全沒登記、只在聊天裡的待決事項發現不了；委任範圍以需求 ID 比對；現行決策書第 6 節、HANDOFF 懸置節與 ARCHITECT 的三項來源例外仍是手寫，尚未轉成紀錄；未接進任何工具。

## 所有權與只能加嚴的覆寫（2026-11-09）

`policy.py` 是 F36／F37／F38 的原型。`plan_update` 用發布清單（每個路徑標 `core` 或 `adapter`）加上專案宣告的 project-owned 清單規劃更新：本機仍等於舊發布的檔案才取代，專案檔保留，受管目錄下沒人宣告的路徑（`ownership-unknown`）或被就地改過的發布檔（`released-file-edited`）一律停止，不猜。`merge` 只接受 schema 宣告的空位，並只能往宣告的方向加嚴（清單只增、下限只升、上限只降、開關只開）；mandatory 沒有覆寫入口，即使覆寫值相同也拒絕；未知欄位與型別不符拒絕，不產生有效政策。`check_schema` 先擋 schema 本身：方向未知、效果（restrict／permit）未確認、或方向與效果不一致（例如只增不減的**允許**清單）都不能當空位——位置合法不等於語意加嚴。`describe` 列出可填空位與不可改部分。

`test_policy.py` 7 個測試；scratch 副本逐一移除 24 個守門都讓測試失敗。邊界：只在合成清單與 schema 上驗證；現行 `sync_project.py` 與骨架都沒有改用這套清單與 schema，專案仍能直接改 skill／hook 原檔；「效果」靠 schema 作者宣告，宣告錯了發現不了；未接進任何工具。

## 改動影響圖（2026-11-09）

`impact.py` 是 F31 的原型。元件→需求的對應直接從 `status.json` 的證據路徑讀出（含子項），不另維護一份會漂移的手寫圖；支持同一需求的 `test_` 檔就是重驗點；專案宣告安裝了哪些元件，決定受影響專案。只要有一個變更路徑沒有需求或專案認領，就回全驗（全部需求、測試、專案）並列出那些未分類路徑，不回一個空的、看似安心的集合。

`test_impact.py` 4 個測試，其中一個讀真實的 `status.json`；scratch 副本逐一移除 8 個守門都讓測試失敗（原本「改到的測試本身也列入」那一行因為已被需求對應涵蓋，刪掉了）。邊界：粒度是檔案；2026-11-10 起除了 `__init__.py` 與 `status.json` 本身（改它們刻意回全驗），每個 v2 檔都被某個 ID 認領，`test_every_v2_file_is_claimed_except_the_index_itself` 守住新增檔不被漏列；較早的實作檔是以「實作檔、行為證據見同 ID 測試」認領，不是額外證據；專案安裝清單由呼叫端提供，未接 `sync_project.py`。

## 可重跑的 mutation 檢查（2026-11-09）

本輪各節提到的「scratch 副本逐一移除守門」原本只存在聊天暫存檔，換機就拿不到（F49）。現在刪改清單存在 `mutants.json`（每項記檔案、原文、替換與要跑的測試模組），`mutants.py` 在暫存複本逐一套用並跑測試，結果分 killed、survived、stale（原文不是恰好出現一次，代表規格過期）；只有全部 killed 才 exit 0，工作樹不被改動。

```bash
python3 -X utf8 src/project_bootstrap/mutants.py
```

2026-11-09 macOS 實跑：144 個全部 killed（之後加入 `doctor.py` 的 8 個，單獨跑也全部 killed，共 152 個），約 90 秒；先前 `lines.py` 刪掉的兩段冗餘守門對應的刪改已從清單移除（執行器把它們報為 stale）。`test_mutants.py` 用合成套件測執行器本身。邊界：只涵蓋本輪新增模組，較早模組的 mutation 仍只在上文敘述；刪改由人挑選；太慢，不在 `verify_v2.py` 預設流程。

2026-11-10 把較早五個模組轉進清單：`gitclaim` 29、`release` 20、`session`＋`registry` 27、`approvals` 26、`broker` 22 個。第一次試跑就有 33 個存活，多數是沒測到的輸入檢查：`broker` 的逐項錯誤代碼（原測試只驗「不是 ok」）、授權撤銷關閉 channel、落盤前重查授權；`release` 的金鑰格式、超長與多欄位聲明；`session` 的建構檢查（起始時間、主題長度與分隔字元、次數、狀態、重複事件）與空 event_id 的收據；`approvals` 的文件形狀（長度、多欄位、十六進位欄位、resource、uses、時間範圍）、金鑰格式、空或超長簽章不得叫起驗證程式、持久化的驗證程式 digest、核准時重查 policy、核准紀錄在而 grant 遺失、已有未簽 grant 時拒裝 policy。已補測試，全部 killed。兩個存活是等價變異未列入：缺檔時 `owner_field('')` 本來就回 None；推送成功後遠端不等於 HEAD 在合成環境造不出來（程式已註明）。同日全量 443 個 macOS 實跑全部 killed（約 6 分鐘），之後加入的 `trail_sources` 7、`broker` 22 個單獨跑也全部 killed，清單共 472 個。launcher 試跑 28 個有 19 個存活（票據長度、範圍與期限輸入、續期條件與 transaction 要求、pipe 授權比對 actor 與範圍、journal 對關閉／撤銷 channel、請求形狀、journal 與收據一致性），`test_launcher.py` 補 6 個逐代碼測試後全部 killed，清單共 500 個（2 個續期守門原本只有 3 分鐘的 lifecycle 測試殺得到，改由新測試直接打）。`materializer` 試跑 25 個有 16 個存活（映射輸入、seed 的特殊權限與重複、事件 id、缺 epoch 證據、狀態指向別的資源、準備階段的 epoch／大小／磁碟基準、模式改變、不安全暫存檔、暫存後晚到的修改），`test_recovery.py` 補 7 個逐代碼測試後全部 killed，清單共 525 個；其中模式衝突原本被後面的二次檢查兜住，差別只在會留下暫存檔，所以測試改斷言「拒絕前不建暫存檔」。lifecycle、supervisor、guardian 與 VM 相關檔仍只有上文敘述。

2026-11-10 再轉進三個生命週期模組並補測試：`supervisor` 11 個（首跑 12 個裡 9 個存活：原測試只驗「有拒絕」不驗代碼，補 4 個逐代碼測試，含謊報 epoch 的真 worker 與停不掉的程序替身；`old-context-still-running` 被 `stop()` 先擋、屬冗餘，不列）、`guardian` 10 個（原本只經 lifecycle 間接測到，新增 `test_guardian.py` 9 個直接驅動 `guardian.py` 子程序的測試：父端先死不啟動、期限已過、EOF 與意外資料都停、忽略 SIGTERM 的子程序在寬限後 SIGKILL、guardian 被 terminate 仍回收、worker 不繼承控制描述元）、`lifecycle` 26 個（首跑 27 個裡 20 個存活，補 `LifecycleCodeTests` 7 個逐代碼測試；`launcher.ticket` 的 handle 檢查與 vault 重複、屬冗餘，不列）。HANDOFF 原記 lifecycle 測試約 3 分鐘，實測整個模組約 5 秒。另加崩潰解除 23 個與 F45 版本規則 3 個。全量 595 個（不含其後加入的 F45 版本規則 3 個）macOS 實跑全部 killed，版本規則 3 個以 --spec 單獨跑全部 killed。

2026-11-10 把 VM 探針相關的兩個 Python 檔轉進清單。`vm_probe` 38 個：首跑 26 個存活——離線測試只驗過幾個代表情境，沒有逐條打 host 停機行要整行相符、無共享就緒的 channel 與 probe id、共享 guest 的鎖／channel／probe id／heartbeat 下限與前進、讀回覆的程序結束／逾時／超長、結果與請求的整行格式和 nonce／序號、各操作的存活與輸入範圍檢查，以及退場要 runner 結束碼 0 並記最後 heartbeat；`test_vm_probe.py` 補 10 個逐代碼測試後全部 killed。原本「讀到 EOF」的刪改會讓測試無限等待（10 分鐘逾時才算 killed），截斷測試改用有限期限後幾秒就失敗。`managed_fixture` 37 個（每個「條件成立就拒絕」的守門自動產生，加 16 個只拆掉複合條件一半的）：首跑 30 個存活，`test_managed_fixture.py` 補 9 個逐代碼測試（輸入範圍與就緒、每個 epoch 只接一個 gate、帳本列未退場或已記錄、接 gate 先查 worker、啟動或退場期間帳本列被改、guest 與 worker 結果不符、worker 回覆格式、逾時與卡住的 reader、恢復時 pending 通知的一致性），並在既有的崩潰恢復測試加斷言：未完成工作在帳本被標為 `invalid`（原本只驗 `complete` 被拒，而拒絕另有原因，刪掉標記那行測試照過）。兩組以 `--spec` 單獨跑全部 killed（約 20 秒與 2 分鐘），清單共 673 個；其後 `trail_sources` 的 AGENTS 規則轉接 7 個（見下文「規則理由」節）單獨跑全部 killed，共 680 個。邊界：`vm_runner.swift`、`vm_guest_init.sh`、`vm_managed_worker.sh` 沒有離線測試，只由真 VM 探針覆蓋，不在清單；2026-11-10 全量 673 個 macOS 實跑全部 killed（約 14 分鐘）。

2026-11-10 稍晚替兩支 guest 殼層腳本補離線測試 `test_vm_guest_scripts.py`：把腳本複製一份，只做兩個替換（`/usr/bin/busybox` 換成殼層內建的 `command`、`>/dev/hvc0` 換成附加到暫存檔），在 host 的 `/bin/dash` 與 `/bin/sh` 各跑一次，回覆直接餵給 `vm_probe` 的 `read_guest_context_ack`／`read_guest_write_request`，所以兩邊任何一邊改了線上格式都會失敗。**第一次跑就量到受管工具的數字檢查有洞**：原本只檢查字元集合，`1-2` 會被當成運算式算出 `-3` 寫進請求，單獨一個 `-` 會讓殼層算術出錯、整支 worker 結束（在 guest 裡它是 PID 1），`010` 會被當八進位。host 那一側本來就只送整數，所以要 parent 有錯才碰得到；兩支腳本都改成先用 `is_uint`／`is_int` 驗（純十進位、不准前導零、最長 6 位），真 VM `vm_probe.py` 重跑 exit 0。舊共享路徑在 `vm_guest_init.sh` 尾端的請求迴圈另外抽出來測（fd 3 用一條雙向 socket 代替 `/dev/hvc1`）。`mutants.json` 新增 18 個刪改，單獨跑全部 killed，清單共 713 個（另含崩潰解除的缺資料庫守門 1 個）。同輪在真 VM 探針加 `runner_refusals`：對真的 runner 執行檔驗參數個數錯、通道描述元不是數字、控制描述元不是數字、kernel 不存在都以非 0 結束且不印停機行；VM 開起來後往控制管道寫一個不是停止命令的位元組，runner 以 7 結束、印 `HOST_INVALID_CONTROL_MESSAGE`、沒有停機行，`crash_release.host_evidence` 拒收那份紀錄。邊界：離線測試跑的是 dash／sh，不是 guest 的 busybox ash；`vm_guest_init.sh` 的掛載、virtiofs、序列埠設定與 `vm_runner.swift` 的其餘路徑仍只有真 VM 探針覆蓋，Swift 檔不在刪改清單。

## 本機能力診斷（2026-11-09）

`doctor.py` 是 F16b 的原型。`diagnose` 把三種缺口分開報：缺工具（PATH 上找不到）、缺設定（環境變數沒設或只有空白）、連線失敗（工具與設定都在，probe 卻沒回 `True` 或拋例外）。缺前提的連線不呼叫，記 `not-attempted` 並列出缺什麼，所以沒設金鑰不會被誤報成服務掛掉。設定只看名稱有沒有值，值本身與例外訊息都不進報告。`test_doctor.py` 2 個測試；`mutants.json` 8 個刪改全部 killed。邊界：清單由呼叫端提供，還沒列骨架實際需要的工具與設定；只看環境變數，不查設定檔。

## 跨文件矛盾偵測（2026-11-10）

`contradictions.py` 是 F45 的原型，只比對宣告過的規則表與待決登記，不判斷任意散文。每條規則列出各說法的正規式與正確說法：寫成反向說法的位置報 `reverse-rule`（文件、節、行號），同一檔不同節說法不同報 `section-conflict`，不同檔說法不同報 `cross-doc-conflict`。待決部分讀決策書第 6 節的登記列（`- **Q1** … 狀態：待決／已決`）：HANDOFF 懸置節每一條都要引用仍待決的編號，否則 `pending-unregistered`；已決編號在懸置節或任何文件與「待決／待使用者決定」同行出現就報 `decided-still-pending`。讀不到的文件、必須出現卻沒出現的規則、缺登記節都是未知，不算通過；程式碼區塊與呼叫端標為歷史的節會跳過，但跳過的行數照列。部署包的範本放在程式碼區塊裡，所以對它設為照掃。

`REPO_CONFIG` 是本 repo 的宣告表（核心優先序、需求數、工作中標記不是互斥鎖、序號跟版本行不保證同號四條規則、決策書第 6 節、HANDOFF 懸置節；ARCHITECT 開頭的日期紀錄行與決策書第 7 節當時的決定標為歷史，照列跳過行數），`python3 -X utf8 experiments/v2/contradictions.py` 直接對本 repo 跑。2026-11-10 第一次跑就抓到一處：HANDOFF 懸置的「崩潰後人工解除的可信核准來源」沒登記，決策書第 6 節卻寫「無」；已補登為 Q1，HANDOFF 改成指向它。同日加入需求數規則，抓到 ARCHITECT 根目錄表仍寫決策書「50 條需求」（決策書是 51），已更正。`test_contradictions.py` 16 個合成測試、`test_contradictions_repo.py` 對本 repo 文件要求未發現，並把每條規則的反向句注入真文件副本確認會報（2026-11-10 加後兩條時，序號規則初版把部署包兩處引述舊說法的括號句當成主張，改成同一子句、中間不跨引號或括號才算）；`mutants.json` 24 個刪改全部 killed。2026-11-10 再加「版本行與 `VERSION` 只跟著 `SKILL.md` 走」：反向說法是「改到範本／hook／部署包就要跳 VERSION」或「VERSION 跟著 source 標記」，同一子句才算，緊接 」 結尾的引述與「不跟著動」不算；本 repo 未發現，注入反向句會報，新增 3 個刪改全部 killed。prompt 名稱已由 `verify_bootstrap.py` 的「結構摘要一致性」守，未重複加進宣告表。邊界：只認宣告過的說法，換個寫法就看不到；登記列格式固定；HANDOFF 懸置每條都要引用編號，之後交棒寫懸置節要照這個格式；未接進現行 A／B 程序。

## 規則理由、否決路線與路線圖（2026-11-10）

`trail.py` 是 F6／F7／F8 的留痕原型。決策紀錄仿 MADR：編號、標題、狀態（採納／被取代／否決）、日期、當時基準、理由，以及考慮過的替代方案（每個要有結果與理由）。規則記它出自哪個決策，`why` 從規則走到理由；決策被取代時，取代關係必須雙向，`why` 會從舊的一路走到現行的，舊理由仍看得到，規則還引用被取代或被否決的決策則報出。`rejected_routes` 列出所有沒走的路與理由。`compare` 拿舊快照比新快照：決策或替代方案消失、理由被改寫都報出——理由變了要新增一筆取代它的決策，不是改舊的。路線圖由里程碑（目標、狀態、放棄須附理由）組成，任務引用里程碑；沒有進行中或規劃中的里程碑、任務掛在已結束里程碑上都會報。

`test_trail.py` 10 個合成測試；`mutants.json` 24 個刪改全部 killed。

`trail_sources.py` 直接讀本 repo 文件，不另存第二份：決策書第 7 節每一條是一筆採納決策（`理由：` 前是決定、後是理由，節標題給日期，決策版本給基準）；實現規劃 3.4 的路線表是一筆決策，標「推薦」的那列是選擇，其餘列是被否決路線並以代價為理由；實現規劃第 7 節的分期表是路線圖，進度由呼叫端給（規劃只有估算）。`test_trail_sources.py` 6 個合成測試、`mutants.json` 12 個刪改全部 killed；`test_trail_repo.py` 對真文件要求 7 筆決策都有理由、兩條否決路線有理由、P0–P5 六個里程碑。2026-11-10 首跑抓到決策書第 7 節第 7 條沒有 `理由：` 標記（理由寫在句中），已補標記、未改字句。2026-11-10 加 `absences_from_architect`：ARCHITECT「這個 repo 刻意沒有的東西」裡粗體開頭說不裝的每一條是一筆採納決策，其餘文字為理由，日期取粗體段最後一個（否則條目內第一個）；首跑抓到「沒有 CI」沒有日期，已依 git 首次出現（`7a5d1ec`，2026-09-13）補上並註明出處。合成 2 個、真文件 1 個測試，7 個刪改全部 killed。2026-11-10 加 `rules_from_agents`：AGENTS.md 每個 `[為什麼](AGENTS-reasons.md#x)` 是一條規則，引用決策 `reasons#x`；理由檔每個 `<a id>` 段落是一筆採納決策，標題是段落標題、其餘是理由、日期取段內最早的日期（第一次記下理由的時間）。真文件測試要求每條規則都走得到有日期的理由、沒有沒人引用的段落。首跑前掃到鐵律 3、鐵律 5、副本規則 6、行末四段沒有日期，已依 git 首次出現（`1fa96a2` 2026-08-05、`b04ecf4` 2026-11-01）補上並註明出處，未改原句；鐵律 5 的段落只是重述規則，當時沒有記錄理由，不替它補。合成 3 個、真文件 1 個測試，7 個刪改全部 killed。邊界：只檢查紀錄格式與關聯，不能證明理由為真；ARCHITECT 其他節與各報告的決策還沒轉；路線圖進度只有 P0 由測試寫死為進行中；未接進任何工具。

## 各線發現合流（2026-11-10）

`confluence.py` 是 F26 的合流原型。每條線回報的發現帶問題鍵、值、已驗證或只是聲稱（F3），以及來源、取得時間、適用範圍（F40，例如 `{"os": "macOS"}`）。`merge` 全部收進同一處：缺來源／時間／範圍的列為不完整；只是聲稱的列為未確認；已驗證、值相同、範圍相同的才成為共同依據並附全部來源；範圍不同的保留成各自帶條件的結論，不算衝突也不丟棄；範圍重疊而值不同的是衝突。`basis` 回答某線在某範圍能依據什麼：只有共同依據或範圍涵蓋它的條件結論，未確認、不完整的不行；同一鍵有未解衝突就整個擋下，即使請求範圍只落在沒參與衝突的那筆。

衝突處置（2026-11-10）：`merge` 多收一個 `resolutions`，每筆是人記下的裁決——裁決者、時間、理由、適用範圍、引用了哪些衝突發現（以線與來源辨識）。裁決只能選它引用的某筆發現的值，不能憑空造值；要引用到衝突裡的**每一筆**才算處置完成，之後又出現的衝突發現會讓衝突重新打開（`reopened`），不會被默默蓋過。處置後被否決的發現連同裁決留在 `resolved`；採用的值以裁決的範圍進入共同依據或帶條件結論，`basis` 拿到的那筆帶 `decision`，看得出是靠裁決而不是一致。缺欄位、引用不存在的發現、選了沒人支持的值都列進 `invalid_resolutions`，衝突照舊擋住。

`test_confluence.py` 13 個合成測試；`mutants.json` 原有 15 個加處置 13 個刪改全部 killed（兩個冗餘寫法已直接簡化掉）。邊界：只比對各線宣告的鍵，用不同字眼問同一件事認不出來；裁決者身分只是字串，沒有驗證是真人；共用前提改變的即時通知屬 F28，未做；未接進任何工具。

## 多專案更新的人工確認上限（2026-11-10）

`campaign.py` 是 F24 的原型，接在 `batch.assess_many` 與 `impact` 後面。每個輸入目標恰好一列動作：要更新、未受影響略過、排除、失敗、需人工逐專案比對（客製內容漂移）。人工確認分組：放行版本一次、整份更新清單一次、全部失敗一次審閱，漂移的專案每個各算一次——不把逐專案比對併成一次假裝省事。超過上限（預設 3，決策書 F24）照實報；有失敗、需比對、重複列或受影響卻沒評估的目標都不是 ok。

`test_campaign.py` 8 個測試（20 個混合目標：10 更新、4 未受影響、1 排除、5 失敗，正好 3 次確認但 NOT OK；另有一組用真的 `assess_many` 產生缺失與排除列）；`mutants.json` 14 個刪改全部 killed。邊界：確認次數是規劃值，沒有量真人實際操作；目標字串由呼叫端把 `impact` 的專案名對到批次列；未接 `sync_project.py`。

## 來源未驗證不得發出（2026-11-10）

`publish.py` 是 F35 的阻擋原型。`publish` 只有在三件事都成立時才把套件寫進發布目錄，否則丟 `Denied` 且目錄維持空的：驗證報告（`evidence.resolve` 的輸出）整體通過而且每一列都是本輪實查，沿用、未驗證、SKIP、FAIL 都拒絕，調試包沒有例外；CI 證明同時簽住 manifest digest 與報告 digest，簽完再改報告或拿別的套件的報告都算偽造結果；簽章只認設定的 CI 金鑰與身分，開發者金鑰或錯的 namespace 都是非 CI 發布。版本字串限定字元，不能用來跳出發布目錄；同版本不重複發布。

`test_publish.py` 5 個測試（ssh-keygen 拋棄式金鑰，非 macOS 時驗證器不可用即拒絕）；`mutants.json` 18 個刪改全部 killed。邊界：CI 金鑰是測試替身，握有那把金鑰就能發布；沒有真的 CI 身分、傳輸或原子安裝；現行 `verify_bootstrap.py` 的 ZIP 發布門檻仍是現行程序的阻擋點，本原型未取代它。

## 真人核准來源的候選探針（2026-11-10）

崩潰解除現在問的是「本機終端前的人」，同 UID 程式可以自己開偽終端答題；使用者說過日後要改走簽署金鑰（Q1 (b)）。`presence_probe.py` 只量作業系統有沒有可用的積木，**不是核准機制，也沒有接進任何放行路徑**：它編一個未簽署的 Swift helper，用 CryptoKit 建三把 Secure Enclave 金鑰，全程禁止互動（不會跳出任何驗證視窗）。

```bash
PYTHONPATH=src python3 -X utf8 -m project_bootstrap.presence_probe
```

2026-11-10 在這台 macOS 27.2／Apple silicon 實跑（exit 0）：未設門檻的對照金鑰可簽、驗章成立；設了 `.userPresence`（Touch ID 或登入密碼，由系統視窗詢問）的金鑰可以建立，簽章被 LocalAuthentication 以 -1004「需要使用者互動」拒絕；設 `.biometryCurrentSet`（只認指紋）的金鑰在禁止互動時連建立都失敗（-1000），所以「只認指紋」這一種沒有量到。結果判讀寫死成 `候選可用但未驗收`，`test_presence_probe.py` 驗任何輸出都不會被判成通過、設了門檻卻簽得出來會報反例；`mutants.json` 7 個刪改全部 killed。

沒有驗的比驗了的多：沒有任何人被問過，所以「本人按了才簽得出來」這一半完全沒有證據；系統視窗上顯示的說明文字由發起簽章的程式提供，人看到的不一定是實際被簽的內容；`.userPresence` 接受登入密碼，知道密碼又能操作畫面的程式不被排除；金鑰的保存、輪替、撤銷與遺失後怎麼辦都沒有設計；SSH、螢幕鎖定、其他 OS 沒有量。要不要拿它做簽核原型是決策書 Q16。

## 繞過規則：擋下或留痕（2026-11-10）

`bypass.py` 是 F21 的原型，照決策書分層。阻擋：`guard_commit` 讀已部署專案的 Git index（不是工作樹），已安裝 manifest 裡屬於 core／adapter 的檔，staged 內容與發布版不同或從 index 刪掉就拒絕提交——共用制度只能回來源改再同步；專案自己的檔不受限。發布未驗證來源由 `publish.py` 擋。留痕：`record` 把步驟完成或略過（略過必須附理由）寫進 JSON lines，每行帶前一行的 SHA-256；`audit` 沿鏈檢查，必要步驟既沒完成也沒登記略過就是無聲略過，鏈斷之後的行一律不採信，繞過 `record` 直接寫入的無理由略過也不算數。

`test_bypass.py` 10 個測試（真 Git index）；`mutants.json` 14 個刪改全部 killed。邊界：能改寫整份紀錄的人也能重算整條鏈，所以只抓意外與局部改動，不證明紀錄為真；`guard_commit` 未掛成 pre-commit hook，`--no-verify` 之類的繞法未處理；未接進現行 A／B 程序。

## 新專案取得制度與就地修改盤點（2026-11-10）

`install.py` 是 F17 的原型。`plan` 先預演、不寫任何檔：每個套件檔一個動作——新建、已相同、`.gitignore` 只補缺的行（不刪不重排）、其他已存在而內容不同的檔一律保留給人決定合併。家目錄與檔案系統根目錄拒絕；資料夾裡有任何不屬於套件的東西（含 `.git`）就標成既有專案，讓呼叫端先問人。`apply` 重新預演，跟人核准的那份不同就拒絕，只新建與附加；新建用排他開檔，預演後才出現的檔不會被蓋掉。

`inventory.py` 是 F39（想要、一次性盤點）的原型。對明列的專案，拿它記錄安裝的 manifest 比對 core／adapter 檔：正常、被改、遺失、讀不到；不知道裝了哪版就是未知，不算乾淨。只讀，被改的檔交給人看，因為那可能是該搬進覆寫位置的專案客製。

`test_install.py` 8 個、`test_inventory.py` 2 個測試；`mutants.json` 各 14、8 個刪改全部 killed（`install` 的 `.git` 判斷與「其他項目」重複，已刪掉冗餘守門）。邊界：只處理呼叫端給的檔案集合，部署包第 3 節的範本還沒轉成套件；未接 `sync_project.py`；盤點不掃整顆磁碟，也不判斷修改是否合理。

## 驗證器輸出轉成證據紀錄（2026-11-10）

`ingest.py` 把真實驗證器輸出轉成 `evidence.py` 的紀錄。`from_bootstrap` 讀 `verify_bootstrap.py` 每項一行的 `[  ok  ]`／`[ FAIL ]`／`[ skip ]` 與結束碼，每項一筆，再加一筆整體；`from_v2` 讀 `verify_v2.py --json` 成測試、索引、整體、嚴格模式四筆（嚴格模式未就緒照實記 FAIL）。每筆帶輪次、命令與 commit、取得時間、範圍與宣告輸入的 digest，`resolve` 因此分得出本輪與沿用，輸入改了沿用就失效。看不懂的狀態行記 ERROR、重複項記 ERROR、結束碼與各行矛盾或完全沒有檢查行時整體 FAIL；`[index] …` 這類資訊行不算檢查（mutation 抓到原本會把它誤記為 ERROR）。2026-11-10 拿本 session 實跑的輸出轉換：58 項加整體共 59 筆，全部 PASS。

`test_ingest.py` 7 個測試，行格式由本地函式產生；`test_ingest_format.py` 拿 `verify_bootstrap.py` 自己的 `record` 比對同一格式（它 import `tools/`，所以不放進 mutation 群組）；`mutants.json` 18 個刪改全部 killed。邊界：宣告輸入由呼叫端列，漏列的輸入改變不會失效；解析只證明紀錄與輸出一致，不證明輸出未被偽造；尚未把紀錄寫進任何持久位置或接進 A4／B7。

## 乾淨第二機接續（2026-11-10）

`resume.py` 是 F16a 的偵測原型。`clone` 用單分支 `git clone` 建第二機的 checkout，只帶已提交的檔；`check` 拿一個家目錄（乾淨機就是空資料夾）照入口文件的開工段落走：段落裡的 `~/` 路徑與 repo 內連結是候選，含程序標記行（預設 `name: handoff`）的才算程序。程序必須在 repo 內找得到——家目錄副本新機上還沒有；段落點名的 repo 連結在 checkout 裡缺席是缺漏，只在第一機工作樹存在是私有附件；可達副本的 `source:` 標記不同列為漂移。

首跑本 repo 就不通過：AGENTS 開工段落只指向全域 skill，沒有全域副本時叫人「直接開那個檔讀」，而新機上那個檔不存在。已在 AGENTS 補「讀部署包 3.8 節」的指標，`test_resume_repo.py` 以空家目錄守住。2026-11-10 對部署出去的專案也跑一次：用 `verify_bootstrap.extract` 從部署包生成骨架，空家目錄下 AGENTS 開工段落指到 repo 內的 `.claude/skills/handoff/SKILL.md`，通過；刪掉那份就 `procedure-not-in-repo`。這是生成骨架，不是逐一檢查已部署的真實專案。

`test_resume.py` 9 個測試（含真 `git clone`）；`mutants.json` 15 個刪改全部 killed。邊界：只在同一台機器模擬乾淨 clone 加空家目錄，不是真的第二台機器或其他 OS；只看連結得到的檔含不含程序標記，不核對節號、不判斷讀者照不照得做；hook、憑證、工具設定在新機的狀態沒查；未接進現行 A 程序。

## F50 與索引權威

`session.py` 實作狀態轉移及改名 adapter 契約；接棒／續聊、等待、交棒、重試、下限次數、缺工具、讀回不符都有測試。handoff receipt 的真實來源尚須工具 adapter 驗證，呼叫端自己填四個 True 不是可信交棒證據。returned state 要先耐久保存再重試外部改名；目前尚無正式持久儲存與工具事件接線，不能宣稱自動改名完整交付。`from_title` 只能恢復顯示欄位；事件去重須保存整份 state，不能只靠標題復原。

全部 51 ID 與 F11／F13／F43 子項的**持續實作狀態唯一權威**已從 `fdc0bbd:HANDOFF.md` 移交 [status.json](status.json)。欄位保留原狀態來源、範圍、重跑入口、未知與下一個驗收點；未驗證不是待決。`registry.py` 直接從決策書第 3 節核對 ID，測缺漏、重複、子項遺失、證據不存在與憑空成功。P0 不接受任何整項「通過」宣稱；日後正式驗收須改驗收證據模型與負向案例，不能只改狀態字串。

HANDOFF 保留 writer、目前行動與此索引的指標；若索引不可讀就停止判定，不從舊摘要恢復權威。原查核報告 F01–F16 是另一組編號，不與需求 ID 混用。

## 接下來的架構工作

1. 管道分權、POSIX 套用、限期資格、請求保存、監護回收、Mac 禁 fork 及單 worker 的 outbox／前提切換已有合成證據。程序群組候選無法阻止 `setsid` 逃逸；多程序工具需另找 OS 隔離及可重啟核對的整樹退場證據。真人授權、票據遺失後重新驗身分及監護失效的恢復仍待做。
2. 將合成 supervisor 的停止／排空／重建上下文協定接到實際可控執行介面；不能把程式裡 application=True 當作模型已理解，也不能把 outbox 當即時通知。真實模型探針仍需另行明確授權。
3. 再鎖定需實際採用的外部元件、驗 Windows／Mac 門檻。未通過前不開始全面搬來源、改現行 A4 或部署專案。
4. 接棒成本已能逐次量測；短入口及證據失效機制需配套驗收後才切換。常態必讀超額照實報不通過，不藉此省略檢查。

## P1 第一片：用 pytest 跑（2026-11-11）

P1 第一片加了 `pyproject.toml` 與 `uv.lock`（見 [ARCHITECT](../../ARCHITECT.md)）。裝了 uv 的機器可以 `uv run pytest` 跑 `tests/` 的全部測試；3.15 與 3.12 實跑結果與 unittest 相同（第一片時 456 個；第二片搬完是 461 個，含 `test_layout.py`）。`verify_v2.py` 仍用 unittest、只要標準函式庫，A4 不需要 uv。

pytest 在虛擬環境裡跑時，`sys.executable` 是 `.venv/bin/python` 這個連結，sandbox 只放行基底 Python 的路徑，受隔離的合成 agent 因此起不來（`launcher-start-failed`）。`broker_fixture.sandbox_plan` 改成直接啟動解析後的基底直譯器；agent 只用標準函式庫，不需要虛擬環境。

第二片搬家後，用 `-c` 起的子程序靠工作目錄 import：測試裡這類子程序的 `cwd` 改成 `src`，`vm_probe.py` 的 crash parent 也是。命令列模組要從 repo 根目錄跑 `PYTHONPATH=src python3 -X utf8 -m project_bootstrap.<模組>`；`mutants.py` 複製 `src` 與 `tests` 兩個目錄並設 `PYTHONPATH`。

## P1 第四片：schema、Markdown 解析、只讀狀態卡、F22 實測（2026-11-11）

- `status_card.py`：效率計畫 4.2 的只讀入口原型。`PYTHONPATH=src python3 -X utf8 -m project_bootstrap.status_card`（加 `--no-fetch` 不連遠端）印出分支、upstream、fetch 成敗、未提交檔、領先／落後、兩端 SHA、本機與 origin 的「工作中」與 HANDOFF 記的最近驗證；異常逐條列原因與程序指向，全綠 exit 0、否則 1。只有 fetch 會動到遠端追蹤分支；測試用 `readonly.read_only` 證明它不改 ref、index 或檔案。現行 A1–A5 不變，卡片不取代任何必讀。
- `schema_check.py`＋`status.schema.json`／`mutants.schema.json`：jsonschema（Draft 2020-12）驗現況索引與 mutation 規格的形狀。schema 合格不等於內容對：ID、證據路徑與 P0 不接受通過仍由 `registry.validate` 查。
- `mdlinks.py`：markdown-it-py 讀連結，`test_mdlinks_repo.py` 對本 repo 的 Markdown 再查一次死連結，當 A4 正規式檢查的第二意見；2026-11-11 兩者都是 0。
- 後兩支要 uv 環境（`uv run pytest`）。`verify_bootstrap.py` 的 `P1_EXTRAS` 列出可以用鎖檔套件的模組；別的程式不能 import 它們；它們的測試開頭寫 `raise unittest.SkipTest('needs …')`；A4 的 `verify_v2` 不跑這些檔，報告與 v2 項會逐一列出（「跳過數必須是 0」的規則不變），不會悄悄少驗。它們沒有 mutation 規格：`mutants.py` 用系統 Python 跑，缺套件會被當成跳過而存活；負向案例寫在測試裡。
- F22 實測：`baseline.py` 量常態必讀 17,373 字元（AGENTS 6,244、HANDOFF 5,745、skill 入口＋mode-a 5,384）；把 HANDOFF 已完成節縮短後是 16,608（HANDOFF 4,980），加開場 hook 輸出 819，約 17,400，仍超過 12,000。狀態卡約 600 字元，但程序沒有改，不算降量。
- 2026-11-11 F22 第二輪（使用者指示「先修 F22 超標」）：AGENTS 規則縮成短句、壓縮前原文逐條補進 `AGENTS-reasons.md`，條件式文件表與 HANDOFF 的地雷搬到 ARCHITECT，開場 hook 末行縮短；skill 與部署包沒動。`baseline.py` 實測 10,462（AGENTS 3,456、HANDOFF 1,622），加 hook 全綠輸出約 600，約 11,100，字元在上限內；5 分鐘那一半沒量，F22 整體改記未驗證。
- A4 仍然只用標準函式庫與正規式；要不要讓 A4 改用這兩個套件（等於要求每台機器都裝 uv），是現行程序的改變，沒有做。

## P2 第一片：正式包格式（2026-11-11）

`package.py` 從 `src/kit` 生成一個包資料夾：每個部署檔一份，加一份 `manifest.json`。manifest 沿用 `release.build_manifest` 的元件 digest（所以 `release.WriteGate` 讀得懂），另外記三件事：每個檔的歸屬與更新方式、哪些檔要可執行、同一份來源生成的 `PROJECT-BOOTSTRAP.md` 的 SHA-256。

歸屬表是 `src/kit/owners.json`，三類對應實現規劃 4.1 的 F36：

| 歸屬 | 更新方式 | 檔案 |
|---|---|---|
| core | whole：整份換 | handoff skill 六個檔、`git-freshness.sh`、`pre-push-handoff.sh` |
| core | region：只換標記區段 | `tools/check_docs.py` |
| adapter | whole | `ag-wrap.sh`、`codex-hook.cmd`、`.agents/ag-hook.cmd`、`.agents/skills/handoff/SKILL.md` |
| adapter | wiring／key：只換包自己的接線 | `.claude/settings.json`、`.codex/hooks.json`／`.agents/hooks.json` |
| project | lines：只補指定行或欄位 | `HANDOFF.md`、`.gitignore`、`CLAUDE.md` |
| project | seed：安裝時寫一次 | 其餘八個 |

更新方式不是新規則，是把 `sync_project.py` 現有的 `WHOLE`／`SURGICAL`／`WIRING`／`AG_WIRING`／`PARTIAL`／`INSTANCE` 搬成資料；`test_package_repo.py` 逐檔比對兩邊，第 5 片把同步器改成讀 manifest 之前，任一邊改了另一邊沒改就失敗。core 與 adapter 的切法是新的：skill 與兩支 hook 腳本是制度內容，其他是平台接線。

範本沒有歸屬、歸屬沒有範本都停止建包，不猜。`tools/build_package.py` 一律建 debug 包，沒有建正式版的旗標；正式版只能經發布步驟（第 3 片，要先定簽章與 channel）。`check` 對照 manifest 列出 digest 不符、缺檔、多檔、符號連結、執行權限不符與歸屬不合法；`install` 只把通過檢查的包換到目標，目標必須不存在或是只含包內檔案的舊包。

`test_package.py` 15 個合成測試、`test_package_repo.py` 4 個；`mutants.json` 新群組 27 個刪改全部 killed。另一個刪改（`whole_owned` 只看更新方式、不看歸屬）存活，但歸屬表本來就不允許 project＋whole，屬等價變異，未列入。本 repo 實建：27 個檔，可重現。

沒做的：`sync_project.py` 與 `install.py` 還沒讀這個包；`policy.plan_update` 只處理整份的 core／adapter 檔，region／wiring／key 還沒有對應的更新規劃；沒有簽章、channel 與專案指標（第 2、3 片）；只在這台 macOS 跑過。

## P2 第二片：專案指標與每次寫入的檢查（2026-11-11）

`pointer.py` 是 D3／D4／D5 的原型。專案不放制度副本，只放 `.bootstrap/pointer.json`：channel 名、已安裝包的 manifest digest，加一個可以是空的 D4 例外。包本身放在專案外的快取資料夾，一個 digest 一個子資料夾，格式是第一片的包。

`WriteCheck.confirm(operation, target)` 在每次受管寫入前跑，什麼都不快取：

1. 重讀指標，所以改了指標下一次寫入就生效。
2. 從快取取出已安裝的包，用 `package.check` 驗過，manifest digest 要等於指標，而且要是正式版。
3. 帶新 nonce 向 channel 要簽過的聲明。拿不到、重播、過期、未來簽發、錯 channel、他人金鑰、欄位型別錯、epoch 倒退都拒絕。
4. channel 的包不是已安裝那份就拒絕（`release-mismatch`）；只有指標宣告了例外、例外釘住的正是已安裝那份、還沒過重新檢視日、而且寫入路徑在例外範圍內，才放行並標 `pinned`。
5. 專案裡整份屬於 core／adapter 的檔逐一比 digest。專案自己的檔（AGENTS、HANDOFF）與 `settings.json` 這類只換部分的接線不比，所以專案改自己的檔不會被擋——這是 `release.WriteGate` 原本做不到的：它比 manifest 裡每一個檔。

`status` 是只讀入口：不連 channel，報版本、digest 與例外，並標「未確認最新」（D5：可以繼續讀，但要講清楚限制）。

`test_pointer.py` 15 個寫入／狀態測試加 3 個指標格式測試；`mutants.json` 新群組 39 個刪改全部 killed（首跑存活兩個：簽名合法但 epoch 是字串、簽發時間在未來，已補測試）。沒有 `ssh-keygen` 的平台不跳過，改驗驗證程式不在時拒絕寫入，跟 `test_release.py` 同一做法。

沒做的：簽章金鑰與 channel 是測試替身（第 3 片）；指標檔還不在部署包裡，也沒有工具會寫它；`preflight.ManagedWrite` 還在用舊的 `WriteGate`，沒改用這個檢查；`check_docs.py` 的共用區段與三種接線檔沒比；最高 epoch 只記在記憶體，換一個程序就能接受較舊的聲明；例外的宣告人是記下的名字，不是驗過的身分。

## P2 第三片前半（3a）：正式發布、金鑰鏈與 Git tag channel（2026-11-11）

依決策書 Q20 三題都選 (a)。`channel.py` 取代第二片「每次寫入對亂數簽章」的做法：CI 是跑完就結束的工作，沒辦法回應每一次寫入，而 Q20 決定不架常駐簽章服務。

- **channel**：來源 repo 裡的 tag `refs/tags/channel/<名稱>/<epoch>-<digest>`。`git ls-remote` 不用 clone、也不寫任何東西就能列出來，所以每次寫入都直接連來源 repo 問一次。新鮮度靠這次直接連線，重播靠 GitHub 的 TLS 擋。（2026-11-11 E3 更正：原本寫「誰能建這些 tag 由伺服器端保護規則限制」，但個人帳號的 repo 不能只放行 GitHub Actions，決策書 Q22 改成只擋 tag 被移動或刪除；有 push 權限的人仍能建新 tag，靠簽章讓它只能讓寫入停下。）
- **發布（CI 端）**：`release` 收第一片的 debug 包和驗證報告，報告要整體通過、每一列都是本輪實查（沿用 `publish.py` 的判斷），才把包標成正式。CI 簽的是 channel、epoch、正式包 digest、報告 digest，加上 `next_keys`：下一版可以用哪些金鑰簽。
- **安裝（客戶端）**：`install` 只接受上一版 `next_keys` 裡的金鑰簽的紀錄，第一次安裝用使用者給的根金鑰。換金鑰要先用舊金鑰發一版、在 `next_keys` 列出新金鑰。包和簽過的紀錄一起放進快取。
- **每次寫入**：`GitWriteCheck` 先做本機檢查（指標、快取裡的包與紀錄、共用檔比對），被擋的寫入不會白跑一趟網路；再列 channel tag。只有最新的 tag 恰好等於已安裝紀錄的 (epoch, digest) 才放行。epoch 比較新而 digest 不同，照第二片的 D4 例外處理；epoch 比較舊是 `channel-rollback`；同一個 digest 卻換了 epoch 是 `channel-epoch-mismatch`；同一個 epoch 兩個 digest 是 `channel-conflict`。已安裝的 epoch 記在快取裡簽過的紀錄，換一個程序也不會接受較舊的 channel，第二片「只記在記憶體」的缺口因此補上。

偽造的 tag 只能讓寫入停下，不能讓舊版繼續寫：指向舊版、epoch 很大的 tag，和舊版簽過的 epoch 對不上。`pointer.py` 為此抽出 `check_request`、`exception_allows`、`check_components` 三個共用步驟，指標可以多一個 `source` 欄位（https、`file:///` 或絕對路徑，不能以 `-` 開頭，避免被 git 當成選項）。

`test_channel.py` 21 個測試，用本機 bare repo 模擬來源、拋棄式 ed25519 金鑰模擬 CI；沒有 `ssh-keygen` 的平台不跳過，改驗驗證程式不在時拒絕安裝。`mutants.json` 的 `channel` 群組 41 個刪改全部 killed；另一個刪改（安裝時不先檢查包）存活，但 `package.install` 會再檢查一次、結果相同，屬等價變異，未列入。`pointer` 群組因重構改寫 10 條、加 2 條 `source` 守門，共 41 個全部 killed。

沒做的（3b，要另行授權）：GitHub Actions workflow、CI 金鑰放進 secret、用保護規則限制 `channel/*` tag 只能由 CI 建立、第一次正式發布與乾淨機器驗收。另外還沒設計：第一次安裝的根金鑰怎麼交給使用者；發布用的命令列入口（目前只有函式）；快取仍可被同一個使用者改（P3）。

## P2 第三片後半（3b）的本機準備（2026-11-11）

依決策書 Q21 五題都選 (a)。這一段只寫檔案，不碰 GitHub：

- `distribute.py`：兩個命令列入口會拒絕的東西都在這裡、都有測試。驗證器輸出經 `ingest.from_bootstrap` 與 `evidence.resolve` 變成報告，每個檢查行加上整體都要是本輪實查；發布公鑰檔一行一把，只有註解就拒絕；下一個 epoch 是最新 tag 加一；包的壓縮檔逐位元組可重現（檔案時間與 gzip 檔頭時間都是 0），解壓只接受 `package/` 底下的一般檔與目錄，拒絕連結、裝置、`..`、反斜線與重複名稱，解出來還要通過 `package.check`；鋪專案只接受空資料夾；專案有 D4 例外時不改指標，要人先拿掉。
- `tools/release_package.py`（CI 跑）：checkout 要乾淨，報告才對得上 HEAD；建 debug 包、跑 `verify_bootstrap.py`、讀 channel tag 算 epoch、用 `release-keys.txt` 當 `next_keys` 簽章，輸出三個檔與要建的 tag 名。它自己不建 tag、不上傳。
- `tools/install_package.py`（使用者跑）：專案還沒有指標時用 `release-keys.txt` 的根公鑰，之後用已安裝那一版的 `next_keys`；先比 channel 名再碰快取；`--seed` 鋪空專案、`--check` 立刻跑一次寫入檢查。它不下載。
- `.github/workflows/release.yml`：push `release-request/<channel>` tag 觸發，跑在 macOS（驗證器有 macOS 專用探針），金鑰放在要使用者核准的 `release` environment；不用第三方 action，tag 帶來的字串只經環境變數進 shell。成功後用 `gh api` 建 channel tag、`gh release create` 上傳三個檔（標為 prerelease）。
- `src/kit/release-keys.txt`：E1（2026-11-11）填入 CI 公鑰，指紋 `SHA256:FjVJTEPBuOaloJZV0GvtZiG3bXYJo68v+cTaVqs0JU0` 也寫在 README。私鑰在本機產生、用 `gh secret set` 存成 `release` environment 的 secret 後就刪掉，沒有印出來；environment 的必要審核人是 repo 擁有者。

`test_distribute.py` 10 個測試，`mutants.json` 新群組 25 個刪改全部 killed（首跑存活三個：gzip 檔頭時間沒驗、反斜線案例同時違反別的規則；開頭 `/` 的檢查被「第一段必須是 package」涵蓋，已從程式刪掉）。`test_release_tools_repo.py` 5 個測試拿 `src/kit` 的真內容從發布走到安裝與寫入檢查，驗證器與 git 狀態用替身（真的驗證器要跑幾分鐘，開發中工作樹也常不乾淨）。

沒驗的：workflow 沒有在 GitHub 上跑過，macOS runner 能不能讓驗證器全部本輪實查通過、`gh api` 建 tag 會不會被之後的保護規則擋、保護規則能不能只放行 GitHub Actions，都要到 E1–E5 才知道。

## P2 第 3b 片 E4：第一次正式發布（2026-11-11）

使用者在 GitHub 核准 [run 42982470611](https://github.com/Baliyoho/project-bootstrap/actions/runs/42982470611) 後，workflow 在 macOS runner 上一次跑完：clone `243074c`、建包、跑完整 `verify_bootstrap.py`（全部本輪實查通過，否則發布工具會拒絕）、簽章、用 `gh api` 建 `channel/beta/1-ed31ffed53dc612b3d90aaa6e3ce4a6c5c4d7911a4f239755a08b4db61c5c78f`，再建同名 prerelease、上傳三個檔（包 61,084 bytes、紀錄 279、簽章 326）。E3 的規則只擋移動與刪除，所以 `GITHUB_TOKEN` 建 tag 沒有被擋。

本機獨立核對：用已提交的 `src/kit/release-keys.txt` 驗簽通過；紀錄是 `beta`、epoch 1，`next_keys` 等於已提交的金鑰；解壓後 `package.check` 乾淨、正式版、版本 `2026-11-10.2`、27 個檔、digest 與紀錄相符；在本機同一個 commit 重建、標成正式版，digest 跟 CI 發的逐位元組相同。

缺口：發布工具把驗證器輸出收進報告，沒有印到 workflow 日誌，所以日誌裡看不到每一項的結果，只能從「有簽章」反推全部通過；報告本身也只以 digest 進入簽章紀錄，沒有隨 Release 上傳。（2026-11-11 稍後已補：`release_package.py` 把驗證器完整輸出與結束碼印到日誌，並把報告寫成第四個檔 `*.report.json`，內容是 canonical JSON，SHA-256 就是簽章紀錄的 `report` 欄位；`test_distribute.py` 與 `test_release_tools_repo.py` 驗這個對應。`beta` epoch 1 是補之前發的，沒有這個檔；下一次發布才會有。）E5（乾淨環境安裝、對真的 GitHub 跑寫入檢查、假 tag 負向測試）還沒做。

## P2 第 3b 片 E5：驗收（2026-11-11）

**乾淨環境**：空的家目錄、不讀系統與使用者 git 設定、不帶 GitHub 登入（`env -i`）。匿名 clone 公開 repo 的 v2 分支，拿到 `243074c`（channel tag 指的那個 commit）；匿名下載 Release 的三個檔，與登入後下載的逐位元組相同。用 clone 裡的 `install_package.py --seed --check` 裝進空專案：27 個檔、根公鑰驗簽、寫指標，對真的 GitHub `git ls-remote` 跑寫入檢查，最新與已安裝都是 `ed31ffed…`、epoch 1，放行。

**本機負向測試**（不碰 GitHub）：專案改自己的 `AGENTS.md`／`HANDOFF.md` 照樣放行；改共用 hook 是 `component-drift`；來源連不到是 `channel-unreachable`；壓縮檔內容被改是 `bad-package`；簽章紀錄被改、換成別的根公鑰都是 `not-signed-by-trusted-key`；被拒的安裝都沒寫指標、沒建快取。（「壓縮檔被改」第一次看似沒擋，是測試腳本忘了傳入那個檔，修正後重跑才算數。）

**GitHub 上的 tag 規則沒有作用**（決策書 Q23）：在 `channel/e5-test/` 用 API 建假 tag（預期成功）後，用 API 移到另一個 commit——成功；改用 `git push` 刪除——也成功。規則評估紀錄是空的（連 workflow 建 `beta` tag 那次都沒有），GitHub 卻回報 ruleset 27014223 是 active、擁有者「永遠不能繞過」。原因沒有查明。所以 channel 歷史沒有伺服器端保護：有 push 權限的人能建、移、刪 channel tag。安全那條線仍由簽章守：客戶端只接受 CI 簽過、而且等於已安裝紀錄的 (epoch, digest)，上面的乾淨環境與 3a 的離線測試都驗過，假 tag 或被移走的 tag 只會讓寫入停下。測試 tag 已刪，`beta` 的 tag 沒有被碰過。使用者同意後也刪掉了 ruleset 27014223，免得它看起來有保護。

沒驗的：Windows／Linux；真實專案的遷移（第 5 片）；第二版發布與沿金鑰鏈升級只在本機測過，GitHub 上還沒發過 epoch 2。

## P2 第 4 片：能力矩陣（2026-11-11）

依決策書 Q24 (a)。`src/kit/capabilities.json` 是每個工具 surface 能做什麼的唯一的家。部署包「跨工具與跨平台」那兩張表（四欄的跨工具表、Antigravity 分 surface 的 hook 表）改由它生成：`kit.md` 那兩處只剩 `<!-- kit-table: tools -->`、`<!-- kit-table: antigravity-hooks -->`，`build_kit.py` 的 `load_source` 展開，`build` 遇到沒展開的指令就停。重生出來的部署包逐位元組不變，所以 `VERSION` 不跳，保鮮期與 README 一致性檢查照舊作用在生成結果上。

矩陣一格是一個事實：哪個能力、替哪些 surface 說話、有或沒有、根據是什麼。根據分三種：`tested` 只算列出的那幾個版本；`docs` 是官方文件，可以帶 `since`；`design` 是本專案這一側做了沒有。Antigravity 那一欄在表上是一格摘要，摘要格只給人看，不當證據；分 surface 的結論來自另一張表的各格。同一個 surface、同一個能力只能有一格說話，每一格的文字在表上剛好出現一次。

`capabilities.report(矩陣, surface, 版本, 自測)` 對一個 surface 的一個版本列出每個能力：

- 只用這個 surface 的格；`tested` 的格只在版本完全相同時算數，否則記 `other-version`，不代用。
- 文件說有只算 `unverified`，文件說某版起才有而版本較舊算 `missing`。
- 自測（呼叫端給的 probe）回傳不是 `True` 或拋例外，就算 `missing`，蓋過矩陣；例外內容不進報告。
- 標成 `strict` 的能力只認本次自測通過。現在只有一個：受控寫入閘（M3），所有 surface 都記 `design`／沒有，所以沒有任何 surface 是 strict ready。
- 不是 `supported` 的能力附上影響與替代做法（F47：缺的要說出來）。

命令列：`PYTHONPATH=src python3 -X utf8 -m project_bootstrap.capabilities <surface> --version <版本>`，印 JSON，不跑自測；strict ready 才 exit 0，否則 1，矩陣壞了是 2。

`test_capabilities.py` 15 個合成測試；`mutants.json` 新群組 33 個刪改全部 killed（寫測試時拿掉兩個互相涵蓋的守門：tested 格不能帶 `since` 已由「只有 docs 格能帶 since」涵蓋，design 格不能有文字已由「每格文字剛好出現一次」涵蓋）。`test_capabilities_repo.py` 5 個測試：`build` 拒絕沒展開的指令、壞矩陣讓部署包生不出來，以及對本 repo 的部署包由矩陣生成且相同、改矩陣沒重生會不同、目前沒有 strict ready、Antigravity 四個 surface 分開判。

沒做的：真實工具上的安裝／啟動自測（probe 目前只有測試替身）；版本怎麼偵測；矩陣還不在正式包裡，客戶端讀不到；F14 的共用 CLI 契約與「相同案例每個 surface 等價」；`PreToolUse` 能擋與受控寫入閘的差別只寫在 `strict` 上，沒有另列能力。（前三項 2026-11-12 補了離線做得到的部分，見下一段。）

## P2 第 4 片補缺口：版本偵測、安裝自測、矩陣進包（2026-11-12）

**矩陣進包**：`tools/build_package.py` 把 `src/kit/capabilities.json` 放進 manifest 的 `capabilities` 欄。manifest digest 涵蓋整份 manifest，所以矩陣跟著發布簽章走，不需要為它另開一種「不部署的檔」歸屬，也不會被鋪進專案。壞矩陣建不出包（`invalid-capabilities`），快取裡的包矩陣被改就過不了 `package.check`（`capabilities-invalid`）或 digest 對不上。`capabilities.from_manifest` 只從包讀，沒有矩陣的舊包（含 `beta` epoch 1）直接停，不退回讀來源那份。包的 digest 因此改變；`PROJECT-BOOTSTRAP.md` 不變，`VERSION` 不跳。

**`selftest.py`**：

- 版本偵測：CLI surface 跑自己的 `--version`（`claude`／`codex`／`agy`；Claude Code 找不到 PATH 上的就用執行中那個的執行檔），App surface 讀 `/Applications/<App>/Contents/Info.plist`。Antigravity IDE（1.x）與 2.0（2.x）都叫 `Antigravity.app`，只能以主版號分，輸出會寫明來源。逾時、非零結束、沒有數字版本、讀不到都回 `None`；`report` 拿到 `None` 就不用任何實測格。不呼叫模型、不連網。
- 安裝自測（只看檔案）：`reads-agents-md` 要 `AGENTS.md` 在，Claude Code 有 `CLAUDE.md` 時要有單獨一行 `@AGENTS.md`，Antigravity 有 `GEMINI.md` 時要提到 `AGENTS.md`；`loads-skill` 找專案或該工具家目錄的 handoff skill（Antigravity 只認專案的 `.agents/skills/`）；`hooks` 要接線檔的 SessionStart 接到 `git-freshness.sh` 且檔案在，Antigravity 另要經可執行的 `ag-wrap.sh`。
- `capabilities.report` 多一個 `checks` 參數：自測沒過讓能力在這個專案變成 `missing`，蓋過矩陣與執行期 probe；通過**不升級**（檔案在不代表工具真的會呼叫），strict 能力仍只認執行期 probe。
- 兩個平台（同日稍後補）：同一個專案會在 Windows 與 Mac 之間交接，所以 hooks 的自測可以指定平台，預設是本機。Windows 那條要 Codex 的 SessionStart 有經 `codex-hook.cmd` 跑 `git-freshness.sh` 的 `commandWindows`、啟動器在；Antigravity 要有 `.\ag-hook.cmd git-freshness.sh` 這條 handler，`.agents/ag-hook.cmd` 與 `ag-wrap.sh` 都在（Windows 經 Git Bash 跑，不看執行位元）；Claude Code 兩邊是同一條命令。Windows 那條壞了只算 Windows 的缺口，不會讓 Mac 上的 hooks 被判成沒有。只看檔案，`.cmd` 本身在 Windows 能不能跑仍沒驗。
- 命令列：`PYTHONPATH=src python3 -X utf8 -m project_bootstrap.selftest <surface> --project DIR [--cache DIR] [--version V] [--os posix|windows]`；有 `--cache` 就讀專案指標指向的已安裝包，沒有就讀來源並在輸出標明。

`test_selftest.py` 23 個合成測試；`mutants.json` 新群組 40 個刪改全部 killed（Windows 那條另加 10 個，首跑存活一個：`run` 沒把平台傳給自測時，兩邊都接好的專案分不出來，已改成拿掉 Windows 啟動器；第一批首跑存活 4 個：Antigravity 非數字版本會當掉、`@AGENTS.md` 只出現在句中、包內矩陣本身壞掉沒測，三個已補測試；另一個是變異寫在錯誤訊息而不是條件上，已改寫）。`capabilities` 群組有一條因 `if` 改成 `elif` 更新原文，33 個仍全部 killed。`test_selftest_repo.py` 3 個測試：真的包帶的矩陣等於來源，用包鋪的專案在六個有接線的 surface、兩個平台自測全過，本 repo 自己（已宣告的例外）判成 hooks 與 skill 沒接。

本機實跑（2026-11-12）：Claude Code 偵測到 `2.1.321`，矩陣只有文件根據；Antigravity.app `2.31.0` 歸到 2.0，矩陣只實測過 `2.28.2`，不代用；這台 PATH 上沒有 `codex`／`agy`，版本是 `None`。

沒做的：啟動自測（真的觸發 hook 並讀回、問工具有沒有讀到指示檔）要模型呼叫，要另行授權；2026-11-12 使用者授權只對 Claude Code 做一次（拋棄式專案用真包鋪、`claude -p` 請它逐字列出開場的 `[git-check]` 行），但這台 PATH 上沒有獨立 CLI，桌面 App 內附的執行檔拿掉宿主 session 的變數單獨跑，回 `Not logged in`（登入是經宿主傳進來的；借用宿主通道等於把探針掛在當前 session 底下，沒有做），沒有用到模型額度。同日使用者在終端機登入 CLI（`claude auth login`，Pro 訂閱）後重跑一次：模型逐字列出三行 `[git-check]`（本機沒落後、「工作中」無人、全綠），全綠行帶著拋棄式專案 origin 的 SHA 與當下時間，這兩個值只有專案的開場 hook 算得出來，所以 Claude Code `2.1.321` 在 macOS 上會跑專案的 SessionStart hook，輸出進到模型的 context。矩陣的 `claude-code/hooks` 據此從 `docs` 改成 `tested: [2.1.321]`（表上文字不變，部署包不變，包的 digest 會變）。只測了這一個 surface、這一個版本、這一個事件；有沒有讀 `AGENTS.md`、push 提醒的 exit 2 會不會真的擋下工具呼叫都沒測；Codex 的專案信任不在專案檔案裡，查不到；Windows 的 `.cmd` 在 Windows 上真的跑不跑（接線檔與檔案在不在已查）。F14 見下一段。

## F14：開場檢查的共用契約與薄 adapter（2026-11-12）

F14 是「換工具不改變程序」，驗收寫「相同案例在每個受支援 surface 有等價結果，不支援明示」。真的開工具要模型呼叫，所以這一段只做到接線與 adapter 層，但用的是部署包真的接線：

- **契約**：`.claude/hooks/git-freshness.sh` 在專案根目錄印出的文字就是開場檢查的全部結果；規則只在這支腳本裡。
- **adapter**（`surfaces.py`）：照每個 surface 的接線檔（`.claude/settings.json`、`.codex/hooks.json`、`.agents/hooks.json`）取出 SessionStart 接到 `git-freshness.sh` 的命令，從該 surface 的工作目錄用 shell 跑。Claude Code／Codex 從專案根目錄或任一子目錄跑、stdout 原樣；Antigravity 從 `.agents/` 跑，解開 `ag-wrap.sh` 的 `injectSteps[0].ephemeralMessage`。Antigravity 接線有兩條（Unix 與 Windows），照部署包 3.20：兩條都跑，恰好一條有輸出才算數，兩條都有輸出就是重複注入、都沒有就是沒注入，都報錯。專案自己另掛的 SessionStart hook 不算這個檢查。
- **比較**（`compare`）：同一個專案狀態，每個 surface 跑一次，時間戳正規化後文字必須逐字相同、結束碼都是 0。能力矩陣說這個 surface、這個版本沒有 hooks 的不跑，結果裡列在 `unsupported` 並附矩陣的理由。工具身分的環境變數（`CLAUDECODE`、`CODEX_*`、`GEMINI_CLI`）是 hook 可以拿來區分的東西，比較時每個 surface 給同一份環境，adapter 不能改變它看到的身分。

`test_surfaces.py` 9 個合成測試；`mutants.json` 新群組 18 個刪改全部 killed（首跑存活一個：專案自己的 SessionStart hook 會被當成這個檢查，已補案例）。`test_surfaces_repo.py` 8 個測試用 `src/kit` 建的真包鋪成 git 專案、配本機 bare origin，跑全綠、落後、未提交、別台機器占用、同機另一工具（三個 surface 同一身分）、沒有 upstream、fetch 失敗，六個 surface 文字都相同；Antigravity IDE 給實測版本 `1.107.0` 時列為不支援、不跑。repo 測試要 import `tools/`，不能放進 mutation（`mutants.py` 只複製 `src` 與 `tests`），所以手動反證兩次：`ag-wrap.sh` 改成在 `.claude/hooks/` 跑 hook，測試仍通過，因為 hook 自己會 `cd` 到 repo 根目錄，屬等價變異；改成把換行換成空白，測試失敗。兩次都已還原。

**push 前提醒（同日稍後補）**：第二個共用檢查是 `pre-push-handoff.sh`，契約是結束碼（2 擋下工具呼叫）與 stderr（給模型看的訊息）。能力矩陣新增 `push-reminder`（根據都是 design，格子不帶文字，部署包的表不變）：Claude Code 與 Codex 有，Antigravity 刻意不接（3.20）。`pre_tool_use` 照各自的 PreToolUse 接線跑，遵守 matcher（沒有、空字串、`*` 是每次都跑，否則是整個工具名的正規式）；`compare_push` 要求結束碼與 stderr 都相同。`test_surfaces_repo.py` 加 4 個：main 上有未推 commit、沒動 HANDOFF 時 `git push` 三個 surface 一樣擋（exit 2、同一段訊息）；`git status`、`HANDOFF_HOOK=off`、commit 裡有 HANDOFF、feature 分支都一樣放行；Antigravity 三個 surface 列為不支援。

**找到一個不等價**：同樣在 main 上有未推 commit、沒動 HANDOFF，`apply_patch` 這類非殼層工具的內容只要提到 `git push`，Codex 會擋（沒有 matcher，每個工具呼叫都跑 hook，而 hook 在整段 payload 裡找字面 `git push`），Claude Code 不會（matcher 只放 Bash 與 PowerShell）。部署包 3.17 那段寫「它自己對非 push 的呼叫是 `exit 0` 立刻收手，功能上沒問題」，這個情境下不成立。登記為決策書 Q27，同日使用者採 (a)：3.11 範本從 stdin 取 `command` 欄位（字串或字串陣列）再比對，只用 grep；`source:` 標記跳到 `v2026-11-12`，`VERSION` 不動，各專案副本要另行授權才同步。修好之後這個案例改成 `test_non_shell_tool_mentioning_git_push_is_allowed_everywhere`：Codex 跑 hook 但放行、Claude Code 不跑，結果相同。`verify_bootstrap.py` 的 push 提醒情境加三條（非殼層工具內容提到 push 放行、`command` 是字串陣列照擋、push 只出現在別的欄位放行）與一個負向儀器（拿掉欄位過濾就重現舊誤擋）。新增 9 條刪改，`surfaces` 群組共 27 個全部 killed。

沒做的：工具本身是否觸發 hook、把文字放進模型上下文；Windows 的 `commandWindows`／`.cmd` 路徑；其他程序步驟的等價案例；`ag-wrap.sh` 會把 stderr 併進訊息、Claude Code／Codex 不注入 stderr，這七種狀態下 hook 沒有 stderr 所以相同，hook 若開始寫 stderr 就會不等價，目前沒有案例守。

**程序入口與 stderr（2026-11-12 再補）**：第三個共用檢查是程序入口。`compare_procedure` 對每個 surface 解出它讀到的指示檔（`CLAUDE.md` 的 `@AGENTS.md`、`GEMINI.md` 的指標都要通到 `AGENTS.md`）與 skill 載入器找到的 handoff skill（專案優先、再家目錄；`.agents/` 指標照連結追到權威版，description 去掉固定開頭），三樣東西（`AGENTS.md` 文字、description、整個 skill 目錄的檔）逐字相同才算等價；矩陣說沒有 `reads-agents-md` 或 `loads-skill` 的不跑。開場檢查另要求 Claude Code／Codex 的 stderr 是空的，因為 `ag-wrap.sh` 用 `2>&1` 把 stderr 併進 Antigravity 的訊息。這個案例在真包上找到一個不等價：3.16 指標的 description 少了權威版後來加的模式 0 那句與三個觸發詞，Codex 與 Antigravity 聽到「幫我建 HANDOFF」不會載入程序；已在部署包補齊（`source:` `v2026-11-12.2`，`VERSION` 不動，各專案未同步）。手動反證：放回舊指標，真包測試失敗。

**Claude Code 啟動自測第二次（2026-11-12，使用者授權一次模型呼叫）**：拋棄式專案用真包鋪，`AGENTS.md` 末尾加一行隨機暗號，main 上留一個沒動 HANDOFF 的未推 commit；`claude -p`（2.1.321，拿掉宿主 session 變數、禁用 Read／Grep／Glob、只放行 `Bash(git push)`）請模型不用工具寫出暗號，再跑一次 `git push`。結果：模型答出暗號的隨機部分（漏了前綴，不是逐字），證明 `AGENTS.md` 經 `CLAUDE.md` 的 import 進到 context；push 被 hook 以 exit 2 擋下，模型逐字收到 `[handoff-check]` 三行，bare origin 沒有前進。矩陣 `claude-code/push-reminder` 從 design 改成 `tested: [2.1.321]`；`claude-code/reads-agents-md` 測的是 import 路徑不是原生讀取，維持 docs 並加註。2 個 turn。沒測：skill 有沒有自動載入、SessionEnd、Codex 與 Antigravity。

**Claude Code 啟動自測第三次：skill 載入（2026-11-12，使用者授權）**：拋棄式專案的 skill description、入口內文、`mode-a.md` 各放一個隨機暗號，`claude -p` 只說「接棒」並禁用 Bash。模型自己呼叫 Skill 工具載入 handoff，但 skill 清單與載入的內容是家目錄 `~/.claude/skills/handoff/` 那份（沒有暗號），是入口文字叫它改用 Read 讀專案那份，才拿到入口與 `mode-a.md` 的暗號。`selftest.SKILLS` 的 Claude Code 順序改成家目錄優先，`compare_procedure` 因此能抓到「家目錄那份與專案不同」的不等價；矩陣 `claude-code/loads-skill` 改 `tested: [2.1.321]` 並加註。怎麼處理登記為決策書 Q28（待決）。5 個 turn。

## P2 第 5 片：遷移器（2026-11-11）

依決策書 Q25 三題都選 (a)。現行同步器 `sync_project.py` 繼續是現行工具（過渡保障），這一片另做一個把舊專案一次搬到「包＋指標」的遷移器，重用同步器的合併、歷史版本掃描與占用檢查，不複製一份。

**同步器讀 `owners.json`**：`sync_project.py` 原本手寫的 `WHOLE`／`WIRING`／`PARTIAL`／`INSTANCE` 清單改由 `src/kit/owners.json` 算出來，名字與內容不變，同步行為不變。`region`／`key`／`lines`／`wiring` 四種檔各有專屬的處理程式，所以 `owners.json` 多一個或少一個這種檔、或 skill 入口不見，同步器就拒絕啟動，不猜怎麼處理。`test_package_repo.py` 原本逐檔比對兩份清單，改成驗這三種壞表都會被拒（另外手動拿掉兩道守門，測試都會失敗）。

**`migrate.py` 判斷**：每個共用檔（整份的 core／adapter 檔，加 `check_docs.py` 的共用區段）分成：

| 狀態 | 意思 | 遷移時 |
|---|---|---|
| `current` | 已經是目標包的內容 | 不動 |
| `known` | 本 repo 發過的舊版（部署包 Git 歷史裡出現過） | 換成目標版 |
| `missing` | 沒有這個檔 | 補上，因為寫入檢查要求每個共用檔都在 |
| `customised` | 本 repo 沒發過的內容 | 停下，交人比對 |
| `unreadable` | 讀不到 | 失敗 |

每個專案恰好一列：`current`（全部已是目標版、混合檔不用合併、指標已指向目標包）、`migrate`（列出要換、要補的檔與要合併的混合檔數）、`manual`（有客製，整個專案不寫，算一次人工比對）、`failed`、`excluded`。報告裡每個要求的目標恰好一次；重複、沒結果、不在清單裡的結果都算失敗；有失敗或需要人工比對就不是 ok。

**`tools/migrate_project.py` 讀寫**：

- 預演（預設）：可給單一專案、`--inventory` 私人清單或 `--all --root`。不 fetch、`git --no-optional-locks` 不刷新 index，專案裡什麼都不寫；`--json` 另存報告，但那份會列出真實專案路徑，只能留在本機。目標包預設由 `src/kit` 建 debug 包，也可給 `--archive`。
- 寫入：只能單一專案，要 `--owner`（先在那個專案走完 A1–A5，與同步器同一個占用檢查）和一次發布的四個參數。順序是：專案乾淨、占用對、驗簽並裝進快取（只寫快取）、判斷（不是 `migrate`／`current` 就拒絕，專案一個檔都沒動）、再核一次占用、寫檔、寫指標、用寫入檢查的元件比對確認結果。不 commit、不 push。

`test_migrate.py` 13 個合成測試，含 20 個目標的報告（12 遷移、3 已是目標版、2 客製、2 排除、1 失敗）；`mutants.json` 新群組全部 killed（首跑存活一個：已是目標版的檔被列進要換，已補測試；Q26 拿掉 `eol` 後剩 21 個）。`test_migrate_repo.py` 5 個測試用本 repo 的真實包與最早一版部署包當「舊版」，建 Git fixture 專案：20 個目標的清單預演（13 遷移（其中一個只有 CRLF 不同，列為備註）、2 已是目標版、2 客製、2 失敗、1 排除），前後比對每個專案（含 `.git`）的位元組與修改時間都沒變；混合檔合併計數；拒絕本 repo；寫入端用拋棄式金鑰簽一次正式發布，遷移後換掉舊 hook、補上缺的啟動器、合併 `settings.json` 時保留專案自己的 `permissions`、CRLF 的啟動器不動，並通過 `GitWriteCheck`；客製與占用不對都被拒、專案檔案不變、沒有寫指標。

**真實專案只讀跑**（Q25 第三題）：在本機一層目錄掃到 8 個資料夾，4 個沒有骨架被排除，4 個有：第一次跑 3 個可遷移（換 4 個舊檔、補 5 個 skill 模式檔），1 個停下。停下那個的兩支 `.cmd` 啟動器去掉 CRLF 後跟發布版一模一樣，是專案的 `.gitattributes` 規定 `*.cmd eol=crlf`；當時寫入檢查逐位元組比對，寫成 LF 也會在下一次 Git checkout 變回 CRLF。這登記成決策書 Q26，2026-11-12 採 (a)，見下一段；之後重跑 4 個都可遷移、0 個人工比對，那兩支列為 `crlf:` 備註。專案名稱與報告只在聊天裡講，沒有進 repo。

**行末（決策書 Q26 (a)，2026-11-12）**：`package.copy_digest` 先把 CRLF 換成 LF 再算 SHA-256，寫入檢查（`pointer.check_components`）、遷移器與 F39 盤點（`inventory.scan`）都用它比專案裡的副本；單獨的 CR（含行中間多一個 CR）仍算不同，包本身（`package.check`）仍逐位元組比對。`test_pointer.py` 加 1 個（CRLF 副本放行、單獨 CR、行中 CR、多一行都擋）、`test_inventory.py` 加 1 個；`mutants.json` 在 pointer 群組加 3 個、inventory 群組加 1 個刪改，連同兩個因改寫而更新原文的舊刪改，pointer 44 個、inventory 9 個全部 killed（首跑存活一個：「刪掉所有 CR」跟真規則在原有案例上分不出來，加了行中 CR 的案例）。

沒做的：真實專案沒有寫入，要逐專案授權；20 個真實目標的報告只有找到的 4 個，其他專案在哪裡要使用者給私人清單；客製檔沒有搬進覆寫位置的工具（F37 只有原型）；批次寫入沒做，寫入一次一個專案；`install.py`（F17）仍沒讀這個包；只在這台 macOS 跑過。

## 第二次正式發布：`beta` epoch 2（2026-11-12）

使用者同意後，先刪掉遠端 epoch 1 留下的觸發 tag `release-request/beta`（workflow 從 tag 名取 channel，只能重用同一個名字；刪之前問過使用者），在 `8bcdbb1`（含 Q27 修正）重推；使用者在 GitHub 核准 [run 43208616478](https://github.com/Baliyoho/project-bootstrap/actions/runs/43208616478) 後一次跑完，建 `channel/beta/2-b2878c41432a8431671a2772b9336bdbda57b05d63e7857eedf844dcc3e20226` 與同名 prerelease，四個檔：包 64,036、紀錄 279、簽章 326、報告 15,304 bytes。`channel/beta/1-…` 沒有被碰。

本機獨立核對：報告檔的 SHA-256 等於紀錄的 `report`；`next_keys` 沒換金鑰；解壓後 `package.check` 乾淨、正式版、版本 `2026-11-10.2`、27 個檔；本機在同一份來源重建、只把 `kind` 換成正式，digest 與 CI 發的相同；manifest 裡的能力矩陣等於 `src/kit/capabilities.json`。

乾淨環境（空家目錄、不讀 git 設定、不帶 GitHub 登入，匿名 clone 到 `8bcdbb1`）：

- 空專案直接裝 epoch 2：根公鑰驗簽、鋪 27 個檔，對真的 GitHub 跑寫入檢查放行（最新與已安裝都是 epoch 2）。
- 同一個專案先裝 epoch 1：寫入檢查 `release-mismatch`（channel 最新已是 epoch 2，舊版停下）。再裝 epoch 2：沿 epoch 1 的 `next_keys` 驗簽，指標換到 epoch 2；寫入檢查 `component-drift: .claude/hooks/pre-push-handoff.sh`——安裝器只換快取與指標，專案裡的共用檔還是 epoch 1 的舊 hook（Q27 正好改了它），把專案檔案換新是遷移器的事，照設計停下。這是第一次在 GitHub 上沿金鑰鏈升級。
- `selftest.py --cache` 讀已安裝的 epoch 2 包：矩陣來源標 `installed b2878c41…`，Codex CLI `0.164.0` 在 posix 與 windows 兩邊的接線自測都過；沒有 strict ready。

沒驗的：遷移器把舊專案的共用檔換成 epoch 2（真實專案依 Q14 不同步，合成專案的寫入端在 `test_migrate_repo.py`）；Windows／Linux 上的安裝。
