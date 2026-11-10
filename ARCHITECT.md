# ARCHITECT — 這個 repo 的結構

> 最後更新：2026-11-10。根目錄表的決策書需求數更正為 51（2026-11-06 補 F50 後漏改，`experiments/v2/contradictions.py` 首次對 ARCHITECT 跑時抓到）。

> 2026-11-09：`experiments/v2/vm_probe.py`、`vm_runner.swift`、`vm_guest_init.sh`、`vm_managed_worker.sh` 與 `test_vm_probe.py` 是 Mac VM 候選的合成探針及離線負向控制：固定映像 digest、無網路 guest。退場與跨 VM 鎖反例掛獨立暫存共享目錄及 `setsid` 後代；新固定工具路徑由 `/init` 在無共享 guest 中啟動 `vm_managed_worker.sh`，只經第二個雙向 virtio console 載入前提並發原始 broker 請求。host 核對請求後由 outbox／broker／materializer 寫入合成工作樹，正式 repo 不掛載進 VM。舊 `managed_fixture.py` 路徑仍用 host worker，按 actor＋epoch 保存各台 VM 退場證據，未確認時重啟保持阻擋；新無共享工具路徑另由 `guest_runs.py`（離線測試 `test_guest_runs.py`）在同一私有資料庫持久記錄每台 guest 的 parent 選定身分 digest 與 host 停機證據，未退場時新 guest、ACK、寫入與重啟都阻擋；每台 run 綁一個 broker channel，退場時輪換 capability。runner 的 host 標記另寫 `.host` 日誌，不與 guest console 混用。這些資料流仍未接真實工具或現行部署包，也不提供 host 故障後的自動復原保證。詳見 [P0 說明](experiments/v2/README.md)。

> 2026-11-09 新增 `experiments/v2/doctor.py` 與 `test_doctor.py`：F16b 本機能力診斷，缺工具／缺設定／連線失敗分開報，不讀出設定值。

> 2026-11-09 新增 `experiments/v2/mutants.py`、`mutants.json` 與 `test_mutants.py`：本輪守門的 mutation 規格與重跑入口（F29／F49），不在 `verify_v2.py` 預設流程。

> 2026-11-09 新增 `experiments/v2/impact.py` 與 `test_impact.py`：F31 改動影響圖，從 `status.json` 證據路徑推出元件→需求→重驗測試，未分類變更回全驗。

> 2026-11-09 新增 `experiments/v2/policy.py` 與 `test_policy.py`：F36 依所有權規劃更新、F37 只能加嚴的覆寫合併、F38 空位 schema 與說明。未接進 `sync_project.py` 或骨架。

> 2026-11-09 新增 `experiments/v2/decisions.py` 與 `test_decisions.py`：F44 待決事項與委任、F34 已宣告例外的紀錄檢查與生成視圖。未接進現行程序。

> 2026-11-09 新增 `experiments/v2/evidence.py`、`facts.py` 與對應測試：M2 證據帳（本輪／沿用／未驗證／不通過分開，沿用依賴 digest 失效與撤銷，F3／F40）與文件命題對 Git／檔案的事實 adapter（F20）。未接進現行程序。

> 2026-11-09 新增 `experiments/v2/state.py` 與 `test_state.py`：M2 狀態模型（目標／任務／下一步／風險＋證據）與生成的 HANDOFF 視圖，F1／F2／F5 原型。未取代現行手寫 HANDOFF。

> 2026-11-09 新增 `experiments/v2/readonly.py` 與 `test_readonly.py`：F23 只讀輪次前後快照比對（ref、index、變更檔、遠端），偵測標記、stage、commit、push。未接進現行程序。

> 2026-11-09 新增 `experiments/v2/lines.py` 與 `test_lines.py`：F12 並行線登記檢查，以 Git 回報的工作樹、index 與分支判定兩線是否共用。只偵測，未接進現行程序。

> 2026-11-09 新增 `experiments/v2/preflight.py` 與 `test_preflight.py`：把 `gitclaim` 的寫入時資格（遠端標記須正好是本 session、不得落後或分岔）與 `release.WriteGate` 組成單一受管寫入前檢查，`batch.py` 可選逐目標發布確認。未接進現行程序。

> 2026-11-09 新增 `experiments/v2/release.py` 與 `test_release.py`：M1 整包 manifest（元件 digest）與每次寫入前的 nonce 簽章新鮮度確認原型（F18／F32／F33），沒有快取路徑。未接進現行 `git-freshness.sh` 或同步工具。

> 2026-11-09 新增 `experiments/v2/gitclaim.py` 與 `test_gitclaim.py`：F9／F10 的 M3 開工資格與收尾閘門原型，對本機 bare origin 實測，收尾成功才產生 `session.py` 的交棒收據。`batch.py`／`test_batch.py` 在其上做多目標彙總（F30）。未接進現行程序。詳見 [P0 說明](experiments/v2/README.md)。

> 2026-11-08 新增 `experiments/v2/tree_probe.py` 與 `test_tree_probe.py`，只在合成 POSIX 程序群組比較一般後代與脫離 session 的後代，透過檔案鎖觀察退場。一鍵入口列出這個候選反例；它不接入 `lifecycle.py`，也不提供任意程序樹保證。詳見 [P0 說明](experiments/v2/README.md)。

> 最後更新：2026-11-08。新增 `experiments/v2/approvals.py`，以固定公開金鑰與驗證器驗收合成動作簽核。私有資料庫同一交易保存簽核文件、簽章與限期授權；broker 在當前前提下才可消耗。簽署測試用一次性金鑰；真人身分、金鑰治理及真實動作未接入。範圍見 [P0 說明](experiments/v2/README.md)。

> 最後更新：2026-11-08。新增 `experiments/v2/managed_fixture.py`，由可信父程序經固定啟動計畫與 guardian 連接單一 macOS 合成 worker。前提切換先封住舊 epoch，再回收並替換 worker，核對新前提摘要才啟用。合成結果由父程序 outbox 送往 broker／materializer。一鍵入口獨立呈現此探針，範圍與失敗案例見 [P0 說明](experiments/v2/README.md)。

> `experiments/v2/lifecycle.py` 經 `guardian.py` 啟動受管 worker。父程序獨占生命管道寫端，監護在 EOF 後以持有的 Popen 終止並 wait；它把回收證據寫到本次啟動專用的私有檔案。新父程序經 `reconcile` 核對原票據、計畫與檔案身分後可續作，`managed_fixture.py` 從初始前提或持久通知重建上下文。缺證據仍停止。Mac fixture 禁止 fork／spawn／signal；任意後代、Windows、真實人類入口未驗收。

> 2026-11-07 重連資格：新增 `experiments/v2/launcher.py` 與 `test_launcher.py`。可信 parent 產生 principal、保存重連票據雜湊與限期資源資格；broker 每次請求及恢復寫盤前重查。原始請求在送出前寫入私有 outbox，重啟沿用相同 bytes；缺漏不猜測重建。Mac 合成管道探針改用此資格層，尚非正式人類授權服務或完整工具 launcher。現行部署結構與程序不變。

> 2026-11-07 恢復覆核：materializer 的私有實驗庫新增 root 身分／資源映射綁定，拒絕以新設定接管舊事件；broker 重送寫入時重查當前資源權限，恢復 replace 後補目錄 fsync 才記 applied。反例與恢復測試同存 `test_recovery.py`。僅合成原型，舊無綁定實驗庫與搬機遷移尚不支援；現行部署結構不變。

> 2026-11-07 最新 P0 批次：新增 `experiments/v2/materializer.py` 與 `test_recovery.py`，在合成 POSIX 工作樹做 prepared→replace→applied 恢復；Lab 交易支援 savepoint，request 收據與內容／合成效果同交易，parent 可輪替 capability 恢復已知 principal。broker 的受隔離 agent 探針已接套用層，實測程序終止及失敗反例；不代表真實專案、Windows、斷電、多 writer 或外部服務 exactly-once 已驗收。下方前批「沒有 materializer」描述當時範圍；現行限制見 [P0 說明](experiments/v2/README.md)。

> 2026-11-07 P0 管道分權：新增 `experiments/v2/broker.py`（parent-only 管理能力、管道身分、資源與請求序號）、`broker_fixture.py`（受隔離合成 agent）及兩份測試；write／effect 的 epoch 在資料交易內檢查。一鍵入口彙整 broker 探針，報告缺項亦有負向測試。內容仍只存實驗庫，沒有正式工作樹 materializer、模型或工具接線；現行部署包及副本不變。

> 最後更新：2026-11-07。v2 P0 補 `supervisor.py` 與其負向測試，驗固定子程序的中止、上下文重建與 epoch 啟用；尚未接入模型／桌面工具。下列歷史日期與數字只對各自基準。

> 2026-11-06 v2 P0 結構：新增 [experiments/v2](experiments/v2/README.md) 的隔離契約、反例、Mac OS 邊界探針、F50 狀態機、成本量測及 [51 ID 現況索引](experiments/v2/status.json)；[tools/verify_v2.py](tools/verify_v2.py) 統一執行，既有驗證器加一項 P0 回歸並有報告負向測試。需求決策版本 2 補 F50；狀態權威由 HANDOFF 逐項移交到索引。這些只測合成資料，不部署；部署包仍是現行 22 檔權威，VERSION／skill／hook／接線不變。下方長結構登記是歷史，不取代本段。

