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

每個管道的整數序號要求連續；同一請求重送回原收據、不重做效果，改內容重用序號及跳號拒絕。只保存最後一個重送收據，較舊序號拒絕。封閉管道不恢復身分；未知例外只回固定錯誤並關閉管道，不把例外原文輸出。請求限制 8 KiB，重複 JSON 欄位、超大／畸形輸入皆拒絕。

`broker_fixture.py` 用實際 macOS sandbox 子程序測 11 次請求。與前面的 `isolation.py` 小範圍機制實驗不同，這個 profile 預設拒絕檔案讀取，只開 OS／Python 執行所需目錄、合成唯讀 repo 與自身 scratch；私有資料庫、另一線 scratch、連到私有庫的 symlink 都不可讀，正式視圖不可直接寫。Python 啟動器還需要逐層解析 runtime 祖先目錄，僅允許祖先目錄本身，不放開整棵樹；缺少它會在測安全邊界前就啟動失敗，不能當成功阻擋。繼承管道不傳 parent capability，其他描述符關閉，環境只留基本 PATH 與禁止 bytecode 寫入設定。

負向案例涵蓋冒名、自行授權、跨線資源、額度耗盡、重送、關閉／假造 channel、pending epoch、例外遮罩、重複 JSON key、深巢狀／過大輸入。整合探針再故意取消私有讀取保護、令子程序啟動失敗、送超大管道訊息，必須報不通過；合法 scratch 與代理寫入須能成功，避免把「整個程式跑不起來」當成保護。

**仍未交付的邊界**：父程序是可信測試 fixture，不是已驗收的人類授權服務；未實作授權簽發／有效期、人類介面、重連及耐久 request 去重，管道斷線後不能自動用新身分重送可能已執行的動作。存放的是代理內容庫，尚無同步到真實工作樹的 materializer／crash recovery；合成 effect 不會刪真檔或呼叫付費 API。尚未做 sandbox 逃逸審查、正式 launcher、跨 OS／跨機或任何模型／桌面工具接線。原始同 UID 反例照留，完整需求判定不因本探針通過而改成通過。

## F50 與索引權威

`session.py` 實作狀態轉移及改名 adapter 契約；接棒／續聊、等待、交棒、重試、下限次數、缺工具、讀回不符都有測試。handoff receipt 的真實來源尚須工具 adapter 驗證，呼叫端自己填四個 True 不是可信交棒證據。returned state 要先耐久保存再重試外部改名；目前尚無正式持久儲存與工具事件接線，不能宣稱自動改名完整交付。`from_title` 只能恢復顯示欄位；事件去重須保存整份 state，不能只靠標題復原。

全部 51 ID 與 F11／F13／F43 子項的**持續實作狀態唯一權威**已從 `fdc0bbd:HANDOFF.md` 移交 [status.json](status.json)。欄位保留原狀態來源、範圍、重跑入口、未知與下一個驗收點；未驗證不是待決。`registry.py` 直接從決策書第 3 節核對 ID，測缺漏、重複、子項遺失、證據不存在與憑空成功。P0 不接受任何整項「通過」宣稱；日後正式驗收須改驗收證據模型與負向案例，不能只改狀態字串。

HANDOFF 保留 writer、目前行動與此索引的指標；若索引不可讀就停止判定，不從舊摘要恢復權威。原查核報告 F01–F16 是另一組編號，不與需求 ID 混用。

## 接下來的架構工作

1. 管道／管理分權已能在合成程序驗證；接續做內容庫到工作樹的 materializer／crash recovery、持久 request 收據與重連規則，再確立正式可信 launcher。逐 surface 列出仍可繞過入口；Mac 子程序探針只是其中一層。
2. 將合成 supervisor 的停止／排空／重建上下文協定接到實際可控執行介面；不能把程式裡 application=True 當作模型已理解，也不能把 outbox 當即時通知。真實模型探針仍需另行明確授權。
3. 再鎖定需實際採用的外部元件、驗 Windows／Mac 門檻。未通過前不開始全面搬來源、改現行 A4 或部署專案。
4. 接棒成本已能逐次量測；短入口及證據失效機制需配套驗收後才切換。常態必讀超額照實報不通過，不藉此省略檢查。
