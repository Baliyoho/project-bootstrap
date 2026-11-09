# v2 P0：可重跑的契約與架構門檻

> 最後更新：2026-11-10
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

2026-11-08 Mac VM 候選已從支援查詢推進到合成 guest。`python3 -X utf8 experiments/v2/vm_probe.py` 在這台 Apple silicon／macOS 27.2 下載並核對 [Alpine 3.24.4 aarch64 netboot](https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/aarch64/netboot/) 的固定 SHA-256，從壓縮的 `vmlinuz-virt` 解出 ARM64 Image，替換 initramfs 的 `/init`，編譯並 ad hoc 簽署帶 [`com.apple.security.virtualization` entitlement](https://developer.apple.com/documentation/virtualization/adding-the-virtualization-entitlement-to-your-project) 的 Swift runner。原壓縮 kernel 使 VM start 回 `VZErrorDomain Code=1`；解壓後啟動成功。影像只快取於本機暫存目錄，repo 不保存下載的二進位。探針建立一個無網路裝置、只共享新暫存目錄的 VM；guest 以 `setsid` 啟動持 guest 檔案鎖、每 0.2 秒寫一次共享 heartbeat 的後代。guest 自查鎖被占用與子程序另有 session，host 另查 heartbeat 在運行中增加。這是有限的合成執行面，沒有測真實工具或任意命令。

同輪實測 [`stop`](https://developer.apple.com/documentation/virtualization/vzvirtualmachine/stop(completionhandler:)) 回呼成功且 VM state=0 後，heartbeat 停止；直接 SIGKILL host runner 後 heartbeat 也停止，重新啟動 VM 才恢復增加，舊 guest 的獨立 heartbeat 檔保持不變。**host 的 `flock` 對同一 virtiofs 檔案在 guest 持鎖期間仍可取得鎖**；再同時啟動兩台 VM 共用同一目錄與鎖檔，兩個 guest 都回報持鎖且各自的 heartbeat 增加。這個鎖不能跨 host／VM 協調單 writer，也不能用 host 鎖取得當作退場證據。

2026-11-08 的後續整合：runner 增加父程序獨占的控制管道，收到停止命令或父端消失時呼叫 VM stop，避免用舊 PID 發訊號。`vm_probe.py` 實跑控制管道 EOF 後的停止，並把一台仍寫 heartbeat 的合成 VM 接到 `managed_fixture.py` 的切換：先在私有資料庫記錄未確認 VM，再封住 epoch 0、回收單 worker、要求 VM stop、核對回呼及 heartbeat 穩定並保存證據，最後才啟用 epoch 1。若退場失敗或證據未保存，切換維持 pending；重啟拒絕把未知 VM 當成已退場。真 VM 探針另以 SIGKILL 父程序實測 guest 因管道 EOF 退場、但新父程序因無持久退場證據而拒絕恢復。

2026-11-09 再接一項固定合成操作：epoch 0／1 的整數乘法各由一台 guest 執行，結果經既有 outbox／broker 寫入合成工作樹。VM 退場紀錄改按 actor＋epoch 保存，兩筆退場證據都保留；舊 epoch 未送出的請求在退場後被拒。首次連續啟兩台的反例抓到啟動狀態只按 actor 更新、使舊列從 retired 倒退為 running；現改按 actor＋epoch 且只許 unconfirmed→running。

同日後續把這項合成操作的請求及結果移出 virtiofs 共享 scratch，改走 runner 配給該 VM 的第二個雙向 virtio console（`/dev/hvc1`）；parent 持有獨立管道端點，guest 不接觸正式工作樹。host 對回覆限制 128 bytes、核對請求 ID／epoch，逾時、截斷、錯 epoch 均拒絕。實跑第一次發現 TTY 回顯把請求當成回覆；guest 須在已開啟的 fd 上設 `raw -echo` 才能收到有效結果。真 VM 探針再次量到兩個 epoch 的結果經 broker 套用。離線負向測試在共享 scratch 放同名 symlink／hardlink 結果，確認 host 的算術結果只讀專用通道；這不證明同 UID host 不能干擾 runner 或 parent。VM 的正式寫入能力仍只有 parent broker，沒有直接掛載合成 repo。[Apple virtio console 文件](https://developer.apple.com/documentation/virtualization/vzvirtioconsoledeviceserialportconfiguration)說明雙向 file handle attachment 的介面。

2026-11-09 再加一條固定合成寫入路徑：parent 對同一 VM 的專用 serial 發出有 nonce／epoch／序號的算術命令，guest 執行後自己格式化受限的 `note` broker 請求。parent 限長 256 bytes 並核對 nonce、epoch、序號及固定 schema，將 guest 原始請求 bytes 寫入獨立 principal 的 `RequestJournal` 後才送 broker；channel 的資格與 `note` 範圍由可信 parent 簽發，票據不交給 guest。真 VM 探針在同一合成資料庫啟動 host worker 及另一 guest principal，確認寫入事件的 actor 是 guest 而非 host worker、檔案內容為 guest 計算的 `10`；前提進入 pending 後仍在運行的 guest 再送舊 epoch 請求，broker 留下拒絕收據且檔案不變。離線測試另驗額外 actor 欄位、錯 epoch、截斷回覆及 outbox 的原 bytes／重啟後重送。這是**單一固定 shell 操作**的管道歸因，不代表 guest 已持有通用工具或可信身分證明；parent 直接提供 guest 的計算輸入，沒有把模型上下文或受管工具搬入 VM。

2026-11-09 後續將固定 guest broker 寫入路徑改成無共享目錄模式：runner 不配置 virtiofs 裝置，guest 反向嘗試 mount `probe` 並要求失敗，也不啟 heartbeat 子程序；雙方啟動標記與專用 serial 就緒後才受理請求。真 VM 再跑 `guest_broker`，合成寫入與 pending epoch 拒絕仍通過；離線負向測試驗缺任一標記、guest 宣稱已 mount 或意外取得共享目錄會阻擋。其他 VM 退場、兩 epoch 與跨 VM `flock` 反例仍刻意掛可寫 scratch，用來量測原邊界；不能把固定 broker 路徑的無共享配置外推到它們。

2026-11-09 再將**固定合成受管程式**拆成 `vm_managed_worker.sh` 並封入 initramfs。無共享 guest 的 `/init` 設好 console 後執行它；worker 一次載入 epoch／factor，之後 parent 只送 value／序號／base，乘法與 broker 請求由 guest worker 完成。`guest_broker` 探針不啟 host worker，在 epoch 0 啟 guest、記原始請求、完成寫入；建立 pending 後，仍在運行的舊 guest 請求遭拒，未完成操作失效。確認舊 VM stop 後啟另一台無共享 VM，載入 epoch 1 的 factor，取得載入確認、application ACK 並啟用新前提；新 guest 寫入 `21`，私有日誌保留兩筆寫入的同一 principal、各自 epoch 及三筆原始請求。真 VM 探針 exit 0；離線負向測試另驗 context ACK 與 base 不符。這只把**固定 shell 工具**放進 VM，沒有模型或通用桌面工具，也沒有讓 guest 取得 broker 管理權或票據。

專用 console 讓請求與同一台 VM 的裝置連接，但不是防同 UID host 程序偽造的身分證明；可信 parent 仍可代送，故 actor 只能代表本合成管道的授權歸屬，**不是對任意實際操作者的完整歸因**。舊 `managed_vm_switch` 路徑仍借 host worker channel 並掛共享 scratch；新 `guest_broker` 是獨立的無共享 guest worker 路徑，不能把兩條路徑的證據拼成完整保障。新路徑的 VM stop 證據已由 `guest_runs.py` 持久記錄（見下段）；掛共享 scratch 的舊路徑仍有 guest 可直接改檔及已寫效果不回滾的問題。正式工作樹、外部網路／效果、host／hypervisor 崩潰、其他 OS、真實工具及成本尚未驗。父程序在保存證據前中斷時故意保持阻擋，尚無安全解除途徑。舊實驗庫的單鍵 VM 紀錄不自動遷移，應使用新合成 fixture 重跑。`VM_PROBE_OK` 只表示本機合成觀察完成，不解除 Mac 多程序工具的阻擋。

2026-11-08：`managed_fixture.py` 將 supervisor 的固定 worker 協定、guardian 和父程序 outbox 接到同一個 macOS 合成執行面。一鍵入口的 `managed_probe` 先在 epoch 0 留下一筆未送出的結果與一件執行中的工作，再寫入通知並封住 epoch 0。舊 worker 確認退場後，替代 worker 沿用固定啟動計畫，從管道讀取新前提並回報摘要；確認與啟用在同一交易完成。重送舊請求保留原始 bytes 並被拒，只有 epoch 1 的新結果寫到合成工作樹。`test_managed_fixture.py` 另驗停止未確認、載入舊前提、離線收件者與回應遺失。

2026-11-09 晚間補上無共享路徑的**持久 run 帳本** `guest_runs.py`。parent 在開機**前**於同一私有資料庫寫入 `starting` 列：parent 自訂 run id、probe id，以及實際交給 runner 的 runner 二進位、kernel、initramfs、`/init` 與工具腳本 SHA-256；host 確認無共享開機後轉 `running`，退場只接受 host 停機標記、相同 probe id 與 runner 結束碼 0，額外欄位一律拒絕。actor 只要有未退場列，就不能再開新 guest；application ACK 只接受 pending epoch 的唯一存活 run，寫入前也要該 run 是當前 epoch 唯一存活者。重開資料庫只讀帳本，未退場就 `vm-retirement-unconfirmed`，不看 PID、時間或 guest 日誌推定。真 VM `guest_broker` 改經帳本完成兩 epoch，關閉再重開資料庫核對兩筆退場與身分；新增 `guest_parent_sigkill` 在 guest 運行中 SIGKILL 父程序，VM 因控制管道 EOF 停止，但重開帳本仍保持 `running` 並阻擋重啟。`test_guest_runs.py` 的 6 個離線測試在 scratch 副本逐一移除 6 個守門條件，都會失敗。同輪發現 runner 的 stderr（host 標記）與 guest console 原本合寫同一日誌，guest 印出 `HOST_STOPPED state=0` 就能混進停機判讀；已改成 `launch()` 把 stderr 寫到另一個 `.host` 檔，所有 VM 探針的 host 啟動／停機判讀只讀該檔且要求整行相符，離線測試驗 guest console 的偽造行不被採用（移除分離後測試失敗）。再把 channel 與 run 生存期綁定：`mark_running` 要求該 run 的 actor 持有的 capability，帳本只存其 SHA-256；`require_live`／ACK 必須出示同一個 capability。退場在同一交易呼叫 `Lab.resume` 輪換 capability，所以舊 guest 的 channel 不只靠 parent 記得查帳本，而是 broker 本身以 `unknown-session` 拒絕；真 VM 在舊 guest 退場後用舊 journal 再送寫入，被拒且檔案不變，替代 guest 由 parent 重新 `connect` 取得新 channel。邊界：身分是 parent 選定檔案的 digest，不是 guest 實際執行內容的證明；host 檔仍由同 UID 可寫，不防 host 程序偽造；父程序在退場前崩潰時 capability 不會輪換（但持有它的 parent 已死，重開帳本仍阻擋），崩潰後也還沒有可信的人工解除路徑。

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

`test_release.py` 6 個測試用拋棄式 ed25519 金鑰實測：每次寫入都重新確認；離線與重播；就地改元件（F32）；只改 hook 或 schema 的新 release 讓舊客戶停止（F18）；他人金鑰、錯 namespace、竄改、錯 channel、過期、未來簽發、型別錯、epoch 倒退、調試版。scratch 副本逐一移除 12 個守門都會讓測試失敗；原本的「開頭為 `/`」檢查被空片段檢查涵蓋而無法單獨測，已刪除。邊界：可信端與金鑰是測試替身，沒有 CI 身分、金鑰治理、網路傳輸或原子安裝；沒有接進現行 `git-freshness.sh`、`sync_project.py` 或任何工具，現行 720 分鐘快取照舊。

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

`test_impact.py` 4 個測試，其中一個讀真實的 `status.json`；scratch 副本逐一移除 8 個守門都讓測試失敗（原本「改到的測試本身也列入」那一行因為已被需求對應涵蓋，刪掉了）。邊界：粒度是檔案；目前有 14 個 v2 檔（如 `broker.py`、`session.py`、`lifecycle.py`）沒被列為任何 ID 的證據，改它們只會回全驗；專案安裝清單由呼叫端提供，未接 `sync_project.py`。

## 可重跑的 mutation 檢查（2026-11-09）

本輪各節提到的「scratch 副本逐一移除守門」原本只存在聊天暫存檔，換機就拿不到（F49）。現在刪改清單存在 `mutants.json`（每項記檔案、原文、替換與要跑的測試模組），`mutants.py` 在暫存複本逐一套用並跑測試，結果分 killed、survived、stale（原文不是恰好出現一次，代表規格過期）；只有全部 killed 才 exit 0，工作樹不被改動。

```bash
python3 -X utf8 experiments/v2/mutants.py
```

2026-11-09 macOS 實跑：144 個全部 killed（之後加入 `doctor.py` 的 8 個，單獨跑也全部 killed，共 152 個），約 90 秒；先前 `lines.py` 刪掉的兩段冗餘守門對應的刪改已從清單移除（執行器把它們報為 stale）。`test_mutants.py` 用合成套件測執行器本身。邊界：只涵蓋本輪新增模組，較早模組的 mutation 仍只在上文敘述；刪改由人挑選；太慢，不在 `verify_v2.py` 預設流程。

## 本機能力診斷（2026-11-09）

`doctor.py` 是 F16b 的原型。`diagnose` 把三種缺口分開報：缺工具（PATH 上找不到）、缺設定（環境變數沒設或只有空白）、連線失敗（工具與設定都在，probe 卻沒回 `True` 或拋例外）。缺前提的連線不呼叫，記 `not-attempted` 並列出缺什麼，所以沒設金鑰不會被誤報成服務掛掉。設定只看名稱有沒有值，值本身與例外訊息都不進報告。`test_doctor.py` 2 個測試；`mutants.json` 8 個刪改全部 killed。邊界：清單由呼叫端提供，還沒列骨架實際需要的工具與設定；只看環境變數，不查設定檔。

## 跨文件矛盾偵測（2026-11-10）

`contradictions.py` 是 F45 的原型，只比對宣告過的規則表與待決登記，不判斷任意散文。每條規則列出各說法的正規式與正確說法：寫成反向說法的位置報 `reverse-rule`（文件、節、行號），同一檔不同節說法不同報 `section-conflict`，不同檔說法不同報 `cross-doc-conflict`。待決部分讀決策書第 6 節的登記列（`- **Q1** … 狀態：待決／已決`）：HANDOFF 懸置節每一條都要引用仍待決的編號，否則 `pending-unregistered`；已決編號在懸置節或任何文件與「待決／待使用者決定」同行出現就報 `decided-still-pending`。讀不到的文件、必須出現卻沒出現的規則、缺登記節都是未知，不算通過；程式碼區塊與呼叫端標為歷史的節會跳過，但跳過的行數照列。部署包的範本放在程式碼區塊裡，所以對它設為照掃。

`REPO_CONFIG` 是本 repo 的宣告表（核心優先序一條規則、決策書第 6 節、HANDOFF 懸置節），`python3 -X utf8 experiments/v2/contradictions.py` 直接對本 repo 跑。2026-11-10 第一次跑就抓到一處：HANDOFF 懸置的「崩潰後人工解除的可信核准來源」沒登記，決策書第 6 節卻寫「無」；已補登為 Q1，HANDOFF 改成指向它。`test_contradictions.py` 15 個合成測試、`test_contradictions_repo.py` 對本 repo 文件要求未發現；`mutants.json` 23 個刪改全部 killed。邊界：只認宣告過的說法，換個寫法就看不到；登記列格式固定；HANDOFF 懸置每條都要引用編號，之後交棒寫懸置節要照這個格式；未接進現行 A／B 程序。

## 規則理由、否決路線與路線圖（2026-11-10）

`trail.py` 是 F6／F7／F8 的留痕原型。決策紀錄仿 MADR：編號、標題、狀態（採納／被取代／否決）、日期、當時基準、理由，以及考慮過的替代方案（每個要有結果與理由）。規則記它出自哪個決策，`why` 從規則走到理由；決策被取代時，取代關係必須雙向，`why` 會從舊的一路走到現行的，舊理由仍看得到，規則還引用被取代或被否決的決策則報出。`rejected_routes` 列出所有沒走的路與理由。`compare` 拿舊快照比新快照：決策或替代方案消失、理由被改寫都報出——理由變了要新增一筆取代它的決策，不是改舊的。路線圖由里程碑（目標、狀態、放棄須附理由）組成，任務引用里程碑；沒有進行中或規劃中的里程碑、任務掛在已結束里程碑上都會報。

`test_trail.py` 10 個合成測試；`mutants.json` 24 個刪改全部 killed。邊界：只檢查呼叫端保存的紀錄，不能證明理由為真或紀錄完整；現行決策書第 7 節、ARCHITECT、各報告仍是手寫散文，尚未轉成紀錄；HANDOFF 清理後要靠路線圖找方向，但本 repo 還沒有路線圖檔；未接進任何工具。

## 各線發現合流（2026-11-10）

`confluence.py` 是 F26 的合流原型。每條線回報的發現帶問題鍵、值、已驗證或只是聲稱（F3），以及來源、取得時間、適用範圍（F40，例如 `{"os": "macOS"}`）。`merge` 全部收進同一處：缺來源／時間／範圍的列為不完整；只是聲稱的列為未確認；已驗證、值相同、範圍相同的才成為共同依據並附全部來源；範圍不同的保留成各自帶條件的結論，不算衝突也不丟棄；範圍重疊而值不同的是衝突。`basis` 回答某線在某範圍能依據什麼：只有共同依據或範圍涵蓋它的條件結論，未確認、不完整的不行；同一鍵有未解衝突就整個擋下，即使請求範圍只落在沒參與衝突的那筆。

`test_confluence.py` 8 個合成測試；`mutants.json` 15 個刪改全部 killed。邊界：只比對各線宣告的鍵，用不同字眼問同一件事認不出來；衝突處置與共用前提改變的即時通知屬 F28，未做；未接進任何工具。

## 多專案更新的人工確認上限（2026-11-10）

`campaign.py` 是 F24 的原型，接在 `batch.assess_many` 與 `impact` 後面。每個輸入目標恰好一列動作：要更新、未受影響略過、排除、失敗、需人工逐專案比對（客製內容漂移）。人工確認分組：放行版本一次、整份更新清單一次、全部失敗一次審閱，漂移的專案每個各算一次——不把逐專案比對併成一次假裝省事。超過上限（預設 3，決策書 F24）照實報；有失敗、需比對、重複列或受影響卻沒評估的目標都不是 ok。

`test_campaign.py` 8 個測試（20 個混合目標：10 更新、4 未受影響、1 排除、5 失敗，正好 3 次確認但 NOT OK；另有一組用真的 `assess_many` 產生缺失與排除列）；`mutants.json` 14 個刪改全部 killed。邊界：確認次數是規劃值，沒有量真人實際操作；目標字串由呼叫端把 `impact` 的專案名對到批次列；未接 `sync_project.py`。

## 來源未驗證不得發出（2026-11-10）

`publish.py` 是 F35 的阻擋原型。`publish` 只有在三件事都成立時才把套件寫進發布目錄，否則丟 `Denied` 且目錄維持空的：驗證報告（`evidence.resolve` 的輸出）整體通過而且每一列都是本輪實查，沿用、未驗證、SKIP、FAIL 都拒絕，調試包沒有例外；CI 證明同時簽住 manifest digest 與報告 digest，簽完再改報告或拿別的套件的報告都算偽造結果；簽章只認設定的 CI 金鑰與身分，開發者金鑰或錯的 namespace 都是非 CI 發布。版本字串限定字元，不能用來跳出發布目錄；同版本不重複發布。

`test_publish.py` 5 個測試（ssh-keygen 拋棄式金鑰，非 macOS 時驗證器不可用即拒絕）；`mutants.json` 18 個刪改全部 killed。邊界：CI 金鑰是測試替身，握有那把金鑰就能發布；沒有真的 CI 身分、傳輸或原子安裝；現行 `verify_bootstrap.py` 的 ZIP 發布門檻仍是現行程序的阻擋點，本原型未取代它。

## 繞過規則：擋下或留痕（2026-11-10）

`bypass.py` 是 F21 的原型，照決策書分層。阻擋：`guard_commit` 讀已部署專案的 Git index（不是工作樹），已安裝 manifest 裡屬於 core／adapter 的檔，staged 內容與發布版不同或從 index 刪掉就拒絕提交——共用制度只能回來源改再同步；專案自己的檔不受限。發布未驗證來源由 `publish.py` 擋。留痕：`record` 把步驟完成或略過（略過必須附理由）寫進 JSON lines，每行帶前一行的 SHA-256；`audit` 沿鏈檢查，必要步驟既沒完成也沒登記略過就是無聲略過，鏈斷之後的行一律不採信，繞過 `record` 直接寫入的無理由略過也不算數。

`test_bypass.py` 10 個測試（真 Git index）；`mutants.json` 14 個刪改全部 killed。邊界：能改寫整份紀錄的人也能重算整條鏈，所以只抓意外與局部改動，不證明紀錄為真；`guard_commit` 未掛成 pre-commit hook，`--no-verify` 之類的繞法未處理；未接進現行 A／B 程序。

## 新專案取得制度與就地修改盤點（2026-11-10）

`install.py` 是 F17 的原型。`plan` 先預演、不寫任何檔：每個套件檔一個動作——新建、已相同、`.gitignore` 只補缺的行（不刪不重排）、其他已存在而內容不同的檔一律保留給人決定合併。家目錄與檔案系統根目錄拒絕；資料夾裡有任何不屬於套件的東西（含 `.git`）就標成既有專案，讓呼叫端先問人。`apply` 重新預演，跟人核准的那份不同就拒絕，只新建與附加；新建用排他開檔，預演後才出現的檔不會被蓋掉。

`inventory.py` 是 F39（想要、一次性盤點）的原型。對明列的專案，拿它記錄安裝的 manifest 比對 core／adapter 檔：正常、被改、遺失、讀不到；不知道裝了哪版就是未知，不算乾淨。只讀，被改的檔交給人看，因為那可能是該搬進覆寫位置的專案客製。

`test_install.py` 8 個、`test_inventory.py` 2 個測試；`mutants.json` 各 14、8 個刪改全部 killed（`install` 的 `.git` 判斷與「其他項目」重複，已刪掉冗餘守門）。邊界：只處理呼叫端給的檔案集合，部署包第 3 節的範本還沒轉成套件；未接 `sync_project.py`；盤點不掃整顆磁碟，也不判斷修改是否合理。

## F50 與索引權威

`session.py` 實作狀態轉移及改名 adapter 契約；接棒／續聊、等待、交棒、重試、下限次數、缺工具、讀回不符都有測試。handoff receipt 的真實來源尚須工具 adapter 驗證，呼叫端自己填四個 True 不是可信交棒證據。returned state 要先耐久保存再重試外部改名；目前尚無正式持久儲存與工具事件接線，不能宣稱自動改名完整交付。`from_title` 只能恢復顯示欄位；事件去重須保存整份 state，不能只靠標題復原。

全部 51 ID 與 F11／F13／F43 子項的**持續實作狀態唯一權威**已從 `fdc0bbd:HANDOFF.md` 移交 [status.json](status.json)。欄位保留原狀態來源、範圍、重跑入口、未知與下一個驗收點；未驗證不是待決。`registry.py` 直接從決策書第 3 節核對 ID，測缺漏、重複、子項遺失、證據不存在與憑空成功。P0 不接受任何整項「通過」宣稱；日後正式驗收須改驗收證據模型與負向案例，不能只改狀態字串。

HANDOFF 保留 writer、目前行動與此索引的指標；若索引不可讀就停止判定，不從舊摘要恢復權威。原查核報告 F01–F16 是另一組編號，不與需求 ID 混用。

## 接下來的架構工作

1. 管道分權、POSIX 套用、限期資格、請求保存、監護回收、Mac 禁 fork 及單 worker 的 outbox／前提切換已有合成證據。程序群組候選無法阻止 `setsid` 逃逸；多程序工具需另找 OS 隔離及可重啟核對的整樹退場證據。真人授權、票據遺失後重新驗身分及監護失效的恢復仍待做。
2. 將合成 supervisor 的停止／排空／重建上下文協定接到實際可控執行介面；不能把程式裡 application=True 當作模型已理解，也不能把 outbox 當即時通知。真實模型探針仍需另行明確授權。
3. 再鎖定需實際採用的外部元件、驗 Windows／Mac 門檻。未通過前不開始全面搬來源、改現行 A4 或部署專案。
4. 接棒成本已能逐次量測；短入口及證據失效機制需配套驗收後才切換。常態必讀超額照實報不通過，不藉此省略檢查。