> 2026-11-06 最新結構登記：新增 [需求實現規劃](project-bootstrap-implementation-plan.md)，根目錄 Markdown 總數 26；內容為技術棧選型與 50 項需求映射，不是已部署架構。部署包、skill、hook、接線與 VERSION 未變。
> 2026-11-06 需求文件分家：原 requirements 改名 history，新增 decision 為現行唯一權威；本 repo 共 25 份 Markdown。下方舊結構登記只描述當時狀態。
> 2026-11-06 最新結構登記：功能完整性複查（v3.9）與八項缺口全部納入（v3.10），**根目錄新增 [project-bootstrap-requirements-completeness-audit-2026-11-06.md](project-bootstrap-requirements-completeness-audit-2026-11-06.md)**，本 repo **24 份 Markdown**（前次 23）。[需求權威版](project-bootstrap-requirements-history.md)第 4 節**新增第九類「不該流出去的東西」與八條 F42–F49**，條目數 42→50；第 6 節留「已更正」指標並記 C01–C08→F42–F49 的對應；第 9 節新增兩個小節。本檔「這個 repo 刻意沒有的東西」那節**新增一條正式例外宣告**（F46 的落地方式，使用者 2026-11-06 決定）。驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，**未改檢查器**，不部署、不同步。⚠️ **本檔漏了一輪**：新增那份報告的 commit（`3d7b991`）按「改本檔的時機」就該同時改本檔，當時沒改——`verify_bootstrap.py` 只查本檔的日期標頭，查不到「根目錄多一個檔案而本檔沒登記」，所以這一類漏掉目前沒有守門人（它正是新納入的 F45 要擋的形狀，而 F45 還沒實作）。
>
> 2026-11-06 前次結構登記：使用者逐項定案第 6 節的五項待決，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3.4**（50 處定點修改，含第 4 節 28 項強度＋第 9 節新增「v3.3 的定案」小節）：第 4 節原標「待定」的 28 項最低強度全部填上（F9／F10／F18／F35／F37 阻擋，F6／F7／F8 留痕，其餘偵測）、F11(b) 保留為必要並定「不允許部分歸因」、F28 定為使用前＋立即通知、證據時效政策三條搬進 F40 驗收、強度表前的說明與第 7 節第 1 步的前置條件連帶改寫、第 6 節只剩 D8 專案數與四項待蒐集資料，兩處歷史「仍未定案」行加上版本指標（v3.3 與 v3.4 同日採納，日期分不出來）。入口摘要同步更新 AGENTS 與本檔。**改了檢查器一處**：`verify_bootstrap.py` 的「結構摘要一致性」原本用全行子字串 `'3.4'` 找 README prompt 那一列，本檔表格寫進 `v3.4` 就把需求文件那一列誤判成它（本輪當場 FAIL），改成認範本編號欄 `| 3.4 |`，並加一個反向保險（缺了那一列仍要被判出來）。本 repo 23 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，不部署、不同步。
>
> 2026-11-06 前次結構登記：使用者指示直接依[2214 最後審閱指令](project-bootstrap-requirements-final-review-2026-11-05-2214.md)的五項替換指令修改，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3.3**（18 處定點修改＋第 9 節新增「v3.2 的修正」小節與一筆勘誤）：第 3 節 D3 段的範圍句只限定理由與事故敘述、D3 改稱方案約束而非實作狀態報告；F13 理由改成明示轉述既有紀錄與 2026-10-30 的查證範圍；第 5 節把達成狀態切換規則收成唯一一份（逐需求 ID／子項、移交條件、未驗證也可移交、部分子項與新位置不可讀的處理），環境那一條改成區分工作假設與已查證觀測，「不滾動更新」改成按用途與內容判定並取消 append-only 豁免；第 7 節第 1 步改成引用第 5 節並補三種紙上核對輸入；第 8／9 節改用新界線（範圍不保證歷史事實正確、不免除勘誤責任、可在原處加「已更正」指標）。入口摘要同步更新 AGENTS 與本檔。本 repo 23 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，**未改檢查器**，不部署、不同步。
>
> 2026-11-05 前次結構登記：使用者採納 [1632 定向審閱](project-bootstrap-requirements-response-review-2026-11-05-1632.md)，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3.2**（12 處定點修改＋第 9 節新增「v3.1 的同日修正」小節）：第 3 節 D1／D2／D3 的理由、F16b 的分類括號、F11 共同邊界與 F13 理由各自定錨到當時的觀測；第 5 節新增三條歷史例外限制、第三類狀態（環境假設）、實作狀態逐項單一權威與逐 ID 切換，並把「HANDOFF 耐久性最低」限定在可見性；F11 驗收 (b) 新增四種現在就可判定的情境並禁止編造還原比例；第 7 節第 1 步新增三個接縫的移交責任；第 8／9 節各加一行整段範圍以取代逐句免責。根目錄新增[對 1632 的逐項回覆](project-bootstrap-requirements-response-review-reply-2026-11-05-2150.md)，其中更正 1620 把共現反例指在第 295 行（真正的反例是第 277 行）。本 repo 22 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，**未改檢查器**，不部署、不同步。

> 2026-11-05 前次結構登記：使用者採納 [1606 審閱](project-bootstrap-requirements-response-review-2026-11-05-1606.md)，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3.1**（9 處定點修改＋第 9 節新增「v3 的同日修正」小節）：第 5 節的現況禁令從「不含任何『現在有沒有』的判斷」改成「不承載持續更新的達成狀態」並允許帶日期的歷史事故、新增決策狀態與達成狀態的分工；第 3 節與 F28 驗收補日期；第 6／7 節移除 F11(b) 的實作判斷；F11 驗收 (b) 補「揭露未知不等於達成歸因」。根目錄新增[對 1606 的逐項回覆](project-bootstrap-requirements-response-review-reply-2026-11-05-1620.md)。本 repo 20 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，**未改檢查器**，不部署、不同步。

> 2026-11-05 前次結構登記：使用者採納第三輪審閱與逐項回覆的結論，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3**（21 處定點修改＋新增第 9 節的改動理由；**未新增功能條目或編號**，但 F11(b) 新增了內容識別與還原程度揭露的要求，已明示為擴張）；根目錄新增[第三輪審閱的逐項回覆](project-bootstrap-requirements-response-review-reply-2026-11-05-1545.md)，是那次採納的理由記錄。本 repo 18 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，不部署、不同步。

> 2026-11-05 前次結構登記：新增 [第三輪需求審閱](project-bootstrap-requirements-response-review-2026-11-05-0927.md)，逐項核對 Opus 2310 回覆；尚未採納、不部署、不同步。17 份 Markdown，驗證 52 項與骨架 22 檔不變。

> 2026-11-04 最新結構登記：新增 [再評估的逐項回覆](project-bootstrap-requirements-response-reply-2026-11-04-2310.md)——對 S1–S6 與六條整體校正的判定、理由與建議措辭，**尚未採納**；需求權威版、skill／hook／接線／`VERSION` 皆未動。本 repo 16 份 Markdown；驗證仍 52 項，骨架仍 22 檔。不部署、不同步。
>
> 2026-11-04 前次結構登記：報告檔名已依使用者要求補上原提交時分 2230，引用同步更新；新增 [需求修訂再評估](project-bootstrap-requirements-response-2026-11-04-2230.md)，核對 Opus 回覆與修訂，屬未採納審閱快照，不部署、不同步。本 repo 15 份 Markdown；驗證仍 52 項，骨架仍 22 檔。下列舊登記保留歷史理由。

> 2026-11-04 本次結構登記：使用者採納需求定義的 v2 修訂，[project-bootstrap-requirements-history.md](project-bootstrap-requirements-history.md) 改成 v2 全文、原 v1 內容刪除（在 git 歷史，基準 `81a8cff`）；中途那個帶版號的臨時檔已 `git mv` 到權威路徑並不再存在——**檔名不帶版號**，否則版號本身會腐化，而 `AGENTS.md` 與審閱意見檔的連結會斷。根目錄淨增一檔（審閱回覆），本 repo 14 份 Markdown；驗證項仍 52 項、骨架仍 22 檔，skill／hook／接線／VERSION 皆未動。前次登記：根目錄新增 `project-bootstrap-requirements-v2.md`（已不存在，已搬到權威路徑） 與 [project-bootstrap-requirements-review-reply-2026-11-04.md](project-bootstrap-requirements-review-reply-2026-11-04.md)——前者是依 Q1–Q7 逐項評估修訂的需求草案（新增 F40 證據時效、「強度」詞彙與 9 項驗收區塊，收緊 D1 與 F11、F13、F26、F28，刪掉「6 個專案時 F30／F31 可以不要」），**尚未採納，權威仍是 v1，採納後應取代並刪除 v1**；後者是對審閱意見的逐項回覆與同意／不同意的理由。兩者都不部署、不同步，驗證項仍 52 項、骨架仍 22 檔，skill／hook／接線／VERSION 皆未動。前次登記：新增需求審閱意見 project-bootstrap-requirements-review-2026-11-04.md，供下一棒討論，尚未採納、不部署、不同步。原登記：根目錄新增 [project-bootstrap-requirements-history.md](project-bootstrap-requirements-history.md)——與使用者逐項定案的功能需求（F1–F39）與前提決定（D1–D8），是「要什麼」的唯一家；現況對照與工具評估尚未做，刻意不寫進它裡面。不部署、不同步，驗證項仍 52 項、骨架仍 22 檔，skill／hook／接線／VERSION 皆未動；`AGENTS.md` 的開工段加一段指向它。前次 2026-11-03：驗證新增「同步升級 mode」與「結構摘要一致性」，共 52 項、骨架仍 22 檔。同步器原子替換前複製既有檔案權限；否則 POSIX 的可執行 wrapper 會隨 inode 替換失去 x bit。Windows 只驗呼叫與失敗契約，POSIX 分支另驗 0755／0640、直接執行與 Git mode diff。結構摘要區分 Claude import／Gemini 文字指標與收工／開工 prompt。只改工具及 ARCHITECT 範本，不改 skill／hook，VERSION 與 source 標記不跳；ARCHITECT 是專案實例，不自動覆蓋既有專案。

> **本檔＝結構的唯一權威**：`project-bootstrap` 由什麼組成、每樣東西的家在哪、改哪裡會影響到什麼。
> 最後更新：2026-11-08（F46 文件設定同組情境：驗證 58 項，骨架 22 檔，未改部署包與版本；前次：需求權威版採納 **v3.4**：使用者定案五項待決——第 4 節 28 項強度全部填上、F11(b) 保留且不允許部分歸因、F28 使用前＋立即通知、證據時效政策進 F40 驗收、第 6 節只剩 D8 與四項待蒐集資料；檢查器「結構摘要一致性」改成認範本編號欄並加反向保險（`v3.4` 這種版本號曾讓它誤判）；23 份 Markdown，骨架與驗證項不變。前次：需求權威版採納 v3.3 修正：18 處定點修改＋第 9 節新增「v3.2 的修正」小節與 append-only 豁免的勘誤，入口摘要同步更新 AGENTS 與本檔；23 份 Markdown，骨架與驗證項不變，未改檢查器。前次：新增 2214 最後審閱指令，23 份 Markdown；骨架與驗證項不變。前次：需求權威版採納 v3.2 修正並在第 9 節新增 v3.1 的同日修正小節，根目錄新增對 1632 的逐項回覆 project-bootstrap-requirements-response-review-reply-2026-11-05-2150.md，22 份 Markdown，驗證項與骨架不變。前次：新增 1632 定向審閱，21 份 Markdown，骨架與驗證項不變。前次：需求權威版採納 v3.1 修正並在第 9 節新增同日修正小節，根目錄新增對 1606 的逐項回覆 project-bootstrap-requirements-response-review-reply-2026-11-05-1620.md，20 份 Markdown，驗證項與骨架不變。前次：新增 1606 審閱回覆，19 份 Markdown，驗證項與骨架不變。前次：需求權威版採納 v3 修訂並新增第 9 節的改動理由，根目錄新增第三輪審閱的逐項回覆 project-bootstrap-requirements-response-review-reply-2026-11-05-1545.md，18 份 Markdown，驗證項與骨架不變。前次：根目錄新增再評估的逐項回覆 project-bootstrap-requirements-response-reply-2026-11-04-2310.md，16 份 Markdown，未採納、不部署、不同步，驗證項與骨架不變。前次：需求定義採納 v2 修訂：project-bootstrap-requirements-history.md 改成 v2 全文、原 v1 刪除，帶版號的臨時檔已搬到權威路徑；根目錄淨增審閱回覆一檔，14 份 Markdown，驗證項與骨架不變。前次：根目錄新增需求定義 v2 草案 project-bootstrap-requirements-v2.md 與審閱回覆 project-bootstrap-requirements-review-reply-2026-11-04.md，兩者未採納、不部署、不同步，驗證項與骨架不變。前次：根目錄新增功能需求定義 project-bootstrap-requirements-history.md：F1–F39 與 D1–D8，不部署、不同步，驗證項與骨架不變。前次：2026-11-03 新增第二輪複審快照 project-bootstrap-reaudit-2026-11-03.md；接棒入口要求先讀，不部署、不同步，驗證項與骨架不變。前次：2026-11-02 F13／F16 新增同步範圍與部署生命週期，第 49／50 項；骨架仍 22 檔。前次：F12 新增第 48 項接力協調邊界；原子 claim 未實作。前次：F10 新增第 47 項核心與實例優先序；同步列人工遷移需求。前次：F11 新增第 45／46 項協作狀態契約與 Git 異常提示，版本 .5。前次：F07 新增第 44 項「ZIP 發布門檻」：SKIP 預設不打包，顯式調試包附 UNVERIFIED.json；部署範本與版本未改。前次：根目錄新增 project-bootstrap-audit-progress.md：查核報告 16 條的處理進度（已修 9／未修 7），寫給下一輪接棒的另一個模型；查核報告是凍結快照，狀態不寫進它裡面，所以這是新的一個家。`AGENTS.md` 的開工段加一行要求先讀它。不部署、不同步，制度與測試未改。前次：修掉查核報告的 F04 與 F08：`verify_state.py` 改成每項檢查回傳 PASS／FAIL／ERROR／SKIP／NOT_CONFIGURED，FAIL／ERROR 讓結束碼非零、`--strict` 連 SKIP 都不放行，輸出過一層祕密遮罩；`check_docs.py` 新增第 7 項「交接快照」（存在、必要欄位與章節、80 行上限），連結檢查改成先塗白程式碼並解析 title／角括號，對外名稱改成「文件與交接快照的機械檢查」。新增第 42 項「verify_state 失敗訊號」與第 43 項「交接快照檢查」，Windows 驗證為 **43 項**、骨架仍為 **22 檔**。3.14／3.15 的 `source:` 標記跳到 `v2026-11-02.3`；`SKILL.md` 未動，`VERSION` 不跳。🔴 3.14 是同步對象而 `VERSION` 沒跳，落後偵測不會提示，需手動同步六個專案。前次：修掉查核報告的 F14 與 F15：兩支維護工具改用包著 `open(..., newline='')` 的 `read_lf`／`write_lf`，檔頭宣告並檢查 `MIN_PY = (3, 8)`；五處「已修正的主張又復活」一起修（README 範本說其他工具沒有 skill 機制、第 6 節的序號算法與鐵律 2 不同、`verify_state` 被寫成有憑證才跑、prompt 的 A／B 跟 skill 相反、可攜層與三層的過度保證）。新增第 40 項「Python 版本下限」與第 41 項「已修正的主張沒復活」，Windows 驗證為 **41 項**、骨架仍為 **22 檔**。`SKILL.md` 與帶 `source:` 標記的範本都沒動，所以 `VERSION` 與標記都不跳、`sync_project.py` 零改動，六個專案沒有新的同步債。前次：修掉查核報告的 F02 與 F03：`sync_project.py` 的所有權從「整組」降到「handler」，同組的專案自訂 hook 不再被靜默刪除，matcher 衝突與重複／異常分組改成拒絕並說明；同步改成 `Plan` → preflight → `apply_plan`，任一項算不出來就零寫入，失敗與不存在的目標非零退出。新增第 38 項「同步安全」，Windows 驗證為 **38 項**、骨架仍為 **22 檔**。`sync_project.py` 不部署，所以沒有 `source:` 標記要跳、沒有副本義務，`VERSION` 不動。前次：修掉查核報告的 F01 與 F09 兩個錯誤安全訊號：兩支 hook 與 `check_docs.py` 的「工作中」判讀從子字串改成精確解析，版本偵測改成判方向並在領先時勸退同步；`SKILL.md` 未動、`VERSION` 刻意不跳，3.10 與 3.14 的 `source:` 標記跳到 `v2026-11-02.2`。「工具欄（負向測試）」擴成「工作中欄位格式（負向測試）」，共用情境表加 5 項，版本偵測加 2 項；Windows 驗證仍為 **37 項**、骨架仍為 **22 檔**。🔴 六個專案的副本尚未同步，而落後的副本正是會印錯誤綠燈的那一版。前次：使用者要求交棒攜帶查核報告，根目錄新增 project-bootstrap-audit.md：查核快照、不部署、不同步；既有制度與測試未改。前次：新增「續聊狀態與計數」程序契約檢查與負向測試，Windows 驗證為 **37 項**；骨架仍為 **22 檔**，交棒計數的家是 session 標題，不新增 repo 歷史檔。前次 2026-11-01：本輪恢復 HANDOFF 為當下交接快照，新增「本 repo 交接狀態」與負向測試，Windows 驗證為 **36 項**；前一輪新增 Codex Windows 啟動器與四項驗證，骨架為 **22 檔**、Windows 驗證為 **35 項**；`sync_project.py --codex-only` 只更新 Codex 接線與依賴的啟動器。原有紀錄：新增「ZIP 說明指標」與「跨工具過期敘述」兩項檢查：ZIP 的工具差異只指向部署包，已知過期散文由回歸測試守住；原有 29 項加到 31 項。修正本檔拓撲中的「2.0 未測」，骨架仍是 21 檔，skill／hook 與 VERSION 均未改。前一次是同日：本 repo 自己多一份 Codex 接線 `.codex/hooks.json`——指向它自己那支 `repo-git-check.sh`，**不是 3.17 的副本**；`sync_project.py` 加一道「拒絕把本 repo 自己當目標」的防護（兩份接線跟 `WIRING` 同名，覆蓋下去會指到不存在的 `git-freshness.sh`）；`verify_bootstrap.py` 從 27 項變 **29 項**（「本 repo settings.json」擴成「本 repo 兩份接線」、新增「sync 拒絕本 repo」）。**骨架仍是 21 檔**，但這次動到範本 3.10（多印一行開工改名提示），所以它的 `source:` 標記跳到 `v2026-11-01`；`SKILL.md` 沒動，`VERSION` 刻意不跳。前一次是同日第二次：`verify_bootstrap.py` 多一項「README 跨工具表一致性」：README 那張跨工具表是部署包那一張的轉述，而保鮮期只守部署包那一份，於是它可以無聲分岔；加的當下就抓到一處。**只動腳本與敘述，骨架仍是 21 檔，範本與 `sync_project.py` 都沒動。**前一次是 2026-10-31 同日第五次：**補上 Antigravity CLI 的 hook 接線，端到端實測過**——新增 3.18 `.claude/hooks/ag-wrap.sh`（轉接層）、3.19 `.agents/ag-hook.cmd`（Windows shim，找 Git Bash）、3.20 `.agents/hooks.json`（只接 `SessionStart`），舊 3.18「其他 skills 慣例」順延成 3.21；`verify_bootstrap.py` 加「Antigravity 接線」情境，`sync_project.py` 的 `WHOLE` 多兩份並新增 `AG_WIRING`（只換 `handoff-git-check` 那一個頂層 key）。骨架從 18 檔變 21 檔。同日第四次：**在 Antigravity CLI `1.4.7` 上把 hook 實測完**——`agy -p` headless 量到專案層 `.agents/hooks.json` 會讀、六個事件全部觸發，cwd 是 `.agents/`；相對路徑可用、絕對路徑才脆弱（`command` 照空白切 token、不解析引號），所以**上一次那個「骨架的不變量可能害探針測不出東西」的推論被推翻**，鐵律 5 跟它沒有衝突；`PreToolUse` 不明確回 `allow_tool` 就等於拒絕。骨架仍不附接線，理由換成「Windows 缺一層 `.cmd` shim」。只改敘述，接線／`verify_bootstrap.py`／`sync_project.py` 都沒動。同日第三次：**重新界定 Antigravity 那輪探針的範圍**——Antigravity 是四個獨立 surface（2.0 桌面 App／CLI／IDE／SDK），探針只覆蓋 IDE `1.107.0`，所以「這個工具沒有 hook 這一層」改寫成「骨架還沒附接線，2.0 與 CLI 沒測」；全域路徑 `~/.gemini/<applicationName>/hooks.json` 是跟著 surface 走的，`antigravity-ide` 那一份不能一般化成整個產品。只改敘述，接線不動、`verify_bootstrap.py` 與 `sync_project.py` 不動。同日第二次：**部署包移除 Antigravity 的 hook 接線**——舊 3.18 `.claude/hooks/antigravity-wrap.sh` 與舊 3.19 `.agents/hooks.json` 刪除，舊 3.20「其他 skills 慣例」遞補回 3.18；`verify_bootstrap.py` 移除「Antigravity 轉接層」六情境，`sync_project.py` 的 `WHOLE`／`WIRING` 各少一份。原因是實測：Antigravity IDE `1.107.0` **不讀專案層的 `.agents/hooks.json`**，那兩個檔部署出去也不會被觸發。同日稍早才加上它們，當天就被自己的驗收條件判出局。前一次是 2026-10-30 同日第二次：三平台能力重查後，`extract()` 的抽取規則從「第一個區塊」改成「區塊依序對應檔名」、`sync_project.py` 把 `CLAUDE.md` 從 `INSTANCE` 搬到 `PARTIAL`、`verify_bootstrap.py` 加「跨工具表保鮮期」、副本拓撲裡 `.agents/skills/` 的角色改變）
>
> **什麼時候改**：只有**結構**變動才改——根目錄多／少一個檔案、部署包增刪一節範本、`verify_bootstrap.py` 增減檢查項、副本拓撲改變。
> 制度內容本身怎麼寫（鐵律的措辭、skill 的步驟）**不要動這一份**，那些的家在 [AGENTS.md](AGENTS.md) 與部署包裡。

## 一句話

唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)——一份自帶所有檔案範本的部署包，複製到新專案資料夾就能生出整套制度。
其餘每個檔案都是它的**說明、指標或測試**，沒有第二個產出物（例外是下面那支本 repo 自己的開場檢查 hook——它誰的副本都不是——以及 `HANDOFF.md`，它是範本 3.3 的*實例*，承載當下交接快照與「工作中」標記）。

## 根目錄

| 路徑 | 是什麼 | 什麼時候動 |
|---|---|---|
| [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) | **權威版部署包**：訪談表＋各檔範本＋上 GitHub＋自檢清單＋維持操作卡 | 制度要改就改它（鐵律第 1 條） |
| [README.md](README.md) | 人的入口：怎麼用、部署後長什麼樣、跨工具相容性、改這份骨架的開場 prompt | 用法或相容性改變 |
| [AGENTS.md](AGENTS.md) | AI 的入口：這個 repo 是什麼、鐵律、副本位置、行末規則 | 多一條鐵律、副本位置改變 |
| [CLAUDE.md](CLAUDE.md)、[GEMINI.md](GEMINI.md) | Claude 用 `@AGENTS.md` import；Gemini 用文字指標 | 幾乎不動 |
| [HANDOFF.md](HANDOFF.md) | **當下交接快照與跨機器工作標記**。範本 3.3 的*實例*，不是副本，不在副本拓撲裡、不要用 `sync_project.py` 同步。≤80 行、覆寫不累積，維護義務與事故見 [AGENTS.md](AGENTS.md)「本 repo 的交接快照」 | A5 寫標記；B6 核對整份現況、待辦、限制與驗證，清掉已完成待辦 |
| [project-bootstrap-audit.md](project-bootstrap-audit.md) | 2026-11-02 使用者要求隨交棒保存的查核快照；供下一手評估改善，不是制度權威、不部署也不同步。原始探針只留在原聊天產物 | 查核結論需勘誤時；實作進度寫 HANDOFF，不在報告累積 |
| [project-bootstrap-audit-progress.md](project-bootstrap-audit-progress.md) | **查核報告 16 條的處理進度**：已修的做了什麼與守門人、未修的建議作法與驗收門檻、跨條目的共同規則。查核報告是凍結快照，所以狀態有自己的家。不部署、不同步 | 任何一條的狀態改變，跟那個改動同一個 commit |
| [project-bootstrap-reaudit-2026-11-03.md](project-bootstrap-reaudit-2026-11-03.md) | **第二輪複審快照**：R01–R09 的證據、改善與驗收門檻、原 F01–F16 的複審判定；2026-11-03 使用者要求下一輪先讀。不部署、不同步，原始探針留在審查聊天產物 | 查核結論需勘誤時；當下實作進度看 HANDOFF |
| [project-bootstrap-efficiency-plan.md](project-bootstrap-efficiency-plan.md) | **效率改進設計提案**：接棒分流、驗證分層、必讀內容精簡、原始碼與部署產物分離；尚未實施，不部署、不同步，不取代現行程序 | 設計決策改變時；實作進度看 HANDOFF |
| [project-bootstrap-requirements-decision.md](project-bootstrap-requirements-decision.md) | 現行需求唯一權威：D1–D8、51 條需求、驗收、待決與變更理由。不承載實作狀態，不部署、不同步 | 需求決策改變時 |
| [project-bootstrap-implementation-plan.md](project-bootstrap-implementation-plan.md) | 依決策書評估既有程式與開源工具；推薦技術棧、50 項映射、可行性門檻、遷移與驗收。不承載滾動達成狀態，不部署、不同步 | 選型或實現方案改變時 |
| [project-bootstrap-requirements-history.md](project-bootstrap-requirements-history.md) | 原 v3.10 全文與修訂理由，歷史封存；不再指示現行操作 | 僅補帶日期的歷史勘誤 |
| [project-bootstrap-requirements-review-2026-11-04.md](project-bootstrap-requirements-review-2026-11-04.md) | 需求審閱建議快照 Q1–Q7，供下一棒 Opus 討論；未採納，不改變需求權威或現行程序。不部署、不同步 | 本次審閱快照；採納結果另改需求文件 |
| [project-bootstrap-requirements-review-reply-2026-11-04.md](project-bootstrap-requirements-review-reply-2026-11-04.md) | **對 Q1–Q7 的逐項評估回覆**：每項的理解、同意／不同意的理由與最後做法，含三點整體判讀與建議處理順序。2026-11-04 全部判定已被採納，所以它是那次修訂的理由記錄。不部署、不同步 | 評估結論改變時；它不是需求權威 |
| [project-bootstrap-requirements-response-2026-11-04-2230.md](project-bootstrap-requirements-response-2026-11-04-2230.md) | 對 Opus 修訂及 Q1–Q7 回覆的再評估；未採納建議，不改變需求權威、不部署、不同步 | 本輪審閱快照，採納結果另改權威文件 |
| [project-bootstrap-requirements-response-reply-2026-11-04-2310.md](project-bootstrap-requirements-response-reply-2026-11-04-2310.md) | **對再評估報告 S1–S6 與六條整體校正的逐項回覆**：判定、理由與建議措辭草案，含四條建議先修的事實／一致性錯誤。未採納，不改變需求權威或現行程序。不部署、不同步 | 評估結論改變時；它不是需求權威 |
| [project-bootstrap-requirements-response-review-2026-11-05-0927.md](project-bootstrap-requirements-response-review-2026-11-05-0927.md) | 第三輪需求審閱：表述、一致性與可驗收性；未採納，不部署、不同步 | 採納結果另改權威文件 |
| [project-bootstrap-requirements-response-review-reply-2026-11-05-1545.md](project-bootstrap-requirements-response-review-reply-2026-11-05-1545.md) | **對第三輪審閱的逐項回覆與 v3 採納記錄**：S1–S6 與六條校正的判定、三條獨立查證（`step_claims()` 的輸入集合、第 5 節的現況判斷禁令、第 4 節的舊歸因）、四處補充與一處加嚴。2026-11-05 判定已被採納，所以它是 v3 的理由記錄。不部署、不同步 | 評估結論改變時；它不是需求權威 |
| [project-bootstrap-requirements-response-review-reply-2026-11-05-1620.md](project-bootstrap-requirements-response-review-reply-2026-11-05-1620.md) | **對 1606 審閱的逐項回覆與 v3.1 採納記錄**：三處待修與四項限縮全部接受、四處定點查證、一處反例確認（第 9 節的歷史引用會觸發字串共現判定）、兩處補充（承載處的耐久性、新增待決項是子題）。2026-11-05 判定已被採納，所以它是 v3.1 的理由記錄。不部署、不同步 | 評估結論改變時；它不是需求權威 |
| [project-bootstrap-requirements-response-review-2026-11-05-1606.md](project-bootstrap-requirements-response-review-2026-11-05-1606.md) | 對需求 v3 與 1545 回覆的審閱；建議未採納，不部署、不同步 | 採納結果另改權威文件 |
| [project-bootstrap-requirements-response-review-2026-11-05-1632.md](project-bootstrap-requirements-response-review-2026-11-05-1632.md) | v3.1 與 1620 回覆五項定向審閱；**2026-11-05 已採納**，不部署、不同步 | 採納結果另改需求權威 |
| [project-bootstrap-requirements-response-review-reply-2026-11-05-2150.md](project-bootstrap-requirements-response-review-reply-2026-11-05-2150.md) | **對 1632 審閱的逐項回覆與 v3.2 採納記錄**：(a)–(e) 的實質建議全部接受、一處措辭建議不接受（第 6 節禁止倒推那句維持原文）；八處定點查證＋一處補查（第 260 行）；三處補充（append-only 不是滾動——**該豁免已由需求 v3.3 取消**、權威切換逐 ID、工作假設不是 F40 證據）；更正 1620 兩處過度宣稱。2026-11-05 判定已被採納，所以它是 v3.2 的理由記錄。不部署、不同步 | 評估結論改變時；它不是需求權威 |
| [project-bootstrap-requirements-final-review-2026-11-05-2214.md](project-bootstrap-requirements-final-review-2026-11-05-2214.md) | v3.2 最後審閱與五項直接修改指令；**2026-11-06 已實作為需求 v3.3**，不另寫回覆。不部署、不同步 | 執行結果改需求正文及 HANDOFF |
| 本檔 | 結構 | 只有結構變動 |
| [LICENSE](LICENSE) | MIT（2026-09-07 起公開） | 授權改變 |
| [tools/verify_bootstrap.py](tools/verify_bootstrap.py) | **部署包的測試**，不是骨架的一部分、也不會被部署出去 | 部署包多一種失效模式時 |
| [tools/sync_project.py](tools/sync_project.py) | **部署包的發佈工具**：把最新內容推到已部署的專案。`check_docs.py` 的專案設定區塊、兩份 hook 接線裡專案自己加的設定都會原樣保留。只改檔案，不 commit | 骨架多一個要同步的檔時（而且要同時歸類進 `WHOLE`／`WIRING`／`PARTIAL`／`INSTANCE`，否則驗證會 FAIL） |
| [VERSION](VERSION) | 一行版本號，與部署包開頭的版本行一致（`verify_bootstrap.py` 會擋不一致）。各專案的 `git-freshness.sh` 抓它判斷自己落後沒有 | 跟版本行一起改 |
| `.claude/settings.json`＋`.codex/hooks.json`＋`.claude/hooks/repo-git-check.sh` | 本 repo 自己的 SessionStart 檢查：git 新鮮度＋`HANDOFF.md` 的「工作中」判讀＋開工改名提示。兩份接線掛的都是**同一支** `repo-git-check.sh`（2026-11-01 補 Codex 這一面），所以它們**不是部署包 3.9／3.17 的副本**，那支 hook 也不是 3.10 的副本——都不在副本拓撲裡、不要用 `sync_project.py` 同步（檔頭寫了為什麼不抄 3.10；2026-11-01 起那支腳本會直接拒絕） | 幾乎不動 |
| `.gitignore`、`.gitattributes` | `dist/` 不進 Git；全檔強制 `eol=lf` | 幾乎不動 |
| `dist/` | 建置產物（`--zip` 產出的骨架壓縮檔），**不進 Git** | 要發佈就重跑一次，不要留在 repo 裡跟部署包唱反調 |

本 repo 的 `.claude/hooks/codex-hook.cmd` 是 **3.17 啟動器的副本**，跟 `repo-git-check.sh` 的角色不同；更新時從部署包抽取這一檔覆蓋，不把本 repo 當成 `sync_project.py` 的目標。它只尋找 Git Bash、加上避免 JSON 誤判的純文字標頭，並保留 stdin／輸出內容／結束碼，沒有交接規則。既有專案的 Codex 接線升級時會補齊這個新依賴；沒有 Codex 接線的專案仍不自動補裝。`--codex-only` 只同步這兩檔，專案 SKILL 與其他設定不變。

## 部署包的內部結構

v2 原型不在部署包內；詳見 [原型說明](experiments/v2/README.md)。來源驗證器的新增檢查「v2 P0 原型回歸（非需求達標）」執行合成契約、索引負向案例、三個預期架構反例、Mac 隔離與子程序上下文替換探針。它明列 `strict_ready=false`，不把實驗成功當成必要需求達標；空／缺項／SKIP／偽稱 ready 的報告有負向測試。

| 節 | 內容 | 誰會讀它 |
|---|---|---|
| 表頭 | 部署 prompt、版本日期、來源 | 拿到這份檔案的人 |
| 交接自動化怎麼運作 | 觸發（hook）／程序（skill）／防呆（hook）三層 | 想理解設計的人 |
| 跨工具與跨平台 | Claude Code／Codex CLI／Codex 桌面 App／Antigravity 的能力矩陣 | 要在別的工具上部署的人 |
| 0 | 這套骨架在解決什麼問題（失效模式 → 對策） | 想知道「為什麼要有這條規則」的人 |
| 1 | 部署前訪談：佔位符表 | 執行部署的 agent |
| 2 | 要建立的檔案結構 | 同上 |
| 3 | **各檔範本**（3.1–3.21，3.17 產兩檔），照抄只換佔位符 | 同上，改到哪份讀哪節 |
| 4 | 先本機驗收，再首次發布 | 同上 |
| 5 | 部署後自檢清單 | 同上 |
| 6 | 之後怎麼維持（一頁操作卡） | 部署完的專案 |

第 3 節的範本清單就是 `verify_bootstrap.py` 裡 `EXPECTED` 的對照表：

| 節 | 產出 | 角色 |
|---|---|---|
| 3.1 | `AGENTS.md` | AI 入口、鐵律、知識庫地圖 |
| 3.2 | `CLAUDE.md`＋`GEMINI.md` | **一節產兩檔**：Claude 用 import，Gemini 用文字指標 |
| 3.3 | `HANDOFF.md` | 當下狀態（≤80 行、覆寫不累積） |
| 3.4 | `README.md` | 人的入口、收工交棒／開工接棒 prompt |
| 3.5 | `ARCHITECT.md` | 結構的唯一權威（2026-09-07 加入） |
| 3.6 | `docs/ai-notes/handover-protocol.md` | 交接的規則與理由 |
| 3.7 | `docs/ai-notes/roadmap.md` | 持久待辦與決策記錄 |
| 3.8 | `.claude/skills/handoff/SKILL.md` | **本骨架的核心**：0 建制／A 接棒／B 交棒／C 同步 |
| 3.9 | `.claude/settings.json` | 兩個 hook 的接線 |
| 3.10 | `.claude/hooks/git-freshness.sh` | SessionStart：git 新鮮度 |
| 3.11 | `.claude/hooks/pre-push-handoff.sh` | PreToolUse：AI push 提醒（有限覆蓋，見部署包 3.11） |
| 3.12 | `.gitignore` | 祕密與運行資料 |
| 3.13 | `.gitattributes` | 行末 LF |
| 3.14 | `tools/check_docs.py` | 文件與交接快照的機械檢查 |
| 3.15 | `tools/verify_state.py` | 一鍵現況查證（骨架） |
| 3.16 | `.agents/skills/handoff/SKILL.md` | Antigravity 的指標檔 |
| 3.17 | `.codex/hooks.json`＋`.claude/hooks/codex-hook.cmd` | Codex 的 hook 接線與 Windows 啟動器（掛 3.10／3.11 同樣那兩個 `.sh`，Windows 明確找 Git Bash） |
| 3.18 | `.claude/hooks/ag-wrap.sh` | Antigravity 轉接層：只做管線（跑腳本、把 stdout 包成 JSON），不含規則 |
| 3.19 | `.agents/ag-hook.cmd` | Antigravity 在 Windows 的 shim：找 Git Bash 再交給 3.18 |
| 3.20 | `.agents/hooks.json` | Antigravity 的 hook 接線（經 3.18 掛同一支 3.10；只接 `SessionStart`） |
| 3.21 | —— | 其他 skills 的**慣例說明**，不產檔 |

## 部署包 → 骨架的抽取規則（改範本前先讀這段）

`verify_bootstrap.py` 的 `extract()` 就是「照著部署包生檔案」的機器版，規則只有四條：

1. **`### 3.x` 標題行裡的反引號路徑＝產出的檔名。** 改標題就是改檔名——3.2 的標題有兩個路徑，所以一節產兩檔。
2. **一節裡的 fence 依序對應標題上的檔名**；fence 比檔名少就全部沿用第一個（多數節是一檔一區塊）。fence 前的散文是給人看的說明，不會進檔案。
3. **標題行沒有路徑就不產檔**（3.21 是慣例說明）。

第 2 條在 2026-10-30 從「只取第一個 fence，`GEMINI.md` 的標題再由腳本替換」改成現在這樣：3.2 的 `CLAUDE.md` 從此只有一行 `@AGENTS.md` import、`GEMINI.md` 維持指標寫法，兩份內容不同了。把其中一份合成在腳本裡，就等於讓範本內容有第二個家——部署包才是權威版。

所以：**新增一份範本＝新增一節＋把檔名加進 `EXPECTED`**。只做前者，驗證會 FAIL 說「多出」；只做後者會 FAIL 說「缺少」。

## `tools/verify_bootstrap.py` 守的東西

| 檢查 | 守什麼 | 失敗代表 |
|---|---|---|
| 重生骨架 | 範本清單與 `EXPECTED` 一致 | 有人刪了範本沒發現，或新增範本沒登記 |
| 填佔位符 | 模擬部署後不該有殘留 | 範本用了訪談表沒有的佔位符 |
| `check_docs` | 在填好的骨架跑要 exit 0 | 範本裡有死連結或缺日期標頭 |
| 佔位符清單 | `PLACEHOLDER_NAMES` 涵蓋範本真正用到的名字 | 有個洞永遠不會被檢查到，而且沒有跡象 |
| 佔位符檢查（負向） | 種一個佔位符回去必須被擋下 | 第 5 項檢查本身壞了 |
| 日期標頭（負向） | 拿掉 `ARCHITECT.md` 的「最後更新」必須被擋下 | `check_docs` 的 `DATED_DIRS` 漏了它 |
| 工作中欄位格式（負向） | 四種壞格式（舊格式沒工具欄、主題含「無」、欄位重複、機器欄空白）都要 exit 2，正常的已交棒值不誤擋。2026-11-02 從「工具欄（負向測試）」擴大 | `check_docs` 用子字串判「已交棒」，正常任務名稱就能跳過整個格式驗證（F01） |
| 真實部署形狀 | 部署包在場＋非 ASCII 檔名時仍 exit 0 | 照說明部署的人一定會踩到 |
| 跨平台防呆 | 無絕對路徑、有 `python3` 退路 | 換一台機器會靜默失效 |
| AI push 提醒情境 | staged／unstaged 不放行、已提交開工／交棒放行；命令選項、remote、refspec、GUI／script 的已知邊界；恢復舊捷徑的負向測試 | 未提交修改不會隨 push 上傳，不能拿來放行；有限提醒不能冒充發布保證（2026-11-02／F06） |
| 工作中標記 | 範本有欄位，且 git-freshness 讀 `origin` 後每種狀態各印對應結論（別台 🔴、自己這台 🟡、已交棒 ✅、欄位不存在 🟡），**且判讀是精確解析而非子字串**（2026-11-02／F01：主題或機器名含「無」要 🔴、機器名互為子字串要 🔴、欄位重複要 🔴，已交棒值前後有空白仍要 ✅） | 跨機器誤接棒防呆靜默失效——下一棒只會看到一切正常 |
| `VERSION` 檔 | 與部署包版本行一致 | 落後偵測會說謊，落後的專案以為自己最新 |
| 版本落後偵測 | 餵**比本機新**的版本要講落後、餵**比本機舊**的要說「比上游新」並勸退同步、同版與 `BOOTSTRAP_VERSION_CHECK=off` 要閉嘴 | 專案不再自己回報落後，同步又回到靠人記得；方向弄反則會叫人把新版蓋成舊版（2026-11-02／F09，舊 fixture 本身就是反的） |
| 本 repo 自己的文件 | 本 repo 的 `.md` 無死連結、`AGENTS.md`／`ARCHITECT.md` 有日期標頭，受管非 Markdown 檔無已知部署佔位符 | 改檔名或搬段落留下死連結，或把未填的部署欄位帶進公開來源。部署包裡指向「部署後才存在的檔」的連結不算，判準是 `EXPECTED`，所以它指向本 repo 檔案的連結照樣會被抓 |
| 本 repo 兩份接線 | `.claude/settings.json` 與 `.codex/hooks.json` 都是合法 JSON、只接 `SessionStart`、都指向真的在的 `repo-git-check.sh`，而且沒被改成指向 `git-freshness.sh`／`pre-push-handoff.sh` | 開場檢查靜默不執行——看起來有防護、實際上沒有。這兩個檔是 JSON、塞不進 `source:` 標記，落後偵測看不到它們，這一項是唯一的守門人 |
| sync 拒絕本 repo | `sync_project.py <本 repo 路徑>` 要印出拒絕，**而且預演輸出裡零 `UPDATE`** | 一次手打路徑就把兩份接線改成指向這裡不存在的腳本。只檢查「有印拒絕」的話，一個印了話卻照樣改檔的版本會通過，比沒有這項更糟 |
| 改名寫進回報模板 | A5／B9 各有必填 `session：` 與無改名工具時的回報選項，附負向測試 | 改名漏做卻在 repo 內沒有任何跡象 |
| 續聊狀態與計數 | skill 與指標 description 觸發已交棒後每則新訊息；程序保留原時間與計數、先恢復工作中、只讀不寫 Git、改檔重跑 A、成功交棒才累加；附 18 個負向測試 | 同一 session 續聊仍掛著已交棒，或把問答／失敗 push 算成交棒；只守程序文字，不宣稱外部工具已實跑 |
| 本 repo 交接狀態 | 必要欄位與章節、≤80 行、骨架版本符合 VERSION、禁止這次已知過期待辦與只改兩欄的入口規則；附負向測試 | 標記清了卻保留已完成待辦，下一棒被迫從聊天重建現況；不保證任意待辦的語意正確，仍需 B6 人工核對 |
| 來源例外可見性（F46 部分） | 每輪印出 handoff skill、pre-push-handoff.sh、check_docs.py 三項已宣告減項；確認來源缺、產物有，並對漏宣告／來源增項／產物缺項跑負向變異 | 三項減項再次從驗證輸出中靜默消失；這只驗可見性，未完成來源／產物全部同組情境 |
| 來源／產物交接快照同組情境（F46 部分） | 同一組 11 種合成快照在來源檢查與部署後 `check_docs.py` 各跑一次：有效、整份缺失、占用欄缺失／重複、章節缺失、超行數、機器／工具欄正反例均須一致；來源檢查遇整份缺失須明確報錯 | 來源少了整份 `HANDOFF.md` 時只拋例外，或產物與來源對相同缺陷給出矛盾結論；實際接手流程仍待驗 |
| 來源／產物文件同組情境（F46 部分） | 同一份合成文件在來源文件檢查與部署後 `check_docs.py` 各跑一次：20 種正反例涵蓋根目錄及巢狀文件的缺檔、死連結、程式碼、角括號加 title、片段、日期及佔位符；沿用來源實際檢查函式 | 同樣的文件缺陷在來源與產物給出不同結論；其他文件項仍待驗 |
| 來源／產物文件設定同組情境（F46 部分） | 9 種合成設定情境對照非 Markdown 已知佔位符、未知樣板、專案自訂過期字串、同列歷史文字與連結／佔位符／過期字串路徑豁免；來源端同時掃自己受管的非 Markdown 檔 | 來源非 Markdown 檔殘留部署欄位，或來源與產物對相同設定給出不同結果；任意專案設定與跨工具遵循仍待驗 |
| 來源提交候選一致性（F46 部分） | 來源 `verify_bootstrap.py --staged` 拒絕未暫存或未追蹤檔；完整／部分 stage 與產物 `check_docs.py --staged` 跑同組 fixture，並對來源未追蹤檔作負向測試 | 用未提交的工作樹內容證明另一份 staged 內容；只驗提交候選形狀，不代表實際接手流程已驗收 |
| 本 repo 工作中判讀 | `repo-git-check.sh` 讀 `origin` 的 `HANDOFF.md` 後每種狀態各印對應結論，且跟 3.10 用同一個欄位字串與**同一張情境表**（含 2026-11-02 的 F01 五項） | 這個 repo 的跨機器防呆靜默失效，或兩支 hook 的欄位格式悄悄分岔 |
| 同步清單涵蓋骨架 | `sync_project.py` 的四份清單加起來要等於 `EXPECTED` | 新增範本沒歸類＝那個檔沒人同步，而且沒有徵兆。2026-10-30 就是這樣查出兩份 hook 接線從來沒被發下去 |
| 同步安全 | F02：骨架只擁有**指向骨架腳本的 handler**（同組的自訂 hook 要保留，matcher 衝突／重複組／異常分組要拒絕，`commandWindows` 要認得）。F03：任一項算不出來就零寫入，失敗與不存在的目標要非零退出、不准宣稱最新版 | 同步靜默刪掉專案設定；或失敗一半卻回 exit 0 並宣稱最新版，而落後的專案以為自己同步過了（2026-11-02／F02、F03） |
| 同步升級 mode | 替換前複製既存 mode；複製失敗保留原檔；新依賴仍可建立；移除複製的負向變異必須失敗。POSIX 另驗 0755／0640、原始 wrapper 直接執行、Git 無 mode diff | 新 inode 預設權限會讓更新後的 POSIX hook 無法執行；Windows 通過不代表 POSIX 實測 |
| 結構摘要一致性 | 本 repo 與生成 ARCHITECT 區分 Claude import／Gemini 文字指標，README prompt 用收工／開工；三個負向測試 | 權威範本已改，結構表格仍教舊寫法 |
| 接線合併 | 餵一份「舊 matcher ＋ 專案自己加的 permissions 與 hook」進去，要換掉舊值、保住專案設定、已一致時不動 | 同步會洗掉專案設定，或落後的專案根本修不好 |
| 跨工具表保鮮期 | 「跨工具與跨平台」那節的「查證日期」不得超過 90 天（`BOOTSTRAP_FRESHNESS=off` 可跳過） | 對外部工具能力的斷言在無聲中過期。這一項只保證有人看過日期，**不保證有人真的重查**——買到的是「必須有意識地決定」。會做成 fail 而不是警告，是因為上一次的對策就是一句警告，而警告沒擋住第二次（Antigravity 的 hooks、Codex 桌面 App 的 hooks，兩次同一種錯） |
| README 跨工具表一致性 | README 那張跨工具表與部署包那一張：同名列的判定符號一致、README 沒有孤兒版本號、有指回部署包的指標（附四種分岔的負向測試） | README 是**人的入口**，而保鮮期只守部署包那一份——事實在部署包被重查改對，README 留在舊事實上，沒有任何徵兆。2026-11-01 加這一項的當下就抓到一處已經發生的分岔（「自動載入程序檔」×「Codex CLI」）。不給 README 自己一個「查證日期」是因為那是同一個事實的第二個時鐘 |
| ZIP 說明指標 | ZIP 隨附說明的工具差異只連到同包部署包的「跨工具與跨平台」及第 5 節，不另列逐工具能力摘要（附六個負向測試） | 壓縮檔第一份說明成為另一個會過期的家；2026-11-01 確認它仍寫著 Codex 桌面 App、Antigravity 沒有 hook，矩陣與 README 的檢查都看不到它 |
| 跨工具過期敘述 | 部署包正文、本 repo 結構說明與重生的結構／協定範本，不得復活 CLI／2.0 測試狀態、Antigravity 接線、skill 入口與 IDE 追查決定的已知舊斷言；附回歸負向測試與範圍測試 | 同一份文件的表改對了，散文卻仍教下一棒照舊事實行動。只檢查已知回歸，不做通用語意判讀、不代替外部查證；表頭的歷史變更記錄與 IDE 未解結果仍保留 |
| Codex Windows 接線 | `commandWindows` 經 Git Bash 啟動器，兩個事件與本 repo 都指向原本那支 `.sh`；三個負向測試 | 真部署的已信任 hook 曾選到 WSL 而 exit 1 |
| Codex Windows 結束碼 | 實跑 PowerShell → cmd → Git Bash；保留 exit 2，拿掉明確 exit 時必須重現 exit 1 | 只測原生 cmd 會把工具仍放行的版本誤報成功；此項只在 Windows 執行 |
| Codex 接線升級 | 舊專案補齊啟動器、保留專案 hook 與 SKILL、預演零寫入、重跑零變更、不替沒有接線的專案補裝 | 只更新 JSON 卻漏掉新依賴會再度靜默失效 |
| Codex Windows 啟動器 | Windows 原生 cmd 實跑中文／空白路徑、不同 cwd、stdin／stdout／stderr／exit 2 與缺少 Git Bash 的情境 | 轉接層若吞掉 exit 2，pre-push 防呆會消失；此項只在 Windows 執行 |
| verify_state 失敗訊號 | 命令非零退出、HTTP 500、連不上、200 但回應內容不對都要讓結束碼非零；缺憑證是 SKIP，`--strict` 才非零、`OPTIONAL` 放行；未填仍回 0；祕密要遮罩。十個情境全部實跑 | 舊版每一種情況都 return 0，畫面印著 `rc7` 而下游拿 exit 0 當服務驗收（2026-11-02／F04） |
| 交接快照檢查 | `HANDOFF.md` 不見了、超過 80 行、缺必要章節或欄位重複都要 exit 2；`--docs-only` 要真的關得掉；程式碼範例、帶 title 與角括號連結不得誤報，但真的死連結仍要抓到 | 第 6 項只在 HANDOFF 出現在輸入清單時才驗，整份刪掉反而回報乾淨；而連結誤報會教人「這支腳本的 FAIL 可以無視」（2026-11-02／F08） |
| Python 版本下限 | 兩支維護工具檔頭的 `MIN_PY` 存在、會擋、兩邊同號；README 範本寫出部署後工具的下限；四支 `.py` 都沒有用到高於下限的 API（掃描前把註解與字串塗白） | 3.13-only 的 API 在舊版 python 上是執行到那一行才炸成 TypeError，不會說「版本太舊」。下限是靜態擔保、不是實測：沒有舊版可跑，要實測得先有 CI（2026-11-02／F14） |
| 已修正的主張沒復活 | 能力表 ✅ 的工具不得被散文說成沒有 skill、交接 prompt 不得有自己的 A／B 編號且要寫出模式、`verify_state` 不得以憑證為前提、版本序號只有一種定義、可攜層不得寫成「到哪都成立」；附九個負向測試 | 事實在部署包被改對，範本、操作卡與入口文件裡的舊說法照樣部署出去。綁結構不綁禁句，「」裡的引用不算主張（鐵律 3 要留為什麼）；守不了一整段敘述的準確度（2026-11-02／F15） |
| ZIP 發布門檻 | 注入結果走 CLI 與實際 ZIP：全過才正常打包；SKIP 預設拒絕，顯式例外附 UNVERIFIED.json 與說明、仍 exit 1；FAIL 不可繞過；拒絕時保留舊檔。含移除門檻的負向測試 | 舊流程有 SKIP 仍先打包再回 1，看似正式產物但未完整驗證（2026-11-02／F07） |
| 協作狀態契約／Git 異常提示 | 六狀態與步驟契約、20 個負向測試，含 R07 先 stage 再驗證；兩支 hook 實跑領先／分岔／fetch 失敗 | 程序順序矛盾或工具提示教人自行 rebase（2026-11-02／F11） |
| 核心與實例優先序 | skill／協定／README 宣告一致、override 範圍明確、11 個負向測試；同步列版本與 MIGRATE，保留舊實例 | 不同步的舊協定會推翻新程序（F10） |
| 接力協調邊界 | A2.5／A5／協定明列協調訊號非鎖、SHA 比對與禁止自動奪權，8 個文字負向測試 | 不宣稱並行互斥；原子 claim 留待另案（F12） |
| 同步範圍與前置檢查 | 真 worktree、含 worktrees 普通目錄、已完結 inventory；fresh fetch／upstream 對齊／明確 owner、dirty／占用／整份檔與 check_docs 共用程式區客製漂移拒絕且零寫入；批次僅預演，單專案 A5 writer 才能寫入 | 路徑字串不是 worktree 證據，批次同步不能悄悄擴大範圍（F13） |
| 部署生命週期 | 訪談自訂 ignore、本機檢查→首 commit→local bare push→clone，mode 100755 與 wrapper 直接執行；7 個負向測試 | 圍欄外追加規則及發布後才驗收無法保護首 commit；不測外部 GitHub 或模型行為（F16） |
| 行末與雜項 | 全 LF、JSON 合法、腳本可執行 | Windows 寫出 CRLF、設定檔打錯字 |

**exit 0 才算改完**（鐵律第 4 條）。印出 `skip` 的項目沒有被驗證，回報時要照實寫。

## 副本拓撲（同一份東西存在於多個地方的，只有這些）

```text
handoff SKILL.md
  部署包 3.8（權威）
    └─→ 各專案 .claude/skills/handoff/SKILL.md
          ├─→ （選用）~/.claude/skills/handoff/   ← 模式 0 建制真正會被載入的地方
          ├─→ （選用）~/.codex/skills/handoff/    ← Codex CLI 與桌面 App（2026-10-30 實測
          │                                          CLI 0.164.0 仍讀這個路徑，雖然官方
          │                                          文件已經不列它）
          └─→ .agents/skills/handoff/SKILL.md     ← 只放指標，不複製內容。2026-10-30 起
                                                     Antigravity 與 Codex 都把它當專案層
                                                     skill 來源，所以它的 description
                                                     必須寫滿觸發詞（那是它被發現的唯一依據）

兩支 hook .sh
  部署包 3.10／3.11（權威）
    └─→ 各專案 .claude/hooks/*.sh   ← 只有這一份腳本
          ├─← .claude/settings.json 指向它
          ├─← .codex/hooks.json 指向同樣那兩個（不複製第二份）
          └─← .agents/hooks.json 經 3.18 的轉接層指向同一支 3.10
                （Windows 還多一層 3.19 的 .cmd shim：agy 的 command 不吃空白
                 也不吃引號，而 Git Bash 的路徑含空白。2026-10-31 在 CLI 1.4.7
                 上端到端實測過；2.0 2.28.2 同日也實測通過；IDE 1.107.0 沒觸發、不再追查）

check_docs.py
  部署包 3.14（權威，「專案設定」區塊除外——那塊本來就該依專案調）
    └─→ 各專案 tools/check_docs.py

三份 hook 接線（JSON）
  部署包 3.9／3.17（權威，只管「指向骨架那幾個 .sh」的那幾組；
                        專案自己加的 permissions／env／額外 hook 原樣保留）
    ├─→ 各專案 .claude/settings.json
    └─→ 各專案 .codex/hooks.json
  部署包 3.20（權威。Antigravity 的頂層 key 就是 hook 名稱，所以骨架只擁有
               handoff-git-check 這一個 key，換掉它、專案自己的 key 原樣保留）
    └─→ 各專案 .agents/hooks.json
```

**本 repo 自己的兩份接線（`.claude/settings.json`、`.codex/hooks.json`）不在上面這張圖裡。**
它們跟 3.9／3.17 路徑同名、形狀也幾乎一樣，但掛的是這個 repo 自己那支 `repo-git-check.sh`——
所以是**同名而非同源**，沒有同步義務，也不跳 `source:` 版本。而「路徑同名」本身就是風險：
`sync_project.py` 的 `WIRING` 清單認的是路徑，手打一次 `sync_project.py <本 repo>` 就會把它們
改成指向這裡不存在的 `git-freshness.sh`。2026-11-01 起那支腳本直接拒絕本 repo（`--all` 本來就
掃不到它），`verify_bootstrap.py` 的「sync 拒絕本 repo」與「本 repo 兩份接線」兩項各守一端。

**JSON 沒辦法放 `source:` 標記**，所以上面那兩份接線在落後偵測裡是隱形的——它們唯一的守門人是 `sync_project.py` 的 `WIRING` 清單加上 `verify_bootstrap.py` 的「同步清單涵蓋骨架」。2026-10-30 把它們補進拓撲，是因為 2026-09-13 給 3.9 補的 `Bash|PowerShell` matcher 一直沒發下去：三個專案停在舊的 `Bash`，而那台機器的主 shell 正是 PowerShell，pre-push 防呆於是在那些專案等於沒裝，一個半月沒有任何徵兆。

每份副本檔頭有 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->`，**改內容就要跳版**，否則沒人分得出哪份落後（鐵律第 2 條）。同一天改第二次起要在日期後面加序號（`v2026-10-24.2`）——日期粒度只能證明「不早於那一天」，2026-10-24 就因此誤判過一次。
沒改內容的檔案不要跟著跳版——謊報「副本落後」之後，這個標記就沒人再信。

## 這個 repo 刻意沒有的東西

> **正式例外宣告（2026-11-06，使用者決定）＝ D4／F34 的「主動宣告」。**
>
> 需求 v3.10 新增的 **F46「制度來源自身的保護不低於它發出去的產物」**（偵測）與這個 repo 三個「刻意沒有」直接衝突。F46 的驗收允許兩條路——補裝，或把減項**宣告為例外**（D4：例外由使用者主動宣告；F34：主動宣告的例外要看得見）。**使用者 2026-11-06 選了宣告為例外。**
>
> **宣告的內容**：這個 repo 刻意不裝 **handoff skill**、**`pre-push-handoff.sh`**、**`check_docs.py`** 三項，理由見下方三條（它們各自已有帶日期的評估記錄，其中 `pre-push-handoff.sh` 2026-10-30 與 2026-11-01 各評估過一次，結論都是不裝但理由不同）。**這不是疏漏，也不是尚未排程。** 替代保障：接棒程序讀全域副本 `~/.claude/skills/handoff/`（沒有全域副本時讀部署包 3.8 節，2026-11-10 起 AGENTS 開工段落明寫）、`.md` 的死連結與日期標頭由 `verify_bootstrap.py` 顧、交接快照由 B6 逐項核對。
>
> ⚠️ **宣告不等於 F46 已達成。** F46 的強度是**偵測**——它還要求「對來源跑與產物同一組情境，缺的項目要**印出來**而不是略過」。2026-11-08 起 `verify_bootstrap.py` 逐項印出三項已宣告例外，並檢查來源與產物的檔案形狀；交接快照 11 種、文件 20 種、文件設定 9 種同組情境均成對跑，另以 `--staged` 核對提交候選，並在本機 bare origin 演練 Git 接力。跨工具／OS 接手與模型遵循仍未驗，所以 **F46 仍未整項通過**。待辦與現況看 [HANDOFF.md](HANDOFF.md)，需求條文看[需求決策書](project-bootstrap-requirements-decision.md) F46 驗收。
>
> 要撤銷這條宣告（改成補裝），是改使用者的決定，不是改措辭。

- **沒有 handoff skill、沒有 `pre-push-handoff.sh`、沒有 `check_docs.py`。** 它是制度的**來源**，不是一個交接中的工作專案；把骨架的這幾份套到它自己身上，就會出現「權威版與它的副本互相同步」的迴圈。跨 session 現況看 `HANDOFF.md`，歷史與版本證據看 `git log` 與各檔的 `source:` 標記；接棒程序讀全域副本 `~/.claude/skills/handoff/`。**`HANDOFF.md` 是 2026-10-30 補回來的例外**，見下一條；`pre-push-handoff.sh` 同一天重新評估過，結論仍是不裝，但理由已經換成另一個，見下面那條。
- **跨機器「工作中」標記：2026-10-30 先是接受這個缺口，同一天決定多機維護就補上了。** 當初不裝的理由是它需要 `HANDOFF.md` 當載體，而那一份得每輪交棒維護——只為防呆而裝，就是多一份沒人讀、然後開始腐化的文件；那時 single writer 靠人顧。改成多機維護之後這個理由不成立了：`git log` 與 `git fetch` **看不到別台機器未提交的變更**，而開場那個 ✅ 只證明「本機沒落後 origin」，誤接棒就會整批繞過那些變更。所以補上 `HANDOFF.md`（範本 3.3 的*實例*，不是副本，沒有同步義務），並在 `repo-git-check.sh` 加判讀段——**沿用 3.10 的同一個載體與同一個欄位，沒有發明第二種標記**，那會變成「這裡會擋、別處不會擋」的不對稱。當時為減少維護成本而限制更新欄位，卻仍保留完整狀態段落，導致已完成待辦凍結；2026-11-01 已取消此限制，維護義務與事故見 [AGENTS.md](AGENTS.md)「本 repo 的交接快照」。**天花板要講明白**：標記只告訴你「東西在那台機器上」，東西本身仍得回那台 push，這不是實作缺漏。
- **`pre-push-handoff.sh`：2026-10-30 決定不裝，2026-11-01 恢復交接快照後重新評估仍不裝。** 原理由是標記之外沒有狀態要寫，推進度時只會逼人編變更或關掉防呆；如今這個前提已取消，不能沿用舊理由。重新評估的限制是：骨架那支 hook 只檢查這批 commit 是否碰過 `HANDOFF.md`，而 A5 的開工標記本來就會碰它；本次三輪 stale 事故正是「檔案都有改、待辦沒改」。因此原樣裝上也攔不住已知故障，還會讓人誤信狀態已被驗證。現階段由 B6 核對整份快照，`verify_bootstrap.py` 檢查版本與已知回歸；不以時間戳或碰過檔案冒充內容正確。若將來有能檢查實質交接的機制再評估。
- **但有一支自己的 SessionStart hook**（`.claude/hooks/repo-git-check.sh`，2026-10-30 加）：做 git 新鮮度比對、「工作中」判讀（2026-10-30 加）與開工改名提示（2026-11-01 加）。**2026-11-01 起 Codex 這一面也接上了**（`.codex/hooks.json`，掛同一支腳本、不複製第二份）——在此之前只有 Claude Code 會跑它，而這個 repo 本來就在多工具維護；代價是它跟那六個專案一樣進了「Codex 要各審一次」的清單（信任綁 `hooks.json` 的絕對路徑），2026-11-01 已完成現行 hook 的注入與阻擋驗收，本次桌面 session 亦收到開場輸出；檔頭明寫**不是 3.10 的副本、不要同步**。在此之前這個 repo 開場完全沒有提醒，A1 的 fetch 全靠使用者記得打「接棒」把全域 skill 載進來。為什麼不直接抄 3.10——`sync_project.py` 的 `discover()` 靠 handoff skill 發現專案，這個 repo 沒有 skill，`--all` 永遠掃不到它，抄過來就會變成「所有專案都同步了、只有來源自己落後」而且毫無跡象的那一份副本。
- **沒有 CI。**（2026-09-13 隨本檔首版 `7a5d1ec` 寫入；日期取自 git 首次出現，當時沒有記錄另外的評估）驗證是一個指令（`python -X utf8 tools/verify_bootstrap.py`），跑它是鐵律第 4 條的義務。
- `tools/` 保存來源維護入口：`verify_bootstrap.py` 測試部署包及 v2 原型、`sync_project.py` 同步它；2026-11-06 新增 `verify_v2.py` 執行隔離原型。三支都不部署。`experiments/v2/` 的程式是未部署的候選實作，沒有從部署包移轉任何現行規則權威。

## 全域約束（誰強制什麼）

| 約束 | 由誰強制 | 理由與做法 |
|---|---|---|
| 全檔 LF | `.gitattributes` 的 `eol=lf`＋`verify_bootstrap.py` 的行末檢查 | [AGENTS.md 行末那節](AGENTS.md) |
| 不寫單位名／內部代號／本機絕對路徑 | 人（提交前擋）＋骨架端的跨平台防呆檢查 | [AGENTS.md 鐵律第 6 條](AGENTS.md) |
| 只放通用制度與 `{{佔位符}}` | `verify_bootstrap.py` 的佔位符清單比對 | [AGENTS.md 鐵律第 5 條](AGENTS.md) |
| 副本改內容就跳 `source:` 版本 | 人 | [AGENTS.md 鐵律第 2 條](AGENTS.md) |

## 改本檔的時機

根目錄多／少一個檔案、部署包增刪一節範本（記得同步 `EXPECTED` 與上面的 3.x 對照表）、`verify_bootstrap.py` 增減檢查項、副本拓撲改變。
**跟該變動同一個 commit**，並更新檔頭的「最後更新」。
