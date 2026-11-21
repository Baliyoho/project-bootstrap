#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""驗證部署包（src/kit 與生成的 bootstrap.py）本身還能不能用，本 repo 唯一的驗證腳本。

改完部署包要重生一次骨架來驗；以前那是一段要人手刻的敘述，常被跳過，所以固化成一個指令
（AGENTS.md 專用規則 9）。本 repo 自己的交接快照、開場 hook 與文件也由它檢查，不另裝 check_docs.py。

用法（在本 repo 根目錄執行）：
  python -X utf8 tools/verify_bootstrap.py
  python -X utf8 tools/verify_bootstrap.py --staged  # B7：驗提交候選與工作樹一致
  python -X utf8 tools/verify_bootstrap.py --keep   # 保留產生的骨架供人工檢查

檢查項一覽（守什麼、失敗代表什麼；這是唯一的一份清單，增減檢查項時改這裡。
驗證項的取捨經過在 docs/history/rationale-history.md 的「#rule-4」那組）：

| 檢查 | 守什麼 | 失敗代表 |
|---|---|---|
| 重生骨架 | 範本清單與 `EXPECTED` 一致 | 有人刪了範本沒發現，或新增範本沒登記 |
| 填佔位符 | 模擬部署後不該有殘留 | 範本用了訪談表沒有的佔位符 |
| `check_docs` | 在填好的骨架跑要 exit 0 | 範本裡有死連結或缺日期標頭 |
| 佔位符清單 | `PLACEHOLDER_NAMES` 涵蓋範本真正用到的名字 | 有個洞永遠不會被檢查到，而且沒有跡象 |
| 真實部署形狀 | 專案裡有非 ASCII 檔名時 check_docs 仍 exit 0、不崩潰 | 崩潰看起來像環境問題，接手的人會跳過驗證 |
| 跨平台防呆 | 無絕對路徑、有 `python3` 退路 | 換一台機器會靜默失效 |
| AI push 提醒情境 | staged／unstaged 不放行、已提交開工／交棒放行；命令選項、remote、refspec、GUI／script 的已知邊界；恢復舊捷徑的負向測試 | 未提交修改不會隨 push 上傳，不能拿來放行；有限提醒不能冒充發布保證（F06） |
| 工作中標記 | 範本有欄位，且 git-freshness 讀 `origin` 那一份後照原文印出（v3 D12）：別台機器、主題含「無」原文完整、已交棒、欄位重複說有幾列、欄位不存在明講讀不到、工具環境變數不改變輸出；拿掉印出那一行的負向測試 | 下一棒看不到誰握著分支（F4 偵測） |
| `VERSION` 檔 | 與部署包版本行一致 | 落後偵測會說謊，落後的專案以為自己最新 |
| 版本落後偵測 | 共用制度版本取自 `AGENTS.md` 開始標記；餵**比本機新**的版本要講落後、餵**比本機舊**的要說「比上游新」、同版與 `BOOTSTRAP_VERSION_CHECK=off` 要閉嘴 | 專案不再自己回報落後（F18 提示） |
| 本 repo 自己的文件 | 用部署後 `check_docs.py` 的同一份函式、換上本 repo 的設定查：`.md` 無死連結、`AGENTS.md`／`ARCHITECTURE.md`／`docs/ai-notes/` 有日期標頭、受管檔無已知部署佔位符；`src/kit/`、`bootstrap.py` 另有規則，`archive/docs/` 封存區不讀（v3 Q39）；`AGENTS.md` 的共用制度連到部署後的路徑，讀檔時塗白 | 改檔名或搬段落留下死連結，或把未填的部署欄位帶進公開來源。本 repo 不裝副本卻跑同一份程式，F46 的「保護不低於產物」在文件這一面是構造上成立 |
| 封存原件 | `archive/docs/` 的 v2 決策書 Git blob 不變（只看 index 記的 blob，不開檔）；程式、測試與設定檔不出現它的路徑（`ARCHIVE_READERS` 登記的除外，登記前要使用者同意）；文件檢查不讀封存區但不外溢。引用、改內容、搬走、略過外溢四種反例都要擋，已登記讀取者放行（v3 Q39） | 有程式又開始讀 v2，或封存原件被改、被搬走 |
| 版本更替 | 現行版本取 AGENTS 連到的決策書（檔名的版本號要跟「決策版本」行相同）；`archive/` 以外的檔名、資料夾名與程式識別字不得帶比它舊的版本號，程式不得引用 `archive/` 底下的版本封存資料夾。文件內文的對照與歷史說明、`v2.1.277` 這種工具版本號不算；本檔自己的反例在執行時拼出版本號，換版後不會擋到自己。版本來源 3 種、檔名／識別字／封存引用 4 種反例（v3 Q47） | 新版成為權威後，舊版本名稱的檔案或程式還留在現行區；也就是 v2 的程式留在 main 那種情形（v3 Q46） |
| 本 repo push 前 hook | `repo-pre-push.sh` 跟部署包 3.11 逐位元組相同；兩份接線的 PreToolUse 都指向它；接線守門 7 個負向測試（沒接、指向別支、matcher 退回 `Bash`、接回 PostToolUse、SessionStart 指錯、腳本不存在）（v3 F10） | 改了 3.11 卻沒重貼，或接線被改掉，本 repo 推 `main` 時沒寫開工標記也不會被擋 |
| 本 repo 兩份接線 | `.claude/settings.json` 與 `.codex/hooks.json` 都是合法 JSON、`SessionStart` 都指向 `repo-git-check.sh`、`PreToolUse` 都指向 `repo-pre-push.sh`，其他事件一律拒絕，而且沒被改成指向 `git-freshness.sh`／`pre-push-handoff.sh` | 開場檢查靜默不執行——看起來有防護、實際上沒有。這兩個檔是 JSON、塞不進 `source:` 標記，落後偵測看不到它們，這一項是唯一的守門人 |
| sync 拒絕本 repo | `sync_project.py <本 repo 路徑>` 要印出拒絕，**而且預演輸出裡零 `UPDATE`** | 一次手打路徑就把兩份接線改成指向這裡不存在的腳本。只檢查「有印拒絕」的話，一個印了話卻照樣改檔的版本會通過，比沒有這項更糟 |
| 改名寫進回報模板 | A5／B9 各有必填 `session：` 與無改名工具時的回報選項，附負向測試 | 改名漏做卻在 repo 內沒有任何跡象 |
| 續聊狀態與計數 | `AGENTS.md` 共用制度有「`↗` 時收到新訊息先改回 `㊣`」（v3 第 5 節、Q54）；skill 參考檔保留時間與計數、只讀不寫 Git、改檔重跑 A、成功交棒才累加；附 17 個負向測試 | 已交棒後續聊沒恢復工作中，或計數被重算 |
| 本 repo 交接狀態 | 必要欄位與章節、≤80 行、骨架版本符合 VERSION、禁止這次已知過期待辦與只改兩欄的入口規則；附負向測試 | 標記清了卻保留已完成待辦，下一棒被迫從聊天重建現況；不保證任意待辦的語意正確，仍需 B6 人工核對 |
| 規則理由連結 | AGENTS.md 與 `docs/maintenance.md` 每節至少一個、專用規則／副本規則／hook 訊息每條各一個指向 `docs/rationale.md` 的連結（從各自的位置算相對路徑），連結的段落存在且非空；只有表格列的「碰到才讀」索引節免連結，夾帶規則句就照一般章節要求；AGENTS 照「## 大段／### 節」切，只放小節的大段標題不算一節（v3 Q58）；附負向測試 | 理由搬到別的檔之後被悄悄刪掉、新增規則沒有理由、連結指向不存在的段落。只查連結與段落存在，不判斷理由寫得對不對 |
| 規則引用有前綴 | 現行文件、範本與程式註解引用 AGENTS 的規則編號時寫「共用規則 N」或「專用規則 N」（「副本規則 N」是維護手冊自己的清單，放行）；`CHANGELOG.md`、`docs/history/`、`archive/`、`experiments/` 是經過，不查；3 個負向測試（v3 Q58） | 共用與專用分開編號後，沒有前綴的「規則 N」分不出指哪一份，舊編號也會躲在裡面不被發現 |
| 來源例外可見性（F46 部分） | 每輪印出已宣告減項（handoff skill、check_docs.py 兩項）；確認來源缺、產物有，並對漏宣告／來源增項／產物缺項跑負向變異 | 減項從驗證輸出中靜默消失；這只驗可見性 |
| 來源／產物交接快照同組情境（F46 部分） | 同一組 13 種合成快照在來源檢查與部署後 `check_docs.py` 各跑一次：有效、整份缺失、占用欄缺失／重複、章節缺失、超行數、機器／工具欄正反例、主題含「無」、已交棒前後有空白均須一致；來源檢查遇整份缺失須明確報錯 | 來源少了整份 `HANDOFF.md` 時只拋例外，或產物與來源對相同缺陷給出矛盾結論；實際接手流程仍待驗 |
| 部署後文件檢查情境 | 部署後 `check_docs.py` 跑 20 種正反例：根目錄及巢狀文件的缺檔、死連結、程式碼、角括號加 title、片段、日期（含 `ARCHITECTURE.md`）及佔位符；本 repo 用同一份函式查自己，所以同時守來源 | 部署後的文件檢查漏擋或誤報；本 repo 的文件檢查也跟著壞 |
| 部署後文件設定情境 | 9 種專案設定情境：非 Markdown 已知佔位符、未知樣板、專案自訂過期字串、同列歷史文字與連結／佔位符／過期字串路徑豁免 | 專案改了「專案設定」區塊後檢查失準；任意專案設定與跨工具遵循仍待驗 |
| 來源提交候選一致性（F46 部分） | 來源 `verify_bootstrap.py --staged` 拒絕未暫存或未追蹤檔；完整／部分 stage 與產物 `check_docs.py --staged` 跑同組 fixture，並對來源未追蹤檔作負向測試 | 用未提交的工作樹內容證明另一份 staged 內容；只驗提交候選形狀，不代表實際接手流程已驗收 |
| 部署後接手流程情境 | 在部署出去的專案上用本機 bare origin 實跑：遠端占用→陳舊接手阻擋→釋出→A2.5／A5 SHA 變更→本機開工→任務推送→交棒；把 hook 改讀本機快照的負向變異要重現錯誤放行。本 repo 的 hook 是逐字副本，不重跑 | hook 讀錯快照，別台機器的「工作中」被當成已交棒；hook 只提醒，模型遵循未驗 |
| 本 repo 開場 hook | `repo-git-check.sh` 跟部署包 3.10 逐位元組相同；多一行與檔案不存在兩個負向測試 | 改了 3.10 卻沒重貼，本 repo 開場印的跟共用制度說的不一樣，或退回會下指示的判讀版 |
| 同步清單涵蓋骨架 | `sync_project.py` 的四份清單加起來要等於 `EXPECTED` | 新增範本沒歸類＝那個檔沒人同步，而且沒有徵兆。2026-10-30 就是這樣查出兩份 hook 接線從來沒被發下去 |
| 同步安全 | F02：骨架只擁有**指向骨架腳本的 handler**（同組的自訂 hook 要保留，matcher 衝突／重複組／異常分組要拒絕，`commandWindows` 要認得）；HANDOFF 的「## 已完成」改名「## 目前進度」。F03：任一項算不出來就零寫入，失敗與不存在的目標要非零退出、不准宣稱最新版 | 同步靜默刪掉專案設定；或失敗一半卻回 exit 0 並宣稱最新版，而落後的專案以為自己同步過了（F02、F03） |
| 同步升級 mode | 替換前複製既存 mode；複製失敗保留原檔；新依賴仍可建立；移除複製的負向變異必須失敗。POSIX 另驗 0755／0640、開場 hook 直接執行、Git 無 mode diff | 新 inode 預設權限會讓更新後的 POSIX hook 無法執行；Windows 通過不代表 POSIX 實測 |
| 結構摘要一致性 | 本 repo 與生成 ARCHITECTURE 寫明 `CLAUDE.md` 用 import；兩個負向測試 | 權威範本已改，結構表格仍教舊寫法 |
| 接線合併 | 餵一份「舊 matcher ＋ 專案自己加的 permissions 與 hook」進去，要換掉舊值、保住專案設定、已一致時不動 | 同步會洗掉專案設定，或落後的專案根本修不好 |
| 跨工具表保鮮期 | 「跨工具與跨平台」那節的「查證日期」不得超過 90 天（`BOOTSTRAP_FRESHNESS=off` 可跳過） | 對外部工具能力的斷言在無聲中過期。這一項只保證有人看過日期，**不保證有人真的重查**——買到的是「必須有意識地決定」。會做成 fail 而不是警告，是因為上一次的對策就是一句警告，而警告沒擋住第二次（Antigravity 的 hooks、Codex 桌面 App 的 hooks，兩次同一種錯） |
| 跨工具過期敘述 | 部署包正文、本 repo 結構說明、重生的結構範本與 handoff skill，不得復活 CLI／2.0 測試狀態、Antigravity 接線、skill 入口與 IDE 追查決定的已知舊斷言；附回歸負向測試與範圍測試 | 同一份文件的表改對了，散文卻仍教下一棒照舊事實行動。只檢查已知回歸，不做通用語意判讀、不代替外部查證；表頭的歷史變更記錄與 IDE 未解結果仍保留 |
| Codex Windows 接線 | `commandWindows` 經 Git Bash 啟動器，兩個事件與本 repo 都指向原本那支 `.sh`；三個負向測試 | 真部署的已信任 hook 曾選到 WSL 而 exit 1 |
| Codex Windows 結束碼 | 實跑 PowerShell → cmd → Git Bash；保留 exit 2，拿掉明確 exit 時必須重現 exit 1 | 只測原生 cmd 會把工具仍放行的版本誤報成功；此項只在 Windows 執行 |
| Codex 接線升級 | 舊專案補齊啟動器、保留專案 hook 與 SKILL、預演零寫入、重跑零變更、不替沒有接線的專案補裝 | 只更新 JSON 卻漏掉新依賴會再度靜默失效 |
| Codex Windows 啟動器 | Windows 原生 cmd 實跑中文／空白路徑、不同 cwd、stdin／stdout／stderr／exit 2 與缺少 Git Bash 的情境 | 轉接層若吞掉 exit 2，pre-push 防呆會消失；此項只在 Windows 執行 |
| verify_state 失敗訊號 | 命令非零退出、HTTP 500、連不上、200 但回應內容不對都要讓結束碼非零；缺憑證是 SKIP，`--strict` 才非零、`OPTIONAL` 放行；未填仍回 0；祕密要遮罩。十個情境全部實跑 | 舊版每一種情況都 return 0，畫面印著 `rc7` 而下游拿 exit 0 當服務驗收（F04） |
| 交接快照檢查 | 超過 80 行、章節重複或欄位重複都要 exit 2（刪檔與缺章節在交接快照同組情境）；`--docs-only` 要真的關得掉；程式碼範例、帶 title 與角括號連結不得誤報，但真的死連結仍要抓到 | 第 6 項只在 HANDOFF 出現在輸入清單時才驗，整份刪掉反而回報乾淨；而連結誤報會教人「這支腳本的 FAIL 可以無視」（F08） |
| Python 版本下限 | 兩支維護工具與安裝程式的 `MIN_PY` 存在、在檔頭擋下舊版，跟 `pyproject.toml` 的 `requires-python` 同號；README 範本寫出同一個下限；4 個負向測試（2026-11-21 使用者選定全部對齊 3.12） | 下限各處說法不一，有人照比較低的那個去裝，跑到用了新 API 的那一行才炸（F14） |
| 已修正的主張沒復活 | 能力表 ✅ 的工具不得被散文說成沒有 skill、交接 prompt 不得有自己的 A／B 編號且要寫出模式、`verify_state` 不得以憑證為前提、版本序號只有一種定義、可攜層不得寫成「到哪都成立」；附九個負向測試 | 事實在部署包被改對，範本、操作卡與入口文件裡的舊說法照樣部署出去。綁結構不綁禁句，「」裡的引用不算主張（專用規則 8 要留為什麼）；守不了一整段敘述的準確度（F15） |
| 協作狀態契約／Git 異常提示 | 六狀態與步驟契約、21 個負向測試，含 R07 先 stage 再驗證。Git 異常：部署 hook 實跑領先／分岔／fetch 失敗要照實報出、不得建議 rebase，`AGENTS.md` 共用制度要有停止條件；本 repo hook 照舊要求停止；2 個負向測試 | 程序順序矛盾或工具提示教人自行 rebase |
| 核心與實例優先序 | skill／README 宣告一致、override 範圍明確、7 個負向測試；同步對舊實例列版本與 MIGRATE，不改寫 | 不同步的舊協定會推翻新程序（F10） |
| 接力協調邊界 | A2.5／A5 明列協調訊號非鎖、SHA 比對與禁止自動奪權，4 個文字負向測試 | 不宣稱並行互斥；原子 claim 留待另案（F12） |
| skill 拆分 | 七個 skill 檔齊全、同版本、都在 `WHOLE`；入口＋`mode-a.md` ≤6,000 字元；入口 12 條、`mode-a.md` 12 條必備句；拆分前每一行逐字留存或列入已改寫清單（13 行） | 入口指向不存在的檔、同步只寫一半、濃縮時丟了停止條件或理由。不證明模型會去讀模式檔 |
| AGENTS.md 共用制度 | 開始／結束標記成對、35 條必備條件（v3 第 5 節；每條共用規則至少一條，三個 ### 節與 ## 大段標題都在，v3 Q58）、共用 ≤40 行、全檔 ≤100 行（v3 D11）、開始標記的版本等於 `VERSION`；39 個負向測試 | 每個 session 都載入的那一層缺了條件、長過預算，或版本提示失準。只證明文字在，不證明模型照做 |
| 同步補齊模式檔 | 只有單檔的舊專案會補上五個新檔、入口最後寫、不認得的檔列為 EXTRA；1 個負向測試 | 同步後新入口指向不存在的模式檔 |
| 同步共用制度 | `AGENTS.md` 沒有共用制度就插在第一個「## 」前、舊版整段換掉、標記外不動、已是權威版不寫、壞標記 FAIL 不寫、舊交接段落、「## 鐵律」與接在結束標記後的編號清單列 MIGRATE、新版「### 專用規則」不列（v3 Q58）、先於 skill 入口寫；2 個負向測試 | 新 skill 指向舊專案 `AGENTS.md` 裡不存在的共用制度（v3 Q34 前置） |
| 同步範圍與前置檢查 | 真 worktree、含 worktrees 普通目錄、已完結 inventory；fresh fetch／upstream 對齊／明確 owner、dirty／占用／整份檔與 check_docs 共用程式區客製漂移拒絕且零寫入；批次僅預演，單專案 A5 writer 才能寫入 | 路徑字串不是 worktree 證據，批次同步不能悄悄擴大範圍（F13） |
| 部署生命週期 | 訪談自訂 ignore、本機檢查→首 commit→local bare push→clone，clone 後開場 hook 印出 `[facts]`；`mode-0.md` 0-5 的驗收、提交、發布順序與不整批 `git add`（v3 Q49）；6 個負向測試 | 圍欄外追加規則及發布後才驗收無法保護首 commit |
| 安裝程式由來源生成 | `bootstrap.py` 與 `src/kit`、`installer.py`、`sync_project.py` 的生成結果逐位元組相同；5 個負向測試（手改、改範本／installer／合併函式沒重生、少一個共用函式）。安裝、衝突、更新、CRLF 與兩支 hook 由 `tests/test_bootstrap_repo.py` 在暫存資料夾實跑 | 手改了安裝程式，或改了來源沒重生（v3 Q49） |
| 部署包由來源生成 | `src/kit` 組得出部署包全文、每個範本剛好用一次、範本集合等於 `EXPECTED`，而且 `PROJECT-BOOTSTRAP.md` 沒被放回來；7 個負向測試（放回來、多／少範本、指錯、重複、缺結尾換行、範本含收尾圍籬） | 部署包全文是範本的第二份副本；2026-11-18 起不提交（v3 Q50），放回來就又多一份會過期的家 |
| 開發骨架 | pyproject 依賴都在 `uv.lock`、外部套件都有 sha256 與授權、最低 Python 3.12、`package = false`；`tools/` 與 `src/project_bootstrap` 的程式除 `DEV_EXTRAS` 列的模組外不 import 鎖檔裡的套件，也不 import 那些模組；import 它們的測試缺套件時 SkipTest；10 個負向測試。不需要 uv，鎖檔是否最新要另跑 `uv lock --check` | 依賴沒鎖或沒審授權；A4 在沒裝 uv 的機器跑不起來 |
| 全域 handoff skill 跟部署包同版 | 家目錄 `~/.claude/skills/handoff/`、`~/.codex/skills/handoff/` 的七個檔跟 `src/kit` 範本逐字相同（不只比 `source:` 版本號）；不同只印「提醒」、不影響結束碼，兩份都沒裝印 skip；4 個負向測試 | 改了部署包卻忘了重裝全域副本，沒有專案層 skill 的 session 讀到舊程序（2026-11-18 使用者指定） |
| 行末與雜項 | 全 LF、JSON 合法、腳本可執行 | Windows 寫出 CRLF、設定檔打錯字 |

Python 版本下限：兩支維護工具、安裝程式與開發環境都是 3.12（MIN_PY），在檔頭就檢查、清楚報錯。
「Python 版本下限」那一項只查各處宣告同號，不掃有沒有用到更新的 API。

結束碼：0＝全過；1＝有跳過項（缺 bash 之類）但無失敗；2＝有失敗。印「提醒」的項目不影響結束碼。
本工具唯讀本 repo，只在系統暫存區寫檔。
"""
import argparse
import atexit
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import http.server
import importlib.machinery
import importlib.util
import tempfile
import threading
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from unittest.mock import patch
from datetime import date

# Python 版本下限（查核報告 F14）。在檔頭就擋，訊息要說「版本太舊」：高於下限的 API 不會在
# 啟動時失敗，而是執行到那一行才炸，那種形狀沒人會聯想到版本。跟安裝程式、開發環境同一個下限
# （2026-11-21 使用者選定全部對齊 3.12），由「Python 版本下限」那一項檢查釘住。
MIN_PY = (3, 12)
if sys.version_info < MIN_PY:
    sys.exit('需要 Python %d.%d 以上，本機是 %d.%d——請改用較新的 python'
             % (MIN_PY + sys.version_info[:2]))

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 部署包的全文（kit.md＋範本）每次從 src/kit 在記憶體生成（v3 Q50）；KIT 只剩一個名字，
# 用來擋有人把 PROJECT-BOOTSTRAP.md 放回來。
KIT = ROOT / 'PROJECT-BOOTSTRAP.md'
_KIT_TEXT = None


def kit_text():
    global _KIT_TEXT
    if _KIT_TEXT is None:
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import build_kit
        finally:
            sys.path.remove(str(ROOT / 'tools'))
        _KIT_TEXT = build_kit.kit_text()
    return _KIT_TEXT

# 第 3 節應該產出的檔案。少一份就是有人刪了範本卻沒發現；多一份就把它加進來。
EXPECTED = {
    'AGENTS.md', 'ARCHITECTURE.md', 'CLAUDE.md', 'HANDOFF.md', 'README.md',
    'docs/ai-notes/roadmap.md',
    '.claude/skills/handoff/SKILL.md', '.claude/skills/handoff/mode-a.md',
    '.claude/skills/handoff/mode-a-stop.md', '.claude/skills/handoff/mode-b.md',
    '.claude/skills/handoff/mode-0.md', '.claude/skills/handoff/reasons.md',
    '.claude/skills/handoff/env.md',
    '.claude/settings.json',
    '.claude/hooks/git-freshness.sh', '.claude/hooks/pre-push-handoff.sh',
    '.codex/hooks.json', '.agents/skills/handoff/SKILL.md',
    '.claude/hooks/codex-hook.cmd',
    '.gitignore', '.gitattributes',
    'tools/check_docs.py', 'tools/verify_state.py',
}

# 模擬部署訪談的答案。值要「像真的」——URL 型佔位符填壞會誤觸 check_docs 的死連結檢查。
ANSWERS = {
    'PROJECT_NAME': '驗證用假專案',
    'ONELINER': '這是 verify_bootstrap.py 生成的測試骨架，不是真專案',
    'GH_OWNER': 'example-owner',
    'GH_REPO': 'example-repo',
    'GH_VISIBILITY': 'private',
    'LANG': '繁體中文',
    'TZ': 'Asia/Taipei',
    'TODAY': date.today().isoformat(),
    'SECRETS': '`.env`',
    'RUNTIME_DIRS': '`data/`',
    'STACK_DIRS': '`src/`',
    'VERIFY_TARGETS': '健康檢查 API',
}
# 與 check_docs.py 的佔位符檢查同一套語法：雙大括號＋全大寫底線。放寬會誤判 verify_state.py
# 範本裡的 docker `--format '{{ .Names }}'`——那不是待填的洞。
PLACEHOLDER_RE = re.compile(r'\{\{([A-Z][A-Z0-9_]{1,40})\}\}')
HEAD_RE = re.compile(r'^### 3\.\d+ ')
FENCE_RE = re.compile(r'^(`{3,})(\w*)\s*$')

# 測試用的全域 git 設定：只關掉自動維護（2026-11-06）。
# Git 2.54（macOS 的 Apple Git-157）每次 commit／push 後都會 `git maintenance run --auto --detach`，
# 小 repo 也做 geometric repack 並寫 MIDX。背景打包跟緊接的本機 clone 撞在一起時，
# clone 會因為要硬連結的鬆散物件已經被打包刪掉而失敗（R03 owner 情境在 Mac 上約一半機率）。
# 不能用 GIT_CONFIG_COUNT：本機 push 啟動遠端 receive-pack 時 git 會清掉那組變數，
# origin 那一端看不到；GIT_CONFIG_GLOBAL 指向的檔案兩端都讀得到。
_GITCONFIG_DIR = tempfile.mkdtemp(prefix='verify-gitconfig-')
atexit.register(shutil.rmtree, _GITCONFIG_DIR, True)
_GITCONFIG = os.path.join(_GITCONFIG_DIR, 'gitconfig')
with open(_GITCONFIG, 'w', encoding='utf-8', newline='') as _f:
    _f.write('[maintenance]\n\tauto = false\n')

GIT_ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME='verify', GIT_AUTHOR_EMAIL='verify@example.com',
    GIT_COMMITTER_NAME='verify', GIT_COMMITTER_EMAIL='verify@example.com',
    GIT_CONFIG_GLOBAL=_GITCONFIG, GIT_CONFIG_SYSTEM=os.devnull,
)

# 工具身分的環境變數簽章（2026-10-31）。測 hook 的「同工具／不同工具」分支時必須先把
# 它們全部清掉再按情境放回去：verify 自己就跑在某個工具裡，os.environ 會把 CLAUDECODE
# 之類的變數帶進來，不清就變成「只有在某個工具上跑才會過」的測試——而「變數會被繼承、
# 會說謊」正是這段邏輯要擋的那件事，測試自己踩進去就什麼都證明不了。
TOOL_VARS = ('CLAUDECODE', 'AI_AGENT', 'CODEX_VERSION', 'CODEX_SESSION_ID',
             'CODEX_THREAD_ID', 'CODEX_CI')


def tool_env(**extra):
    env = {k: v for k, v in GIT_ENV.items() if k not in TOOL_VARS}
    env.update(extra)
    return env


results = []  # (status, 標題, 說明)  status: OK / FAIL / SKIP
QUIET = False


def record(status, title, detail=''):
    results.append((status, title, detail))
    if QUIET and status == 'OK':  # NOTE 跟 FAIL／SKIP 一樣在 --quiet 下照印
        return
    icon = {'OK': '  ok  ', ' FAIL ': ' FAIL ', 'FAIL': ' FAIL ', 'SKIP': ' skip ', 'NOTE': ' 提醒 '}[status]
    print(f'[{icon}] {title}{("  — " + detail) if detail else ""}')


def run(cmd, cwd=None, stdin=None, env=None):
    return subprocess.run(
        cmd, cwd=cwd, input=stdin, capture_output=True, text=True,
        encoding='utf-8', errors='replace', env=env or GIT_ENV,
    )


def git(args, cwd):
    return run(['git', *args], cwd=cwd)


def crlf_count(path):
    data = path.read_bytes()
    return data.count(b'\r\n')


_bash = False


def find_bash():
    """找一個看得懂 Windows 路徑的 bash。

    不能只用 shutil.which('bash')：Windows 上那常常是 WSL 的 bash，它讀不到 C:\\ 路徑，
    於是每個 hook 情境都回 1，看起來像 hook 壞了。用實際探測一個已知存在的檔案來篩掉它。
    """
    global _bash
    if _bash is not False:
        return _bash
    cands = []
    git_exe = shutil.which('git')
    if git_exe:                                   # Git for Windows：cmd/git.exe → bin/bash.exe
        base = pathlib.Path(git_exe).resolve().parent.parent
        cands += [base / 'bin' / 'bash.exe', base / 'usr' / 'bin' / 'bash.exe']
    found = shutil.which('bash')
    if found:
        cands.append(pathlib.Path(found))
    cands.append(pathlib.Path(r'C:\Program Files\Git\bin\bash.exe'))
    for c in cands:
        if not c.exists():
            continue
        probe = subprocess.run(
            [str(c), '-c', f'test -f "{(ROOT / "src/kit/kit.md").as_posix()}"'], capture_output=True)
        if probe.returncode == 0:
            _bash = str(c)
            return _bash
    _bash = None
    return None


def read_lf(path, encoding='utf-8'):
    """讀檔，不做換行轉換（等同 Path.read_text(newline='')，但不需要 3.13）。

    不要改回 `Path.read_text(..., newline='')`：那個參數 3.13 才有，低於 MIN_PY 的 Python
    會跑到那一行才炸（查核報告 F14）。`open()` 的 newline 參數一直都有。
    """
    with open(path, encoding=encoding, newline='') as fh:
        return fh.read()


def write_lf(path, text, encoding='utf-8'):
    """寫檔，不做換行轉換（`Path.write_text` 的 newline 參數要 3.10，見 read_lf）。"""
    with open(path, 'w', encoding=encoding, newline='') as fh:
        fh.write(text)


# ── 1. 重生骨架 ────────────────────────────────────────────────
SKILL_DIR = '.claude/skills/handoff/'
# 入口排最前、新寫的正常路徑摘要排最後：下面依標題找段落的檢查（「### A5 」之類）要先碰到
# 逐字搬來的原文，摘要另外由「skill 拆分」那一項守。
SKILL_FILES = ('SKILL.md', 'mode-a-stop.md', 'mode-b.md', 'mode-0.md', 'reasons.md', 'env.md', 'mode-a.md')
SKILL_ROUTINE = ('SKILL.md', 'mode-a.md')       # 正常接棒要讀的兩個檔
SKILL_ROUTINE_LIMIT = 6000                       # skill 拆分設計稿第 3 節（2026-11-10）。v3 起 skill 是碰到才讀的參考檔（D12），這個上限只守它的大小


def skill_text(dest):
    """整個 handoff skill 目錄的文字。2026-11-10 拆成六個檔之後，內容檢查看的是目錄而不是入口。"""
    return '\n'.join(read_lf(dest / (SKILL_DIR + name)) for name in SKILL_FILES)


def extract(dest, text=None):
    lines = (kit_text() if text is None else text).split('\n')
    heads = [i for i, ln in enumerate(lines) if HEAD_RE.match(ln)]
    written = set()
    for n, i in enumerate(heads):
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        paths = [p for p in re.findall(r'`([^`]+)`', lines[i]) if '.' in p or '/' in p]
        if not paths:
            continue                       # 例：3.20 是慣例說明，不是檔案
        # 一節裡的圍籬區塊依序對應標題上的檔名；區塊比檔名少就全部沿用第一個
        # （多數節是一個檔、一個區塊）。不要在這支腳本裡合成範本內容：那等於讓範本有第二個家。
        blocks, j = [], i
        while j < end:
            m = FENCE_RE.match(lines[j])
            if not m:
                j += 1
                continue
            fence = m.group(1)
            k, body = j + 1, []
            while k < end and lines[k].rstrip() != fence:
                body.append(lines[k])
                k += 1
            blocks.append('\n'.join(body) + '\n')
            j = k + 1
        if not blocks:
            continue
        for n_p, p in enumerate(paths):
            f = dest / p
            f.parent.mkdir(parents=True, exist_ok=True)
            with open(f, 'w', encoding='utf-8', newline='') as fh:
                fh.write(blocks[n_p] if n_p < len(blocks) else blocks[0])
            written.add(p)
    return written


def step_regenerate(dest):
    written = extract(dest)
    missing, extra = EXPECTED - written, written - EXPECTED
    if missing or extra:
        detail = ''
        if missing:
            detail += f'缺少 {sorted(missing)}'
        if extra:
            detail += f' 多出 {sorted(extra)}（新範本記得加進 EXPECTED）'
        record('FAIL', '重生骨架', detail.strip())
        return False
    record('OK', '重生骨架', f'{len(written)} 檔與 EXPECTED 一致')
    return True


# ── 2. 填佔位符 ────────────────────────────────────────────────
def ignore_rules(answer):
    """訪談的 Markdown 路徑清單 → .gitignore 的每行一個 pattern。"""
    rules = re.findall(r'`([^`]+)`', answer) or answer.splitlines()
    rules = [r.strip() for r in rules]
    if not rules or any(not r.strip() or r.startswith('!') or '\n' in r or '\r' in r for r in rules):
        raise ValueError('ignore 訪談須是非空且不含 ! 的路徑清單')
    return '\n'.join(r.strip() for r in rules)


def step_fill(dest, answers=None, report=True):
    answers = ANSWERS if answers is None else answers
    unknown, seen, filled = set(), set(), 0
    for f in sorted(dest.rglob('*')):
        if not f.is_file():
            continue
        text = f.read_text(encoding='utf-8')
        if '{' not in text:
            continue

        def sub(m):
            key = m.group(1)
            seen.add(key)
            if key not in answers:
                unknown.add(key)
                return f'UNKNOWN_{key}'
            return ignore_rules(answers[key]) if f.name == '.gitignore' and key in ('SECRETS', 'RUNTIME_DIRS') else answers[key]

        new, n = PLACEHOLDER_RE.subn(sub, text)
        if n:
            filled += n
            with open(f, 'w', encoding='utf-8', newline='') as fh:
                fh.write(new)
    left = [
        f.relative_to(dest).as_posix()
        for f in dest.rglob('*')
        if f.is_file() and PLACEHOLDER_RE.search(f.read_text(encoding='utf-8'))
    ]
    if unknown:
        record('FAIL', '填佔位符', f'第 1 節訪談表沒有這些佔位符：{sorted(unknown)}（新增佔位符要同步 ANSWERS）')
        return False
    if left:
        record('FAIL', '填佔位符', f'仍有殘留：{left}')
        return False
    if report:
        record('OK', '填佔位符', f'替換 {filled} 處、{len(seen)} 種，無殘留')
    return seen


def step_placeholder_list(dest, seen):
    """check_docs.py 的 PLACEHOLDER_NAMES 必須蓋住範本裡真正出現的佔位符。

    那份清單是封閉列舉（不是語法比對），漏掉一個名字就是那個洞永遠不會被檢查到，
    而且沒有任何跡象——所以在這裡對一次。
    """
    src = (dest / 'tools' / 'check_docs.py').read_text(encoding='utf-8')
    m = re.search(r'PLACEHOLDER_NAMES\s*=\s*\(([^)]*)\)', src, re.S)
    if not m:
        record('FAIL', '佔位符清單涵蓋範本', 'check_docs.py 裡找不到 PLACEHOLDER_NAMES')
        return False
    declared = set(re.findall(r"'([A-Z0-9_]+)'", m.group(1)))
    missing = seen - declared
    if missing:
        record('FAIL', '佔位符清單涵蓋範本',
               f'範本用了但清單沒列：{sorted(missing)}——這些洞不會被檢查到')
        return False
    unused = declared - seen
    detail = f'{len(declared)} 個名字涵蓋範本用到的 {len(seen)} 種'
    if unused:
        detail += f'（{sorted(unused)} 只在訪談表出現，不進範本）'
    record('OK', '佔位符清單涵蓋範本', detail)
    return True


# ── 3./4. check_docs ───────────────────────────────────────────
def step_check_docs(dest):
    git(['init', '-q', '-b', 'main'], dest)
    git(['add', '-A'], dest)
    r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
    if r.returncode != 0:
        record('FAIL', 'check_docs.py', f'exit {r.returncode}\n{r.stdout.strip()}\n{r.stderr.strip()}')
        return False
    record('OK', 'check_docs.py', 'exit 0')
    return True


def step_portability(dest):
    """跨平台／跨工具的靜默失效防呆。

    這兩類問題的共通點是「在原機器上完全正常，換一台才壞，而且壞得無聲無息」：
      - 絕對路徑：曾經真的發生——某專案的 .codex/hooks.json 寫死了
        C:\\Users\\<某人>\\Desktop\\<專案>\\...，那台機器一切正常，Mac 上 hook 直接不執行。
      - 硬寫 `python`：macOS／Linux 常常只有 python3，`python` 不存在。文件裡寫死
        `python xxx.py` 的那一行，換平台就是一句跑不動的指令。
    """
    abs_re = re.compile(r'[A-Za-z]:[\\/]Users[\\/]|/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/')
    py_re = re.compile(r'(?<![a-zA-Z0-9_./-])python(?!3)(?![a-zA-Z0-9_])')
    bad = []
    for f in sorted(dest.rglob('*')):
        if not f.is_file() or '.git' in f.parts:
            continue
        rel = f.relative_to(dest).as_posix()
        text = f.read_text(encoding='utf-8')
        # 判準是「整份檔案有沒有交代退路」，不是每一行都得重述——逐行要求會逼出
        # 一堆複述噪音，而讀者是整份讀的。檔內任何一處提到 python3 就算交代過了。
        told = 'python3' in text
        for n, line in enumerate(text.split('\n'), 1):
            if abs_re.search(line):
                bad.append(f'{rel}:{n}  絕對路徑  {line.strip()[:60]}')
            if not told and py_re.search(line):
                bad.append(f'{rel}:{n}  用了 python 但整份沒交代 python3 退路  {line.strip()[:60]}')
    if bad:
        record('FAIL', '跨平台防呆', f'{len(bad)} 處：\n           ' + '\n           '.join(bad[:8]))
        return False
    record('OK', '跨平台防呆', '無絕對路徑、無缺 python3 退路的 python 呼叫')
    return True


# bash 3.2 在 UTF-8 語系下的變數名界線（2026-11-06）。
# `$name` 後面緊接多位元組字元時，bash 3.2 會把那個字的第一個位元組當成變數名的一部分：
# `（branch=$branch）` 印成 `（branch=��`。判斷邏輯不受影響，壞的是每一句結論訊息。
# 用靜態掃描而不是實跑：維護者多在 Windows 的 bash 5 上跑驗證，那裡不會重現。
MB_VAR_RE = re.compile(r'\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])')


def mb_var_hits(text):
    """回傳 (行號, 命中) 清單；整行註解不求值，略過。"""
    hits = []
    for n, line in enumerate(text.split('\n'), 1):
        if line.lstrip().startswith('#'):
            continue
        hits += [(n, m.group()) for m in MB_VAR_RE.finditer(line)]
    return hits


def step_bash32_multibyte(dest):
    # 負向測試：壞寫法一定要抓到，正確寫法與註解不能誤報
    probes = [
        ('echo "（b=$b）"', 1), ('echo "「$tool」"', 1), ('echo "$a、$b"', 1),
        ('echo "（b=${b}）"', 0), ('# 註解裡的 $b） 不求值', 0), ('echo "$b ok"', 0),
    ]
    wrong = [s for s, want in probes if len(mb_var_hits(s)) != want]
    if wrong:
        record('FAIL', 'bash 3.2 多位元組變數', '偵測器本身壞了：' + '；'.join(wrong))
        return False
    files = [f for f in sorted(dest.rglob('*.sh')) if '.git' not in f.parts]
    files += sorted((ROOT / '.claude' / 'hooks').glob('*.sh'))
    bad = []
    for f in files:
        rel = f.relative_to(dest).as_posix() if dest in f.parents else \
            '本 repo:' + f.relative_to(ROOT).as_posix()
        for n, hit in mb_var_hits(f.read_text(encoding='utf-8')):
            bad.append(f'{rel}:{n}  {hit}…（改成 ${{{hit[1:]}}}）')
    if bad:
        record('FAIL', 'bash 3.2 多位元組變數',
               f'{len(bad)} 處：\n           ' + '\n           '.join(bad[:8]))
        return False
    record('OK', 'bash 3.2 多位元組變數',
           f'骨架與本 repo 共 {len(files)} 支 .sh 無「$變數緊接全形字」；{len(probes)} 個正負向探針通過（靜態，未在 bash 3.2 實跑）')
    return True


def step_deploy_shape(dest):
    """專案裡有非 ASCII 檔名時，check_docs 要照常回報，不能崩潰。

    2026-08-05 實際部署踩到：`git ls-files` 預設把非 ASCII 檔名輸出成八進位跳脫，
    check_docs 直接 traceback。崩潰看起來像環境問題，接手的人會跳過驗證。
    """
    noise = dest / '讀我-先看這個.md'
    with open(noise, 'w', encoding='utf-8', newline='') as fh:
        fh.write('# 說明\n\n> 最後更新：2026-08-05\n')
    try:
        git(['add', '-A'], dest)
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
        if 'Traceback' in r.stderr:
            tail = r.stderr.strip().splitlines()[-1][:120]
            record('FAIL', '真實部署形狀', f'check_docs 崩潰而非回報問題：{tail}')
            return False
        if r.returncode != 0:
            head = '\n           '.join(r.stdout.strip().splitlines()[:6])
            record('FAIL', '真實部署形狀', f'exit {r.returncode}\n           {head}')
            return False
        record('OK', '真實部署形狀', '非 ASCII 檔名，check_docs 仍 exit 0')
        return True
    finally:
        noise.unlink(missing_ok=True)
        git(['add', '-A'], dest)


# ── 5. AI push 提醒情境 ────────────────────────────────────
def step_hook(dest, tmp):
    bash = find_bash()
    if not bash:
        record('SKIP', 'AI push 提醒情境', '找不到看得懂 Windows 路徑的 bash（裝 Git for Windows 即可）')
        return None
    origin = tmp / 'origin.git'
    work = tmp / 'hookwork'
    run(['git', 'init', '-q', '--bare', str(origin)])
    shutil.copytree(dest, work, ignore=shutil.ignore_patterns('.git'))
    git(['init', '-q', '-b', 'main'], work)
    git(['add', '-A'], work)
    git(['commit', '-qm', 'init'], work)
    git(['remote', 'add', 'origin', str(origin)], work)
    git(['push', '-q', '-u', 'origin', 'main'], work)
    git(['remote', 'set-head', 'origin', 'main'], work)
    hook = str(work / '.claude' / 'hooks' / 'pre-push-handoff.sh')
    push = '{"tool_input":{"command":"git push origin main"}}'

    noise = []

    def fire(payload, env=None):
        r = run([bash, hook], cwd=work, stdin=payload, env=env or GIT_ENV)
        if r.stderr.strip():
            noise.append(r.stderr.strip()[:200])
        return r.returncode

    cases = []
    cases.append(('非 push 指令', 0, fire('{"tool_input":{"command":"git status -sb"}}')))

    (work / 'README.md').open('a', encoding='utf-8', newline='').write('\n驗證用改動\n')
    git(['commit', '-qam', 'docs: touch'], work)
    cases.append(('權威分支未更新 HANDOFF', 2, fire(push)))

    def command(value):
        return fire(json.dumps({'tool_input': {'command': value}}))

    # F06：明列有限提醒的邊界，不把 substring 判讀冒充 shell／refspec 解析。
    cases.append(('選項 -c（刻意漏判）', 0, command('git -c color.ui=false push origin main')))
    cases.append(('其他 remote（仍看 origin，可能誤擋）', 2, command('git push backup main')))
    cases.append(('其他 refspec（仍看目前分支，可能誤擋）', 2, command('git push origin HEAD:feature/x')))
    cases.append(('僅提到 push（已知誤擋）', 2, command('echo git push')))
    cases.append(('script 間接 push（刻意漏判）', 0, command('./publish.sh')))
    cases.append(('GUI 無命令 payload（不覆蓋）', 0, fire('{}')))
    # Q27（2026-11-12）：只看 command 欄位。非殼層工具的內容提到 git push 不擋（舊版會，Codex 沒有 matcher）。
    patch_payload = json.dumps({'tool_name': 'apply_patch', 'tool_input': {'input': '*** 說明：收工再 git push\n'}},
                               ensure_ascii=False)
    cases.append(('非殼層工具內容提到 push（Q27 放行）', 0, fire(patch_payload)))
    cases.append(('command 是字串陣列', 2, fire(json.dumps({'tool_input': {'command': ['bash', '-lc', 'git push']}}))))
    cases.append(('push 只出現在 command 以外的欄位', 0,
                  fire(json.dumps({'tool_input': {'command': 'git status', 'description': 'then git push'}}))))
    cases.append(('停用開關確實繞過阻擋', 0, fire(push, env=dict(GIT_ENV, HANDOFF_HOOK='off'))))

    (work / 'HANDOFF.md').open('a', encoding='utf-8', newline='').write('\n- 驗證用\n')
    cases.append(('HANDOFF 僅 unstaged', 2, fire(push)))
    git(['add', 'HANDOFF.md'], work)
    cases.append(('HANDOFF 僅 staged', 2, fire(push)))
    (work / 'HANDOFF.md').open('a', encoding='utf-8', newline='').write('\n- 尚未提交\n')
    cases.append(('HANDOFF staged 加 unstaged', 2, fire(push)))

    # 負向儀器：把 F06 修正前的放行捷徑插回去，必須重現錯誤的 exit 0。
    hook_path = pathlib.Path(hook)
    fixed = read_lf(hook_path)
    anchor = 'git diff --name-only "origin/$branch..HEAD"'
    at = fixed.index(anchor)
    try:
        write_lf(hook_path, fixed[:at] + 'git diff --quiet -- HANDOFF.md 2>/dev/null || exit 0\n' + fixed[at:])
        cases.append(('負向：舊捷徑重現錯誤放行', 0, fire(push)))
    finally:
        write_lf(hook_path, fixed)
    # 負向儀器（Q27）：拿掉只看 command 欄位那一道，非殼層工具的內容必須重現舊版的誤擋。
    field = "  | grep -qF 'git push' || exit 0\n"
    if fixed.count(field) != 1:
        cases.append(('負向：hook 沒有唯一的 command 欄位過濾', 'present', 'missing'))
    else:
        try:
            write_lf(hook_path, fixed.replace(field, "  >/dev/null; true\n"))
            cases.append(('負向：拿掉欄位過濾重現舊誤擋', 2, fire(patch_payload)))
        finally:
            write_lf(hook_path, fixed)
    git(['commit', '-qam', 'chore: handoff'], work)
    cases.append(('交棒快照已提交', 0, fire(push)))
    git(['push', '-q', 'origin', 'main'], work)
    handoff = work / 'HANDOFF.md'
    write_lf(handoff, read_lf(handoff).replace('無（已交棒）', '`fixture` ／ `Codex CLI`'))
    git(['commit', '-qam', 'chore: claim'], work)
    cases.append(('開工標記已提交（不等於交棒）', 0, fire(push)))
    # Q31（2026-11-12）：origin 上已有開工標記，中途安全點不必更新 HANDOFF。
    git(['push', '-q', 'origin', 'main'], work)
    (work / 'README.md').open('a', encoding='utf-8', newline='').write('\n中途安全點\n')
    git(['commit', '-qam', 'docs: safe point'], work)
    cases.append(('origin 有開工標記的中途安全點（Q31 放行）', 0, fire(push)))
    allow = "git show \"origin/$branch:HANDOFF.md\" 2>/dev/null | grep -F '**工作中**' | grep -vqF '無（已交棒）' && exit 0\n"
    current = read_lf(hook_path)
    if current.count(allow) != 1:
        cases.append(('負向：hook 沒有唯一的開工標記放行', 'present', 'missing'))
    else:
        try:
            write_lf(hook_path, current.replace(allow, ''))
            cases.append(('負向：拿掉標記放行就擋回中途安全點', 2, fire(push)))
        finally:
            write_lf(hook_path, current)
    git(['push', '-q', 'origin', 'main'], work)
    write_lf(handoff, read_lf(handoff).replace('`fixture` ／ `Codex CLI`', '無（已交棒）'))
    git(['commit', '-qam', 'chore: release'], work)
    git(['push', '-q', 'origin', 'main'], work)
    (work / 'README.md').open('a', encoding='utf-8', newline='').write('\n交棒後又改\n')
    git(['commit', '-qam', 'docs: after release'], work)
    cases.append(('origin 已交棒、沒更新 HANDOFF（Q31 仍擋）', 2, fire(push)))
    write_lf(handoff, read_lf(handoff).replace('**工作中**', '**佔用**'))
    git(['commit', '-qam', 'chore: drop field'], work)
    git(['push', '-q', 'origin', 'main'], work)
    (work / 'README.md').open('a', encoding='utf-8', newline='').write('\n沒有工作中欄\n')
    git(['commit', '-qam', 'docs: no field'], work)
    cases.append(('origin 沒有工作中欄（Q31 仍擋）', 2, fire(push)))
    # 還原成 Q31 之前這一步結束時的狀態：origin 已交棒、本機多一個未推的開工標記，後面的步驟沿用。
    write_lf(handoff, read_lf(handoff).replace('**佔用**', '**工作中**'))
    git(['commit', '-qam', 'chore: restore field'], work)
    git(['push', '-q', 'origin', 'main'], work)
    write_lf(handoff, read_lf(handoff).replace('無（已交棒）', '`fixture` ／ `Codex CLI`'))
    git(['commit', '-qam', 'chore: claim'], work)

    git(['checkout', '-q', '-b', 'feature/x'], work)
    (work / 'README.md').open('a', encoding='utf-8', newline='').write('\nwip\n')
    git(['commit', '-qam', 'wip'], work)
    cases.append(('feature 分支', 0, fire('{"tool_input":{"command":"git push origin feature/x"}}')))
    cases.append(('feature 推 main refspec（刻意漏判）', 0, command('git push origin HEAD:main')))

    git(['checkout', '-q', 'main'], work)
    cases.append(('HANDOFF_HOOK=off', 0, fire(push, env=dict(GIT_ENV, HANDOFF_HOOK='off'))))

    bad = [f'{n}：期望 {want}、實得 {got}' for n, want, got in cases if want != got]
    if bad:
        detail = '；'.join(bad)
        if noise:
            detail += '\n           hook stderr：' + ' | '.join(dict.fromkeys(noise))
        record('FAIL', 'AI push 提醒情境', detail)
        return False
    record('OK', 'AI push 提醒情境', '、'.join(f'{n}→{want}' for n, want, _ in cases))
    return work        # 有 origin、有 commit，git-freshness 才走得到比對邏輯


# ── 6. 行末與雜項 ──────────────────────────────────────────────
FACTS_MAX_LINES = 5   # 需求決策書 v3 第 5 節：開場 hook 輸出 ≤ 5 行


def facts_output_problems(out):
    """SessionStart JSON 裡的 context：每行 [facts]、最多五行、第一行有時間戳。"""
    bad = []
    try:
        envelope = json.loads(out)
        hook = envelope['hookSpecificOutput']
        if set(envelope) != {'hookSpecificOutput'} or hook['hookEventName'] != 'SessionStart':
            return ['SessionStart JSON 外殼不正確']
        facts = hook['additionalContext']
        if not isinstance(facts, str):
            return ['additionalContext 不是字串']
    except (ValueError, TypeError, KeyError):
        return ['不是有效的 SessionStart JSON']
    lines = [l for l in facts.split('\n') if l.strip()]
    if not lines:
        return ['沒有輸出']
    if any(not l.startswith('[facts] ') for l in lines):
        bad.append('有不是 [facts] 開頭的行（hook 只報事實，不下指示）')
    if len(lines) > FACTS_MAX_LINES:
        bad.append('輸出 %d 行，超過 %d 行' % (len(lines), FACTS_MAX_LINES))
    if not re.search(r'（session 名用 [0-9]{2}\.[0-9]{2}\.[0-9]{2}）', lines[0]):
        bad.append('第一行沒有 session 名用的 MM.DD.HH')
    return bad


SHARED_START = '<!-- 共用制度開始'
SHARED_END = '<!-- 共用制度結束 -->'
SHARED_MAX_LINES = 40   # 需求決策書 v3 D11
AGENTS_MAX_LINES = 100


def shared_rules(agents):
    """AGENTS.md 裡開始與結束標記之間的共用制度（含兩行標記）；找不到就回空字串。"""
    if agents.count(SHARED_START) != 1 or agents.count(SHARED_END) != 1:
        return ''
    a = agents.index(SHARED_START)
    b = agents.index(SHARED_END) + len(SHARED_END)
    return agents[a:b] if a < b else ''


AGENTS_STOP_TOKENS = ('歷史分岔、fetch 失敗、來源不明的未提交變更', '停下來告訴使用者', '本機要跟 origin 一致')


def agents_stop_problems(agents):
    shared = shared_rules(agents)
    return ['AGENTS.md 共用制度缺：' + t for t in AGENTS_STOP_TOKENS if t not in shared]


def facts_busy_cases(push_busy, me):
    """開場 hook 的「工作中」情境表（v3 D12：照原文印、不判讀）。

    守「印得出來、印得完整、不被環境左右」：主題或機器名含「無」、欄位重複這些舊陷阱，
    只印原文時不會放行，但原文仍要看得到。
    """
    sess = '`㊣　10.30.09｜測試｜工作中`'
    claude = tool_env(CLAUDECODE='1')
    cases = []
    busy = '[facts] origin 上的 HANDOFF：- **工作中**：'

    value = '`other-box` ／ `Claude Code` ／ ' + sess
    out = push_busy(value, claude)
    cases.append(('別台機器→印出原文', busy + value in out))

    out_plain = push_busy(value, tool_env())
    out_both = push_busy(value, tool_env(CLAUDECODE='1', CODEX_VERSION='0.164.0'))
    cases.append(('工具環境變數不改變輸出', strip_clock(out) == strip_clock(out_plain) == strip_clock(out_both)))

    value = '`%s` ／ `Codex CLI` ／ `㊣　26110209｜修無效連結｜工作中｜交棒0次`' % me
    out = push_busy(value, claude)
    cases.append(('主題含「無」→原文完整', busy + value in out))

    out = push_busy('無（已交棒）', claude)
    cases.append(('已交棒→印出無（已交棒）', busy + '無（已交棒）' in out))
    cases.append(('第一行有 MM.DD.HH', not facts_output_problems(out)))

    out = push_busy('無（已交棒）\n- **工作中**：`other-box` ／ `Codex CLI` ／ ' + sess, claude)
    cases.append(('欄位重複→說有幾列', '有 2 列「工作中」' in out))
    return cases, out


def strip_clock(out):
    return re.sub(r'時間 \S+ \S+ \S+（session 名用 [0-9]{2}\.[0-9]{2}\.[0-9]{2}）', '時間 <t>', out)


def step_busy(dest, work):
    """「工作中」標記整條鏈：範本有欄位 → hook 讀得到 origin 那一份 → 照原文印出來。

    任何一環斷掉都沒有徵兆，下一棒只會看到一切正常然後接棒，所以要自動測試。
    """
    field = '**工作中**'
    if field not in (dest / 'HANDOFF.md').read_text(encoding='utf-8'):
        record('FAIL', '工作中欄位在範本裡', 'HANDOFF.md 範本沒有「工作中」欄位，防呆沒有依據')
        return False
    record('OK', '工作中欄位在範本裡', 'HANDOFF.md 有「- **工作中**：無（已交棒）」')

    bash = find_bash()
    if not bash:
        record('SKIP', 'git-freshness 工作中標記', '找不到看得懂 Windows 路徑的 bash')
        return None
    if work is None:
        record('SKIP', 'git-freshness 工作中標記', 'hook fixture 沒建起來，缺少有 origin 的 repo 可測')
        return None

    # hook 用 ${HOSTNAME:-$(hostname)} 判斷「是不是這台機器」，這裡走同一條路徑取名字——
    # 自己另外用 socket.gethostname() 會在大小寫或 FQDN 上跟 hook 的實際行為對不上。
    me = run([bash, '-c', 'echo "${HOSTNAME:-$(hostname 2>/dev/null || uname -n 2>/dev/null)}"'],
             cwd=work).stdout.strip()
    hook = '.claude/hooks/git-freshness.sh'
    target = work / 'HANDOFF.md'
    base = target.read_text(encoding='utf-8')
    line = next((l for l in base.split('\n') if l.startswith('- ' + field)), None)
    if line is None:
        record('FAIL', 'git-freshness 工作中標記', 'fixture 的 HANDOFF.md 找不到「工作中」欄位列')
        return False

    def push_busy(value, env=None):
        write_lf(target, base.replace(line, '- %s：%s' % (field, value)))
        git(['commit', '-qam', 'chore: busy'], work)
        git(['push', '-q', 'origin', 'main'], work)
        return run([bash, hook], cwd=work, env=env or tool_env()).stdout

    cases, out = facts_busy_cases(push_busy, me)
    # 欄位整列拿掉：舊骨架的樣子。要明講讀不到，不能安靜放過——
    # 安靜放過跟「查過了沒事」在畫面上一模一樣，那就回到了這個機制要解決的問題本身。
    write_lf(target, base.replace(line + '\n', ''))
    git(['commit', '-qam', 'chore: drop busy field'], work)
    git(['push', '-q', 'origin', 'main'], work)
    out = run([bash, hook], cwd=work, env=tool_env()).stdout
    cases.append(('欄位不存在→明講讀不到', '讀不到「工作中」那一行' in out))
    # 儀器自檢（2026-11-13）：把讀 origin 那一行改成不印，「別台機器」必須 FAIL。
    original_hook = (work / hook).read_bytes()
    try:
        text = original_hook.decode('utf-8')
        planted = text.replace('emit "[facts] origin 上的 HANDOFF：${busy:-讀不到「工作中」那一行}"', ':')
        if planted == text:
            cases.append(('負向測試找得到要拿掉的那一行', False))
        else:
            (work / hook).write_bytes(planted.encode('utf-8'))
            git(['commit', '-qam', 'chore: planted hook'], work)
            mutant = push_busy('`other-box` ／ `Claude Code` ／ x', tool_env())
            cases.append(('負向測試：不印「工作中」就抓得到', '`other-box`' not in mutant))
    finally:
        (work / hook).write_bytes(original_hook)
        git(['commit', '-qam', 'chore: restore hook'], work)
        git(['push', '-q', 'origin', 'main'], work)

    bad = [n for n, good in cases if not good]
    if bad:
        record('FAIL', 'git-freshness 工作中標記',
               '、'.join(bad) + '\n           最後一次輸出：' + out.strip()[:200])
        return False
    record('OK', 'git-freshness 工作中標記', '、'.join(n for n, _ in cases))
    return True


def repo_hook_problems(hook_text, deployed_text):
    if hook_text is None:
        return ['repo-git-check.sh 不存在']
    if hook_text != deployed_text:
        return ['repo-git-check.sh 跟部署包 3.10 的 git-freshness.sh 不同：'
                '改完部署包要手動重貼（sync_project 拒絕本 repo）']
    return []


def step_repo_busy(dest):
    """本 repo 的開場 hook 要跟部署包 3.10 逐位元組相同（v3 D12）。

    sync_project.py 掃不到本 repo，副本落後不會有徵兆，所以由這一項逐位元組比對。
    部署 hook 的行為由「git-freshness 工作中標記」「Git 異常提示」等項實跑，這裡不重跑。
    """
    path = ROOT / REPO_START_HOOK
    hook = read_lf(path) if path.is_file() else None
    deployed = read_lf(dest / '.claude/hooks/git-freshness.sh')
    bad = repo_hook_problems(hook, deployed)
    if not repo_hook_problems(deployed + 'echo "[repo-check] 全綠"\n', deployed):
        bad.append('負向測試未重現：多印一行的副本應該被擋')
    if not repo_hook_problems(None, deployed):
        bad.append('負向測試未重現：hook 不存在應該被擋')
    record('FAIL' if bad else 'OK', '本 repo 開場 hook', '；'.join(bad) if bad else
           'repo-git-check.sh 跟部署包 3.10 逐位元組相同（只報事實、最多 5 行）；2 個負向測試')
    return not bad


def step_version_check(work):
    """骨架版本落後偵測：用快取檔餵假版本，不打網路，驗的是比對邏輯本身。

    五個情境：落後要講、領先不能說成落後、領先要勸退同步、同版要閉嘴、關掉開關要閉嘴（F09）。
    """
    bash = find_bash()
    if not bash or work is None:
        record('SKIP', '骨架版本落後偵測', '缺 bash 或 hook fixture')
        return None
    hook = '.claude/hooks/git-freshness.sh'
    cache = work / '.claude' / '.bootstrap-version'
    mark = '共用制度落後'

    # 🔴 快取裡放的是「上游最新版」，所以落後的情境要餵一個**比本機新**的版本。
    # 餵比本機舊的版本是「本機領先」，方向弄反時沒有徵兆（查核報告 F09）。
    write_lf(cache, '2099-01-01')
    lag = run([bash, hook], cwd=work).stdout
    off = run([bash, hook], cwd=work, env=dict(GIT_ENV, BOOTSTRAP_VERSION_CHECK='off')).stdout
    write_lf(cache, '1999-01-01')
    ahead = run([bash, hook], cwd=work).stdout
    write_lf(cache, (ROOT / 'VERSION').read_text(encoding='utf-8').strip())
    same = run([bash, hook], cwd=work).stdout
    cache.unlink(missing_ok=True)

    cases = [('落後→講', mark in lag),
             ('領先→不說落後', mark not in ahead),
             ('領先→說比上游新', '比上游新' in ahead),
             ('同版→閉嘴', mark not in same),
             ('開關 off→閉嘴', mark not in off)]
    bad = [n for n, good in cases if not good]
    if bad:
        record('FAIL', '骨架版本落後偵測',
               '、'.join(bad) + '\n           落後情境輸出：' + lag.strip()[:200])
        return False
    record('OK', '骨架版本落後偵測', '、'.join(n for n, _ in cases))
    return True


# A5／B9 回報模板裡那行 `session：`。改 session 名稱是整套程序裡唯一不留 repo 痕跡的動作，
# 所以它沒有辦法被真正地「驗」——能釘的只有「回報模板有沒有逼人講」。這一項守的就是那一行
# 別被後人順手刪掉：刪掉之後規則還在文件裡，但漏掉就再也看不出來，跟沒有這條規則一樣。
RENAME_LINE = 'session：'


def rename_block(text, heading):
    """取某個步驟標題底下第一個 ```text 區塊的內容；找不到回 None。"""
    i = text.find(heading)
    if i < 0:
        return None
    j = text.find('```text', i)
    if j < 0:
        return None
    k = text.find('```', j + len('```text'))
    if k < 0:
        return None
    return text[j + len('```text'):k]


def rename_line_problems(skill):
    """回傳問題清單；空清單＝兩個模板都把改名寫進去了。"""
    problems = []
    for heading in ('### A5 ', '### B9 '):
        block = rename_block(skill, heading)
        if block is None:
            problems.append('%s 底下找不到 ```text 回報模板' % heading.strip())
            continue
        hit = [l.strip() for l in block.splitlines() if l.strip().startswith(RENAME_LINE)]
        if not hit:
            problems.append('%s 的回報模板沒有「%s」那一行' % (heading.strip(), RENAME_LINE))
        elif '不適用' not in hit[0]:
            # 少了這個選項，沒有改名能力的工具（例如 Codex CLI）就只剩「整行省掉」
            # 一條路可走，必填會退化成「有能力的工具才填」——正好放掉要守的那一半。
            problems.append('%s 的「%s」那一行沒有留「不適用」這個選項'
                            % (heading.strip(), RENAME_LINE))
    return problems


def step_rename_line(dest):
    """A5／B9 回報模板要有必填的 `session：` 一行，而且留著「不適用」選項。

    改 session 名稱不留 repo 痕跡，漏做完全無聲（2026-11-01 量到六個收尾 session 有兩個漏了）。
    為什麼漏沒有量過，所以做法是讓「有沒有做」露出來，不是猜原因。
    """
    skill = skill_text(dest)
    problems = rename_line_problems(skill)
    if problems:
        record('FAIL', '改名寫進回報模板', '；'.join(problems))
        return False

    # 負向測試：一個永遠回 ok 的檢查跟沒有這一項在畫面上一模一樣。
    a5 = 'session：㊣　<MM.DD.HH｜主題>｜工作中｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次'
    b9 = 'session：↗　<MM.DD.HH｜主題>｜已交棒｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次'
    cases = (
        ('A5 那一行被刪掉', skill.replace(a5 + '\n', '')),
        ('B9 那一行被刪掉', skill.replace(b9 + '\n', '')),
        ('「不適用」選項被拿掉', skill.replace('（已改）／不適用：<本工具不能改名>', '（已改）')),
    )
    bad = []
    for name, mutated in cases:
        if mutated == skill:
            # 改壞的字串沒對上就等於沒測到，而它會安靜地「通過」。
            bad.append('%s：負向測試沒改到任何字，字串對不上了' % name)
        elif not rename_line_problems(mutated):
            bad.append('%s：沒被擋下' % name)
    if bad:
        record('FAIL', '改名寫進回報模板', '；'.join(bad))
        return False
    record('OK', '改名寫進回報模板',
           'A5／B9 模板各有一行 session：且留著「不適用」；三個負向測試都擋得住')
    return True


SESSION_RESUME_RULE = '是 `↗` 時收到任何新訊息，先改回 `㊣`'


def session_resume_problems(skill, agents):
    """續聊的程序契約；不模擬模型或外部 session 改名工具。

    「每則新訊息先恢復工作中」由每個 session 都載入的 AGENTS.md 共用制度承載（v3 第 5 節），
    skill 這邊守命名與交棒計數的程序句子。
    """
    problems = []
    if SESSION_RESUME_RULE not in shared_rules(agents):
        problems.append('AGENTS.md 共用制度缺續聊恢復規則')
    # 命名規則分散在入口（摘要）、mode-b.md（計數）與 reasons.md（細則），所以看整個 skill 目錄；
    # 入口自己該有哪些句子由「skill 拆分」守。
    naming = skill
    required = (
        '每則使用者新訊息都先檢查 session 狀態',
        '包含只問問題、補充、更正與致謝',
        '先用改名工具恢復 `㊣ 工作中`，再回答或執行任務',
        '保留原本的 `MM.DD.HH`、主題與交棒次數',
        '只讀續聊不改 HANDOFF、不 commit、不 push，也不為了結束回答再交棒',
        '續聊要改檔前重新走 A1–A5，重查 origin 的工作中標記',
        '續聊回覆必須有 `session：` 一行',
        '交棒次數的家是該 session 標題尾端的 `｜交棒<N>次`，新 session 從 0 起算',
        '只有 B1–B8 完成且 B8 push 成功，才在 B9 把 N 加 1',
        '開工標記、中途安全點、失敗的 push 與重複回報同一次成功交棒都不增加',
        '交棒≥1次',
        '沒有改名能力的工具，以同一 session 最近一次 `session：` 回報保存 N',
        '舊 session 要明確重新讀取新版 skill',
    )
    problems.extend('命名程序缺規則：' + rule for rule in required if rule not in naming)
    for heading in ('### A5 ', '### B9 '):
        block = rename_block(skill, heading) or ''
        session_line = next((l for l in block.splitlines() if l.strip().startswith(RENAME_LINE)), '')
        # 可改名與不適用兩邊都要留計數，避免沒有工具時默默丟失 N。
        if session_line.count('交棒<N>次') != 2:
            problems.append(heading.strip() + ' 回報缺累計交棒次數')
    b9 = skill.partition('### B9 ')[2].partition('## C.')[0]
    if '依「同一 session 的交棒計數」將 N 加 1' not in b9:
        problems.append('B9 沒套用交棒計數')
    return problems


def step_session_resume(dest):
    skill = skill_text(dest)
    pointer = read_lf(dest / 'AGENTS.md')
    problems = session_resume_problems(skill, pointer)
    # 每個守門條件都故意拿掉一次；沒有改到字串也必須失敗，不能空測。
    rules = (
        '每則使用者新訊息都先檢查 session 狀態',
        '包含只問問題、補充、更正與致謝',
        '先用改名工具恢復 `㊣ 工作中`，再回答或執行任務',
        '保留原本的 `MM.DD.HH`、主題與交棒次數',
        '只讀續聊不改 HANDOFF、不 commit、不 push，也不為了結束回答再交棒',
        '續聊要改檔前重新走 A1–A5，重查 origin 的工作中標記',
        '續聊回覆必須有 `session：` 一行',
        '交棒次數的家是該 session 標題尾端的 `｜交棒<N>次`，新 session 從 0 起算',
        '只有 B1–B8 完成且 B8 push 成功，才在 B9 把 N 加 1',
        '開工標記、中途安全點、失敗的 push 與重複回報同一次成功交棒都不增加',
        '交棒≥1次',
        '沒有改名能力的工具，以同一 session 最近一次 `session：` 回報保存 N',
        '舊 session 要明確重新讀取新版 skill',
        '依「同一 session 的交棒計數」將 N 加 1',
    )
    cases = [(rule, skill.replace(rule, ''), pointer) for rule in rules]
    cases.append(('AGENTS.md 續聊恢復規則', skill, pointer.replace(SESSION_RESUME_RULE, '')))
    for heading in ('### A5 ', '### B9 '):
        block = rename_block(skill, heading) or ''
        cases.append((heading + '計數', skill.replace(block, block.replace('交棒<N>次', '')), pointer))
    for name, changed_skill, changed_pointer in cases:
        if (changed_skill, changed_pointer) == (skill, pointer):
            problems.append('負向測試沒改到字串：' + name)
        elif not session_resume_problems(changed_skill, changed_pointer):
            problems.append('負向測試未擋住：' + name)
    if problems:
        record('FAIL', '續聊狀態與計數', '；'.join(problems))
        return False
    record('OK', '續聊狀態與計數',
           'AGENTS.md 共用制度與 skill 參考檔涵蓋逐訊息恢復、只讀續聊、重查占用、累計與舊版恢復；'
           '%d 個負向測試通過（未呼叫模型／改名工具）' % len(cases))
    return True


REPO_HANDOFF_HEADINGS = ('任務目標', 'Git 狀態', '目前進度', '未完成／下一步',
                         '地雷與注意事項', '服務查證與期望快照', '懸置事項（AI 勿自行處理）')
REPO_HANDOFF_STALE = (
    r'Codex\s*接線從來沒真的跑過',
    r'Codex\s*這一面還沒有\s*bash\s*解析的解法',
    r'新發現、還沒處理.{0,80}ZIP_README',
)


def repo_handoff_rule_problems(text):
    flat = re.sub(r'\s+', ' ', text.replace('`', '').replace('**', ''))
    patterns = (r'每輪只維護.{0,45}兩欄', r'每輪一定要維護的只有.{0,45}兩欄',
                r'HANDOFF\.md.{0,12}只當.{0,15}標記的載體',
                r'本 repo 沒有\s*HANDOFF\.md',
                r'本 repo 刻意沒有\s*HANDOFF\.md', r'接線在、但還沒真的跑過')
    return ['交接入口仍有舊規則：' + pattern for pattern in patterns if re.search(pattern, flat)]


def repo_handoff_problems(text, version):
    """本 repo 的交接快照：部署後 check_docs.py 的快照與「工作中」檢查（同一份函式，F46），
    加上本 repo 才有的：骨架版本要等於 VERSION、章節不能是空的、已知已完成的待辦不得復活。

    2026-11-01：舊快照凍結三輪但全數驗證通過；後兩項只查已知回歸，不聲稱理解所有待辦。
    """
    if text is None:
        return ['HANDOFF.md 不存在']
    checker = product_checker()
    with tempfile.TemporaryDirectory() as raw, pushd(raw):
        write_lf(pathlib.Path('HANDOFF.md'), text)
        files = [pathlib.Path('HANDOFF.md')]
        problems = checker.check_snapshot(files) + checker.check_busy_field(files)[1]
    problems += repo_handoff_rule_problems(text)
    matches = re.findall(r'^- \*\*骨架版本\*\*：(.+)$', text, re.M)
    if len(matches) != 1 or matches[0].strip() != '`' + version + '`':
        problems.append('HANDOFF 骨架版本要有且只有一列，而且等於 VERSION')
    for heading in REPO_HANDOFF_HEADINGS:
        body = re.findall(r'^## ' + re.escape(heading) + r'\n(.*?)(?=^## |\Z)', text, re.M | re.S)
        if len(body) == 1 and not body[0].strip():
            problems.append('交接章節是空的：' + heading)
    flat = re.sub(r'\s+', ' ', text.replace('`', '').replace('**', ''))
    problems.extend('已完成待辦復活：' + p for p in REPO_HANDOFF_STALE if re.search(p, flat))
    return problems


def step_repo_handoff():
    handoff = ROOT / 'HANDOFF.md'
    text = handoff.read_text(encoding='utf-8') if handoff.is_file() else None
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    problems = repo_handoff_problems(text, version)
    for name in ('AGENTS.md', 'docs/maintenance.md', 'ARCHITECTURE.md', 'README.md',
                 '.claude/hooks/repo-git-check.sh'):
        problems.extend(name + '：' + p for p in
                        repo_handoff_rule_problems((ROOT / name).read_text(encoding='utf-8')))
    # 固定的有效基線讓負向測試不依賴實際快照的待辦內容或工作中／已交棒狀態。
    control = '\n'.join('- **%s**：%s' % (label, value) for label, value in (
        ('交接時間', '2026-11-01 23:18（+08）'), ('交棒者', 'Codex'),
        ('待續分支', '無。'), ('工作中', '無（已交棒）'), ('骨架版本', '`' + version + '`')))
    control += '\n' + '\n'.join('## ' + h + '\n無。\n' for h in REPO_HANDOFF_HEADINGS)
    cases = (
        ('整份缺失', None),
        ('版本落後', control.replace('`' + version + '`', '`2000-01-01`')),
        ('只剩標記', '- **工作中**：無（已交棒）\n'),
        ('缺待辦章節', control.replace('## 未完成／下一步\n無。\n', '')),
        ('空待辦章節', control.replace('## 未完成／下一步\n無。', '## 未完成／下一步\n')),
        ('工作中欄位重複', control + '\n- **工作中**：無（已交棒）'),
        ('超過行數', control + '\n' * 81),
        ('驗收舊待辦', control + '\nCodex 接線從來沒真的跑過。'),
        ('啟動器舊待辦', control + '\nCodex 這一面還沒有 `bash` 解析的解法。'),
        ('ZIP 舊待辦', control + '\n新發現、還沒處理：`ZIP_README` 有過期斷言。'),
    )
    if repo_handoff_problems(control, version):
        problems.append('有效快照被誤擋')
    busy = control.replace('無（已交棒）', '`desk` ／ `Codex CLI` ／ `session`，2026-11-01 開工')
    if repo_handoff_problems(busy, version):
        problems.append('工作中快照被誤擋')
    for name, mutated in cases:
        if mutated == control or not repo_handoff_problems(mutated, version):
            problems.append('負向測試未擋住：' + name)
    rules = ('每輪只維護「待續分支」與「工作中」兩欄。',
             '每輪一定要維護的只有「待續分支」與「工作中」兩欄。',
             'HANDOFF.md 只當「工作中」標記的載體。',
             '本 repo 沒有 HANDOFF.md。', '本 repo 刻意沒有 HANDOFF.md 與 hooks。',
             '接線在、但還沒真的跑過。')
    for old in rules:
        if not repo_handoff_rule_problems(old):
            problems.append('負向測試未擋住入口舊規則：' + old)
    if problems:
        record('FAIL', '本 repo 交接狀態', '；'.join(problems))
        return False
    record('OK', '本 repo 交接狀態',
           '快照必要欄位、≤80 行、版本一致、已知舊待辦與入口規則；%d 個負向測試通過'
           % (len(cases) + len(rules)))
    return True


# 規則的理由在理由檔，入口只留連結；「保留每條規則的為什麼」（維護手冊「新增或改規則」）不能只靠自律：
# 規則沒有理由連結、連結指不到段落、或段落是空的，都要擋。連結從各自的位置算相對路徑：
# AGENTS.md 寫 docs/rationale.md#x，維護手冊寫 rationale.md#x。
REASON_FILE = 'docs/rationale.md'


def reason_link_re(target):
    return re.compile(r'\]\(' + re.escape(target) + r'#([A-Za-z0-9-]+)\)')


REASON_LINK = reason_link_re(REASON_FILE)
# 2026-11-21（v3 Q58）：AGENTS 分成共用與專用兩大段，規則各自編號；共用規則在標記之間、塗白不查，
# 要逐條連理由的是「### 專用規則」。
REASON_ITEM_SECTIONS = ('專用規則', '副本規則', '改兩支 hook 的訊息時')
# 「碰到才讀」是「什麼時候 → 讀哪份」的索引表（原則草稿第 4 節），不要求理由連結；但這一節只能有表格列，
# 夾帶一句規則就照一般章節要求理由連結，免得規則躲進索引逃掉理由連結。
REASON_INDEX_SECTIONS = ('碰到才讀',)
REASON_MIN_BODY = 40
CONTRIB_FILE = 'docs/maintenance.md'
CONTRIB_REASON = 'rationale.md'
CONTRIB_LINK = reason_link_re(CONTRIB_REASON)


def blank_shared_copy(text):
    """本 repo AGENTS.md 裡的共用制度是部署包的逐字副本（2026-11-14 使用者決定貼入）：
    它連到部署後才存在的 skill 路徑、章節也沒有本 repo 的理由連結，這兩項檢查跳過它，
    改由 shared_copy_problems 要求它跟部署包逐字相同。行數保留，錯誤行號才對得上。

    2026-11-21（v3 Q58）：共用規則與專用規則分開編號，專用規則在結束標記後自己的「### 專用規則」，
    不再接在共用規則底下，所以標記之間整段塗白（取代 Q56 留最後一個標題的做法）。"""
    if text.count(SHARED_START) != 1 or text.count(SHARED_END) != 1:
        return text
    a = text.rfind('\n', 0, text.index(SHARED_START)) + 1
    b = text.index(SHARED_END) + len(SHARED_END)
    if b <= a:
        return text
    return text[:a] + '\n' * text[a:b].count('\n') + text[b:]


def shared_copy_problems(agents, template):
    """本 repo AGENTS.md 的共用制度副本：要剛好一份，而且跟部署包範本逐字相同。"""
    def block(text):
        if text.count(SHARED_START) != 1 or text.count(SHARED_END) != 1:
            return None
        a = text.rfind('\n', 0, text.index(SHARED_START)) + 1
        b = text.index(SHARED_END) + len(SHARED_END)
        return text[a:b] if b > a else None
    want, have = block(template), block(agents)
    if want is None:
        return ['部署包範本找不到共用制度']
    if have is None:
        return ['本 repo AGENTS.md 沒有剛好一份共用制度（全域 handoff skill 指向它）']
    if have != want:
        return ['本 repo AGENTS.md 的共用制度跟部署包不同：改完部署包要手動重貼（sync_project 拒絕本 repo）']
    return []


def reason_link_problems(agents, reasons, link=REASON_LINK, depth=3, need=('專用規則',)):
    """agents／reasons：兩份文件的全文 → 問題清單。link：從規則檔的位置連到理由檔的連結樣式。

    depth：切到第幾級標題。AGENTS 是「## 大段／### 節」（v3 Q58），切到 ###；只放小節、
    自己沒有內文的大段標題是容器，不算一節。維護手冊的 ### 是同一節裡的細目，傳 2。
    need：一定要有的規則節。拿掉「### 專用規則」標題，規則就混進別節、不再逐條查理由。"""
    problems = []
    agents = blank_shared_copy(agents)
    bodies = {}
    chunks = re.split(r'(?m)^<a id="([A-Za-z0-9-]+)"></a>\s*$', reasons)
    for anchor, body in zip(chunks[1::2], chunks[2::2]):
        if anchor in bodies:
            problems.append('理由檔的錨點重複：' + anchor)
        text = '\n'.join(l for l in body.split('\n') if not l.startswith('## '))
        bodies[anchor] = text.strip()
    if not bodies:
        problems.append('理由檔沒有任何錨點')
    used = set()
    heads = list(re.finditer(r'(?m)^(#{2,%d}) (.*)$' % depth, agents))
    if not heads:
        problems.append('AGENTS.md 沒有任何章節')
    titles = [m.group(2).strip() for m in heads]
    for name in need:
        if not any(title.startswith(name) for title in titles):
            problems.append('找不到「%s」一節' % name)
    for k, m in enumerate(heads):
        title = titles[k]
        body = agents[m.end():heads[k + 1].start() if k + 1 < len(heads) else len(agents)]
        if not body.strip() and k + 1 < len(heads) and len(heads[k + 1].group(1)) > len(m.group(1)):
            continue
        found = link.findall(body)
        used.update(found)
        index_only = (any(title.startswith(name) for name in REASON_INDEX_SECTIONS)
                      and all(not l.strip() or l.lstrip().startswith('|') for l in body.split('\n')))
        if not found and not index_only:
            problems.append('章節沒有理由連結：' + title)
        if not any(title.startswith(name) for name in REASON_ITEM_SECTIONS):
            continue
        items, current = [], None
        for line in body.split('\n'):
            if re.match(r'(- |\d+\. )', line):
                current = [line]
                items.append(current)
            elif current is not None and line.startswith(' '):
                current.append(line)
            else:
                current = None
        if not items:
            problems.append('章節沒有任何規則項目：' + title)
        for item in items:
            if not link.search('\n'.join(item)):
                problems.append('規則沒有理由連結（%s）：%s' % (title, item[0][:30]))
    for anchor in sorted(used):
        if anchor not in bodies:
            problems.append('理由連結指不到段落：#' + anchor)
        elif len(bodies[anchor]) < REASON_MIN_BODY:
            problems.append('理由段落是空的或過短：#' + anchor)
    return problems


def append_to_section(text, heading, line):
    """在 heading（含 `## `／`### `）那一節的最後加一行；那一節不必是全檔最後一節
    （2026-11-20，索引節放在它後面）。下一個任何層級的標題就是節尾（v3 Q58）。"""
    start = text.find('\n' + heading + '\n')
    if start < 0:
        return text
    nxt = re.search(r'(?m)^#{1,6} ', text[start + len(heading) + 2:])
    end = len(text) if nxt is None else start + len(heading) + 2 + nxt.start() - 1
    return text[:end].rstrip('\n') + '\n' + line + '\n' + text[end:]


def step_reason_links():
    title = '規則理由連結'
    agents = read_lf(ROOT / 'AGENTS.md')
    path = ROOT / REASON_FILE
    reasons = read_lf(path) if path.is_file() else ''
    problems = reason_link_problems(agents, reasons)
    # 碰到才需要的規則在維護手冊，同一套理由連結檢查。
    contrib_path = ROOT / CONTRIB_FILE
    contributing = read_lf(contrib_path) if contrib_path.is_file() else ''
    if not contributing:
        problems.append(CONTRIB_FILE + ' 不存在')
    else:
        problems.extend(CONTRIB_FILE + '：' + p for p in
                        reason_link_problems(contributing, reasons, CONTRIB_LINK, depth=2, need=()))
    template = read_lf(ROOT / 'src/kit/files/AGENTS.md.tmpl')
    problems.extend(shared_copy_problems(agents, template))
    copy_cases = (
        ('共用制度副本被改一個字', agents.replace('### 共用規則', '### 共用規矩', 1)),
        ('共用制度副本被拿掉', agents.replace(SHARED_END, '', 1)),
    )
    for name, mutated in copy_cases:
        if mutated == agents:
            problems.append('負向測試沒有改到內容：' + name)
        elif not shared_copy_problems(mutated, template):
            problems.append('負向測試未擋住：' + name)
    if reason_link_problems(agents.replace(SHARED_END, '', 1), reasons) == reason_link_problems(agents, reasons):
        problems.append('負向測試未擋住：副本標記壞掉時理由連結檢查仍跳過那幾節')
    first = REASON_LINK.search(agents.split('\n### 專用規則', 1)[-1])
    rule = '](%s#%s)' % (REASON_FILE, first.group(1)) if first else None
    anchor = '<a id="%s"></a>' % first.group(1) if first else None
    cases = () if not first else (
        ('理由檔不存在', agents, ''),
        ('規則拿掉理由連結', agents.replace('[為什麼' + rule, '', 1), reasons),
        ('連結指向不存在的段落', agents.replace(rule, '](%s#no-such-reason)' % REASON_FILE, 1),
         reasons),
        ('理由段落被清空', agents,
         re.sub(re.escape(anchor) + r'.*?(?=\n<a id=|\Z)', anchor + '\n\n## 空\n', reasons,
                count=1, flags=re.S)),
        ('錨點重複', agents, reasons + '\n' + anchor + '\n\n## 重複\n' + '字' * REASON_MIN_BODY),
        ('整節沒有理由連結', agents + '\n## 新的一節\n\n只有規則，沒有理由。\n', reasons),
        ('新增規則沒有理由', append_to_section(agents, '### 專用規則', '99. 新規則。'), reasons),
        ('索引節夾帶規則', agents + '\n### 碰到才讀\n\n| 什麼時候 | 讀哪份 |\n|---|---|\n\n不要改 X。\n',
         reasons),
        # v3 Q58：空的大段標題只有後面接小節時才算容器；沒有小節的空標題照樣要理由連結。
        ('空的大段標題後面沒有小節', agents + '\n## 空的大段\n\n## 另一個大段\n\n內文。[為什麼](%s#%s)\n'
         % (REASON_FILE, first.group(1)), reasons),
        ('專用規則寫回共用規則底下', agents.replace('\n### 專用規則\n', '\n', 1), reasons),
    )
    contrib_cases = () if not contributing else (
        ('維護手冊副本規則拿掉理由連結',
         contributing.replace('[為什麼](%s#copy-1)' % CONTRIB_REASON, '', 1)),
        ('維護手冊用根目錄的相對路徑連理由',
         contributing.replace('](%s#copy-1)' % CONTRIB_REASON, '](%s#copy-1)' % REASON_FILE, 1)),
        ('維護手冊新增 hook 訊息規則沒有理由', contributing.rstrip('\n') + '\n- 新規則。\n'),
        ('維護手冊整節沒有理由連結', contributing + '\n## 新的一節\n\n只有規則，沒有理由。\n'),
    )
    for name, mutated in contrib_cases:
        if mutated == contributing:
            problems.append('負向測試沒有改到內容：' + name)
        elif not reason_link_problems(mutated, reasons, CONTRIB_LINK, depth=2, need=()):
            problems.append('負向測試未擋住：' + name)
    if not first:
        problems.append('規則一節找不到任何理由連結，負向測試無從建立')
    for name, mutated_agents, mutated_reasons in cases:
        if (mutated_agents, mutated_reasons) == (agents, reasons):
            problems.append('負向測試沒有改到內容：' + name)
        elif not reason_link_problems(mutated_agents, mutated_reasons):
            problems.append('負向測試未擋住：' + name)
    if problems:
        record('FAIL', title, '；'.join(problems))
        return False
    record('OK', title,
           'AGENTS.md、docs/maintenance.md 每節與專用規則／副本規則／hook 訊息每條都連到 %s 的非空段落；%d 個負向測試通過'
           '；共用制度副本與部署包逐字相同（3 個負向測試）'
           '（只查連結與段落存在，不判斷理由寫得對不對）' % (REASON_FILE, len(cases) + len(contrib_cases)))
    return True



# 2026-11-21（v3 Q58）：共用規則與專用規則各自從 1 編號。沒有前綴的「規則 N」分不出指哪一份，
# 舊的接續編號也會躲在裡面不被發現。「副本規則 N」是維護手冊自己的清單，放行。
# 經過類的檔寫的是當時的編號，不查：變更紀錄、熱歷史、冷區、實驗紀錄；bootstrap.py 是生成物。
BARE_RULE_REF = re.compile(r'(?<!共用)(?<!專用)(?<!副本)規則 ?[0-9]+|規則第 ?[0-9]+ ?條')
BARE_RULE_SKIP = ('CHANGELOG.md', 'docs/history/', 'archive/', 'experiments/', 'bootstrap.py')
BARE_RULE_SUFFIXES = ('.md', '.py', '.tmpl', '.json', '.sh')


def bare_rule_refs(text):
    """text 裡沒有前綴的規則編號引用。"""
    return [m.group(0) for m in BARE_RULE_REF.finditer(text)]


def step_rule_refs():
    title = '規則引用有前綴'
    tracked = [p for p in run(['git', 'ls-files', '-z'], cwd=ROOT).stdout.split('\0') if p]
    hits, scanned = [], 0
    for rel in tracked:
        if rel.startswith(BARE_RULE_SKIP) or not rel.endswith(BARE_RULE_SUFFIXES):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        scanned += 1
        for n, line in enumerate(read_lf(path).split('\n'), 1):
            hits.extend('%s:%d「%s」' % (rel, n, ref) for ref in bare_rule_refs(line))
    # 樣本在執行時拼出來，本檔自己也在掃描範圍內。
    must_flag = ('見規則' + ' 9', '見規則' + '9', '規則第' + ' 12 條')
    must_pass = ('共用規則 3', '專用規則 8', '副本規則 7', '規則 N', '每條規則')
    bad = ['負向測試未擋：' + s for s in must_flag if not bare_rule_refs(s)]
    bad += ['誤擋：' + s for s in must_pass if bare_rule_refs(s)]
    if hits or bad:
        record('FAIL', title, '；'.join(bad + ['沒有前綴的規則編號 %d 處：%s' % (len(hits), '、'.join(hits[:8]))]
                                        if hits else bad))
        return False
    record('OK', title, '%d 個現行檔沒有不帶「共用／專用」前綴的規則編號；%d 個負向測試、%d 個放行樣本'
           % (scanned, len(must_flag), len(must_pass)))
    return True

SOURCE_EXCEPTIONS = (
    ('handoff skill', '.claude/skills/handoff/SKILL.md'),
    ('check_docs.py', 'tools/check_docs.py'),
)


def source_exception_problems(architecture, source, generated):
    """F46 partial: report declared source reductions, without calling them parity."""
    marker = '> **宣告的內容**：'
    if architecture.count(marker) != 1:
        return ['正式例外宣告缺失或重複']
    declaration = architecture.split(marker, 1)[1].split('\n>\n', 1)[0]
    problems = []
    for label, relative in SOURCE_EXCEPTIONS:
        hits = declaration.count('**`' + label + '`**') + declaration.count('**' + label + '**')
        if hits != 1:
            problems.append('宣告未逐項列出：' + label)
        if (source / relative).exists():
            problems.append('來源已出現既定減項，須重新審查宣告：' + relative)
        if not (generated / relative).is_file():
            problems.append('產物缺少對照項：' + relative)
    return problems


def step_source_exceptions(dest, tmp):
    # 2026-11-20（v3 Q53）：宣告從 ARCHITECTURE 搬到決策書第 4 節 F46 底下。
    architecture = (ROOT / 'project-bootstrap-requirements-decision-v3.md').read_text(encoding='utf-8')
    problems = source_exception_problems(architecture, ROOT, dest)
    with tempfile.TemporaryDirectory(prefix='source-exception-', dir=str(tmp)) as name:
        source, generated = pathlib.Path(name) / 'source', pathlib.Path(name) / 'generated'
        source.mkdir()
        for label, relative in SOURCE_EXCEPTIONS:
            target = generated / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('fixture', encoding='utf-8')
        if source_exception_problems(architecture, source, generated):
            problems.append('有效例外 fixture 被誤擋')
        for label, relative in SOURCE_EXCEPTIONS:
            head, rest = architecture.split('> **宣告的內容**：', 1)
            declared, tail = rest.split('\n>\n', 1)
            altered_declaration = declared.replace('**`' + label + '`**', '已省略', 1)
            if altered_declaration == declared:
                altered_declaration = declared.replace('**' + label + '**', '已省略', 1)
            altered = head + '> **宣告的內容**：' + altered_declaration + '\n>\n' + tail
            if altered == architecture or not source_exception_problems(altered, source, generated):
                problems.append('宣告負向測試未擋住：' + label)
            (source / relative).parent.mkdir(parents=True, exist_ok=True)
            (source / relative).write_text('fixture', encoding='utf-8')
            if not source_exception_problems(architecture, source, generated):
                problems.append('來源增項負向測試未擋住：' + label)
            (source / relative).unlink()
            (generated / relative).unlink()
            if not source_exception_problems(architecture, source, generated):
                problems.append('產物缺項負向測試未擋住：' + label)
            (generated / relative).write_text('fixture', encoding='utf-8')
    if problems:
        record('FAIL', '來源例外可見性（F46 部分）', '；'.join(problems))
        return
    record('OK', '來源例外可見性（F46 部分）',
           '已宣告例外：' + '；'.join(label + '（來源缺、產物有）' for label, _ in SOURCE_EXCEPTIONS)
           + '；三類負向變異通過；未驗收來源／產物全部同組情境'
           + '（pre-push 2026-11-14 起補裝，改由「本 repo push 前 hook」守）')


def step_handoff_parity(dest):
    """Run identical synthetic snapshot shapes through source and generated checks."""
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    control = '\n'.join('- **%s**：%s' % (label, value) for label, value in (
        ('交接時間', '2026-11-08 12:00（+08）'), ('交棒者', 'synthetic'),
        ('待續分支', '無'), ('工作中', '無（已交棒）'), ('骨架版本', '`' + version + '`')))
    control += '\n' + '\n'.join('## ' + h + '\n無。\n' for h in REPO_HANDOFF_HEADINGS)
    occupied = control.replace('- **工作中**：無（已交棒）',
                               '- **工作中**：`fixture` ／ `Codex CLI` ／ '
                               '`㊣　26110815｜測試｜工作中`')
    cases = (
        ('有效快照', control, True),
        ('整份缺失', None, False),
        ('缺占用欄', control.replace('- **工作中**：無（已交棒）\n', ''), False),
        ('重複占用欄', control + '\n- **工作中**：無（已交棒）\n', False),
        ('缺下一步章節', control.replace('## 未完成／下一步\n無。\n', ''), False),
        ('超過 80 行', control + ('\n內容' * 81), False),
        ('有效占用標記', occupied, True),
        ('機器欄空白', occupied.replace('`fixture`', '``'), False),
        ('工具欄空白', occupied.replace('`Codex CLI`', '``'), False),
        ('工具欄缺失', occupied.replace(' ／ `Codex CLI`', ''), False),
        ('舊格式把 session 誤作工具',
         occupied.replace('`Codex CLI` ／ ', ''), False),
        # 主題含「無」不能讓格式驗證被跳過（舊版 `'無' in value` 就放行，F01）。
        ('主題含「無」仍驗格式',
         occupied.replace('`Codex CLI` ／ ', '').replace('測試', '修無效連結'), False),
        ('已交棒前後有空白不誤擋', control.replace('無（已交棒）', '　無（已交棒）　'), True),
    )
    target = dest / 'HANDOFF.md'
    original = target.read_text(encoding='utf-8')
    problems = []
    try:
        for name, body, expected in cases:
            source_ok = not repo_handoff_problems(body, version)
            if body is None:
                target.unlink()
                git(['rm', '-q', '--', 'HANDOFF.md'], dest)
            else:
                write_lf(target, body)
                git(['add', '--', 'HANDOFF.md'], dest)
            result = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            product_ok = result.returncode == 0
            if source_ok != expected or product_ok != expected or \
                    result.returncode != (0 if expected else 2):
                problems.append('%s：來源=%s、產物=exit %s（預期 %s）' % (
                    name, source_ok, result.returncode, expected))
    finally:
        write_lf(target, original)
        git(['add', '--', 'HANDOFF.md'], dest)
    record('FAIL' if problems else 'OK', '來源／產物交接快照同組情境（F46 部分）',
           '；'.join(problems) if problems else
           '%d 種同組情境，含缺檔、結構與機器／工具欄正反例；兩端判定一致' % len(cases))


def step_product_documents(dest):
    """部署後 check_docs.py 的連結、日期與佔位符情境。

    本 repo 用同一份函式查自己（repo_document_problems），所以這些情境同時守住產物與來源（F46）。
    """
    control = '# ARCHITECTURE\n\n> 最後更新：2026-11-08\n\n[x](README.md)\n'
    cases = (
        ('有效連結與日期', control, True),
        ('整份文件缺失', None, False),
        ('死連結', control.replace('README.md', 'missing.md'), False),
        ('缺日期標頭', control.replace('> 最後更新：2026-11-08\n', ''), False),
        ('行內程式碼不算連結', control + '\n`[example](missing.md)`\n', True),
        ('程式碼圍欄不算連結', control + '\n```markdown\n[x](missing.md)\n```\n', True),
        ('圍欄後死連結仍攔截', control + '\n```markdown\n[x](missing.md)\n```\n[x](missing.md)\n', False),
        ('角括號路徑與 title', control.replace('[x](README.md)',
                                          '[x](<README.md> "title")'), True),
        ('角括號路徑與 title 的死連結', control.replace('[x](README.md)',
                                                 '[x](<missing.md> "title")'), False),
        ('片段連結', control.replace('[x](README.md)', '[x](README.md#section)'), True),
        ('日期標頭超出前八行',
         control.replace('> 最後更新：2026-11-08\n', '\n'.join(['前言'] * 9)
                         + '\n> 最後更新：2026-11-08\n'), False),
    )
    nested_rel = 'docs/ai-notes/roadmap.md'
    nested_control = '# fixture\n\n> 最後更新：2026-11-08\n\n[x](../../README.md)\n'
    nested_cases = (
        ('巢狀文件有效日期與連結', nested_control, True),
        ('巢狀文件缺失', None, False),
        ('巢狀文件缺日期', nested_control.replace('> 最後更新：2026-11-08\n', ''), False),
        ('巢狀文件日期超出前八行',
         nested_control.replace('> 最後更新：2026-11-08\n',
                                '\n'.join(['前言'] * 9) + '\n> 最後更新：2026-11-08\n'), False),
        ('巢狀文件死連結', nested_control.replace('../../README.md', 'missing.md'), False),
        ('巢狀文件程式碼圍欄豁免',
         nested_control + '\n~~~markdown\n[x](missing.md)\n~~~\n', True),
        ('巢狀文件圍欄後死連結',
         nested_control + '\n~~~markdown\n[x](missing.md)\n~~~\n[x](missing.md)\n', False),
        ('已知佔位符殘留', nested_control + '\n' + '{{' + 'GH_OWNER' + '}}' + '\n', False),
        ('非部署佔位符保留', nested_control + '\n{{PROJECT_LOCAL_VALUE}}\n', True),
    )
    target = dest / 'ARCHITECTURE.md'
    original = target.read_text(encoding='utf-8')
    nested_target = dest / nested_rel
    nested_original = nested_target.read_text(encoding='utf-8')
    problems = []
    try:
        for name, body, expected in cases:
            if body is None:
                target.unlink()
                git(['rm', '-q', '--', 'ARCHITECTURE.md'], dest)
            else:
                write_lf(target, body)
                git(['add', '--', 'ARCHITECTURE.md'], dest)
            result = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            if result.returncode != (0 if expected else 2):
                problems.append('%s：exit %s（預期 %s）' % (name, result.returncode, expected))
        write_lf(target, original)
        git(['add', '--', 'ARCHITECTURE.md'], dest)
        for name, body, expected in nested_cases:
            if body is None:
                nested_target.unlink()
                git(['rm', '-q', '--', nested_rel], dest)
            else:
                # git rm 會把變空的目錄一起刪掉（docs/ai-notes/ 只有這一份）。
                nested_target.parent.mkdir(parents=True, exist_ok=True)
                write_lf(nested_target, body)
                git(['add', '--', nested_rel], dest)
            result = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            if result.returncode != (0 if expected else 2):
                problems.append('%s：exit %s（預期 %s）' % (name, result.returncode, expected))
    finally:
        write_lf(target, original)
        git(['add', '--', 'ARCHITECTURE.md'], dest)
        nested_target.parent.mkdir(parents=True, exist_ok=True)
        write_lf(nested_target, nested_original)
        git(['add', '--', nested_rel], dest)
    record('FAIL' if problems else 'OK', '部署後文件檢查情境',
           '；'.join(problems) if problems else
           '%d 種情境，含巢狀文件日期、佔位符、圍欄、角括號與 title、片段；本 repo 用同一份函式（F46）'
           % (len(cases) + len(nested_cases)))


def step_product_document_policy(dest):
    """部署後 check_docs.py 的專案設定：過期字串、非 Markdown 佔位符、連結與佔位符豁免。"""
    checker = dest / 'tools/check_docs.py'
    original_checker = checker.read_text(encoding='utf-8')
    readme = dest / 'README.md'
    original_readme = readme.read_text(encoding='utf-8')
    fixture_rel = 'tools/fixture.py'
    fixture = dest / fixture_rel
    token = '{{' + 'GH_OWNER' + '}}'
    cases = (
        ('設定後的有效文件', 'value = "ok"\n', '# fixture\n', False, False, False, True, ''),
        ('非 Markdown 已知佔位符', 'value = "' + token + '"\n',
         '# fixture\n', False, False, False, False, '[holes]'),
        ('非 Markdown 未知樣板保留', 'value = "{{PROJECT_LOCAL_VALUE}}"\n',
         '# fixture\n', False, False, False, True, ''),
        ('佔位符豁免路徑', 'value = "' + token + '"\n',
         '# fixture\n', False, True, False, True, ''),
        ('自訂過期字串', 'value = "ok"\n',
         '# fixture\nretired.example\n', False, False, False, False, '[stale]'),
        ('同列歷史敘述豁免', 'value = "ok"\n',
         '# fixture\nretired.example 已退役\n', False, False, False, True, ''),
        ('過期字串路徑豁免', 'value = "ok"\n',
         '# fixture\nretired.example\n', True, False, False, True, ''),
        ('無豁免的死連結', 'value = "ok"\n',
         '# fixture\n[x](missing.md)\n', False, False, False, False, '[links]'),
        ('連結路徑豁免', 'value = "ok"\n',
         '# fixture\n[x](missing.md)\n', False, False, True, True, ''),
    )
    problems = []
    try:
        for name, py_body, md_body, stale_exempt, hole_exempt, link_exempt, expected, channel in cases:
            write_lf(fixture, py_body)
            write_lf(readme, md_body)
            git(['add', '--', fixture_rel, 'README.md'], dest)
            configured = original_checker.replace(
                "STALE_PATTERNS = [\n    # ('localhost:8080', '已遷到正式網域，文件不該再出現本機位址'),\n]",
                "STALE_PATTERNS = [('retired.example', '合成舊網域')]")
            if configured == original_checker:
                problems.append('找不到產物過期字串設定區塊')
                break
            if stale_exempt:
                configured = configured.replace('STALE_OK_PATHS = ()',
                                                "STALE_OK_PATHS = ('README.md',)")
            if hole_exempt:
                configured = configured.replace(
                    "PLACEHOLDER_OK_PATHS = ('PROJECT-BOOTSTRAP.md',)",
                    "PLACEHOLDER_OK_PATHS = ('PROJECT-BOOTSTRAP.md', 'tools/fixture.py')")
            if link_exempt:
                configured = configured.replace(
                    "LINK_OK_PATHS = ('PROJECT-BOOTSTRAP.md',)",
                    "LINK_OK_PATHS = ('PROJECT-BOOTSTRAP.md', 'README.md')")
            write_lf(checker, configured)
            result = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            if (result.returncode != (0 if expected else 2) or
                    (channel and channel not in result.stdout)):
                problems.append('%s：exit %s（預期 %s／%s）' % (
                    name, result.returncode, expected, channel))
    finally:
        write_lf(checker, original_checker)
        write_lf(readme, original_readme)
        git(['add', '--', 'README.md'], dest)
        if fixture.exists():
            git(['rm', '-qf', '--', fixture_rel], dest)
    record('FAIL' if problems else 'OK', '部署後文件設定情境',
           '；'.join(problems) if problems else
           '%d 種情境，含非 Markdown 佔位符、自訂過期字串、死連結與豁免' % len(cases))




def source_staged_problems(root):
    """B7：來源驗證器檢查工作樹，不能拿它證明另一份 staged 內容。

    來源沒有部署後的 check_docs.py；選用 --staged 時，整個提交候選須已 stage，
    且不能留下未暫存或未追蹤檔。未追蹤的連結目標若只在本機存在，
    也可能讓待提交 Markdown 的死連結檢查錯誤通過。
    """
    commands = (
        ('staged', ['diff', '--cached', '--name-only', '-z']),
        ('unstaged', ['diff', '--name-only', '-z']),
        ('untracked', ['ls-files', '--others', '--exclude-standard', '-z']),
    )
    names = {}
    for label, args in commands:
        result = git(args, root)
        if result.returncode:
            return ['讀取 %s 檔案集合失敗：%s' % (label, result.stderr.strip()[:160])]
        names[label] = [name for name in result.stdout.split('\0') if name]
    problems = []
    if not names['staged']:
        problems.append('沒有 staged 提交候選')
    for label in ('unstaged', 'untracked'):
        if names[label]:
            problems.append('%s 檔案尚未納入候選：%s' %
                            (label, '、'.join(names[label][:5])))
    return problems


def step_source_staged_parity(dest, tmp):
    """同一份 staged/unstaged 形狀對照來源檢查與產物 --staged。"""
    source = tmp / 'source-staged-fixture'
    shutil.copytree(dest, source, ignore=shutil.ignore_patterns('.git'))
    git(['init', '-q', '-b', 'main'], source)
    git(['add', '-A'], source)
    git(['commit', '-qm', 'fixture'], source)
    no_stage_rejected = bool(source_staged_problems(source))
    readme = source / 'README.md'
    with readme.open('a', encoding='utf-8', newline='') as handle:
        handle.write('\n驗證提交候選。\n')
    git(['add', '--', 'README.md'], source)
    cases = []
    source_ok = not source_staged_problems(source)
    product = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=source)
    cases.append(('完整 stage', source_ok, product.returncode, True))
    with readme.open('a', encoding='utf-8', newline='') as handle:
        handle.write('未暫存內容。\n')
    source_ok = not source_staged_problems(source)
    product = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=source)
    cases.append(('部分 stage', source_ok, product.returncode, False))
    restored = git(['checkout', '--', 'README.md'], source)
    untracked_baseline_clean = restored.returncode == 0 and not source_staged_problems(source)
    (source / 'untracked-target.md').write_text('未追蹤\n', encoding='utf-8')
    untracked_rejected = bool(source_staged_problems(source))
    problems = []
    for name, source_ok, product_exit, expected in cases:
        if source_ok != expected or product_exit != (0 if expected else 2):
            problems.append('%s：來源=%s、產物=exit %s（預期 %s）' %
                            (name, source_ok, product_exit, expected))
    if not no_stage_rejected:
        problems.append('空提交候選未被來源檢查攔截')
    if not untracked_baseline_clean:
        problems.append('未追蹤負向測試的起點不乾淨')
    if not untracked_rejected:
        problems.append('未追蹤檔未被來源檢查攔截')
    record('FAIL' if problems else 'OK', '來源提交候選一致性（F46 部分）',
           '；'.join(problems) if problems else
           '完整 stage 通過、部分 stage 兩端拒絕、來源另拒未追蹤檔；未驗實際接手流程')


def handoff_flow_case(dest, tmp, bash):
    """以本機 bare origin 真正推送開工／交棒，再由另一個 checkout 接棒。

    跑部署出去的專案；本 repo 的開場 hook 跟它逐位元組相同（「本 repo 開場 hook」守），不重跑。
    hook 照原文印「工作中」（v3 D12），判讀交給模型。
    """
    home = tmp / 'flow-product'
    origin, writer, reader = home / 'origin.git', home / 'writer', home / 'reader'
    home.mkdir()
    shutil.copytree(dest, writer, ignore=shutil.ignore_patterns('.git'))
    hook_rel = '.claude/hooks/git-freshness.sh'
    free_mark, foreign_mark = '- **工作中**：無（已交棒）', '- **工作中**：`other-box`'
    needle = 'origin/${branch}:HANDOFF.md'

    handoff = writer / 'HANDOFF.md'
    busy_line = next(line for line in read_lf(handoff).splitlines()
                     if line.startswith('- **工作中**：'))
    write_lf(handoff, read_lf(handoff).replace(busy_line,
             '- **工作中**：無（已交棒）'))
    def must(result, action):
        if result.returncode:
            raise AssertionError('%s exit %s：%s' % (
                action, result.returncode, result.stderr.strip()[:160]))
        return result
    must(run(['git', 'init', '-q', '--bare', str(origin)]), 'init bare')
    must(git(['init', '-q', '-b', 'main'], writer), 'init writer')
    must(git(['add', '-A'], writer), 'stage baseline')
    must(git(['commit', '-qm', 'baseline'], writer), 'commit baseline')
    must(git(['remote', 'add', 'origin', str(origin)], writer), 'remote')
    must(git(['push', '-q', '-u', 'origin', 'main'], writer), 'push baseline')
    must(run(['git', 'clone', '-q', '-b', 'main', str(origin), str(reader)]), 'clone reader')
    env = tool_env(CLAUDECODE='1', BOOTSTRAP_VERSION_CHECK='off')
    hook = reader / hook_rel
    def check_hook(expected):
        result = must(run([bash, str(hook)], cwd=reader, env=env), 'SessionStart hook')
        if expected not in result.stdout:
            raise AssertionError('hook 未印 %s：%s' % (expected, result.stdout.strip()[:200]))
    def set_busy(value, action):
        path = writer / 'HANDOFF.md'
        old = next(line for line in read_lf(path).splitlines()
                   if line.startswith('- **工作中**：'))
        write_lf(path, read_lf(path).replace(old, '- **工作中**：' + value))
        must(git(['add', '--', 'HANDOFF.md'], writer), 'stage ' + action)
        must(git(['commit', '-qm', action], writer), 'commit ' + action)
        must(git(['push', '-q', 'origin', 'main'], writer), 'push ' + action)

    check_hook(free_mark)
    set_busy('`other-box` ／ `Claude Code` ／ `㊣　26110816｜測試｜工作中｜交棒0次`',
             'foreign claim')
    # reader 的本機快照仍空閒；hook 必須 fetch 並讀 origin 那份。
    if '無（已交棒）' not in read_lf(reader / 'HANDOFF.md'):
        raise AssertionError('陳舊 checkout 起點不是空閒快照')
    check_hook(foreign_mark)
    counts = must(git(['rev-list', '--left-right', '--count', 'HEAD...@{upstream}'], reader),
                  'A1 counts').stdout.strip()
    if counts != '0\t1':
        raise AssertionError('A1 未辨認落後一筆：' + counts)

    # 負向變異：改成讀 HEAD，陳舊 reader 會錯把遠端占用判成已交棒。
    original = read_lf(hook)
    if original.count(needle) != 1:
        raise AssertionError('無法定位 hook 的遠端快照讀取')
    try:
        write_lf(hook, original.replace(needle, 'HEAD:HANDOFF.md'))
        mutant = must(run([bash, str(hook)], cwd=reader, env=env), 'local-only mutant')
        if free_mark not in mutant.stdout or foreign_mark in mutant.stdout:
            raise AssertionError('本機快照負向變異沒有重現錯誤放行')
    finally:
        write_lf(hook, original)

    must(git(['pull', '-q', '--ff-only'], reader), 'A1 fast-forward')
    check_hook(foreign_mark)
    set_busy('無（已交棒）', 'foreign release')
    must(git(['pull', '-q', '--ff-only'], reader), 'pull release')
    check_hook(free_mark)
    # A2.5 看到空閒到 A5 開工之間若遠端前進，舊 SHA 不能再授予寫入資格。
    observed = must(git(['rev-parse', 'origin/main'], reader), 'A2.5 SHA').stdout.strip()
    (writer / 'README.md').open('a', encoding='utf-8', newline='').write('\n另一棒先行。\n')
    must(git(['add', '--', 'README.md'], writer), 'stage intervening change')
    must(git(['commit', '-qm', 'intervening change'], writer), 'commit intervening change')
    must(git(['push', '-q', 'origin', 'main'], writer), 'push intervening change')
    must(git(['fetch', '-q', 'origin'], reader), 'A5 refetch')
    current = must(git(['rev-parse', 'origin/main'], reader), 'A5 SHA').stdout.strip()
    if observed == current:
        raise AssertionError('A5 未偵測遠端在觀測後前進')
    must(git(['pull', '-q', '--ff-only'], reader), 'catch up after changed SHA')
    me = must(run([bash, '-c', 'echo "${HOSTNAME:-$(hostname)}"'], cwd=reader),
              'hostname').stdout.strip()
    writer = reader
    set_busy('`%s` ／ `Claude Code` ／ `㊣　26110816｜測試｜工作中｜交棒0次`' % me,
             'own claim')
    check_hook('- **工作中**：`%s`' % me)
    (reader / 'README.md').open('a', encoding='utf-8', newline='').write('\n合成任務。\n')
    must(git(['add', '--', 'README.md'], reader), 'stage task')
    must(git(['commit', '-qm', 'synthetic task'], reader), 'commit task')
    must(git(['push', '-q', 'origin', 'main'], reader), 'push task')
    set_busy('無（已交棒）', 'own release')
    check_hook(free_mark)
    remote = must(git(['show', 'origin/main:HANDOFF.md'], reader), 'remote release').stdout
    if '- **工作中**：無（已交棒）' not in remote:
        raise AssertionError('交棒後 origin 標記未清')
    if git(['status', '--porcelain'], reader).stdout.strip() or \
            git(['rev-list', '--left-right', '--count', 'HEAD...@{upstream}'], reader).stdout.strip() != '0\t0':
        raise AssertionError('交棒後 reader 未乾淨對齊 origin')


def step_product_handoff_flow(dest, tmp):
    """實際 Git 接力：不把 hook 提醒算作程序執行。"""
    title = '部署後接手流程情境'
    bash = find_bash()
    if not bash:
        record('SKIP', title, '缺可用 bash')
        return
    try:
        handoff_flow_case(dest, tmp, bash)
    except (AssertionError, OSError, StopIteration) as exc:
        record('FAIL', title, str(exc))
        return
    record('OK', title, '遠端占用→陳舊接手阻擋→釋出→A2.5/A5 SHA 變更→本機開工→任務推送→交棒；'
           '本機快照錯誤放行變異重現。本 repo 的 hook 是逐字副本，不重跑；hook 只提醒，模型遵循未驗')


REPO_START_HOOK = '.claude/hooks/repo-git-check.sh'
REPO_PRE_PUSH_HOOK = '.claude/hooks/repo-pre-push.sh'

# v2 決策書凍結封存（v3 Q39）。使用者原話：「v2 應該是凍結的對照原件，
# 不該再被任何程式讀取」「一般時候不能讀，除非需要回朔歷史，在經過我的同意以後可以讀」。
# 檔名用拼接寫，因為本檔自己也在「封存原件」的掃描範圍內。
ARCHIVE_DIR = 'archive/docs/'
FROZEN_ARCHIVES = {
    ARCHIVE_DIR + 'requirements-decision' + '-v2.md': '95277d358a0a09131bc3e85115806f991bf528bd',
}
ARCHIVE_NAMES = ('project-bootstrap-requirements-decision' + '.md',
                 'requirements-decision' + '-v2.md')
# 程式不得引用封存區裡任何檔，所以檔名
# 清單由 Git 追蹤的封存區檔案即時產生，不在這裡列舉（列舉了本檔自己就會引用它們）。索引例外：
# 它的檔名是通用的 README.md，而且是封存區對外的入口。
ARCHIVE_INDEX = ARCHIVE_DIR + 'README.md'
# 經使用者同意、為回溯歷史而讀封存原件的程式。加一筆之前先取得使用者同意，並登記在決策書。
ARCHIVE_READERS = ()
ARCHIVE_CODE_SUFFIXES = ('.py', '.sh', '.cmd', '.json', '.toml', '.tmpl', '.yml', '.lock')
# 新的穩定版本成為權威後，屬於舊版本名稱的一切要刪除、封存或改名（v3 Q47）。
# 版本號是 v 加數字；後面接 .數字 的是工具版本（Claude Code v2.1.277），不算。
VERSION_TOKEN = re.compile(r'(?<![A-Za-z0-9.])[vV]([0-9]+)(?![0-9])(?!\.[0-9])')
# 程式裡用 _ 或 - 黏在識別字或標籤上的版本號（step_vN、vN_report、bootstrap-vN-…）。
VERSION_LABEL = re.compile(r'(?<![A-Za-z0-9])[vV]([0-9]+)(?=[_-][A-Za-z])'
                           r'|(?<=[A-Za-z0-9][_-])[vV]([0-9]+)(?![0-9A-Za-z])(?!\.[0-9])')
ARCHIVED_VERSION = re.compile(r'archive/[vV]([0-9]+)-')
BOOK_LINK = re.compile(r'唯一需求書是\[[^\]]*\]\((project-bootstrap-requirements-decision-v([0-9]+)\.md)\)')
BOOK_VERSION = re.compile(r'^> 決策版本：([0-9]+)。', re.M)


REPO_SKIP = ('src/kit/', ARCHIVE_DIR, 'bootstrap.py')
PRODUCT_CHECKER = ROOT / 'src/kit/files/tools/check_docs.py.tmpl'


def repo_scanned_files(tracked_files):
    """本 repo 文件檢查要讀的檔：src/kit/ 另有規則，封存區不讀（v3 Q39）。

    bootstrap.py 是 src/kit 的生成結果、刻意保留佔位符，由「安裝程式由來源生成」守，這裡不再查。
    """
    return [p for p in tracked_files if not any(p == s or p.startswith(s) for s in REPO_SKIP)]


def product_checker(path=PRODUCT_CHECKER):
    """載入部署後的 check_docs.py，換上本 repo 的設定（F46）。

    範本沒有佔位符，原文就是部署出去的那支。本 repo 不裝副本，改在這裡用同一份程式查自己，
    跟部署專案改檔頭「專案設定」區塊是同一種做法；保護因此不會低於產物。
    """
    loader = importlib.machinery.SourceFileLoader('check_docs_product', str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    module.DATED_DIRS = ('AGENTS.md', 'ARCHITECTURE.md', 'docs/ai-notes/')
    module.LINK_OK_PATHS = module.PLACEHOLDER_OK_PATHS = REPO_SKIP
    return module


class SharedBlanked(type(pathlib.Path())):
    """讀檔時把 AGENTS.md 的共用制度塗白：那一段連到部署後才存在的 skill 路徑。"""

    def read_text(self, *args, **kwargs):
        return blank_shared_copy(super().read_text(*args, **kwargs))


@contextmanager
def pushd(folder):
    """check_docs.py 用相對路徑讀檔、在 cwd 跑 git，所以要在受查的 repo 裡呼叫。"""
    old = os.getcwd()
    os.chdir(folder)
    try:
        yield
    finally:
        os.chdir(old)


def repo_document_problems(root, checker=None):
    """本 repo 的文件檢查，用部署後 check_docs.py 的同一份函式。回傳 (缺檔, 死連結, 缺日期, 殘留佔位符)。"""
    checker = checker or product_checker()
    with pushd(root):
        def keep(path):
            return repo_scanned_files([path.as_posix()]) != []
        mds = [path for path in checker.tracked_md() if keep(path)]
        missing = [path.as_posix() for path in mds if not path.is_file()]
        mds = [SharedBlanked(path) if path.as_posix() == 'AGENTS.md' else path
               for path in mds if path.is_file()]
        others = [path for path in checker.tracked(*checker.PLACEHOLDER_GLOBS)
                  if keep(path) and path.is_file()]
        return (missing, checker.check_links(mds)[1], checker.check_dates(mds),
                checker.check_placeholders(others))


def archive_problems(root, tracked_files, blob_of, frozen=None, readers=None):
    """封存原件逐位元組不變（只看 Git 記的 blob，不開檔），程式與測試不引用封存區的任何檔。"""
    frozen = FROZEN_ARCHIVES if frozen is None else frozen
    readers = ARCHIVE_READERS if readers is None else readers
    problems = []
    names = list(ARCHIVE_NAMES)
    for rel in sorted(tracked_files):
        base = rel.rsplit('/', 1)[-1]
        if rel.startswith(ARCHIVE_DIR) and rel != ARCHIVE_INDEX and base not in names:
            names.append(base)
    for path, expected in sorted(frozen.items()):
        actual = blob_of(path)
        if actual is None:
            problems.append('%s 不在 index：封存原件不能搬走或刪掉' % path)
        elif actual != expected:
            problems.append('%s 的 blob 變了（%s，應為 %s）：封存原件凍結，不改' %
                            (path, actual[:12], expected[:12]))
    for rel in tracked_files:
        if (rel.startswith(ARCHIVE_DIR) or rel in readers
                or not rel.endswith(ARCHIVE_CODE_SUFFIXES)):
            continue
        try:
            text = (root / rel).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        for name in names:
            if name in text:
                problems.append('%s 引用封存區的檔（%s）：平常不讀，要回溯歷史先經使用者'
                                '同意，再登記到 ARCHIVE_READERS' % (rel, name))
    return problems


def index_blob(root, path):
    out = git(['ls-files', '-s', '--', path], root).stdout.split()
    return out[1] if len(out) >= 2 else None
REPO_WIRING = ('.claude/settings.json', '.codex/hooks.json')


def repo_wiring_problems(root):
    """本 repo 兩份接線的問題清單；抽成函式讓負向測試能對暫存目錄跑。

    這兩份指向本 repo 自己的 `repo-*.sh`，跟部署包的接線只是長得像，沒有 `source:` 標記、
    落後偵測看不到，這一項是唯一的守門人。SessionStart 只能指向 `repo-git-check.sh`、
    PreToolUse 只能指向 `repo-pre-push.sh`，其他事件一律拒絕；被 sync_project.py 改成指向
    不存在的 `git-freshness.sh`／`pre-push-handoff.sh` 時，開場檢查會靜默失效。
    """
    problems, present = [], []
    targets = {'SessionStart': REPO_START_HOOK, 'PreToolUse': REPO_PRE_PUSH_HOOK}
    for rel in REPO_WIRING:
        cfg = root / rel
        if not cfg.exists():
            problems.append('%s 不存在' % rel)
            continue
        raw = cfg.read_text(encoding='utf-8')
        try:
            data = json.loads(raw)
        except Exception as e:
            problems.append('%s 不是合法 JSON：%s' % (rel, e))
            continue
        present.append(rel)
        for bad in ('git-freshness.sh', 'pre-push-handoff.sh'):
            if bad in raw:
                problems.append('%s 指向 %s，而這個 repo 沒有那個檔'
                                '（被 sync_project.py 覆蓋過？）' % (rel, bad))
        hooks = data.get('hooks', {})
        for event, groups in hooks.items():
            commands = [h.get('command', '') + ' ' + h.get('commandWindows', '')
                        for g in (groups or []) for h in (g.get('hooks') or [])]
            if event in targets:
                if not commands or any(targets[event] not in c for c in commands):
                    problems.append('%s 的 %s 沒有都指向 %s' % (rel, event, targets[event]))
            else:
                problems.append('%s 接了 %s，但這個 repo 只允許 SessionStart＋PreToolUse' % (rel, event))
        for event in targets:
            if event not in hooks:
                problems.append('%s 沒接 %s' % (rel, event))
        if rel == '.claude/settings.json':
            matchers = [g.get('matcher') for g in hooks.get('PreToolUse') or []]
            if matchers and any(m != 'Bash|PowerShell' for m in matchers):
                problems.append('%s 的 PreToolUse matcher 不是 Bash|PowerShell（跟部署包 3.9 不同）' % rel)
    for rel in (REPO_START_HOOK, REPO_PRE_PUSH_HOOK):
        if not (root / rel).exists():
            problems.append('%s 不存在——接線指著一個不在的腳本' % rel)
    return problems, present


def step_self():
    """本 repo 自己的 .md 與設定檔：死連結、日期標頭、殘留佔位符、接線合法。

    本 repo 刻意不裝 `check_docs.py`（裝了就成了要同步的副本），改用部署後那支的同一份函式
    換上本 repo 的設定來查（repo_document_problems）。settings.json 壞掉的後果是 SessionStart
    hook 靜默不執行，所以一起查。
    """
    ok = True
    tracked_files = [p for p in run(['git', 'ls-files', '-z'], cwd=ROOT).stdout.split('\0') if p]
    # src/kit/ 由「部署包由來源生成」照部署包的豁免規則查，這裡再查會誤報。
    # 封存區不讀（v3 Q39、Q45）：v2 原件逐位元組凍結，檔內相對連結失效是已宣告例外。
    tracked_files = repo_scanned_files(tracked_files)
    mds = [p for p in tracked_files if p.endswith('.md')]
    missing, dead, undated, holes = repo_document_problems(ROOT)
    if dead or undated or missing or holes:
        detail = []
        if missing:
            detail.append('缺檔：%s' % '、'.join(missing[:5]))
        if dead:
            detail.append('死連結 %d 處：%s' % (len(dead), '、'.join(dead[:5])))
        if undated:
            detail.append('缺「最後更新」：%s' % '、'.join(undated))
        if holes:
            detail.append('殘留部署佔位符：%s' % '、'.join(holes[:5]))
        record('FAIL', '本 repo 自己的文件', '；'.join(detail))
        ok = False
    else:
        record('OK', '本 repo 自己的文件',
               '%d 個 .md 無死連結、受管非 Markdown 無殘留部署佔位符，日期標頭齊備'
               '（用部署後 check_docs.py 的同一份函式）' % len(mds))

    problems, present = repo_wiring_problems(ROOT)
    if problems:
        record('FAIL', '本 repo 兩份接線', '；'.join(problems))
        ok = False
    elif not present:
        record('SKIP', '本 repo 兩份接線', '都不存在——開場沒有 git 檢查，接棒全靠人記得')
    else:
        record('OK', '本 repo 兩份接線',
               '%s 都是合法 JSON、SessionStart 指向 repo-git-check.sh、PreToolUse 指向 repo-pre-push.sh'
               % '＋'.join(present))
    return ok


def step_archive(tmp):
    """封存原件（v3 Q39）：v2 決策書凍結在 archive/docs/。

    程式與測試不引用封存區的檔（回溯歷史要先經使用者同意並登記到 ARCHIVE_READERS）、
    Git 記的 blob 不變、文件檢查不讀它。三件事都對合成 fixture 跑負向測試：只有真檔案一次
    乾淨，證明不了守門會擋。
    """
    tracked = [p for p in run(['git', 'ls-files', '-z'], cwd=ROOT).stdout.split('\0') if p]
    problems = archive_problems(ROOT, tracked, lambda path: index_blob(ROOT, path))

    root = tmp / 'archive-fixture'
    (root / 'tools').mkdir(parents=True)
    (root / 'archive/docs').mkdir(parents=True)
    (root / 'docs').mkdir()
    old, new = ARCHIVE_NAMES
    (root / 'tools/ok.py').write_text("BOOK = 'v3.md'\n", encoding='utf-8')
    (root / 'tools/reader.py').write_text("BOOK = '%s'\n" % new, encoding='utf-8')
    (root / 'tools/old.sh').write_text('cat %s\n' % old, encoding='utf-8')
    (root / 'docs/notes.md').write_text('[v2](archive/%s)\n' % new, encoding='utf-8')
    frozen = {ARCHIVE_DIR + new: 'a' * 40}
    files = ['tools/ok.py', 'tools/reader.py', 'tools/old.sh', 'docs/notes.md']
    blobs = {ARCHIVE_DIR + new: 'a' * 40}
    clean = archive_problems(root, ['tools/ok.py', 'docs/notes.md'], blobs.get, frozen, ())
    if clean:
        problems.append('乾淨 fixture 被誤擋：%s' % clean)
    caught = archive_problems(root, files, blobs.get, frozen, ())
    for rel in ('tools/reader.py', 'tools/old.sh'):
        if not any(c.startswith(rel + ' ') for c in caught):
            problems.append('程式引用封存路徑沒被擋：%s' % rel)
    if any(c.startswith('docs/notes.md') for c in caught):
        problems.append('文件提到封存路徑被當成程式引用')
    if archive_problems(root, ['tools/reader.py'], blobs.get, frozen, ('tools/reader.py',)):
        problems.append('已登記（經使用者同意）的讀取者仍被擋')
    # 不在 FROZEN_ARCHIVES 的封存檔一樣不能被程式引用；索引例外。
    other = 'old-' + 'plan.md'
    (root / 'tools/plan.py').write_text("PLAN = '%s'\n" % other, encoding='utf-8')
    (root / 'tools/index.py').write_text("INDEX = 'README.md'\n", encoding='utf-8')
    later = ['tools/plan.py', 'tools/index.py', ARCHIVE_DIR + other, ARCHIVE_INDEX]
    caught = archive_problems(root, later, blobs.get, frozen, ())
    if not any(c.startswith('tools/plan.py ') for c in caught):
        problems.append('程式引用凍結原件以外的封存檔沒被擋')
    if any(c.startswith('tools/index.py ') for c in caught):
        problems.append('封存索引的通用檔名被當成封存檔')
    for label, lookup in (('內容改動', {ARCHIVE_DIR + new: 'b' * 40}.get),
                          ('搬走或刪掉', {}.get)):
        if not archive_problems(root, [], lookup, frozen, ()):
            problems.append('封存原件%s沒被擋' % label)

    # 文件檢查只略過 archive/docs/，不能連帶略過別處的死連結：熱歷史 docs/history/ 與
    # archive/ 底下其他資料夾的說明檔照常檢查（v3 Q44、Q45）。
    (root / 'docs/history').mkdir(parents=True)
    (root / 'archive/other').mkdir(parents=True)
    (root / 'archive/docs/x.md').write_text('[死](nowhere.md)\n', encoding='utf-8')
    (root / 'archive/other/README.md').write_text('[死](nowhere.md)\n', encoding='utf-8')
    (root / 'docs/history/h.md').write_text('[死](nowhere.md)\n', encoding='utf-8')
    (root / 'docs/live.md').write_text('[死](nowhere.md)\n', encoding='utf-8')
    checked = ['archive/other/README.md', 'docs/history/h.md', 'docs/live.md']
    scanned = repo_scanned_files(['archive/docs/x.md'] + checked + ['src/kit/kit.md'])
    with pushd(root):
        dead = product_checker().check_links([pathlib.Path(p) for p in scanned if p.endswith('.md')])[1]
    if (scanned != checked
            or not all(any(d.startswith(p) for d in dead) for p in checked)):
        problems.append('封存區的略過蓋到別處：掃描 %s、死連結 %s' % (scanned, dead))

    if problems:
        record('FAIL', '封存原件', '；'.join(problems))
        return False
    record('OK', '封存原件', '%d 份凍結原件 blob 未變、程式與測試不引用封存區任何檔、文件檢查不讀封存區；'
           '引用／其他封存檔／改動／搬走／略過外溢五種反例都擋下，已登記讀取者與索引放行'
           % len(FROZEN_ARCHIVES))
    return True


def current_version(agents, read):
    """(現行版本, 問題)：AGENTS 連到的決策書檔名的版本號，且要跟它的「決策版本」行相同（v3 Q47）。"""
    link = BOOK_LINK.search(agents)
    if not link:
        return None, 'AGENTS.md 找不到「唯一需求書是[…](project-bootstrap-requirements-decision-vN.md)」'
    try:
        book = read(link.group(1))
    except OSError:
        return None, '讀不到 %s' % link.group(1)
    line = BOOK_VERSION.search(book)
    if not line or line.group(1) != link.group(2):
        return None, '%s 的「決策版本」行跟檔名的版本號不同' % link.group(1)
    return int(link.group(2)), ''


def version_name_problems(current, tracked, read_text):
    """archive/ 以外屬於舊版本名稱的東西（v3 Q47）。文件內文的對照與歷史說明不查。"""
    bad = []
    for rel in tracked:
        if rel.startswith('archive/'):
            continue
        old = sorted({int(n) for n in VERSION_TOKEN.findall(rel) if int(n) < current})
        if old:
            bad.append('%s：檔名或資料夾名帶舊版本號 %s' % (rel, '、'.join('v%d' % n for n in old)))
        if not rel.endswith(ARCHIVE_CODE_SUFFIXES):
            continue
        text = read_text(rel)
        for number, line in enumerate((text or '').split('\n'), 1):
            labels = [int(a or b) for a, b in VERSION_LABEL.findall(line)]
            if any(n < current for n in labels):
                bad.append('%s:%d：識別字或標籤帶舊版本號' % (rel, number))
            if ARCHIVED_VERSION.search(line):
                bad.append('%s:%d：程式引用 archive/ 底下的版本封存資料夾' % (rel, number))
    return bad


def step_version_names(tmp):
    """版本更替（2026-11-18，需求決策書 v3 Q47）。

    新的穩定版本成為權威後，舊版本名稱的檔案、資料夾、程式識別字與對封存版本的引用都要清掉。
    現行版本從 AGENTS 連到的決策書讀，所以換版只要 AGENTS 改連新版，這一項就開始要求清理。
    """
    def read_repo(rel):
        try:
            return (ROOT / rel).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return None
    problems = []
    current, why = current_version(read_lf(ROOT / 'AGENTS.md'),
                                   lambda rel: (ROOT / rel).read_text(encoding='utf-8'))
    if current is None:
        problems.append(why)
    else:
        tracked = [p for p in run(['git', 'ls-files', '-z'], cwd=ROOT).stdout.split('\0') if p]
        problems += version_name_problems(current, tracked, read_repo)

    # 反例用合成的現行版本 3。版本號一律在執行時拼出來：本檔自己也在掃描範圍內，
    # 寫死的字面值換版後會變成「舊版本名稱」擋住自己。
    def v(n):
        return 'v' + str(n)
    book = 'project-bootstrap-requirements-decision-%s.md' % v(3)
    agents = '唯一需求書是[需求決策書 %s](%s)。' % (v(3), book)
    texts = {book: '> 決策版本：3。2026-11-13 起是現行需求權威\n'}
    if current_version(agents, lambda rel: texts[rel]) != (3, ''):
        problems.append('版本來源：正常的 AGENTS 與決策書讀不出 3')
    for label, a, t in (('AGENTS 沒連決策書', '唯一需求書在別處。', texts),
                        ('決策版本行跟檔名不同', agents, {book: '> 決策版本：4。\n'}),
                        ('決策書讀不到', agents, {})):
        def read(rel, t=t):
            if rel not in t:
                raise OSError(rel)
            return t[rel]
        if current_version(a, read)[0] is not None:
            problems.append('版本來源反例沒被擋：' + label)
    # 反例：檔名、識別字、封存引用；放行：現行與較新的版本、工具版本號、文件內文、封存區本身
    files = {
        'docs/plan-%s.md' % v(2): '', 'docs/plan-%s.md' % v(3): '', 'docs/plan-%s-draft.md' % v(4): '',
        'archive/%s-old/tools/x.py' % v(2): 'def step_%s(): pass\n' % v(2),
        'tools/label.py': 'def step_%s():\n    pass\n' % v(2),
        'tools/temp.py': "PREFIX = 'bootstrap-%s-x'\n" % v(1),
        'tools/ref.py': "OLD = 'archive/%s-x/a.py'\n" % v(1),
        'tools/ok.py': "TOOL = '%s.1.277'\n# %s 時代的做法，見歷史紀錄\nNEW = 'step_%s'\n" % (v(2), v(2), v(3)),
        'docs/history.md': 'step_%s 與 archive/%s-x 是舊名\n' % (v(2), v(1)),
    }
    found = version_name_problems(3, sorted(files), files.get)
    for rel in ('docs/plan-%s.md' % v(2), 'tools/label.py', 'tools/temp.py', 'tools/ref.py'):
        if not any(f.startswith(rel) for f in found):
            problems.append('反例沒被擋：' + rel)
    for rel in ('docs/plan-%s.md' % v(3), 'docs/plan-%s-draft.md' % v(4), 'archive/', 'tools/ok.py',
                'docs/history.md'):
        if any(f.startswith(rel) for f in found):
            problems.append('不該擋的被擋：' + rel)

    if problems:
        record('FAIL', '版本更替', '；'.join(problems))
        return False
    record('OK', '版本更替', '現行版本 v%d（AGENTS 連到的決策書，檔名與「決策版本」行一致）；archive/ 以外沒有舊版本名稱的'
           '檔案、資料夾或程式識別字，程式不引用版本封存資料夾；版本來源 3 種、檔名／識別字／封存引用 4 種反例都擋下，'
           '現行與較新版本、工具版本號、文件內文與封存區放行' % current)
    return True


def step_repo_pre_push(dest, tmp):
    """本 repo 的 push 前 hook 要跟部署包 3.11 逐位元組相同（v3 F10）。

    F10 是 v3 唯一要「阻擋」的需求：推權威分支、這次推送沒改 HANDOFF.md、origin 的「工作中」
    又是「無（已交棒）」時擋下。行為由「AI push 提醒情境」對部署 hook 實跑；接線由
    「本 repo 兩份接線」守，這裡再對接線守門跑負向測試。
    """
    issues = []
    path = ROOT / REPO_PRE_PUSH_HOOK
    deployed = read_lf(dest / '.claude/hooks/pre-push-handoff.sh')
    if not path.is_file():
        issues.append('%s 不存在' % REPO_PRE_PUSH_HOOK)
    elif read_lf(path) != deployed:
        issues.append('%s 跟部署包 3.11 不同：改完部署包要手動重貼（sync_project 拒絕本 repo）'
                      % REPO_PRE_PUSH_HOOK)

    good = {rel: (ROOT / rel).read_text(encoding='utf-8') for rel in REPO_WIRING}

    def wiring(edit=None, drop=()):
        base = tmp / ('pre-push-wiring-%d' % len(list(tmp.glob('pre-push-wiring-*'))))
        for rel, text in good.items():
            data = json.loads(text)
            if edit and rel in edit:
                edit[rel](data)
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            (base / rel).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        for rel in (REPO_START_HOOK, REPO_PRE_PUSH_HOOK):
            if rel not in drop:
                (base / rel).parent.mkdir(parents=True, exist_ok=True)
                (base / rel).write_text('#!/bin/sh\n', encoding='utf-8')
        return repo_wiring_problems(base)[0]

    def handler(cmd, matcher='Bash|PowerShell'):
        return [{'matcher': matcher, 'hooks': [{'type': 'command', 'command': cmd}]}]

    push_cmd = 'bash "%s"' % REPO_PRE_PUSH_HOOK
    if wiring():
        issues.append('現行接線複本被判有問題：' + '；'.join(wiring()))
    breakers = {
        'Codex 沒接 PreToolUse': {'.codex/hooks.json': lambda d: d['hooks'].pop('PreToolUse')},
        'Claude Code 沒接 PreToolUse': {'.claude/settings.json': lambda d: d['hooks'].pop('PreToolUse')},
        'PreToolUse 指向別支': {'.claude/settings.json': lambda d: d['hooks'].update(PreToolUse=handler('bash other.sh'))},
        'matcher 只剩 Bash': {'.claude/settings.json': lambda d: d['hooks'].update(PreToolUse=handler(push_cmd, 'Bash'))},
        '接回動作提醒的 PostToolUse': {'.claude/settings.json': lambda d: d['hooks'].update(PostToolUse=handler(push_cmd))},
        'SessionStart 指向 push 前 hook': {'.claude/settings.json': lambda d: d['hooks'].update(SessionStart=handler(push_cmd))},
    }
    for name, edit in breakers.items():
        if not wiring(edit):
            issues.append('負向測試沒擋住：' + name)
    if not wiring(drop=(REPO_PRE_PUSH_HOOK,)):
        issues.append('負向測試沒擋住：push 前 hook 腳本不存在')
    record('FAIL' if issues else 'OK', '本 repo push 前 hook', '；'.join(issues) if issues else
           'repo-pre-push.sh 跟部署包 3.11 逐位元組相同，兩份接線的 PreToolUse 都指向它；接線守門 %d 個負向測試都擋住'
           '（行為由「AI push 提醒情境」對部署 hook 實跑）' % (len(breakers) + 1))


def step_sync_self_guard():
    """`sync_project.py <本 repo 路徑>` 必須拒絕，而且預演輸出裡一個 `UPDATE` 都沒有。

    本 repo 的兩份接線跟 `WIRING` 清單同名、指的卻是自己的 hook；被同步一次就改成指向
    不存在的 `git-freshness.sh`，開場檢查靜默失效（2026-11-01 實測手打路徑會印出兩個 `UPDATE`）。
    只查有印出拒絕不夠：「印了話卻照樣改檔」的版本也會過。
    """
    out = run([sys.executable, '-X', 'utf8', 'tools/sync_project.py', str(ROOT)],
              cwd=ROOT).stdout
    refused, untouched = '不是同步目標' in out, 'UPDATE' not in out
    if not (refused and untouched):
        record('FAIL', 'sync 拒絕本 repo',
               '%s%s' % ('' if refused else '沒印出拒絕；',
                         '' if untouched else '預演仍要改檔（UPDATE）')
               + chr(10) + '           輸出：' + out.strip()[:200])
        return False
    record('OK', 'sync 拒絕本 repo', '手打本 repo 路徑→拒絕，預演零 UPDATE')
    return True


def wiring_command(script):
    """接線裡那一串 Unix 命令的唯一來源。

    期望值有兩份就是下一個會悄悄分岔的地方——這裡同時被「Codex Windows 接線」與
    「接線 cwd 定位」兩項引用。
    """
    return 'bash "$(git rev-parse --show-cdup).claude/hooks/%s"' % script


def wiring_command_windows(script):
    r"""Windows 那一欄多一次斜線正規化：`--show-cdup` 回的是 `../`，
    `cmd /d /c "../.claude\hooks\codex-hook.cmd"` 會死在 `'..' is not recognized`（2026-11-02 實測）。
    `commandWindows` 由 Codex 外層的 PowerShell 執行，所以用得上 `-replace`。
    """
    return (r"""cmd /d /c "$((git rev-parse --show-cdup) -replace '/','\')"""
            + r""".claude\hooks\codex-hook.cmd" """ + script)


def codex_wiring_problems(cfg, scripts):
    problems = []
    for event, script in scripts.items():
        hooks = [h for g in cfg.get('hooks', {}).get(event, []) for h in g.get('hooks', [])
                 if script in h.get('command', '')]
        if len(hooks) != 1:
            problems.append('%s 的 %s 接線不是一份' % (event, script))
            continue
        h = hooks[0]
        if h.get('command') != wiring_command(script):
            problems.append('%s 的 Unix 接線改變了' % event)
        windows = wiring_command_windows(script)
        if event == 'PreToolUse':
            windows += '; exit $LASTEXITCODE'
        if h.get('commandWindows') != windows:
            problems.append('%s 沒經 Windows 啟動器執行同一支腳本' % event)
    return problems


def step_codex_windows(dest, tmp):
    """真部署發生過：已信任卻選到 WSL，exit 1；驗接線與實際 batch 的 stdin／結束碼。"""
    cfg = json.loads((dest / '.codex/hooks.json').read_text(encoding='utf-8'))
    scripts = {'SessionStart': 'git-freshness.sh', 'PreToolUse': 'pre-push-handoff.sh'}
    bad = codex_wiring_problems(cfg, scripts)
    for event in scripts:
        stale = json.loads(json.dumps(cfg))
        del stale['hooks'][event][0]['hooks'][0]['commandWindows']
        if not codex_wiring_problems(stale, scripts):
            bad.append('%s 拿掉 commandWindows 的負向測試沒擋住' % event)
    stale = json.loads(json.dumps(cfg))
    stale['hooks']['PreToolUse'][0]['hooks'][0]['commandWindows'] = 'bash .claude/hooks/pre-push-handoff.sh'
    if not codex_wiring_problems(stale, scripts):
        bad.append('Windows 改回 PATH bash 的負向測試沒擋住')
    own = json.loads((ROOT / '.codex/hooks.json').read_text(encoding='utf-8'))
    bad += codex_wiring_problems(own, {'SessionStart': 'repo-git-check.sh'})
    launcher = dest / '.claude/hooks/codex-hook.cmd'
    raw = launcher.read_bytes()
    body = raw.decode('ascii') if raw.isascii() else ''
    if not body or '\r' in body or re.search(r'^\s*(?::|\()|\(\s*$', body, re.M):
        bad.append('啟動器必須 ASCII、LF、無 label 與多行括號區塊')
    if (ROOT / '.claude/hooks/codex-hook.cmd').read_bytes() != raw:
        bad.append('本 repo 的 Windows 啟動器與權威範本不同')
    if bad:
        record('FAIL', 'Codex Windows 接線', '；'.join(bad))
        return False
    record('OK', 'Codex Windows 接線',
           '兩個事件與本 repo 均用 commandWindows；Unix 命令保留；三個負向測試通過，啟動器 ASCII／LF 且副本一致')

    import sync_project as sp
    project = tmp / 'codex-upgrade'
    (project / '.codex').mkdir(parents=True)
    old = json.loads(json.dumps(cfg))
    for groups in old['hooks'].values():
        for group in groups:
            for h in group['hooks']:
                h.pop('commandWindows', None)
    old['hooks']['SessionStart'].append({'hooks': [{'type': 'command', 'command': 'project-own'}]})
    wiring = project / '.codex/hooks.json'
    wiring.write_text(json.dumps(old), encoding='utf-8')
    skill = project / '.claude/skills/handoff/SKILL.md'
    skill.parent.mkdir(parents=True)
    skill.write_text('project skill must stay untouched', encoding='utf-8')
    preview = sp.sync(project, dest, codex_only=True)
    if preview.changed != 2 or preview.errors or (project / sp.CODEX_LAUNCHER).exists():
        bad.append('Codex 限定預演沒有列出兩項，或竟然寫檔')
    plan = sp.sync(project, dest, codex_only=True)
    changed = len(sp.apply_plan(plan)[0])
    got = json.loads(wiring.read_text(encoding='utf-8'))
    if changed != 2 or codex_wiring_problems(got, scripts):
        bad.append('舊專案沒同時升級接線與新增啟動器')
    if skill.read_text(encoding='utf-8') != 'project skill must stay untouched':
        bad.append('Codex 限定同步竟改了 SKILL.md')
    if not any(h.get('command') == 'project-own' for g in got['hooks']['SessionStart'] for h in g['hooks']):
        bad.append('Codex 同步洗掉專案自己的 hook')
    if sp.sync(project, dest, codex_only=True).changed != 0:
        bad.append('Codex 限定同步重跑仍改檔')
    absent = tmp / 'codex-absent'
    absent.mkdir()
    if sp.sync(absent, dest, codex_only=True).changed or list(absent.iterdir()):
        bad.append('沒有 Codex 接線的專案被自動補裝')
    if bad:
        record('FAIL', 'Codex 接線升級', '；'.join(bad))
        return False
    record('OK', 'Codex 接線升級',
           '預演零寫入、舊接線補齊啟動器、自有 hook 與 SKILL 保留、重跑零變更、沒裝 Codex 的專案不補裝')

    if os.name != 'nt':
        return True  # batch 執行只適用 Windows；其他平台仍跑上面的接線與升級測試。
    fixture = tmp / 'Codex 空白路徑' / '.claude/hooks'
    fixture.mkdir(parents=True)
    shim = fixture / 'codex-hook.cmd'
    shim.write_bytes(raw)
    write_lf(fixture / 'probe.sh',
             '#!/usr/bin/env bash\nIFS= read -r payload\nprintf "[git-check] %s\\n" "$payload"\n'
             'printf "err:%s\\n" "$payload" >&2\nexit 2\n')
    command = '"%s" /d /s /c ""%s" probe.sh"' % (os.environ['COMSPEC'], shim)
    r = run(command, cwd=tmp, stdin='stdin-survives\n')
    if (r.returncode != 2 or r.stdout.strip() != 'Git status check:\n[git-check] stdin-survives'
            or r.stderr.strip() != 'err:stdin-survives'):
        record('FAIL', 'Codex Windows 啟動器',
               '空白／中文路徑、不同 cwd、stdin 或 exit 2 沒保留：%r' % ((r.returncode, r.stdout, r.stderr),))
        return False
    # Codex 的 Windows hook 外面還有 PowerShell -Command；只測 cmd 會漏掉 2 被折成 1。
    powershell = shutil.which('powershell') or shutil.which('pwsh')
    if not powershell:
        record('SKIP', 'Codex Windows 結束碼', '找不到 PowerShell，無法驗完整啟動鏈')
        return None
    ps_command = cfg['hooks']['PreToolUse'][0]['hooks'][0]['commandWindows'].replace(
        'pre-push-handoff.sh', 'probe.sh')
    ps = run([powershell, '-NoProfile', '-NonInteractive', '-Command', ps_command],
             cwd=fixture.parents[1], stdin='stdin-survives\n')
    old_ps = run([powershell, '-NoProfile', '-NonInteractive', '-Command',
                  ps_command.replace('; exit $LASTEXITCODE', '')],
                 cwd=fixture.parents[1], stdin='stdin-survives\n')
    if ps.returncode != 2 or old_ps.returncode != 1:
        record('FAIL', 'Codex Windows 結束碼',
               'PowerShell 完整啟動鏈應回 2、拿掉明確 exit 應回 1，實得 %s／%s'
               % (ps.returncode, old_ps.returncode))
        return False
    record('OK', 'Codex Windows 結束碼',
           'PowerShell → cmd → Git Bash 保留 exit 2；拿掉明確 exit 的負向測試重現 exit 1')
    # 原始回歸：只有方括號標記時，CLI 0.166.0 把它當 JSON。證明標頭真的不能被刪掉。
    stale = raw.replace(b'echo Git status check:\n', b'')
    if stale == raw:
        record('FAIL', 'Codex Windows 啟動器', '移除純文字標頭的負向測試沒有改到內容')
        return False
    try:
        shim.write_bytes(stale)
        negative = run(command, cwd=tmp, stdin='stdin-survives\n')
        if negative.stdout.startswith('Git status check:\n') or not negative.stdout.startswith('[git-check]'):
            record('FAIL', 'Codex Windows 啟動器', '移除標頭後沒有重現方括號開頭的舊輸出')
            return False
    finally:
        shim.write_bytes(raw)
    # Windows 啟動 cmd 時會重建 ProgramFiles；須在同一個 cmd 裡設定，負向情境才真的沒 Git。
    missing = fixture / 'missing-git.cmd'
    write_lf(missing, '@echo off\nset "ProgramFiles=%~dp0missing"\n'
             'set "ProgramFiles(x86)=%~dp0missing"\n'
             'set "LOCALAPPDATA=%~dp0missing"\n'
             'call "%~dp0codex-hook.cmd" probe.sh\nexit /b %ERRORLEVEL%\n', encoding='ascii')
    missing_command = '"%s" /d /s /c ""%s""' % (os.environ['COMSPEC'], missing)
    env = dict(os.environ, PATH=os.environ['SystemRoot'] + '\\System32')
    r = run(missing_command, cwd=tmp, env=env, stdin='no-git\n')
    if r.returncode != 1 or 'Git Bash not found' not in r.stderr:
        record('FAIL', 'Codex Windows 啟動器', '找不到 Git Bash 時沒明確失敗：%r' % ((r.returncode, r.stderr),))
        return False
    record('OK', 'Codex Windows 啟動器',
           '原生 cmd 實跑：中文／空白路徑、不同 cwd、純文字標頭、stdin／輸出內容／stderr／exit 2 保留；缺 Git Bash 明確 exit 1')
    return True


def step_wiring_cwd(dest, tmp):
    """接線要從子目錄也找得到腳本（查核報告 F05）。

    hook 的 `command` 以 session 的 cwd 執行，從子目錄開 session 時舊接線是 exit 127，
    而 SessionStart 失敗跟「檢查過了沒事」在畫面上一樣。所以跑的是接線 JSON 裡原始的命令，
    不是直接拿完整路徑跑腳本（那在任何 cwd 都會過）。fixture 路徑含空白與中文；不打網路。
    """
    files = {
        '骨架 .claude/settings.json': dest / '.claude/settings.json',
        '骨架 .codex/hooks.json': dest / '.codex/hooks.json',
        '本 repo .claude/settings.json': ROOT / '.claude/settings.json',
        '本 repo .codex/hooks.json': ROOT / '.codex/hooks.json',
    }
    bad = []
    for name, path in files.items():
        if not path.exists():
            bad.append('%s 不存在' % name)
            continue
        cfg = json.loads(path.read_text(encoding='utf-8'))
        for groups in cfg.get('hooks', {}).values():
            for group in groups:
                for h in group.get('hooks', []):
                    for key in ('command', 'commandWindows'):
                        cmd = h.get(key)
                        if cmd and 'rev-parse --show-cdup' not in cmd:
                            bad.append('%s 的 %s 沒從 Git root 定位：%s' % (name, key, cmd))
    if bad:
        record('FAIL', '接線 cwd 定位', '；'.join(bad))
        return False

    bash = find_bash()
    if not bash:
        record('SKIP', '接線 cwd 定位', '四份接線的文字檢查過了，但找不到看得懂 Windows 路徑的 bash，沒實跑')
        return None

    origin = tmp / 'cwd-origin.git'
    work = tmp / '我的 專案 cwd'
    run(['git', 'init', '-q', '--bare', str(origin)])
    shutil.copytree(dest, work, ignore=shutil.ignore_patterns('.git'))
    git(['init', '-q', '-b', 'main'], work)
    git(['add', '-A'], work)
    git(['commit', '-qm', 'init'], work)
    git(['remote', 'add', 'origin', str(origin)], work)
    git(['push', '-q', '-u', 'origin', 'main'], work)
    # 未推送、而且沒動 HANDOFF 的 commit：pre-push 防呆該回 2。拿 exit 2 當「腳本真的跑到了」
    # 的證據，比只看 exit 0 強——後者連「什麼都沒發生」都會過。
    with (work / 'README.md').open('a', encoding='utf-8', newline='') as fh:
        fh.write('\n驗證用改動\n')
    git(['commit', '-qam', 'docs: touch'], work)

    cfg = json.loads((work / '.codex/hooks.json').read_text(encoding='utf-8'))
    handler = {e: [h for g in groups for h in g['hooks']][0]
               for e, groups in cfg['hooks'].items()}
    env = dict(GIT_ENV, BOOTSTRAP_VERSION_CHECK='off')
    push = '{"tool_input":{"command":"git push origin main"}}'
    cases = []

    def check(name, ok, got):
        cases.append((name, ok, got))

    for sub in ('.', 'tools', 'docs/ai-notes'):
        cwd = work if sub == '.' else work / sub
        r = run([bash, '-c', handler['SessionStart']['command']], cwd=cwd, stdin='{}', env=env)
        check('%s 開場檢查' % sub, r.returncode == 0 and '[facts]' in r.stdout,
              (r.returncode, r.stdout[:100], r.stderr[:100]))
        r = run([bash, '-c', handler['PreToolUse']['command']], cwd=cwd, stdin=push, env=env)
        check('%s push 防呆' % sub, r.returncode == 2, (r.returncode, r.stderr[:100]))

    # 負向①：舊形式從子目錄必須失敗，否則這一項根本沒在量東西。
    r = run([bash, '-c', 'bash .claude/hooks/git-freshness.sh'],
            cwd=work / 'tools', stdin='{}', env=env)
    check('舊形式從子目錄→失敗（負向）', r.returncode != 0 and '[facts]' not in r.stdout,
          (r.returncode, r.stdout[:80]))

    if os.name == 'nt':
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        if powershell:
            win = handler['SessionStart']['commandWindows']
            r = run([powershell, '-NoProfile', '-NonInteractive', '-Command', win],
                    cwd=work / 'tools', stdin='{}', env=env)
            check('Windows 啟動鏈從子目錄', r.returncode == 0 and '[facts]' in r.stdout,
                  (r.returncode, r.stdout[:100], r.stderr[:100]))
            # 負向②：拿掉斜線正規化就會變成 `../.claude\...`，cmd 吃不下混合斜線。
            naive = win.replace("$((git rev-parse --show-cdup) -replace '/','\\')",
                                '$(git rev-parse --show-cdup)')
            if naive == win:
                check('混合斜線負向測試改到了命令', False, naive)
            else:
                r = run([powershell, '-NoProfile', '-NonInteractive', '-Command', naive],
                        cwd=work / 'tools', stdin='{}', env=env)
                check('混合斜線從子目錄→失敗（負向）',
                      r.returncode != 0 and '[facts]' not in r.stdout,
                      (r.returncode, r.stdout[:80]))
        else:
            cases.append(('Windows 啟動鏈', None, '找不到 PowerShell'))

    failed = ['%s：實得 %r' % (n, got) for n, ok, got in cases if ok is False]
    if failed:
        record('FAIL', '接線 cwd 定位', '；'.join(failed))
        return False
    skipped = [n for n, ok, _ in cases if ok is None]
    done = '、'.join(n for n, ok, _ in cases if ok)
    if skipped:
        record('SKIP', '接線 cwd 定位', '%s；跳過：%s' % (done, '、'.join(skipped)))
        return None
    record('OK', '接線 cwd 定位', done)
    return True


def fixture_origin(project, claim=False):
    """本機 bare remote，讓同步測試遵守真實 A1／A5 前提。"""
    def must(args):
        r = git(args, project)
        if r.returncode:
            raise RuntimeError('fixture origin: ' + r.stderr)
    remote = project.parent / (project.name + '-origin.git')
    must(['init', '--bare', '-q', str(remote)])
    must(['remote', 'add', 'origin', str(remote)])
    must(['push', '-qu', 'origin', 'HEAD'])
    owner = '`fixture-machine` ／ `Codex CLI` ／ `fixture-session`，2026-11-03 開工'
    if claim:
        write_lf(project / 'HANDOFF.md', '- **工作中**：' + owner + '\n')
        must(['add', 'HANDOFF.md'])
        must(['commit', '-qm', 'A5 claim'])
        must(['push', '-q', 'origin', 'HEAD'])
    return owner


def wiring_preservation_problems(sp):
    """R01／R02：保存內容與觸發條件，不能只靠成功退出推定。"""
    own = {'type': 'command', 'command': 'bash .claude/hooks/pre-push-handoff.sh'}
    auth_group = {'matcher': 'Bash|PowerShell', 'hooks': [dict(own, timeout=30)]}
    auth = json.dumps({'hooks': {'PreToolUse': [auth_group]}})
    bad = []
    commands = [
        'python audit_hook.py --watch git-freshness.sh',
        'echo pre-push-handoff.sh',
        'bash project/pre-push-handoff.sh',
        own['command'] + ' && echo project-audit',
    ]
    for field in ('command', 'commandWindows'):
        for command in commands:
            custom = {'type': 'command', field: command}
            group = dict(auth_group, hooks=[own, custom])
            cur = json.dumps({'hooks': {'PreToolUse': [group]}})
            new, _, err = sp.merge_wiring(auth, cur)
            if not err or new is not None or sp.handler_scripts(custom):
                bad.append('R01 未拒絕不明命令：' + field + ' ' + command)
    # 任一命令欄不明，就不能認領整個雙平台 handler。
    mixed = dict(own, commandWindows='echo pre-push-handoff.sh')
    if sp.handler_scripts(mixed):
        bad.append('R01 雙平台命令只認得一欄仍被認領')
    for matcher in (None, '', '*', 'Bash', 'Bash|PowerShell'):
        group = {'hooks': [own, {'type': 'command', 'command': 'echo all-tools-audit'}]}
        if matcher is not None:
            group['matcher'] = matcher
        cur = json.dumps({'hooks': {'PreToolUse': [group]}})
        new, _, err = sp.merge_wiring(auth, cur)
        if matcher != 'Bash|PowerShell':
            if not err or new is not None:
                bad.append('R02 matcher 語意被改：' + repr(matcher))
        elif err or not new or json.loads(new)['hooks']['PreToolUse'][0]['hooks'][-1] != group['hooks'][-1]:
            bad.append('R02 一致 matcher 的自訂 handler 沒保留')
    for side in ('current', 'authority'):
        cur_group = dict(auth_group, hooks=[own, {'type': 'command', 'command': 'echo custom'}])
        ag = dict(auth_group)
        (cur_group if side == 'current' else ag)['extra-setting'] = True
        if not sp.merge_wiring(json.dumps({'hooks': {'PreToolUse': [ag]}}),
                               json.dumps({'hooks': {'PreToolUse': [cur_group]}}))[2]:
            bad.append('R02 組層欄位變動未拒絕：' + side)
    return bad


def step_sync_safety(tmp):
    """同步器的資料保全與失敗訊號（查核報告 F02／F03）。

    F02：骨架擁有的是指向骨架腳本的 handler，不是整組；專案加在同一組的 hook 要保留。
    F03：先算完、驗完才寫；任一檔算不出來就零寫入，任何目標沒完成就非零退出。
    """
    import sync_project as sp
    bad = wiring_preservation_problems(sp)
    # 負向測試恢復兩種舊判準；同一套行為斷言必須能抓到缺口。
    import types
    source = read_lf(ROOT / 'tools/sync_project.py')
    start = source.index('def handler_scripts(')
    end = source.index('\n\ndef scripts_in(', start)
    old_handler = '''def handler_scripts(handler):
    cmd = '%s %s' % (handler.get('command', ''), handler.get('commandWindows', ''))
    return frozenset(s for s in OWNED_SCRIPTS if s in cmd)
'''
    mutants = [source[:start] + old_handler + source[end:],
               source.replace('if meta_now.get(k) != meta_auth.get(k)',
                              'if k in meta_now and k in meta_auth and meta_now[k] != meta_auth[k]')]
    for i, text in enumerate(mutants):
        mutant = types.ModuleType('sync_mutant')
        mutant.__file__ = str(ROOT / 'tools/sync_project.py')
        exec(compile(text, mutant.__file__, 'exec'), mutant.__dict__)
        if not wiring_preservation_problems(mutant):
            bad.append('R01／R02 負向測試沒抓到舊判準 ' + str(i))

    def J(o):
        return json.dumps(o, ensure_ascii=False, indent=2)

    own = {'type': 'command', 'command': 'bash .claude/hooks/pre-push-handoff.sh'}
    mine = {'type': 'command', 'command': 'echo project-own'}
    auth = J({'hooks': {'PreToolUse': [{'matcher': 'Bash|PowerShell',
                                        'hooks': [dict(own, timeout=30)]}]}})

    # ① 同一組裡有專案自己的 handler，而骨架 handler 要更新 → 兩者都要在
    cur = J({'hooks': {'PreToolUse': [{'matcher': 'Bash|PowerShell',
                                       'hooks': [dict(own, timeout=10), mine]}]}})
    new, _, err = sp.merge_wiring(auth, cur)
    if err or new is None:
        bad.append('同組自訂 hook：%s' % (err or '沒認出骨架 handler 要更新'))
    else:
        hs = json.loads(new)['hooks']['PreToolUse'][0]['hooks']
        if not any(h.get('command') == 'echo project-own' for h in hs):
            bad.append('同組自訂 hook 被刪掉了（F02 的原始缺陷）')
        if not any(h.get('timeout') == 30 for h in hs):
            bad.append('同組的骨架 handler 沒更新成權威版')

    # ② 同一組裡有專案 handler，而權威版要改這一組的 matcher → 拒絕並說出新舊值，
    #    不要靜默把專案那個 handler 的觸發條件一起換掉
    stale = J({'hooks': {'PreToolUse': [{'matcher': 'Bash',
                                         'hooks': [dict(own, timeout=30), mine]}]}})
    new, _, err = sp.merge_wiring(auth, stale)
    if not err or new is not None:
        bad.append('matcher 衝突沒被拒絕——專案 handler 的觸發條件會被悄悄換掉')
    elif 'Bash|PowerShell' not in err or 'matcher' not in err:
        bad.append('matcher 衝突的訊息沒說出要改什麼（看不出該怎麼手動處理）')

    # ③ 專案有兩組都指向同一支骨架腳本 → 不敢猜要更新哪一組
    dup = J({'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [own]},
                                      {'matcher': 'Bash', 'hooks': [own]}]}})
    if sp.merge_wiring(auth, dup)[2] is None:
        bad.append('重複的骨架組沒被拒絕')

    # ④ 分組方式跟權威版不同（兩支腳本擠在一組）→ 拒絕，不要在後面另外補一組，
    #    否則同一支腳本掛兩次：開場印兩遍、防呆跑兩次
    other = {'type': 'command', 'command': 'bash .claude/hooks/git-freshness.sh'}
    lumped = J({'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [own, other]}]}})
    merged, _, err = sp.merge_wiring(auth, lumped)
    if err is None:
        hs = json.loads(merged)['hooks']['PreToolUse'] if merged else []
        n = sum('pre-push-handoff.sh' in h.get('command', '')
                for g in hs for h in g.get('hooks', []))
        bad.append('分組方式不同卻照樣合併了（骨架腳本出現 %d 次）' % n)

    # ⑤ 只有 commandWindows 的 handler 也要算成骨架的（Codex 的 Windows 接線就是這形狀）
    if 'pre-push-handoff.sh' not in sp.handler_scripts(
            {'type': 'command', 'commandWindows':
             'cmd /d /c "$((git rev-parse --show-cdup) -replace \'/\',\'\\\').claude\\hooks\\codex-hook.cmd" pre-push-handoff.sh; exit $LASTEXITCODE'}):
        bad.append('只有 commandWindows 的 handler 沒被認成骨架的')

    # ⑥ HANDOFF 舊節名「## 已完成」改名「## 目前進度」：註記保留、內文不動、新名不動
    for before, after in (
        ('## 已完成\n\n- 已完成的事\n', '## 目前進度\n\n- 已完成的事\n'),
        ('## 已完成（2026-11-01）\n- x\n', '## 目前進度（2026-11-01）\n- x\n'),
        ('## 目前進度\n\n- 已完成\n', None),
    ):
        if sp.ensure_progress_heading(before) != after:
            bad.append('「## 已完成」改名結果不對：%r' % before[:24])

    # ── F03：拿一個最小假專案跑真的 CLI
    proj = tmp / 'sync-safety' / 'proj'
    (proj / '.claude' / 'skills' / 'handoff').mkdir(parents=True)
    skill = proj / '.claude' / 'skills' / 'handoff' / 'SKILL.md'
    write_lf(skill, 'stale skill')
    wiring = proj / '.claude' / 'settings.json'
    write_lf(wiring, '{ not json')
    write_lf(proj / 'HANDOFF.md', sp.BUSY_FIELD + '\n')
    for args in (['init', '-q', '-b', 'main'], ['add', '.'], ['commit', '-qm', 'fixture']):
        if git(args, proj).returncode:
            raise RuntimeError('同步安全 Git fixture 建立失敗')
    owner = fixture_origin(proj, claim=True)

    def cli(*args):
        extra = ['--owner', owner] if str(proj) in args else []
        return run([sys.executable, '-X', 'utf8', 'tools/sync_project.py'] + list(args) + extra,
                   cwd=ROOT)

    for group in (
        {'matcher': 'Bash|PowerShell', 'hooks': [own, {'type': 'command',
          'command': 'python audit_hook.py --watch git-freshness.sh'}]},
        {'hooks': [own, mine]},
    ):
        text = J({'hooks': {'PreToolUse': [group]}})
        write_lf(wiring, text)
        r = cli(str(proj), '--write', '--allow-dirty', '--accept-drift', '.claude/skills/handoff/SKILL.md')
        if r.returncode == 0 or read_lf(wiring) != text or read_lf(skill) != 'stale skill':
            bad.append('R01／R02 CLI 未拒絕或未維持零寫入')
    write_lf(wiring, '{ not json')

    r = cli(str(proj), '--write', '--allow-dirty', '--accept-drift', '.claude/skills/handoff/SKILL.md')
    if r.returncode == 0:
        bad.append('壞 JSON 的目標竟然 exit 0（F03 的原始缺陷）')
    if skill.read_text(encoding='utf-8') != 'stale skill':
        bad.append('算不出來卻已經寫了別的檔——preflight 沒有擋住部分寫入')
    if '全部都已經是' in r.stdout:
        bad.append('失敗卻宣稱「全部都已經是最新版」')

    r = cli(str(tmp / 'sync-safety' / 'absent'))
    if r.returncode == 0 or '全部都已經是' in r.stdout:
        bad.append('不存在的目標竟然 exit 0 或宣稱最新版')

    # 修好之後要真的寫得進去、而且 exit 0——修法不能嚴到什麼都不敢改
    write_lf(wiring, '{"hooks":{}}')
    r = cli(str(proj), '--write', '--allow-dirty', '--accept-drift', '.claude/skills/handoff/SKILL.md')
    if r.returncode != 0 or skill.read_text(encoding='utf-8') == 'stale skill':
        bad.append('正常的目標沒同步成功（exit %d）' % r.returncode)
    r = cli(str(proj), '--allow-dirty')
    if r.returncode != 0 or '全部都已經是' not in r.stdout:
        bad.append('重跑沒有回到「全部都已經是」且 exit 0')

    if bad:
        record('FAIL', '同步安全', '；'.join(bad))
        return False
    record('OK', '同步安全',
           'handler 層所有權：同組自訂 hook 保留、matcher 衝突與重複／異常分組拒絕、'
           'commandWindows 認得出來；R01／R02 命令所有權與缺省 matcher 組合、兩個負向變異通過；HANDOFF「## 已完成」改名「## 目前進度」；'
           'preflight：壞 JSON 零寫入、失敗非零退出、修好後照樣同步得動')
    return True


def step_sync_coverage(dest):
    """同步清單要涵蓋骨架每一個檔，而且 hook 接線真的會被修好。

    兩份接線是 JSON、放不了 `source:` 標記，曾經不在同步清單裡，matcher 的修正就一直沒發下去、
    沒有徵兆（2026-10-30 查出）。新增範本忘了歸類要 FAIL；接線合併要換掉舊值、保住專案設定。
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    import sync_project as sp

    declared = (set(sp.WHOLE) | {sp.SURGICAL} | set(sp.WIRING)
                | set(sp.PARTIAL) | set(sp.INSTANCE))
    missing, extra = EXPECTED - declared, declared - EXPECTED
    if missing or extra:
        bits = []
        if missing:
            bits.append('範本有、清單沒歸類：%s（這些檔沒人同步，而且不會有徵兆）'
                        % sorted(missing))
        if extra:
            bits.append('清單有、範本沒有：%s' % sorted(extra))
        record('FAIL', '同步清單涵蓋骨架', '；'.join(bits))
        return False
    record('OK', '同步清單涵蓋骨架',
           '%d 個範本全部歸類（整份覆蓋 %d／手術 1／接線 %d＋AG 1／補欄位 %d／專案實例 %d）'
           % (len(EXPECTED), len(sp.WHOLE), len(sp.WIRING), len(sp.PARTIAL),
              len(sp.INSTANCE)))

    # 接線合併：拿真的範本當權威，餵一份「舊 matcher ＋ 專案自己加的東西」進去。
    auth = (dest / '.claude' / 'settings.json').read_text(encoding='utf-8')
    stale = json.loads(auth)
    stale['hooks']['PreToolUse'][0]['matcher'] = 'Bash'          # 2026-09-13 之前的舊值
    stale['permissions'] = {'allow': ['Bash(git status)']}       # 專案自己加的
    stale['hooks']['SessionStart'].append(                       # 專案自己加的 hook
        {'hooks': [{'type': 'command', 'command': 'bash .claude/hooks/project-own.sh'}]})
    new, _, err = sp.merge_wiring(auth, json.dumps(stale, ensure_ascii=False, indent=2))
    if err or new is None:
        record('FAIL', '接線合併', err or '舊 matcher 沒被認出來——落後的專案不會被修好')
        return False
    got = json.loads(new)
    start = [h for g in got['hooks']['SessionStart'] for h in g.get('hooks', [])]
    checks = {
        '換掉舊 matcher': got['hooks']['PreToolUse'][0].get('matcher') == 'Bash|PowerShell',
        '保留專案 permissions': got.get('permissions') == stale['permissions'],
        '保留專案自己的 hook': any('project-own.sh' in h.get('command', '') for h in start),
        '骨架 hook 不重複': sum('git-freshness.sh' in h.get('command', '')
                             for h in start) == 1,
    }
    bad = [k for k, v in checks.items() if not v]
    if bad:
        record('FAIL', '接線合併', '沒做到：%s' % '、'.join(bad))
        return False
    # 已經一致就不該回報要改，否則每次同步都製造假變更，雜訊會讓人不再看輸出。
    same, _, err2 = sp.merge_wiring(auth, auth)
    if err2 or same is not None:
        record('FAIL', '接線合併', '內容已一致卻說要改（%s）' % (err2 or '會製造假變更'))
        return False
    record('OK', '接線合併', '舊 matcher 換新、專案 permissions 與自有 hook 保留、已一致不動')
    return True


def step_eol(dest):
    # 封存區不開檔（v3 Q39）；它在 Git 裡的內容由「封存原件」的 blob 比對守。
    tracked = [
        ROOT / p for p in
        run(['git', 'ls-files'], cwd=ROOT).stdout.split('\n')
        if p and not p.startswith(ARCHIVE_DIR)
    ]
    generated = [f for f in dest.rglob('*') if f.is_file() and '.git' not in f.parts]
    bad = [f for f in tracked + generated if f.is_file() and crlf_count(f)]
    if bad:
        record('FAIL', '行末全 LF', f'{len(bad)} 檔含 CRLF：{[str(b) for b in bad[:5]]}')
        return False
    record('OK', '行末全 LF', f'本 repo {len(tracked)} 檔＋骨架 {len(generated)} 檔')
    return True


FRESHNESS_DAYS = 90
# 權威清單在部署包「這張表的保鮮期」那一段，這裡只是它的副本（用途只有放進 fail 訊息）。
# 網址要跟部署包同步改，指著轉址等於每次重查都先撞一次牆。
FRESHNESS_PAGES = ('code.claude.com/docs/en/hooks', 'code.claude.com/docs/en/memory',
                   'learn.chatgpt.com/docs/hooks', 'learn.chatgpt.com/docs/build-skills',
                   'antigravity.google/docs/hooks', 'antigravity.google/docs/rules')


def step_table_freshness():
    """「跨工具與跨平台」那張表的查證日期不得超過 FRESHNESS_DAYS 天。

    外部工具能力的斷言會無聲過期，同一種錯踩過兩次，第一次之後加的警告沒擋住第二次。
    這一項只保證有人看過日期，不保證真的重查；90 天一次，不會變成反射動作。
    """
    if os.environ.get('BOOTSTRAP_FRESHNESS') == 'off':
        record('SKIP', '跨工具表保鮮期', 'BOOTSTRAP_FRESHNESS=off')
        return True
    m = re.search(r'查證日期：(\d{4})-(\d{2})-(\d{2})', kit_text())
    if not m:
        record('FAIL', '跨工具表保鮮期',
               '「跨工具與跨平台」那節找不到「查證日期：YYYY-MM-DD」——這一項是靠它判斷的')
        return False
    checked = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    age = (datetime.date.today() - checked).days
    if age > FRESHNESS_DAYS:
        record('FAIL', '跨工具表保鮮期',
               '查證日期 %s 已經 %d 天（上限 %d）。先真的重讀這幾頁再改日期：%s。'
               '只是要跑別的驗證就 BOOTSTRAP_FRESHNESS=off'
               % (checked, age, FRESHNESS_DAYS, '、'.join(FRESHNESS_PAGES)))
        return False
    record('OK', '跨工具表保鮮期', '查證日期 %s，%d 天內（上限 %d）' % (checked, age, FRESHNESS_DAYS))
    return True


TOOL_VERDICTS = '✅❌⬜🟡'


def tool_section(text):
    """「## 跨工具與跨平台」那一節（到下一個 `## ` 為止）。"""
    i = text.find('## 跨工具與跨平台')
    if i < 0:
        return ''
    j = text.find('\n## ', i + 3)
    return text[i:j if j > 0 else len(text)]


def tool_matrix(section):
    """那一節裡的能力矩陣：表頭是空的第一欄＋至少三個工具名。

    回傳 (欄名, {列名: [判定符號]})。只讀第一張這種形狀的表：那一節還有別的表，
    拿列名當 key 全掃會在兩邊都沒有的列名上比出假問題。
    """
    lines = section.splitlines()
    for n, line in enumerate(lines):
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if cells[0] or len(cells) < 4:
            continue
        rows = {}
        for body in lines[n + 2:]:
            if not body.startswith('|'):
                break
            row = [c.strip() for c in body.strip('|').split('|')]
            if len(row) != len(cells):
                break
            rows[row[0]] = [c[:1] if c[:1] in TOOL_VERDICTS else '?' for c in row[1:]]
        return tuple(cells[1:]), rows
    return (), {}


# 只守已知回歸，不把所有「未解」「沒觸發」都擋掉，也不掃表頭的歷史變更記錄。
# 若未來有新證據改變結論，應連同本表一起更新；不是用保鮮期代替實際查證。
STALE_TOOL_PROSE = (
    ('2.0 仍列未測', r'2\.0\s*(?:未測|尚未測)'),
    ('CLI／2.0 仍列未測', r'(?:還沒|尚未)在\s*2\.0\s*與\s*CLI\s*上測過'),
    ('Antigravity 仍列未附接線', r'Antigravity\s*骨架(?:還沒|尚未)附接線'),
    ('skill 仍被稱作唯一入口', r'那是這個工具上唯一的入口'),
    ('IDE 追查又列下一步', r'要查就在\s*IDE\s*上重跑'),
)


def stale_tool_prose_problems(text):
    # 表頭的 dated changelog 保留事故史；第一個二級標題之後才是現行說明與範本。
    body = re.search(r'^## ', text, re.M)
    current = text[body.start():] if body else text
    current = re.sub(r'\s+', ' ', current.replace('`', '').replace('**', ''))
    return [label for label, pattern in STALE_TOOL_PROSE if re.search(pattern, current)]


def step_tool_prose(dest):
    documents = (
        ('部署包正文', kit_text()),
        ('本 repo ARCHITECTURE', (ROOT / 'ARCHITECTURE.md').read_text(encoding='utf-8')),
        ('重生 ARCHITECTURE', (dest / 'ARCHITECTURE.md').read_text(encoding='utf-8')),
        ('重生 handoff skill', skill_text(dest)),
    )
    problems = [f'{name}：{problem}' for name, text in documents
                for problem in stale_tool_prose_problems(text)]
    regressions = (
        'IDE `1.107.0` 沒觸發、2.0 未測。',
        '而那正是還沒在 2.0 與 CLI 上測過的事。',
        'Antigravity 骨架還沒附接線。',
        '**那是這個工具上唯一的入口**。',
        '要查就在 IDE 上重跑這份接線。',
    )
    for name, text in documents:
        for old in regressions:
            if not stale_tool_prose_problems(text + '\n' + old):
                problems.append(f'負向測試未擋住（{name}）：{old}')
    control = ('> 2026-10-30 當時寫的是：2.0 未測、Antigravity 骨架還沒附接線。\n'
               '\n## 現況\nCLI／2.0 已實測；IDE 沒觸發，原因未解、不再追查。\n')
    if stale_tool_prose_problems(control):
        problems.append('範圍測試誤擋歷史紀錄或 IDE 未解事實')
    if problems:
        record('FAIL', '跨工具過期敘述', '；'.join(problems))
        return False
    record('OK', '跨工具過期敘述',
           '正文與重生範本無已知舊斷言；%d 個回歸負向測試通過，歷史紀錄與 IDE 未解事實保留'
           % (len(documents) * len(regressions)))
    return True

# ── Python 版本下限（F14）────────────────────────────────────────────────
PY_FLOOR_SOURCES = ('tools/verify_bootstrap.py', 'tools/sync_project.py', 'src/project_bootstrap/installer.py')


def py_floor_problems(texts, pyproject, readme):
    """texts：{路徑: 原始碼}。回傳 (下限, 問題清單)。"""
    problems, floors = [], {}
    for rel, text in sorted(texts.items()):
        m = re.search(r'^MIN_PY = \((\d+), (\d+)\)$', text, re.M)
        if not m:
            problems.append('%s 沒有 `MIN_PY = (x, y)`' % rel)
            continue
        floors[rel] = (int(m.group(1)), int(m.group(2)))
        if not re.search(r'^\s*if sys\.version_info < MIN_PY:', text, re.M) or '需要 Python' not in text:
            problems.append('%s 宣告了 MIN_PY 卻沒有擋下舊版並清楚報錯' % rel)
    m = re.search(r'^requires-python = ">=(\d+)\.(\d+)"$', pyproject, re.M)
    if not m:
        problems.append('pyproject.toml 沒有 requires-python = ">=x.y"')
    else:
        floors['pyproject.toml'] = (int(m.group(1)), int(m.group(2)))
    if len(set(floors.values())) > 1:
        problems.append('Python 下限各處不同：%s' % '、'.join('%s %d.%d' % ((k,) + v) for k, v in sorted(floors.items())))
    floor = sorted(floors.values())[0] if floors else None
    if floor and '需要 Python %d.%d 以上' % floor not in readme:
        problems.append('README.md 範本沒有寫「需要 Python %d.%d 以上」' % floor)
    return floor, problems


def step_python_floor(dest):
    """Python 版本下限各處同號（查核報告 F14）。

    安裝程式要 3.12，沒有 3.12 的機器裝不起專案，所以維護工具、開發環境與部署後工具都用同一個
    下限。部署後的兩支不加守門（加了就得跳標記、同步每個專案），下限寫在 README 範本。
    只查宣告一致，不保證沒人用了比下限更新的 API。
    """
    texts = {rel: read_lf(ROOT / rel) for rel in PY_FLOOR_SOURCES}
    pyproject, readme = read_lf(ROOT / 'pyproject.toml'), read_lf(dest / 'README.md')
    floor, problems = py_floor_problems(texts, pyproject, readme)
    if not problems:
        first = PY_FLOOR_SOURCES[0]
        cases = (
            ('一支工具的 MIN_PY 不同', dict(texts, **{first: texts[first].replace(
                'MIN_PY = (%d, %d)' % floor, 'MIN_PY = (3, 8)', 1)}), pyproject, readme),
            ('拿掉檔頭守門', dict(texts, **{first: texts[first].replace(
                'if sys.version_info < MIN_PY', 'if False', 1)}), pyproject, readme),
            ('pyproject 下限不同', texts, pyproject.replace('>=%d.%d' % floor, '>=3.11', 1), readme),
            ('README 範本沒寫下限', texts, pyproject, readme.replace('需要 Python', '需要 python', 1)),
        )
        problems = ['負向測試未擋：' + name for name, *args in cases if not py_floor_problems(*args)[1]]
    if problems:
        record('FAIL', 'Python 版本下限', '；'.join(problems))
        return False
    record('OK', 'Python 版本下限', '兩支維護工具、安裝程式與 pyproject 都是 %d.%d，README 範本寫出同一個下限；'
           '%d 個負向測試（只查宣告一致）' % (floor + (len(cases),)))
    return True


# ── 已修正的主張不得在別處復活（F15）──────────────────────────────────────
# 這裡刻意**不是**一張「禁句表」：查核報告 F15 的改善建議明寫「不要只增加特定舊句的禁止
# regex，因為新的措辭會再次繞過」。所以每一項都綁在一個**結構**上——能力表的那一格、
# skill 的字母對應、同一條規則的單一定義——句子怎麼改寫都還是得跟那個結構對得起來。
CLAIM_SERIAL = '當天第幾個帶 `source:` 標記的改動'
CLAIM_STALE_SERIAL = '部署包當天的第幾次修改'
# 否認句要**跟工具名相鄰**才算在講那個工具：`AGENTS.md` 有一行同時提到 Codex 與「沒有全域
# 副本、或工具不會自動載入 skill」，那是在講這個 repo 少一個檔，不是在講 Codex 少一層機制。
# 兩件事同形，只靠「同一行」分不開（加這一項的當下就誤判到）。
CLAIM_DENY = r'%s[^。\n]{0,20}(?:沒有|不支援)[^。\n]{0,16}skill'
CLAIM_QUOTE = re.compile(r'「[^」]*」')


def claim_text(line):
    """把「」裡的內容拿掉之後的那一行：引用不算主張。

    保留理由時常要引用被改掉的舊說法；不區分引用與主張，守門人會逼下一棒把理由刪掉。
    """
    return CLAIM_QUOTE.sub('', line)


def claim_problems(docs):
    """docs：{'kit', 'readme', 'dep_readme', 'dep_skill', 'agents'} → 問題清單。"""
    problems = []

    # ① 散文不得否認能力表裡已經 ✅ 的工具。
    cols, rows = tool_matrix(tool_section(docs['kit']))
    if not rows.get('自動載入程序檔'):
        problems.append('部署包能力表找不到「自動載入程序檔」那一列，這一項無從判斷')
    else:
        yes = set()
        for col, verdict in zip(cols, rows['自動載入程序檔']):
            if verdict == '✅':
                yes.add(col.replace(' CLI', '').replace(' 桌面 App', '').strip())
        for name in sorted(docs):
            for line in docs[name].split('\n'):
                bare = claim_text(line)
                for tool in sorted(yes):
                    for hit in re.finditer(CLAIM_DENY % re.escape(tool), bare):
                        # 「…沒有 handoff skill」講的是少一個檔，不是少一層機制。例外只能看
                        # 命中的那一段，不能整行放行：要擋的句子跟「handoff skill」常在同一行。
                        if 'handoff skill' in hit.group(0):
                            continue
                        problems.append('%s 有一句說「%s 沒有 skill」，但能力表那一格是 ✅：%s'
                                        % (name, tool, hit.group(0)[:40]))

    # ② 交接 prompt 不得有自己的字母編號（曾經跟 skill 正好相反）。README 範本不放交接 prompt
    #    （v3 Q40）：README 部署後不更新，放在那裡的程序一定會過期。
    if '**A 接棒**' not in docs['kit'] or '**B 交棒**' not in docs['kit']:
        problems.append('部署包的 skill 模式表沒有「**A 接棒**／**B 交棒**」，字母對應無從比對')
    sec = docs['dep_readme']
    if '## 換一個 AI 接手工作' in sec or re.search(r'^#+ .*(?:收工時|開工時)', sec, re.M):
        problems.append('README 範本又放了交接 prompt——程序的家是 AGENTS 共用制度與 handoff skill')
    if re.search(r'^#+ *[AB] *[.．、]', sec, re.M):
        problems.append('README 範本又長出自己的 A／B 編號——字母只留 skill 那一套')
    i = sec.find('## 協作方式')
    collab = sec[i:sec.find('\n## ', i + 3)] if i >= 0 else ''
    if '「接棒」' not in collab or '「交棒」' not in collab:
        problems.append('README 範本的「## 協作方式」沒寫出跟 AI 說「接棒」「交棒」')

    # ③ verify_state 不得被「有憑證」這個不相干的前提擋掉。
    for name in sorted(docs):
        for line in docs[name].split('\n'):
            if 'verify_state' in line and re.search(r'有憑證(?:才|就)', claim_text(line)):
                problems.append('%s 把 verify_state 寫成有憑證才跑：%s'
                                % (name, line.strip()[:50]))
    # 交接協定已移出部署包（v3 Q41），「一律跑」由 skill 的 A4 帶著。
    if '**一律跑**' not in docs['dep_skill']:
        problems.append('handoff skill 的一鍵驗證沒有寫「一律跑」')

    # ④ 版本序號只有一種算法，而且要講明它跟版本行不保證同號。算法的細節是步驟，
    #    本 repo 寫在維護手冊；AGENTS 只留「不保證同號」那一句（原則草稿第 4 節）。
    for name in ('kit', 'maintenance'):
        if CLAIM_SERIAL not in docs[name]:
            problems.append('%s 沒有把序號規則寫成「%s」' % (name, CLAIM_SERIAL))
    for name in ('kit', 'agents'):
        if '不保證同號' not in docs[name]:
            problems.append('%s 沒有講明序號跟版本行不保證同號' % name)
    for name in sorted(docs):
        for line in docs[name].split('\n'):
            if CLAIM_STALE_SERIAL in claim_text(line):
                problems.append('%s 還在用舊的序號算法（只有引用舊版時才能出現）：%s'
                                % (name, line.strip()[:50]))

    # ⑤ 可攜層不得被寫成「到哪都成立」——載入、遵循、執行是三種不同的證據。
    if '載入、遵循、執行是三種不同的證據' not in docs['kit']:
        problems.append('部署包沒有把「載入／遵循／執行是三種證據」寫出來')
    for name in sorted(docs):
        for line in docs[name].split('\n'):
            if '到哪都成立' in claim_text(line):
                problems.append('%s 還在寫「可攜層到哪都成立」：%s' % (name, line.strip()[:50]))
    if '層自動發生' in docs['readme']:
        problems.append('README 還在寫「層自動發生」——那幾層壓低漏做的機會，不保證發生')
    return problems


def step_claims(dest):
    """已修正的主張不得在範本、操作卡與入口文件裡復活（查核報告 F15）。

    每一項都綁在一個結構上（能力表的格子、skill 的字母對應、同一條規則的單一定義），
    不是禁句表，因為新的措辭會繞過禁句。只守可機械判定的那一面；「舊版 …」的引用刻意放行，
    保留理由時常要引用舊說法。
    """
    docs = {
        'kit': kit_text(),
        'readme': read_lf(ROOT / 'README.md'),
        'agents': read_lf(ROOT / 'AGENTS.md'),
        'maintenance': read_lf(ROOT / CONTRIB_FILE),
        'dep_readme': read_lf(dest / 'README.md'),
        'dep_skill': skill_text(dest),
    }
    problems = claim_problems(docs)
    if problems:
        record('FAIL', '已修正的主張沒復活', '；'.join(problems[:6]))
        return False

    # 負向測試：五項各自要擋得住一次真的退化。
    cases = (
        ('能力表 ✅ 卻說沒有 skill', 'dep_readme',
         lambda t: t.replace('## 協作方式', '## 協作方式\n\nCodex 沒有 skill 機制。')),
        ('README 又長出 A／B 編號', 'dep_readme',
         lambda t: t.replace('## 協作方式', '### A. 交棒\n\n## 協作方式')),
        ('README 又放回交接 prompt', 'dep_readme',
         lambda t: t.replace('## 協作方式', '## 換一個 AI 接手工作\n\n## 協作方式')),
        ('README 不講接棒交棒', 'dep_readme',
         lambda t: t.replace('「接棒」', '「開工」')),
        ('verify_state 又變成有憑證才跑', 'dep_skill',
         lambda t: t.replace('**一律跑**，不是「有憑證才跑」', '`verify_state` 有憑證才跑')),
        ('skill 不寫一律跑', 'dep_skill', lambda t: t.replace('**一律跑**', '跑')),
        ('序號算法退回舊版', 'maintenance',
         lambda t: t.replace(CLAIM_SERIAL, CLAIM_STALE_SERIAL)),
        ('不再講明跟版本行同不同號', 'kit', lambda t: t.replace('不保證同號', '一樣')),
        ('可攜層又寫成到哪都成立', 'kit',
         lambda t: t.replace('- **可攜層——不需要任何設定就讀得到**',
                             '- **可攜層——到哪都成立**')),
        # 標題的層數會變，所以錨點只取不含層數的那半句。
        ('README 又寫層自動發生', 'readme',
         lambda t: t.replace('把漏做的機會壓低', '自動發生')),
    )
    missed = []
    for name, key, mutate in cases:
        bad = dict(docs)
        bad[key] = mutate(docs[key])
        if bad[key] == docs[key]:
            missed.append('%s（改寫沒命中，測試本身壞了）' % name)
        elif not claim_problems(bad):
            missed.append(name)
    if missed:
        record('FAIL', '已修正的主張沒復活', '負向測試沒排到：%s' % '、'.join(missed))
        return False

    record('OK', '已修正的主張沒復活',
           '能力表與散文一致、字母只剩 skill 那一套、verify_state 不以憑證為前提、'
           '序號規則單一定義、可攜層不過度保證；%d 個負向測試通過' % len(cases))
    return True


# ── verify_state 的失敗訊號（F04）────────────────────────────────────────
# 驅動程式：把 CHECKS 從外面灌進去，不碰範本的「專案設定」區塊。用 import 而不是
# 文字替換，是因為要驗的是 main() 的**行為**（狀態分類與結束碼），不是它長什麼樣。
STATE_DRIVER = """import json
import sys
sys.path.insert(0, '.')
import verify_state as vs
cfg = json.loads(sys.argv[1])
vs.BASE = cfg.get('base', '')
vs.SECRET_FILE = cfg.get('secret_file', '.env')
vs.HTTP_CHECKS = [tuple(x) for x in cfg.get('http', [])]
vs.CMD_CHECKS = [tuple(x) for x in cfg.get('cmd', [])]
vs.OPTIONAL = tuple(cfg.get('optional', []))
sys.exit(vs.main(cfg.get('argv', [])))
"""


class _StateHandler(http.server.BaseHTTPRequestHandler):
    """/good → 200 ＋ JSON；其餘 → 500。只聽 127.0.0.1，不碰網路。"""

    def do_GET(self):
        body = b'{"status": "ok"}' if self.path == '/good' else b'boom'
        self.send_response(200 if self.path == '/good' else 500)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def step_state_exit(dest):
    """verify_state 不得把失敗吞成 exit 0（查核報告 F04）。

    它的結束碼會被當成「服務驗過」的結論。九個情境全部實跑：rc7、HTTP 500、連不上、
    200 但內容不對、全綠、缺憑證（預設／`--strict`／OPTIONAL）、未填 CHECKS、祕密遮罩。
    `NOT_CONFIGURED` 回 0 是刻意的，也列在情境裡，免得被順手改成非零。
    """
    work = pathlib.Path(tempfile.mkdtemp(prefix='state-exit-'))
    shutil.copyfile(dest / 'tools' / 'verify_state.py', work / 'verify_state.py')
    write_lf(work / 'driver.py', STATE_DRIVER)
    write_lf(work / 'empty.env', 'OTHER=1\n')
    write_lf(work / 'real.env', 'API_KEY=supersecretvalue\n')

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _StateHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d' % srv.server_address[1]
    leak = [sys.executable, '-c', 'print("leak " + "supersecretvalue")']
    cases = (
        ('命令非零退出', {'cmd': [['boom', [sys.executable, '-c', 'import sys; sys.exit(7)']]]},
         2, 'FAIL', None),
        ('HTTP 500', {'base': base, 'http': [['bad', '/bad', False]]}, 2, 'FAIL', None),
        ('連不上', {'http': [['down', 'http://127.0.0.1:1/', False]]}, 2, 'ERROR', None),
        ('200 但內容不對', {'base': base, 'http': [['good', '/good', False, 'absent']]},
         2, 'FAIL', None),
        ('全綠', {'base': base, 'http': [['good', '/good', False, 'ok']],
                  'cmd': [['fine', [sys.executable, '-c', 'pass']]]}, 0, 'PASS', None),
        ('缺憑證（預設）', {'base': base, 'secret_file': 'empty.env',
                            'http': [['needs', '/good', True]]}, 0, 'SKIP', None),
        ('缺憑證（--strict）', {'base': base, 'secret_file': 'empty.env', 'argv': ['--strict'],
                                'http': [['needs', '/good', True]]}, 3, 'SKIP', None),
        ('缺憑證但列進 OPTIONAL', {'base': base, 'secret_file': 'empty.env',
                                   'argv': ['--strict'], 'optional': ['needs'],
                                   'http': [['needs', '/good', True]]}, 0, 'SKIP', None),
        ('未填 CHECKS', {}, 0, 'NOT_CONFIGURED', None),
        ('祕密遮罩', {'secret_file': 'real.env', 'cmd': [['leak', leak]]},
         0, '***', 'supersecretvalue'),
    )
    # R04：跨 stdout 300／stderr 200 摘要邊界，以及換行先於遮罩的組合。
    for stream, size in (('stdout', 290), ('stderr', 190)):
        argv = [sys.executable, '-c', 'import sys; sys.%s.write("x"*%d+"supersecretvalue")' % (stream, size)]
        cases += ((stream + ' 邊界遮罩', {'secret_file': 'real.env', 'cmd': [['boundary', argv]]},
                   0, '***', 'supersecr'),)
    bad = []
    try:
        for name, cfg, want_rc, want_in, forbid in cases:
            r = run([sys.executable, '-X', 'utf8', 'driver.py', json.dumps(cfg)], cwd=work)
            if r.returncode != want_rc:
                bad.append('%s：期望 exit %d，實得 %d（%s）'
                           % (name, want_rc, r.returncode,
                              r.stdout.strip().replace('\n', ' / ')[:70] or r.stderr[:70]))
            elif want_in not in r.stdout:
                bad.append('%s：輸出裡沒有「%s」（%s）'
                           % (name, want_in, r.stdout.strip()[:70]))
            elif forbid and forbid in r.stdout:
                bad.append('%s：祕密原文出現在輸出裡' % name)
        original_script = read_lf(work / 'verify_state.py')
        old_script = original_script.replace('mask(p.stdout)', 'p.stdout').replace('mask(p.stderr)', 'p.stderr')
        write_lf(work / 'verify_state.py', old_script)
        cfg = cases[-2][1]
        r = run([sys.executable, '-X', 'utf8', 'driver.py', json.dumps(cfg)], cwd=work)
        if 'supersecr' not in r.stdout:
            bad.append('R04 負向測試沒有重現摘要邊界洩出前綴')
    finally:
        srv.shutdown()
        srv.server_close()
        shutil.rmtree(work, ignore_errors=True)
    if bad:
        record('FAIL', 'verify_state 失敗訊號', '；'.join(bad[:4]))
        return False
    record('OK', 'verify_state 失敗訊號',
           '%d 個情境實跑：非零退出與 HTTP 失敗讓結束碼非零、連不上算 ERROR、'
           '200 但內容不對也算 FAIL、缺憑證是 SKIP（--strict 才非零，OPTIONAL 放行）、'
           '未填仍回 0、祕密有遮罩' % len(cases))
    return True


# ── 交接快照檢查（F08）──────────────────────────────────────────────────
# 連結誤報的 fixture：三種「看起來像連結但不是」的寫法都不該被報成死連結。
LINK_FIXTURE = """\
# 連結誤報測試

> 最後更新：2026-11-02

圍欄裡的程式碼範例不是連結：

```python
print('[x](does-not-exist.md)')
```

行內的 `[y](also-missing.md)` 也不是。

真的連結要解析得對：[說明](README.md)、[帶 title](README.md "說明")、
[角括號](<README.md>)。
"""


def step_snapshot_guard(dest):
    """check_docs 交接快照與連結檢查裡「同組情境」沒涵蓋的部分（查核報告 F08）。

    刪檔、缺章節與工作中欄位的正反例在「來源／產物交接快照同組情境」。這裡守：
    超行與 `--docs-only` 開關、章節重複與欄位重複的訊息、R07 stage 集合、R08／R09 與
    把守門拿掉的負向變異，以及連結不誤報、真的死連結仍要抓到。
    """
    handoff = dest / 'HANDOFF.md'
    original = handoff.read_text(encoding='utf-8')
    # 放在根目錄：fixture 裡那三個「真的連結」指向 README.md，放到 docs/ai-notes/
    # 底下會解析不到，那會變成 fixture 自己製造的死連結（第一版就是這樣誤判）。
    probe = dest / 'link-probe.md'

    def check(args=()):
        git(['add', '-A'], dest)
        return run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', *args], cwd=dest)

    bad = []
    try:
        # R07：未追蹤新文件先 stage 後才能進提交驗證集合。
        write_lf(probe, '[dead](missing-r07.md)\n')
        git(['add', '--', probe.name], dest)
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=dest)
        if r.returncode != 2 or 'missing-r07.md' not in r.stdout:
            bad.append('R07 新增文件 stage 後沒抓到死連結')
        write_lf(probe, '[good](README.md)\n')
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=dest)
        if r.returncode != 2 or '[index]' not in r.stdout:
            bad.append('R07 工作樹好內容遮住 index 壞內容')
        # 移除 index 門檻會錯誤通過；驗證新守門確實改變行為。
        checker = dest / 'tools/check_docs.py'
        checker_original = read_lf(checker)
        write_lf(checker, checker_original.replace('if args.staged:', 'if False:'))
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=dest)
        if r.returncode != 0:
            bad.append('R07 負向測試沒重現部分 stage 被錯放')
        write_lf(checker, checker_original)
        probe.unlink()
        git(['add', '-A'], dest)

        for value in ('`machine` ／ ``', '`machine` ／ `   `', '`` ／ `Codex CLI`'):
            write_lf(handoff, original.replace('無（已交棒）', value))
            r = check()
            if r.returncode != 2:
                bad.append('R08 空機器／工具欄沒擋下：' + value)
        write_lf(handoff, original.replace('無（已交棒）', '`machine` ／ ``'))
        write_lf(checker, checker_original.replace('or not fields[1] ', ''))
        if check().returncode != 0:
            bad.append('R08 負向測試沒重現空工具欄被放行')
        write_lf(checker, checker_original)
        write_lf(handoff, original)

        spaced = dest / 'existing file.md'
        write_lf(spaced, '# Existing\n')
        write_lf(probe, '[valid](<existing file.md> "title")\n')
        r = check()
        if r.returncode:
            bad.append('R09 角括號／空白／title 合用誤報')
        old_order = checker_original.replace(
            "    link = TITLE_RE.sub('', link).strip()\n    if link.startswith('<') and link.endswith('>'):\n        link = link[1:-1].strip()",
            "    if link.startswith('<') and link.endswith('>'):\n        link = link[1:-1].strip()\n    else:\n        link = TITLE_RE.sub('', link).strip()")
        write_lf(checker, old_order)
        if check().returncode != 2:
            bad.append('R09 負向測試沒重現角括號 title 誤報')
        write_lf(checker, checker_original)
        spaced.unlink()
        probe.unlink()

        # --docs-only 用「超行」驗，不用「刪檔」：刪掉 HANDOFF.md 會讓 README／AGENTS
        # 指向它的連結變成**真的**死連結，於是 --docs-only 照樣 exit 2——那不是開關沒用。
        write_lf(handoff, original.rstrip('\n') + '\n' + '- 填行\n' * 90)
        r = check()
        if r.returncode != 2 or '80 行' not in r.stdout:
            bad.append('超過 80 行沒被擋下（exit %d）' % r.returncode)
        r = check(['--docs-only'])
        if r.returncode != 0:
            bad.append('--docs-only 下仍然 exit %d（這個開關要真的關掉第 7 項）'
                       % r.returncode)

        # 章節重複＝往下疊成日誌（B6 禁止）。2026-11-02 在真專案上量到一份有兩個
        # 同名章節（標題後面加日期）——所以比對開頭、罰重複，而不是罰標題的措辭。
        write_lf(handoff, original + '\n## 目前進度（更早）\n\n- 舊的\n')
        r = check()
        if r.returncode != 2 or '不要往下疊' not in r.stdout:
            bad.append('章節重複沒被擋下（exit %d）' % r.returncode)

        write_lf(handoff, original.replace('- **交棒者**', '- **交接時間**', 1))
        r = check()
        if r.returncode != 2 or '交棒者' not in r.stdout:
            bad.append('欄位重複／缺漏沒被擋下（exit %d）' % r.returncode)
        write_lf(handoff, original)

        write_lf(probe, LINK_FIXTURE)
        r = check()
        if r.returncode != 0:
            bad.append('連結誤報：程式碼範例／帶 title／角括號被當成死連結（exit %d：%s）'
                       % (r.returncode, r.stdout.strip()[:90]))
        write_lf(probe, LINK_FIXTURE + '\n[真的死連結](no-such-file.md)\n')
        r = check()
        if r.returncode != 2 or 'no-such-file.md' not in r.stdout:
            bad.append('真的死連結沒被抓到（exit %d）——不誤報不能靠什麼都不報換'
                       % r.returncode)
    finally:
        write_lf(handoff, original)
        probe.unlink(missing_ok=True)
        git(['add', '-A'], dest)

    if bad:
        record('FAIL', '交接快照檢查', '；'.join(bad[:4]))
        return False
    record('OK', '交接快照檢查',
           '超 80 行／章節重複／欄位重複都 exit 2，--docs-only 真的關得掉'
           '（用超行情境驗，刪檔會連帶產生真的死連結）；'
           '程式碼範例、帶 title 與角括號連結不誤報，真的死連結仍 exit 2；R07 stage 集合／部分 stage、R08 空欄、R09 空白角括號 title 組合與負向變異')
    return True


def facts_python_probes(bash, hook, work):
    # PATH 有 python3 卻不能執行，且失敗的 stdout 不得混進下一次的 JSON。
    wrapper = '''
python3() { printf '%s\\n' 'unusable python3'; return 49; }
python() {
    [ "$BOOTSTRAP_VERIFY_DISABLE_PYTHON" != 1 ] || return 49
    "$BOOTSTRAP_VERIFY_PYTHON" "$@"
}
. "$1"
'''
    cmd = [bash, '-c', wrapper, 'facts-python-probe', hook]
    env = dict(GIT_ENV, BOOTSTRAP_VERSION_CHECK='off', BOOTSTRAP_VERIFY_PYTHON=sys.executable)
    start_payload = '{}'
    fallback = run(cmd, cwd=work, stdin=start_payload, env=dict(env, BOOTSTRAP_VERIFY_DISABLE_PYTHON='0'))
    unavailable = run(cmd, cwd=work, stdin=start_payload, env=dict(env, BOOTSTRAP_VERIFY_DISABLE_PYTHON='1'))
    bad = []
    if fallback.returncode != 0 or facts_output_problems(fallback.stdout) or fallback.stderr:
        bad.append('python3 執行失敗時，未由 python 輸出純 SessionStart JSON')
    if (unavailable.returncode != 1 or unavailable.stdout
            or 'Git facts unavailable:' not in unavailable.stderr):
        bad.append('兩個 Python 指令都失敗時，未以 stderr 與 exit 1 回報')
    return bad


def step_misc(dest, work=None):
    ok = True
    for label, rel in (('settings.json', '.claude/settings.json'),
                       ('.codex/hooks.json', '.codex/hooks.json')):
        try:
            json.loads((dest / rel).read_text(encoding='utf-8'))
            record('OK', f'{label} 合法 JSON')
        except Exception as e:
            record('FAIL', f'{label} 合法 JSON', str(e))
            ok = False

    # VERSION 檔是落後偵測的依據：各專案抓它跟自己的 source 標記比。它跟部署包開頭
    # 「版本：**…**」那一行必須一致——不一致的話偵測就會說謊，而那種謊沒有任何徵兆：
    # 落後的專案會以為自己是最新的，正好是這個機制要解決的問題本身。
    kit_ver = re.search(r'^> 版本：\*\*([^*]+)\*\*', kit_text(), re.M)
    vfile = ROOT / 'VERSION'
    if not vfile.exists():
        record('FAIL', 'VERSION 檔', '不存在——落後偵測沒有依據')
        ok = False
    elif not kit_ver:
        record('FAIL', 'VERSION 檔', '部署包找不到「> 版本：**…**」那一行')
        ok = False
    elif vfile.read_text(encoding='utf-8').strip() != kit_ver.group(1).strip():
        record('FAIL', 'VERSION 檔', 'VERSION=%s 但部署包版本行=%s'
               % (vfile.read_text(encoding='utf-8').strip(), kit_ver.group(1).strip()))
        ok = False
    else:
        record('OK', 'VERSION 檔', '與部署包版本行一致（%s）' % kit_ver.group(1).strip())

    step_table_freshness()
    step_tool_prose(dest)
    step_python_floor(dest)
    step_claims(dest)
    step_state_exit(dest)
    step_snapshot_guard(dest)

    r = run([sys.executable, '-X', 'utf8', 'tools/verify_state.py'], cwd=dest)
    if r.returncode == 0 and 'NOT_CONFIGURED' in r.stdout:
        record('OK', 'verify_state.py', '未填檢查項時印 NOT_CONFIGURED')
    else:
        record('FAIL', 'verify_state.py', f'exit {r.returncode}：{r.stdout.strip()[:120]}')
        ok = False

    bash = find_bash()
    if not bash:
        record('SKIP', 'git-freshness.sh', '找不到看得懂 Windows 路徑的 bash')
    elif work is None:
        # 只有 git init／add、還沒有任何 commit 的骨架，這支 hook 判斷不了就靜默放行（設計如此），
        # 拿它來測等於什麼都沒測。所以只在 hook fixture（有 origin、有 commit）上驗。
        record('SKIP', 'git-freshness.sh', 'hook fixture 沒建起來，缺少有 origin 與 commit 的 repo 可測')
    else:
        hook = '.claude/hooks/git-freshness.sh'
        r = run([bash, hook], cwd=work)
        bad = facts_output_problems(r.stdout)
        # 儀器自檢：JSON 仍有效時，多一行指示、多到六行，都要被看出來。
        if not bad:
            planted = []
            for extra in ('\n[git-check] 先走 handoff skill', '\n[facts] x' * 3):
                mutant = json.loads(r.stdout)
                mutant['hookSpecificOutput']['additionalContext'] += extra
                planted.append(facts_output_problems(json.dumps(mutant, ensure_ascii=False)))
            if not all(planted):
                bad.append('負向測試未重現：多一行指示或超過五行應該被擋')
        bad.extend(facts_python_probes(bash, hook, work))
        if r.returncode == 0 and not bad:
            record('OK', 'git-freshness.sh',
                   'SessionStart JSON 只含 [facts]、最多五行；超出規格會被擋，python3 失敗會回退，兩者皆失敗明確回報')
        else:
            record('FAIL', 'git-freshness.sh',
                   f'exit {r.returncode}：{"；".join(bad)}：{(r.stdout + r.stderr).strip()[:160]}')
            ok = False
    return ok


def flow_contract_problems(skill):
    """F11：檢查結構與關鍵操作契約，不宣稱測到模型遵循。"""
    bad = []
    table = re.search(r'### A／B／C 狀態轉移.*?(?=\n\*\*證據的範圍)', skill, re.S)
    expected = {
        '待接棒': ('A1', 'fetch exit 0', 'ahead=0、behind=0', '停下'),
        '已定位': ('A4', '結束碼', 'A5 開工成功後'),
        '開工中': ('HANDOFF', 'push exit 0', 'origin', '停止修改'),
        '工作中': ('B7 → B8', 'exit 0', 'upstream', '工作中'),
        '待交棒': ('B7', 'exit 0', '無（已交棒）', '不可發布'),
        '已交棒': ('B9', 'origin', '重走 A'),
    }
    rows = {}
    if table:
        for line in table.group().splitlines():
            if line.startswith('|'):
                cells = [c.strip() for c in line.strip('|').split('|')]
                if cells[0] in expected:
                    if cells[0] in rows:
                        bad.append('重複狀態：' + cells[0])
                    rows[cells[0]] = cells
    for state, tokens in expected.items():
        cells = rows.get(state, [])
        if len(cells) != 5 or not all(cells) or any(t not in ' '.join(cells) for t in tokens):
            bad.append('狀態缺前提／操作／證據／失敗處理：' + state)

    contracts = (
        ('### A1 ', 'ahead-only（ahead > 0、behind = 0） | **停**'),
        ('### A1 ', 'fetch 失敗（非零退出） | **停**'),
        ('### A1 ', 'HEAD...@{upstream}'),
        ('### A2 ', '切換到待續分支後重跑 A1'),
        ('### A4 ', '此步只記錄差異與結束碼、不修改專案檔案'),
        ('### A4 ', '開工標記 push 成功後'),
        ('### A5 ', '這是開工 push 例外'),
        ('### A5 ', 'push 成功後重讀 origin'),
        ('### B1 ', '動任何檔案、提交或推送前先核對占用'),
        ('### B1 ', '已確認推送的完整標記比對'),
        ('### B1 ', '無法確認歸屬就停下'),
        ('### B1 ', '使用者明確確認舊標記與工作屬於自己時，照 `mode-a-stop.md` A2.5 選項 2 接手'),
        ('### B7 ', 'B6 覆寫完成後'),
        ('### B7 ', 'tools/check_docs.py'),
        ('### B7 ', 'exit 0 才提交發布'),
        ('### B7 ', 'B3 後改過，連 B3 也重跑'),
        ('### B8 ', '比對 B1 的占用分支 SHA 與完整標記'),
        ('### B8 ', '兩者任一對不上就停下，不推送'),
        ('### B8 ', 'fetch 失敗 → **停下**'),
        ('## C.', '保留本 session 的「工作中」標記'),
        ('## C.', '不走 B6 的釋出標記與 B9 的交棒計數'),
    )
    for heading, token in contracts:
        part = skill.split(heading, 1)[-1].split('\n### ', 1)[0].split('\n## ', 1)[0]
        if heading not in skill or token not in part:
            bad.append(heading + '缺契約：' + token)
    mode = skill.split('## 判斷模式', 1)[-1].split('### A／B／C', 1)[0]
    # 交棒只由使用者決定（Q31），不能退回「準備 push 預設先做 B」。
    for token in ('使用者沒要求就不得自行交棒', 'A5 開工標記與 C 中途安全點都不宣稱交棒'):
        if token not in mode:
            bad.append('入口缺：' + token)
    b7 = skill.split('### B7 ', 1)[-1].split('### B8 ', 1)[0]
    stage_pos = b7.find('git diff --cached --name-only')
    verify_pos = b7.find('tools/check_docs.py --staged')
    if stage_pos < 0 or verify_pos < stage_pos:
        bad.append('R07 必須先檢視 stage 集合再執行 --staged 驗證')
    return bad


def step_flow_contract(dest, tmp):
    skill = skill_text(dest)
    bad = flow_contract_problems(skill)
    # 每種契約都故意拿掉一次，避免檢查器永遠回成功。
    mutations = ('| 待接棒 |', '| 已定位 |', '| 開工中 |', '| 工作中 |', '| 待交棒 |', '| 已交棒 |',
                 'ahead-only（ahead > 0、behind = 0）', 'fetch 失敗（非零退出）',
                 '切換到待續分支後重跑 A1', '此步只記錄差異與結束碼、不修改專案檔案',
                 '這是開工 push 例外', 'push 成功後重讀 origin', 'B6 覆寫完成後',
                 'B3 後改過，連 B3 也重跑', 'fetch 失敗 → **停下**',
                 '保留本 session 的「工作中」標記', '不走 B6 的釋出標記與 B9 的交棒計數',
                 '使用者沒要求就不得自行交棒', 'A5 開工標記與 C 中途安全點都不宣稱交棒')
    mutations += ('tools/check_docs.py --staged', 'git diff --cached --name-only',
                  '動任何檔案、提交或推送前先核對占用', '已確認推送的完整標記比對', '無法確認歸屬就停下',
                  '使用者明確確認舊標記與工作屬於自己時，照 `mode-a-stop.md` A2.5 選項 2 接手',
                  '比對 B1 的占用分支 SHA 與完整標記', '兩者任一對不上就停下，不推送')
    for token in mutations:
        mutated = skill.replace(token, '移除契約')
        if mutated == skill or not flow_contract_problems(mutated):
            bad.append('負向測試未擋：' + token)
    record('FAIL' if bad else 'OK', '協作狀態契約', '；'.join(bad) if bad else
           '六狀態與 A1／A2／A4／A5／B1／B7／B8／C 契約齊備；27 個負向測試通過，含 R07 stage 順序（不代表模型遵循）')

    bash = find_bash()
    if not bash:
        record('SKIP', 'Git 異常提示', '缺少可用 bash')
        return
    origin, work, peer = (tmp / n for n in ('flow-origin.git', 'flow-work', 'flow-peer'))
    def must(args, cwd=None):
        r = run(['git', *args], cwd=cwd)
        if r.returncode:
            raise RuntimeError('Git fixture 失敗：' + r.stderr)
        return r
    must(['init', '-q', '--bare', str(origin)])
    must(['init', '-q', '-b', 'main', str(work)])
    write_lf(work / 'file', 'init\n')
    must(['add', 'file'], work)
    must(['commit', '-qm', 'init'], work)
    must(['remote', 'add', 'origin', str(origin)], work)
    must(['push', '-qu', 'origin', 'main'], work)
    must(['clone', '-q', '-b', 'main', str(origin), str(peer)])
    write_lf(work / 'file', 'local\n')
    must(['commit', '-qam', 'local'], work)
    # 本 repo 的 repo-git-check.sh 是 3.10 的逐字副本（「本 repo 開場 hook」逐位元組比對），不重跑。
    scripts = [('部署 hook', read_lf(dest / '.claude/hooks/git-freshness.sh'))]
    issues = []
    # 2026-11-13（v3 D12）：部署出去的 hook 只報事實，「停下來」寫在 AGENTS.md 的共用規則 3；
    # 不准建議 rebase。
    facts_marks = {'ahead-only': '落後 origin/main 0 個 commit、領先 1 個',
                   'diverged': '落後 origin/main 1 個 commit、領先 1 個',
                   'fetch failure': 'fetch origin 失敗'}

    def deployed_ok(state, out):
        return facts_marks[state] in out and 'git pull --rebase' not in out and not facts_output_problems(out)

    def check_scripts(state):
        for name, source in scripts:
            path = tmp / 'flow-probe.sh'
            write_lf(path, source)
            r = run([bash, str(path)], cwd=work, env=tool_env(BOOTSTRAP_VERSION_CHECK='off'))
            if r.returncode or not deployed_ok(state, r.stdout):
                issues.append(name + ' ' + state + ' 沒有照實報出狀態，或給了 rebase 建議')
    check_scripts('ahead-only')
    write_lf(peer / 'file', 'remote\n')
    must(['commit', '-qam', 'remote'], peer)
    must(['push', '-q', 'origin', 'main'], peer)
    check_scripts('diverged')
    # 在真分岔 fixture 上植入舊建議，儀器必須辨識這是錯誤提示。
    old = scripts[0][1].replace('exit 0\n', 'echo "[facts] 開工前必須先整合（git pull --rebase）"\nexit 0\n')
    path = tmp / 'flow-old.sh'
    write_lf(path, old)
    r = run([bash, str(path)], cwd=work, env=tool_env(BOOTSTRAP_VERSION_CHECK='off'))
    if old == scripts[0][1] or deployed_ok('diverged', r.stdout):
        issues.append('負向測試未重現舊分岔建議')
    must(['remote', 'set-url', 'origin', str(tmp / 'missing-origin.git')], work)
    check_scripts('fetch failure')
    # 停下來的條件改住在 AGENTS.md 共用制度。
    agents = read_lf(dest / 'AGENTS.md')
    issues.extend(agents_stop_problems(agents))
    if not agents_stop_problems(agents.replace(AGENTS_STOP_TOKENS[0], '移除條件')):
        issues.append('負向測試未重現：拿掉停止條件應該被擋')
    record('FAIL' if issues else 'OK', 'Git 異常提示', '；'.join(issues) if issues else
           '部署 hook 實跑 ahead-only／分岔／fetch 失敗都照實報出、不建議 rebase，AGENTS.md 共用制度有停止條件；'
           '本 repo hook 是它的逐字副本；植入 rebase 建議與拿掉停止條件兩個負向測試')


def core_priority_problems(skill, protocol=None, readme=None):
    """2026-11-17（v3 Q41）起部署包不再產出交接協定，protocol 只在測舊實例時才給。"""
    bad = []
    for name, text in (('skill', skill), ('protocol', protocol)):
        if text is None:
            continue
        if text.count('**核心優先序：SKILL.md**') != 1:
            bad.append(name + ' 核心優先序不唯一或不一致')
        for token in ('不同步的專案實例', '升級時須人工遷移', '不得在單一專案就地修改共用 skill',
                      'override', '使用者明確指示仍優先'):
            if token not in text:
                bad.append(name + ' 缺 ' + token)
        if re.search(r'兩者衝突時.*(?:以協定為準|以本檔為準)', text):
            bad.append(name + ' 恢復舊優先序')
    if readme is not None:
        plain = readme.replace('**', '')
        if '核心優先序：SKILL.md' not in plain or '使用者明確指示仍優先' not in plain:
            bad.append('README 缺核心優先序或使用者優先宣告')
        if re.search(r'兩者衝突(?:時)?.*以協定為準', plain):
            bad.append('README 恢復舊優先序')
    return bad


def step_core_priority(dest, tmp):
    import sync_project as syncer
    skill = skill_text(dest)
    bad = core_priority_problems(skill)
    readme = read_lf(ROOT / 'README.md')
    bad.extend(core_priority_problems(skill, readme=readme))
    for mutant in (readme.replace('核心優先序：SKILL.md', '舊優先序'),
                   readme + '\n兩者衝突以協定為準。\n',
                   readme + '\n兩者衝突時**以協定為準**。\n'):
        if not core_priority_problems(skill, readme=mutant):
            bad.append('R06 README 負向測試沒擋住反向或缺失宣告')
    for token in ('**核心優先序：SKILL.md**', '升級時須人工遷移', '不得在單一專案就地修改共用 skill'):
        if not core_priority_problems(skill.replace(token, '舊規則')):
            bad.append('負向測試未擋 ' + token)
    # 不依賴 Git 歷史也可驗：把 skill 頂端的舊宣告還原。
    if not core_priority_problems('兩者衝突時**以協定為準**，並就地修正本檔。\n' + skill):
        bad.append('反向優先序未擋')
    project = tmp / 'priority-project'
    shutil.copytree(dest, project)
    write_lf(project / 'docs/ai-notes/handover-protocol.md', '舊協定，專案自訂規則保留\n')
    plan = syncer.sync(project, dest)
    if not any('MIGRATE' in m for m in plan.msgs) or not any('核心版本' in m for m in plan.msgs):
        bad.append('同步未列核心版本與人工遷移需求')
    if any(rel == 'docs/ai-notes/handover-protocol.md' for _, _, rel in plan.writes):
        bad.append('同步覆蓋專案協定')
    record('FAIL' if bad else 'OK', '核心與實例優先序', '；'.join(bad) if bad else
           'skill 與 README 宣告一致、override 範圍明確、7 個負向測試；'
           '同步對舊實例列核心版本與 MIGRATE，不改寫')


def coordination_problems(skill):
    """2026-11-17（v3 Q41）：交接協定移出部署包，只剩 skill 的 A2.5 與 A5 要帶著這些邊界。"""
    bad = []
    a25 = skill.split('### A2.5 ', 1)[-1].split('### A3 ', 1)[0]
    a5 = skill.split('### A5 ', 1)[-1].split('### A6 ', 1)[0]
    for label, text, tokens in (
        ('A2.5', a25, ('接力式 single-writer', '協調訊號，不是互斥鎖', '同一工作樹不得同時有兩個 writer',
                       '不得自動奪取 writer', '不是穩定 owner token', '同時記錄觀測到的', '原子 claim 尚未實作', '未做並行實驗')),
        ('A5', a5, ('協調訊號，不是互斥鎖', 'SHA 與 A2.5 觀測值不同就停止', '不能當一般 merge 衝突合併', '不等於取得原子 claim'))):
        for token in tokens:
            if token not in text:
                bad.append(label + ' 缺 ' + token)
    return bad


def step_coordination(dest):
    skill = skill_text(dest)
    bad = coordination_problems(skill)
    probes = ('協調訊號，不是互斥鎖', '不得自動奪取 writer', '原子 claim 尚未實作', '未做並行實驗')
    for token in probes:
        if not coordination_problems(skill.replace(token, '移除邊界')):
            bad.append('負向測試未擋 ' + token)
    record('FAIL' if bad else 'OK', '接力協調邊界', '；'.join(bad) if bad else
           'A2.5／A5 明列協調範圍、SHA 比對與禁止自動奪取；4 個負向測試，不代表並行互斥實測')


def sync_owner_cli_problems(cli, folder, gen, scenarios=None):
    """R03：真 local bare origin；成功流程與拒絕情境都檢查檔案內容。"""
    bad = []
    for scenario in (scenarios or ('own', 'other', 'ahead', 'behind', 'diverged', 'offline', 'no-upstream', 'local-marker')):
        work = folder / ('owner-' + scenario)
        shutil.copytree(gen, work, ignore=shutil.ignore_patterns('.git'))
        step_fill(work, report=False)
        wiring = work / '.codex/hooks.json'
        write_lf(wiring, '{"hooks":{}}\n')
        def must(args, cwd=work):
            r = git(args, cwd)
            if r.returncode:
                raise RuntimeError('owner fixture: ' + r.stderr)
            return r
        must(['init', '-q', '-b', 'main'])
        must(['add', '.'])
        must(['commit', '-qm', 'fixture'])
        owner = fixture_origin(work)
        handoff = work / 'HANDOFF.md'
        text = read_lf(handoff).replace('無（已交棒）', owner)
        write_lf(handoff, text)
        must(['commit', '-qam', 'A5 own claim'])
        must(['push', '-q', 'origin', 'HEAD'])
        if scenario in ('behind', 'diverged'):
            peer = folder / ('peer-' + scenario)
            must(['clone', '-q', str(work.parent / (work.name + '-origin.git')), str(peer)])
            # bare HEAD 的預設分支可能不是 main，明確切換。
            must(['checkout', '-q', 'main'], peer)
            write_lf(peer / 'HANDOFF.md', read_lf(peer / 'HANDOFF.md').replace(owner, '`peer` ／ `Codex CLI`'))
            must(['commit', '-qam', 'peer busy'], peer)
            must(['push', '-q', 'origin', 'HEAD'], peer)
        if scenario in ('ahead', 'diverged'):
            write_lf(work / 'local-note', 'local commit\n')
            must(['add', 'local-note'])
            must(['commit', '-qm', 'local ahead'])
        if scenario == 'offline':
            must(['remote', 'set-url', 'origin', str(folder / 'absent-origin.git')])
        if scenario == 'no-upstream':
            must(['branch', '--unset-upstream'])
        if scenario == 'local-marker':
            write_lf(handoff, text.replace(owner, '`peer` ／ `Codex CLI`'))
        before = {str(p.relative_to(work)): p.read_bytes() for p in work.rglob('*')
                  if p.is_file() and '.git' not in p.relative_to(work).parts}
        if scenario == 'own':
            for invalid in ([str(work), '--write'], ['--all', '--root', str(folder), '--write'],
                            [str(work), '--write', '--owner', '無（已交棒）']):
                if run(cli + invalid).returncode == 0 or wiring.read_bytes() != before[str(wiring.relative_to(work))]:
                    bad.append('R03 無 owner／批次／空閒 writer 未拒絕')
        args = [str(work), '--codex-only', '--write', '--owner',
                '`someone-else` ／ `Codex CLI`' if scenario == 'other' else owner, '--allow-dirty']
        r = run(cli + args)
        if scenario != 'own':
            after = {str(p.relative_to(work)): p.read_bytes() for p in work.rglob('*')
                     if p.is_file() and '.git' not in p.relative_to(work).parts}
            if r.returncode == 0 or after != before:
                bad.append('R03 未拒絕或非零寫入：' + scenario)
            continue
        if r.returncode or read_lf(wiring) != read_lf(gen / '.codex/hooks.json'):
            bad.append('R03 自身 A5 claim 無法同步')
            continue
        # B7／B8：驗最終文件，明確 stage，發布清標記快照。
        write_lf(handoff, read_lf(handoff).replace(owner, '無（已交棒）'))
        must(['add', 'HANDOFF.md', '.codex/hooks.json'])
        checked = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=work)
        if checked.returncode:
            bad.append('R03 同步後 B7 文件檢查失敗：' + checked.stdout)
        must(['commit', '-qm', 'B7 final snapshot'])
        must(['fetch', '-q', 'origin'])
        must(['push', '-q', 'origin', 'HEAD'])
        if '無（已交棒）' not in must(['show', 'origin/main:HANDOFF.md']).stdout or must(['status', '--porcelain']).stdout:
            bad.append('R03 B8 未清標記或工作樹不乾淨')
    return bad


def inventory_cli_problems(cli, folder, normal):
    """R05：active 失效不能冒充成功；archived 與重複路徑另驗。"""
    bad = []
    inv = folder / 'active-cases.json'
    active = {'path': str(normal), 'status': 'active'}
    missing = {'path': 'missing-active', 'status': 'active'}
    cases = [([active, missing], False),
             ([active, dict(missing, status='archived')], True),
             ([missing], False), ([active, active], False)]
    for i, (items, success) in enumerate(cases):
        write_lf(inv, json.dumps(items))
        r = run(cli + ['--inventory', str(inv)])
        if (r.returncode == 0) != success or (not success and '全部都已經是' in r.stdout):
            bad.append('R05 inventory CLI 結果錯誤 ' + str(i))
        if i == 0 and ('FAIL' not in r.stdout or '沒有完成' not in r.stdout):
            bad.append('R05 混合 active 失敗未列入彙總')
    return bad


def step_sync_scope(dest, tmp):
    import sync_project as sp
    folder = tmp / 'scope'
    folder.mkdir()
    folder = folder.resolve()  # Windows TEMP 可能是 8.3 短路徑；決策輸出已正規化。
    bad = []
    def must(args, cwd=None):
        r = run(['git', *args], cwd=cwd)
        if r.returncode:
            raise RuntimeError('scope fixture: ' + r.stderr)
        return r
    def project(name):
        p = folder / name
        shutil.copytree(dest, p, ignore=shutil.ignore_patterns('.git'))
        must(['init', '-q', '-b', 'main'], p)
        must(['add', '.'], p)
        must(['commit', '-qm', 'fixture'], p)
        return p
    normal = project('normal-worktrees-name')
    archived = project('archived')
    owner = fixture_origin(normal)
    fixture_origin(archived)
    linked = folder / 'arbitrary-checkout'
    must(['worktree', 'add', '-q', '-b', 'peer', str(linked)], normal)
    decisions = dict(sp.discover_decisions([folder], ['archived']))
    if decisions.get(normal, 'missing') is not None:
        bad.append('名字含 worktrees 的普通目錄被排除')
    if 'worktree' not in (decisions.get(linked) or ''):
        bad.append('任意名稱的真 worktree 未排除')
    if decisions.get(archived) != '明確排除':
        bad.append('明確排除未列原因')
    inv = folder / 'inventory.json'
    write_lf(inv, json.dumps([{'path': normal.name, 'status': 'active'},
                             {'path': archived.name, 'status': 'archived'}]))
    if dict(sp.inventory_decisions(inv)).get(archived) != 'inventory 已完結':
        bad.append('已完結專案未排除')
    cli = [sys.executable, '-X', 'utf8', str(ROOT / 'tools/sync_project.py')]
    r = run(cli + ['--inventory', str(inv)])
    if r.returncode or 'INCLUDE' not in r.stdout or 'EXCLUDE' not in r.stdout or '全域' not in r.stdout:
        bad.append('inventory CLI 範圍／排除原因未列出')
    bad.extend(inventory_cli_problems(cli, folder, normal))
    # 負向測試恢復「active 失效當正常排除」，走相同真 CLI 案例。
    mutant = folder / 'sync-mutant.py'
    source = read_lf(ROOT / 'tools/sync_project.py')
    write_lf(mutant, source.replace("reason = 'inventory active 無法處理：' + reason", 'reason = reason'))
    wrapper = ('import sys; sys.path.insert(0, %r); __file__=%r; '
               'exec(compile(open(%r, encoding="utf-8").read(), __file__, "exec"))'
               % (str(ROOT / 'tools'), str(ROOT / 'tools/sync_project.py'), str(mutant)))
    if not inventory_cli_problems([sys.executable, '-X', 'utf8', '-c', wrapper], folder, normal):
        bad.append('R05 負向測試沒抓到 active 失效被排除')
    bad.extend(sync_owner_cli_problems(cli, folder, dest))
    owner_mutant = folder / 'owner-mutant.py'
    first = source.index('def sync_owner_check(')
    last = source.index('\n\ndef preflight(', first)
    write_lf(owner_mutant, source[:first] +
             "def sync_owner_check(project, owner=None, writing=False):\n    return git_output(project, 'rev-parse', 'HEAD')\n" + source[last:])
    owner_wrapper = ('import sys; sys.path.insert(0, %r); __file__=%r; '
                     'exec(compile(open(%r, encoding="utf-8").read(), __file__, "exec"))'
                     % (str(ROOT / 'tools'), str(ROOT / 'tools/sync_project.py'), str(owner_mutant)))
    negative_folder = folder / 'owner-negative'
    negative_folder.mkdir()
    if not sync_owner_cli_problems([sys.executable, '-X', 'utf8', '-c', owner_wrapper], negative_folder, dest, ('other',)):
        bad.append('R03 移除資格檢查的 CLI 負向測試沒抓到錯誤寫入')
    write_lf(normal / 'HANDOFF.md', '- **工作中**：' + owner + '\n')
    must(['commit', '-qam', 'A5 claim'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    # 真的寫入入口：dirty、占用、客製漂移都必須零寫入、非零退出。
    skill = normal / '.claude/skills/handoff/SKILL.md'
    original = read_lf(skill)
    def rejected(label, extra=()):
        before = skill.read_bytes()
        common = (normal / sp.SURGICAL).read_bytes()
        r = run(cli + [str(normal), '--write', '--owner', owner, *extra])
        if r.returncode == 0 or skill.read_bytes() != before or (normal / sp.SURGICAL).read_bytes() != common or label not in r.stdout:
            bad.append(label + ' preflight 沒擋／已有寫入')
    write_lf(normal / 'note', 'unfinished\n')
    rejected('dirty')
    (normal / 'note').unlink()
    write_lf(normal / 'HANDOFF.md', '- **工作中**：`peer` ／ `Codex CLI`\n')
    must(['commit', '-qam', 'busy'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    rejected('占用')
    write_lf(normal / 'HANDOFF.md', '- **工作中**：' + owner + '\n')
    write_lf(skill, original + '\nproject custom rule\n')
    must(['commit', '-qam', 'custom'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    rejected('客製漂移')
    r = run(cli + [str(normal), '--write', '--owner', owner, '--accept-drift', '.claude/skills/handoff/SKILL.md'])
    if r.returncode or 'project custom rule' in read_lf(skill):
        bad.append('明確接受單檔漂移後仍無法同步')
    must(['add', '.'], normal)
    must(['commit', '-qm', 'synced'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    checker = normal / sp.SURGICAL
    original_checker = read_lf(checker)
    write_lf(checker, original_checker + '\n# project custom implementation\n')
    must(['commit', '-qam', 'custom checker'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    rejected('客製漂移')
    write_lf(checker, original_checker)
    # 反向測試：把新 preflight 拿掉，客製漂移會真的被覆蓋。
    write_lf(skill, original + '\nproject custom rule\n')
    plan = sp.sync(normal, dest)
    done, error = sp.apply_plan(plan)
    if error or '.claude/skills/handoff/SKILL.md' not in done or 'project custom rule' in read_lf(skill):
        bad.append('移除 preflight 的負向測試未重現覆蓋')
    record('FAIL' if bad else 'OK', '同步範圍與前置檢查', '；'.join(bad) if bad else
           '真 worktree／含 worktrees 普通目錄／已完結 inventory；R03 自身 writer→同步→B7→B8、七種資格拒絕與負向變異；R05 active 失效、archived、重複路徑與 CLI 負向變異；dirty／占用／整份檔與共用程式漂移拒絕且零寫入')


def deployment_order_problems(skill, readme):
    """本機驗收、首次提交、發布的順序（2026-11-18 起在 mode-0.md 的 0-5，決策書 v3 Q49）。

    部署包第 4 節的指令搬進了 skill：安裝後由 agent 做，部署包不在專案裡。
    """
    bad = []
    section = skill.split('### 0-5 ', 1)[-1].split('### 0-6 ', 1)[0] if '### 0-5 ' in skill else ''
    sequence = ('本機驗收後才首次發布', '`.gitignore` 必須先就位再 `git add`', 'git add <路徑>',
                'git check-ignore', 'tools/check_docs.py', 'git commit -m', 'gh repo create')
    positions = [section.find(token) for token in sequence]
    if any(i < 0 for i in positions) or positions != sorted(positions):
        bad.append('本機驗收／首次提交／發布順序缺失或反轉')
    told = section.replace('不用 `git add .` 或 `git add -A`', '')
    if 'git add .' in told or 'git add -A' in told:
        bad.append('0-5 叫人整批 git add')
    if 'bootstrap.py' not in readme or '本機驗收' not in readme:
        bad.append('README 入口沒指向 bootstrap.py 或沒要求先本機驗收')
    return bad


def deployment_index_problems(work, paths):
    bad = []
    for path in paths:
        if git(['check-ignore', '--no-index', '-q', '--', path], work).returncode:
            bad.append('未忽略 ' + path)
        if git(['ls-files', '--', path], work).stdout.strip():
            bad.append('已進索引 ' + path)
    return bad


def step_deployment_lifecycle(tmp):
    work, remote, clone = (tmp / n for n in ('deploy-life', 'deploy-origin.git', 'deploy-clone'))
    extract(work)
    # manifest 是訪談輸入與預期的單一 fixture，全部是假資料，不需要外部帳戶。
    manifest = dict(ANSWERS, SECRETS='`credentials/odd-session.fixture`、`keys/測試 key.fixture`',
                    RUNTIME_DIRS='`run outputs/`')
    if not step_fill(work, manifest, report=False):
        record('FAIL', '部署生命週期', '訪談替換失敗')
        return
    paths = ['credentials/odd-session.fixture', 'keys/測試 key.fixture', 'run outputs/state.fixture']
    for name in paths:
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        write_lf(path, 'synthetic deployment fixture only\n')
    def must(args, cwd=None):
        r = run(args, cwd=cwd)
        if r.returncode:
            raise RuntimeError('deployment fixture: ' + r.stderr + r.stdout)
        return r
    must(['git', 'init', '-q', '-b', 'main', str(work)])
    must(['git', 'add', '.'], work)
    kit = kit_text()
    skill = skill_text(work)
    bad = deployment_order_problems(skill, read_lf(ROOT / 'README.md'))
    for invalid in (' !fixture', '` !fixture`'):
        try:
            ignore_rules(invalid)
        except ValueError:
            pass
        else:
            bad.append('反向納入祕密的 ignore 輸入未拒絕')
    must([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], work)
    state = must([sys.executable, '-X', 'utf8', 'tools/verify_state.py'], work)
    if 'NOT_CONFIGURED' not in state.stdout:
        bad.append('未填服務狀態未明列')
    bad.extend(deployment_index_problems(work, paths))
    # 移除自訂 ignore 規則和執行位元，儀器都必須真的擋得住。
    ignore = read_lf(work / '.gitignore')
    write_lf(work / '.gitignore', ignore.replace(ignore_rules(manifest['SECRETS']), '').replace(ignore_rules(manifest['RUNTIME_DIRS']), ''))
    if not any('未忽略' in s for s in deployment_index_problems(work, paths)):
        bad.append('負向測試未抓到自訂 ignore 缺失')
    write_lf(work / '.gitignore', ignore)
    for token in ('git check-ignore', '### 0-5 ', 'gh repo create'):
        if not deployment_order_problems(skill.replace(token, '移除門檻', 1), read_lf(ROOT / 'README.md')):
            bad.append('順序負向測試未擋 ' + token)
    if not deployment_order_problems(skill.replace('git add <路徑>', 'git add .', 1), read_lf(ROOT / 'README.md')):
        bad.append('順序負向測試未擋整批 git add')
    if bad:
        record('FAIL', '部署生命週期', '；'.join(bad))
        return
    must(['git', 'commit', '-qm', 'bootstrap verified locally'], work)
    must(['git', 'init', '-q', '--bare', str(remote)])
    must(['git', 'remote', 'add', 'origin', str(remote)], work)
    must(['git', 'push', '-qu', 'origin', 'main'], work)
    must(['git', 'clone', '-q', '-b', 'main', str(remote), str(clone)])
    if git(['ls-tree', '-r', '--name-only', 'HEAD', '--', *paths], clone).stdout.strip():
        bad.append('初次 commit 含假憑證或運行資料')
    # clone 後仍驗索引與開場 hook；不呼叫模型、不測外部工具注入。
    bad.extend(deployment_index_problems(clone, paths))
    bash = find_bash()
    if not bash:
        record('SKIP', '部署生命週期', '缺少 Git Bash，無法驗 clone 後執行開場 hook')
        return
    r = run([bash, '.claude/hooks/git-freshness.sh'], cwd=clone,
            env=tool_env(BOOTSTRAP_VERSION_CHECK='off'))
    if r.returncode or '[facts]' not in r.stdout:
        bad.append('clone 後開場 hook 執行失敗')
    record('FAIL' if bad else 'OK', '部署生命週期', '；'.join(bad) if bad else
           '自訂憑證／空白中文路徑 ignore；本機驗收→首 commit→local bare push→clone，clone 後開場 hook 印出 [facts]；5 個負向測試，未呼叫模型或 GitHub（Antigravity wrapper 的 100755 兩項 2026-11-13 隨 v3 D8 移除）')


def sync_mode_problems(sp, dest, tmp):
    """同一套斷言用於現行實作及移除 copymode 的負向變異。"""
    from unittest import mock
    import stat
    def must(args, cwd=None):
        result = run(args, cwd=cwd)
        if result.returncode:
            raise RuntimeError('%r: %s' % (args, result.stderr))
        return result
    work = tmp / 'mode-upgrade'
    work.mkdir(parents=True, exist_ok=True)
    wrapper = work / '.claude/hooks/git-freshness.sh'
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    original = read_lf(dest / '.claude/hooks/git-freshness.sh')
    write_lf(wrapper, original + '\n# before upgrade\n')
    wrapper.chmod(0o755)
    must(['git', 'init', '-q', work.as_posix()])
    must(['git', 'config', 'core.filemode', 'true'], work)
    must(['git', 'add', '.'], work)
    must(['git', 'update-index', '--chmod=+x', '.claude/hooks/git-freshness.sh'], work)
    must(['git', 'commit', '-qm', 'before mode upgrade'], work)
    plan = sp.Plan()
    plan.update(wrapper, '.claude/hooks/git-freshness.sh', original + '\n# after upgrade\n')
    bad = []
    copier = sp.shutil.copymode
    with mock.patch.object(sp.shutil, 'copymode', wraps=copier) as copied:
        done, error = sp.apply_plan(plan)
        if copied.call_args_list != [mock.call(wrapper, wrapper.with_name('git-freshness.sh.sync-tmp'))]:
            bad.append('替換前未複製既存 mode')
    if error or done != ['.claude/hooks/git-freshness.sh'] or '# after upgrade' not in read_lf(wrapper):
        bad.append('升級內容未完成')
    if os.name == 'posix':
        if stat.S_IMODE(wrapper.stat().st_mode) != 0o755:
            bad.append('0755 升級後 mode 改變')
        diff = must(['git', 'diff', '--summary'], work).stdout
        if 'mode change' in diff:
            bad.append('Git 出現 mode change')
        try:
            result = run([str(wrapper)], cwd=work, env=tool_env(BOOTSTRAP_VERSION_CHECK='off'))
            if result.returncode or '[facts]' not in result.stdout:
                bad.append('升級後原始 wrapper 無法直接執行')
        except OSError:
            bad.append('升級後原始 wrapper 拒絕執行')
        ordinary = work / 'config.txt'
        write_lf(ordinary, 'before')
        ordinary.chmod(0o640)
        config_plan = sp.Plan()
        config_plan.update(ordinary, 'config.txt', 'after')
        if sp.apply_plan(config_plan)[1] or stat.S_IMODE(ordinary.stat().st_mode) != 0o640:
            bad.append('一般檔案 0640 未保留')
    before = wrapper.read_bytes()
    with mock.patch.object(sp.shutil, 'copymode', side_effect=OSError('fixture denied')):
        done, error = sp.apply_plan(plan)
    if done or not error or wrapper.read_bytes() != before:
        bad.append('權限複製失敗仍替換原檔或回報成功')
    # 新依賴沒有原檔，應照原本的建立流程，不向不存在的路徑複製權限。
    missing = work / 'new.cmd'
    new_plan = sp.Plan()
    new_plan.update(missing, 'new.cmd', 'new')
    with mock.patch.object(sp.shutil, 'copymode', side_effect=OSError('must not copy')):
        if sp.apply_plan(new_plan)[1] or read_lf(missing) != 'new':
            bad.append('新增依賴被既存 mode 流程擋住')
    return bad


def step_sync_mode(dest, tmp):
    """2026-11-03：同步升級要保留 mode；Windows 只驗呼叫與失敗契約。"""
    import sync_project as sp
    import types
    bad = sync_mode_problems(sp, dest, tmp / 'current-mode')
    source = read_lf(ROOT / 'tools/sync_project.py')
    mutant = types.ModuleType('sync_mode_mutant')
    mutant.__file__ = str(ROOT / 'tools/sync_project.py')
    exec(compile(source.replace('shutil.copymode(path, tmp)', 'pass'), mutant.__file__, 'exec'), mutant.__dict__)
    if not sync_mode_problems(mutant, dest, tmp / 'mutant-mode'):
        bad.append('移除 mode 保留的負向變異未失敗')
    record('FAIL' if bad else 'OK', '同步升級 mode', '；'.join(bad) if bad else
           ('POSIX 0755／0640、原始 wrapper 直接執行、Git 無 mode diff；' if os.name == 'posix' else
            'Windows 僅驗 copymode 呼叫契約（非 POSIX 實測）；') +
           '複製失敗保留原檔、新增依賴、移除保留的負向變異')


def step_architecture_summary(dest):
    def problems(docs):
        bad = []
        for name, text in docs.items():
            rows = [line for line in text.splitlines() if line.startswith('|')]
            pointers = [line for line in rows
                        if line.startswith('| [CLAUDE.md](CLAUDE.md)') or line.startswith('| 3.2 |')]
            if not pointers or any('import' not in line for line in pointers):
                bad.append(name + ' 沒寫 CLAUDE.md 用 import')
        return bad
    docs = {'repo': read_lf(ROOT / 'ARCHITECTURE.md'), 'generated': read_lf(dest / 'ARCHITECTURE.md')}
    bad = problems(docs)
    for name in docs:
        mutant = dict(docs)
        mutant[name] = docs[name].replace('import', '只有標題不同')
        if not problems(mutant):
            bad.append('負向測試未抓到指標摘要退化：' + name)
    record('FAIL' if bad else 'OK', '結構摘要一致性', '；'.join(bad) if bad else
           '本 repo 與生成 ARCHITECTURE 寫明 CLAUDE.md 用 import；兩個負向測試')


def tests_report_problem(report):
    """Reject an empty, partial or failed test report (tools/run_tests.py --json)."""
    try:
        tests = report['tests']
        if report['passed'] is not True or report['registry_errors']:
            return '測試或現況索引核對沒過'
        if tests['run'] < 1 or any(tests[key] != 0 for key in ('failed', 'errors', 'skipped')):
            return '測試為空、失敗或有未驗證項'
        if not isinstance(tests.get('needs_uv'), list):
            return '報告沒列出 A4 不跑的測試檔'
    except (KeyError, TypeError):
        return '測試報告缺失或無效'
    return ''


@contextmanager
def background_command(command, cwd):
    """Overlap an isolated read-only process; always reap it, including on errors.

    Files avoid pipe backpressure when a failing suite emits a large traceback.
    This is concurrency within the verifier, not another model invocation.
    """
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        proc = subprocess.Popen(command, cwd=cwd, env=GIT_ENV,
                                stdout=stdout, stderr=stderr)
        def collect():
            code = proc.wait()
            stdout.seek(0)
            stderr.seek(0)
            return subprocess.CompletedProcess(command, code,
                stdout.read().decode('utf-8', errors='replace'),
                stderr.read().decode('utf-8', errors='replace'))
        try:
            yield collect
        finally:
            if proc.poll() is None:
                proc.terminate()
            proc.wait()


def step_tests(result=None):
    """測試套件與現況索引（2026-11-18，v3 Q46 起取代「v2 P0 原型回歸」）。"""
    if result is None:
        result = run([sys.executable, '-X', 'utf8', str(ROOT / 'tools/run_tests.py'), '--json'], cwd=ROOT)
    try:
        report = json.loads(result.stdout)
        problem = tests_report_problem(report)
        valid = result.returncode == 0 and not problem
        needs_uv = report['tests'].get('needs_uv', [])
        detail = problem or ('%s 個測試通過、現況索引與決策書一致%s' % (
            report['tests']['run'],
            '（另有 %d 個測試檔要外部套件，A4 不跑、要 uv run pytest：%s）' % (
                len(needs_uv), '、'.join(needs_uv)) if needs_uv else ''))
    except (ValueError, KeyError, TypeError):
        valid, detail = False, '測試報告缺失或無效'
    if not valid and result.stderr:
        detail += '\n' + result.stderr[-12000:]
    record('OK' if valid else 'FAIL', '測試套件與現況索引', detail)


SPLIT_BASELINE = ROOT / 'tools/skill_split_baseline.json'
# skill 入口必須自己帶著的句子：停止條件與禁令。每個 session 都要守的句子在 AGENTS.md 共用制度
# （SHARED_MUST），這裡不重複（v3 第 5 節；取捨在理由檔歷史紀錄的「#rule-4」）。
ENTRY_MUST = (
    '不要憑空建立交接檔案', '`reset --hard`', '`push --force`', '自行 `stash`',
    '接棒時 ahead-only', 'fetch 失敗',
    '功能分支要併進 `main`', '憑證缺失', 'HANDOFF 沒授權的破壞性操作', '建 GitHub repo 與第一次 push',
    '~/.claude/skills/handoff/', '使用者沒要求就不得自行交棒',
)
# AGENTS.md 共用制度（開始與結束標記之間）必須有的條件（v3 第 5 節、Q57、Q58）：
# 每條共用規則至少一句在這裡，整條被刪會被擋；大段與三個 ### 節的標題也列進來，結構被改掉會被擋。
SHARED_MUST = (
    '## 共用制度', '### 協作目標', '### 環境事實', '### 共用規則',
    '本機的檔案可能是舊的', '唯一的訊號是 origin 上 `HANDOFF.md` 的「工作中」那一行',
    '`[facts]`', '開場 `[facts]` 有不正常的值，或使用者要求交棒時', '.claude/skills/handoff/',
    'session 命名：工具能改名才做',
    '要先推成你自己', '推不上去就不算', '只讀、只回答問題的 session 不寫',
    '「待續分支」寫了分支名，就在那條分支上做', '`main` 上的測試要一直是過的',
    '不改檔、不推送，停下來告訴使用者', 'origin 上的「工作中」是別人，或確認不了是不是你',
    '歷史分岔、fetch 失敗、來源不明的未提交變更',
    '不提交祕密或金鑰樣式的內容', '`.gitignore` 排除的東西', '不用 `git add -A` 或 `git add .`',
    '`reset --hard`', 'force push', '自行 stash',
    '沒驗證過的事不寫成已驗證',
    '使用者要求交棒時才交棒', '沒要求就保留你的「工作中」',
    '確認 origin 上的「工作中」標記確由本 session 推上', '「工作中」改回 `無（已交棒）`',
    '<符號>　MM.DD.HH｜<主題>｜<狀態>｜交棒<N>次', '兩種狀態：`㊣` 工作中、`↗` 已交棒',
    '交棒的 push 成功後才改 `↗`，N 加 1', '是 `↗` 時收到任何新訊息，先改回 `㊣`',
    '各寫一行 `session：<實際標題>`', '`session：不適用：<原因>；交棒<N>次`',
)
MODE_A_MUST = (
    '印出幾行 `[facts]`', 'bash .claude/hooks/git-freshness.sh', '不要自己判斷「大概沒事」', '`mode-a-stop.md`',
    '切換後重做 A1', '都不能寫成通過',
    'session：㊣　<MM.DD.HH｜主題>｜工作中｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次',
    '只讀、只問問題的 session 不寫開工標記', '**工具欄不能省**', '遠端 SHA 跟 A1 記下的不同就停',
    'push 失敗就不是「已標記」', '不是互斥鎖',
)


def shared_rules_problems(agents, version):
    """AGENTS.md 共用制度（v3 第 5 節、D11）：標記成對、內容齊、行數在預算內、版本與 VERSION 相同。"""
    shared = shared_rules(agents)
    if not shared:
        return ['AGENTS.md 找不到成對的共用制度開始／結束標記']
    bad = ['共用制度缺：' + token for token in SHARED_MUST if token not in shared]
    n = shared.count('\n') + 1
    if n > SHARED_MAX_LINES:
        bad.append('共用制度 %d 行，超過 %d 行（v3 D11）' % (n, SHARED_MAX_LINES))
    total = agents.rstrip('\n').count('\n') + 1
    if total > AGENTS_MAX_LINES:
        bad.append('AGENTS.md 全檔 %d 行，超過 %d 行（v3 D11）' % (total, AGENTS_MAX_LINES))
    mark = re.search(r'共用制度開始 source: PROJECT-BOOTSTRAP\.md v([0-9][0-9.-]*)', shared)
    if not mark:
        bad.append('共用制度開始標記沒有 source 版本（開場 hook 靠它比對上游）')
    elif mark[1] != version:
        bad.append('共用制度版本 v%s 與 VERSION %s 不同' % (mark[1], version))
    return bad


def step_shared_rules(dest):
    agents = read_lf(dest / 'AGENTS.md')
    version = read_lf(ROOT / 'VERSION').strip()
    bad = shared_rules_problems(agents, version)
    shared = shared_rules(agents)
    cases = []
    if not bad:
        for token in SHARED_MUST:
            cases.append(('拿掉 ' + token, agents.replace(token, '')))
        pad = SHARED_MAX_LINES - (shared.count('\n') + 1) + 1
        cases.append(('共用制度超過 40 行', agents.replace(SHARED_END, '-\n' * pad + SHARED_END)))
        cases.append(('全檔超過 100 行', agents + '-\n' * AGENTS_MAX_LINES))
        cases.append(('結束標記不見', agents.replace(SHARED_END, '')))
        cases.append(('版本標記與 VERSION 不同', agents.replace('md v' + version, 'md v2000-01-01', 1)))
    for name, text in cases:
        if text == agents or not shared_rules_problems(text, version):
            bad.append('負向測試未擋：' + name)
    record('FAIL' if bad else 'OK', 'AGENTS.md 共用制度', '；'.join(bad) if bad else
           '標記成對、%d 條必備條件、共用 %d／%d 行、全檔 %d／%d 行、版本與 VERSION 相同；%d 個負向測試'
           '（只證明文字在、在預算內，不證明模型照做）'
           % (len(SHARED_MUST), shared.count('\n') + 1, SHARED_MAX_LINES,
              agents.rstrip('\n').count('\n') + 1, AGENTS_MAX_LINES, len(cases)))


def line_key(line):
    return hashlib.sha256(line.strip().encode('utf-8')).hexdigest()[:16]


def skill_split_problems(files, version, whole, baseline):
    """handoff skill 拆檔之後要守的東西（決策書 F22／Q9）。

    files 是 {檔名: 內容}。拆檔最怕三件事，而且都沒有徵兆：入口指向不存在的檔、各檔版本不一
    （同步只寫了一半）、濃縮時把停止條件或理由弄丟。
    """
    missing = [name for name in SKILL_FILES if name not in files]
    if missing:
        return ['缺 skill 檔：' + '、'.join(missing)]
    bad = []
    entry = files['SKILL.md']
    for name in SKILL_FILES[1:]:
        if '`%s`' % name not in entry:
            bad.append('入口沒有指到 ' + name)
    for name in SKILL_FILES:
        if SKILL_DIR + name not in whole:
            bad.append(name + ' 不在 sync_project 的 WHOLE')
        mark = re.search(r'source: PROJECT-BOOTSTRAP\.md v([0-9][0-9.-]*)', files[name])
        if not mark:
            bad.append(name + ' 缺 source 版本標記')
        elif mark[1] != version:
            bad.append('%s 的版本標記 v%s 與 VERSION %s 不同' % (name, mark[1], version))
    size = sum(len(files[name]) for name in SKILL_ROUTINE)
    if size > SKILL_ROUTINE_LIMIT:
        bad.append('skill 入口＋mode-a.md 共 %d 字元，超過 %d' % (size, SKILL_ROUTINE_LIMIT))
    bad.extend('入口缺：' + token for token in ENTRY_MUST if token not in entry)
    bad.extend('mode-a.md 缺：' + token for token in MODE_A_MUST if token not in files['mode-a.md'])
    have = {line_key(line) for text in files.values() for line in text.split('\n') if line.strip()}
    rewritten = baseline['rewritten']
    lost = [key for key in baseline['lines'] if key not in have and key not in rewritten]
    if lost:
        bad.append('拆分前的 SKILL.md 有 %d 行不在任何一個檔、也不在已改寫清單（%s…）' % (len(lost), lost[0]))
    if any(key not in baseline['lines'] or not str(note).strip() for key, note in rewritten.items()):
        bad.append('已改寫清單有不屬於舊文本的行，或沒寫去處')
    return bad


def step_skill_split(dest):
    import sync_project as syncer
    files = {name: read_lf(dest / (SKILL_DIR + name)) for name in SKILL_FILES
             if (dest / (SKILL_DIR + name)).is_file()}
    version = read_lf(ROOT / 'VERSION').strip()
    baseline = json.loads(read_lf(SPLIT_BASELINE))
    bad = skill_split_problems(files, version, syncer.WHOLE, baseline)
    size = sum(len(files.get(name, '')) for name in SKILL_ROUTINE)

    def mutated(name, text):
        copy = dict(files)
        copy[name] = text
        return copy
    cases = []
    if not bad:
        cases.append(('少一個模式檔', {k: v for k, v in files.items() if k != 'mode-b.md'}, version, syncer.WHOLE, baseline))
        cases.append(('入口不再指到 reasons.md', mutated('SKILL.md', files['SKILL.md'].replace('`reasons.md`', '理由檔')),
                      version, syncer.WHOLE, baseline))
        cases.append(('模式檔不在 WHOLE', files, version,
                      tuple(rel for rel in syncer.WHOLE if not rel.endswith('mode-a-stop.md')), baseline))
        cases.append(('只有一個檔的版本標記不同',
                      mutated('mode-0.md', files['mode-0.md'].replace('md v' + version, 'md v2000-01-01', 1)),
                      version, syncer.WHOLE, baseline))
        cases.append(('模式檔沒有版本標記',
                      mutated('reasons.md', files['reasons.md'].replace('source: PROJECT-BOOTSTRAP.md v', 'from v', 1)),
                      version, syncer.WHOLE, baseline))
        cases.append(('入口灌到超過上限', mutated('SKILL.md', files['SKILL.md'] + '字' * (SKILL_ROUTINE_LIMIT - size + 1)),
                      version, syncer.WHOLE, baseline))
        for token in ENTRY_MUST:
            cases.append(('入口拿掉 ' + token, mutated('SKILL.md', files['SKILL.md'].replace(token, '')),
                          version, syncer.WHOLE, baseline))
        for token in MODE_A_MUST:
            cases.append(('mode-a.md 拿掉 ' + token, mutated('mode-a.md', files['mode-a.md'].replace(token, '')),
                          version, syncer.WHOLE, baseline))
        # 理由檔少一行（任挑「反例」裡的一條）：覆蓋率必須擋下，理由可以搬不能消失。
        victim = next((line for line in files['reasons.md'].split('\n') if line.startswith('- ❌ 開工沒 fetch')), '')
        cases.append(('理由檔刪掉一條反例', mutated('reasons.md', files['reasons.md'].replace(victim + '\n', '', 1) if victim else files['reasons.md']),
                      version, syncer.WHOLE, baseline))
        ghost = dict(baseline, rewritten=dict(baseline['rewritten'], **{'0' * 16: '憑空多一筆'}))
        cases.append(('已改寫清單混進不存在的行', files, version, syncer.WHOLE, ghost))
        unexplained = dict(baseline, rewritten={key: '' for key in baseline['rewritten']})
        cases.append(('已改寫清單沒寫去處', files, version, syncer.WHOLE, unexplained))
    for name, *args in cases:
        if not skill_split_problems(*args):
            bad.append('負向測試未擋：' + name)
    record('FAIL' if bad else 'OK', 'skill 拆分', '；'.join(bad) if bad else
           '%d 個檔齊全、同版本、都在同步清單；入口＋mode-a.md %d／%d 字元；入口 %d 條、mode-a %d 條必備句；'
           '拆分前 %d 行逐字留存、%d 行列為已改寫；%d 個負向測試（不代表模型會去讀模式檔）'
           % (len(SKILL_FILES), size, SKILL_ROUTINE_LIMIT, len(ENTRY_MUST), len(MODE_A_MUST),
              len(baseline['lines']) - len(baseline['rewritten']), len(baseline['rewritten']), len(cases)))


RULE_MAP_HEAD = '## 規則 → 理由在哪（對照表）'
RULE_MAP_SOURCES = ('SKILL.md', 'mode-a.md', 'mode-a-stop.md', 'mode-b.md', 'mode-0.md', 'env.md')
RULE_MAP_WORDS = ('本段內文', '沒有寫下理由', '分節標題')


def skill_headings(text):
    """## 與 ### 段落標題，略過圍欄裡的（mode-b.md 的 HANDOFF 範本也有 ## 標題）。"""
    heads, fence = [], None
    for line in text.split('\n'):
        run = re.match(r'(`{3,})', line)
        if run:
            if fence is None:
                fence = run[1]
            elif line.strip() == fence:
                fence = None
            continue
        if fence is None and re.match(r'#{2,3} ', line):
            heads.append(line.split(' ', 1)[1].strip())
    return heads


def rule_map_problems(files):
    """reasons.md 的對照表要涵蓋入口與四個模式檔的每個段落（決策書 Q17 (b)）。

    只查涵蓋與指向：左欄每個段落都在、沒有多出不存在的段落；右欄指到的段落真的存在，
    或是三個固定字樣之一。理由寫得對不對，這裡看不出來。
    """
    reasons = files.get('reasons.md', '')
    if RULE_MAP_HEAD not in reasons:
        return ['reasons.md 沒有「規則 → 理由在哪」對照表']
    section = reasons.split(RULE_MAP_HEAD, 1)[1].split('\n## ', 1)[0]
    heads = {name: skill_headings(files.get(name, '')) for name in RULE_MAP_SOURCES + ('reasons.md',)}
    rows, bad = {}, []
    for line in section.split('\n'):
        if not line.startswith('| ') or line.startswith('| 規則（'):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split(' | ')]
        if len(cells) != 2:
            bad.append('對照表格式不對：' + line[:40])
            continue
        if cells[0] in rows:
            bad.append('對照表重複列：' + cells[0])
        rows[cells[0]] = [item.strip() for item in cells[1].split('<br>') if item.strip()]
    for name in RULE_MAP_SOURCES:
        for head in heads[name]:
            if '%s § %s' % (name, head) not in rows:
                bad.append('對照表缺：%s § %s' % (name, head))
    for left, targets in rows.items():
        name, _, head = left.partition(' § ')
        if name not in RULE_MAP_SOURCES or head not in heads[name]:
            bad.append('對照表左欄指到不存在的段落：' + left)
        if not targets:
            bad.append('對照表沒寫理由在哪：' + left)
        for target in targets:
            if target in RULE_MAP_WORDS:
                continue
            name, sep, head = target.partition(' § ')
            if (not sep or name not in heads or head not in heads[name]
                    or '## ' + head == RULE_MAP_HEAD):
                bad.append('對照表右欄指到不存在的段落：' + target)
    return bad


def step_skill_rule_map(dest):
    files = {name: read_lf(dest / (SKILL_DIR + name)) for name in SKILL_FILES
             if (dest / (SKILL_DIR + name)).is_file()}
    bad = rule_map_problems(files)
    rows = sum(len(skill_headings(files.get(name, ''))) for name in RULE_MAP_SOURCES)

    def mutated(name, old, new):
        copy = dict(files)
        if old not in copy[name]:
            return None
        copy[name] = copy[name].replace(old, new, 1)
        return copy
    cases = []
    if not bad:
        a2_row = '| mode-a.md § A2 站對分支 | mode-a-stop.md § A2 站對分支 |\n'
        cases = [
            ('少一列', mutated('reasons.md', a2_row, '')),
            ('模式檔段落改名', mutated('mode-b.md', '### B8 發布', '### B8 發佈')),
            ('入口多一段沒列', mutated('SKILL.md', '## 全程禁令', '## 新規則\n\n## 全程禁令')),
            ('右欄指錯段落', mutated('reasons.md', a2_row, a2_row.replace('§ A2 站對分支 |\n', '§ A2 換分支 |\n'))),
            ('右欄空白', mutated('reasons.md', a2_row, '| mode-a.md § A2 站對分支 |  |\n')),
            ('重複列', mutated('reasons.md', a2_row, a2_row * 2)),
            ('右欄指到對照表自己', mutated('reasons.md', a2_row, a2_row.replace(
                'mode-a-stop.md § A2 站對分支 |', 'reasons.md § 規則 → 理由在哪（對照表） |'))),
            ('沒有對照表', mutated('reasons.md', RULE_MAP_HEAD, '## 別的標題')),
        ]
        for name, copy in cases:
            if copy is None or not rule_map_problems(copy):
                bad.append('負向測試未擋：' + name)
    record('FAIL' if bad else 'OK', 'skill 規則對照表', '；'.join(bad) if bad else
           'reasons.md 對照表涵蓋入口與四個模式檔共 %d 個段落，右欄都指到存在的段落；%d 個負向測試'
           '（只查涵蓋與指向，不判斷理由寫得對不對）' % (rows, len(cases)))


def step_sync_skill_parts(dest, tmp):
    """舊專案只有單檔 SKILL.md：同步要補上五個新檔，而且入口最後才寫（2026-11-10）。

    只看 sync() 算出來的計畫，不寫入、不碰同步資格檢查（那由「同步資格」等項目守）。
    """
    import sync_project as syncer
    parts = [SKILL_DIR + name for name in SKILL_FILES if name != 'SKILL.md']
    entry = SKILL_DIR + 'SKILL.md'

    def planned(project, **kw):
        plan = syncer.sync(project, dest, **kw)
        return [rel for _, _, rel in plan.writes], '\n'.join(plan.msgs)
    old = tmp / 'parts-old'
    (old / SKILL_DIR).mkdir(parents=True)
    write_lf(old / entry, '---\nname: handoff\ndescription: old\n---\n\n單檔舊版\n')
    write_lf(old / (SKILL_DIR + 'notes-local.md'), '專案就地加的檔\n')
    writes, msgs = planned(old)
    bad = []
    if any(rel not in writes for rel in parts):
        bad.append('有入口的舊專案沒有補齊五個新檔')
    if entry not in writes or any(writes.index(rel) > writes.index(entry) for rel in parts if rel in writes):
        bad.append('入口不是 skill 檔裡最後寫的')
    if 'EXTRA' not in msgs or 'notes-local.md' not in msgs:
        bad.append('skill 目錄裡不認得的檔沒有被列出來')
    # 沒有這套 skill 的專案不能被補裝；Codex 限定同步也不能動 skill。
    bare = tmp / 'parts-bare'
    bare.mkdir()
    write_lf(bare / 'README.md', 'x\n')
    writes, _ = planned(bare)
    if any(rel.startswith(SKILL_DIR) for rel in writes):
        bad.append('沒有 handoff skill 的專案被補裝了模式檔')
    writes, _ = planned(old, codex_only=True)
    if any(rel.startswith(SKILL_DIR) for rel in writes):
        bad.append('Codex 限定同步動了 skill 目錄')
    # 負向：WHOLE 裡沒有模式檔時，這項檢查必須看得出「沒補齊」。
    with patch.object(syncer, 'WHOLE', tuple(rel for rel in syncer.WHOLE if rel not in syncer.SKILL_PARTS)):
        writes, _ = planned(old)
    if all(rel in writes for rel in parts):
        bad.append('負向測試未重現：WHOLE 拿掉模式檔後仍顯示補齊')
    record('FAIL' if bad else 'OK', '同步補齊模式檔', '；'.join(bad) if bad else
           '只有單檔的舊專案會補上五個新檔、入口最後寫、不認得的檔列為 EXTRA；沒有 skill 的專案與 Codex 限定同步不動；1 個負向測試')


def step_sync_shared_section(dest, tmp):
    """AGENTS.md 共用制度的同步（2026-11-14，v3 Q34 前置）。

    v3 的必守條件住在 AGENTS.md 標記之間，新 skill 指向那一節；同步器只發 skill 的話，
    舊專案會拿到一個指向空白的 skill，而且沒有徵兆。這裡釘：沒有就插在第一個「## 」前、
    舊版就整段換掉、標記外一個字不動、已是權威版不寫、標記壞掉就 FAIL 不寫、
    舊交接段落列成 MIGRATE、AGENTS.md 排在 skill 入口之前寫。
    """
    import sync_project as syncer
    entry = SKILL_DIR + 'SKILL.md'
    block_src = read_lf(dest / 'AGENTS.md')
    a = block_src.index(SHARED_START)
    b = block_src.index(SHARED_END) + len(SHARED_END)
    block = block_src[a:b]
    head = '# AGENTS.md — 舊專案\n\n> 最後更新：2026-01-01\n\n'
    body = '## 專案是什麼\n\n專案自己的內容。\n\n## 跨模型／跨機器協作規範\n\n舊規則。\n'

    def project(name, agents):
        p = tmp / ('shared-' + name)
        (p / SKILL_DIR).mkdir(parents=True)
        write_lf(p / entry, '---\nname: handoff\ndescription: old\n---\n\n舊版\n')
        write_lf(p / 'AGENTS.md', agents)
        return p

    def run(p):
        plan = syncer.sync(p, dest)
        writes = {rel: text for _, text, rel in plan.writes}
        order = [rel for _, _, rel in plan.writes]
        return plan, writes, order, '\n'.join(plan.msgs)

    bad = []
    plan, writes, order, msgs = run(project('fresh', head + body))
    new = writes.get('AGENTS.md')
    if new is None:
        bad.append('沒有共用制度的專案沒有補上')
    else:
        if new != head + block + '\n\n' + body:
            bad.append('補上的位置不在第一個「## 」前，或動到標記外的內容')
        if 'AGENTS.md' in order and entry in order and order.index('AGENTS.md') > order.index(entry):
            bad.append('AGENTS.md 排在 skill 入口之後寫')
    if 'MIGRATE AGENTS.md' not in msgs or '跨模型／跨機器協作規範' not in msgs:
        bad.append('標記外的舊交接段落沒有列成 MIGRATE')

    old_block = block.replace('### 協作目標', '### 舊目標', 1)
    _, writes, _, _ = run(project('stale', head + old_block + '\n\n' + body))
    if writes.get('AGENTS.md') != head + block + '\n\n' + body:
        bad.append('舊版共用制度沒有整段換成權威版，或動到標記外')

    _, writes, _, _ = run(project('same', head + block + '\n\n## 專案是什麼\n\nx\n'))
    if 'AGENTS.md' in writes:
        bad.append('已是權威版還是寫了 AGENTS.md')

    # 2026-11-21（v3 Q58）：專案規則放在「## 專案專用」的「### 專用規則」、從 1 編號；舊專案標記外的
    # 「## 鐵律」與 Q56 版接在結束標記後的編號清單都要列 MIGRATE、不改寫，新版的專用規則不列。
    legacy_rules = head + block + '\n\n## 鐵律（違反會造成實際損害）\n\n1. 舊規則。\n'
    continued = head + block + '\n8. 舊的接續編號規則。\n'
    current = head + block + '\n\n## 專案專用\n\n### 專用規則\n\n1. 新規則。\n'
    for name, text, label in (('legacy-rules', legacy_rules, '## 鐵律'),
                              ('continued-rules', continued, '結束標記後接著共用規則編號的清單')):
        _, writes, _, msgs = run(project(name, text))
        if label not in msgs or 'v3 Q58' not in msgs:
            bad.append('標記外的「%s」沒有列成 MIGRATE（v3 Q58）' % label)
        if 'AGENTS.md' in writes:
            bad.append('標記外有「%s」時改寫了 AGENTS.md' % label)
    _, _, _, msgs = run(project('current-rules', current))
    if 'v3 Q58' in msgs:
        bad.append('新版的「### 專用規則」被誤列成 MIGRATE')
    with patch.object(syncer, 'legacy_rule_sections', lambda text: []):
        _, _, _, msgs = run(project('legacy-rules-neg', legacy_rules))
    if 'v3 Q58' in msgs:
        bad.append('負向測試未重現：拿掉舊規則偵測後仍列了 MIGRATE')

    broken = {
        '只有開始標記': head + block.replace(SHARED_END, '') + body,
        '兩個開始標記': head + block + '\n' + block.split('\n', 1)[0] + '\n' + body,
        '結束標記在前': head + SHARED_END + '\n' + block.replace(SHARED_END, '') + '\n' + body,
    }
    for name, text in broken.items():
        plan, writes, _, _ = run(project('broken-%d' % len(bad) + name, text))
        if 'AGENTS.md' in writes or not any('AGENTS.md' in e for e in plan.errors):
            bad.append('標記壞掉沒有 FAIL 或照樣寫入：' + name)

    # 負向：同步器拿掉共用制度這一步時，上面第一個情境必須看得出「沒補上」。
    with patch.object(syncer, 'sync_shared_section', lambda *a, **k: None):
        _, writes, _, _ = run(project('neg', head + body))
    if 'AGENTS.md' in writes:
        bad.append('負向測試未重現：拿掉共用制度同步後仍寫了 AGENTS.md')
    record('FAIL' if bad else 'OK', '同步共用制度', '；'.join(bad) if bad else
           '沒有就插在第一個「## 」前、舊版整段換掉、標記外不動、已是權威版不寫、'
           '3 種壞標記 FAIL 不寫、舊交接段落、「## 鐵律」與接續編號清單列 MIGRATE、新版專用規則不列、'
           'AGENTS.md 先於 skill 入口；2 個負向測試')


def run_checks(dest, tmp):
    # run_tests reads the source repo and uses its own temporary fixtures.
    # The other checks mutate only their generated fixtures, so overlap is safe.
    with background_command(
            [sys.executable, '-X', 'utf8', str(ROOT / 'tools/run_tests.py'), '--json'], ROOT) as collect:
        _run_checks(dest, tmp, collect)


def _run_checks(dest, tmp, collect):
    work = None
    seen = step_regenerate(dest) and step_fill(dest)
    if seen and step_check_docs(dest):
        step_placeholder_list(dest, seen)
        step_deploy_shape(dest)
        step_codex_windows(dest, tmp)
        step_wiring_cwd(dest, tmp)
        step_portability(dest)
        step_bash32_multibyte(dest)
        hooked = step_hook(dest, tmp)
        work = hooked if isinstance(hooked, pathlib.Path) else None
        step_busy(dest, work)
        step_repo_busy(dest)
        step_version_check(work)
        step_rename_line(dest)
        step_session_resume(dest)
    step_eol(dest)
    step_self()
    step_archive(tmp)
    step_version_names(tmp)
    step_repo_handoff()
    step_reason_links()
    step_rule_refs()
    if seen:
        step_source_exceptions(dest, tmp)
        step_repo_pre_push(dest, tmp)
        step_handoff_parity(dest)
        step_product_documents(dest)
        step_product_document_policy(dest)
        step_source_staged_parity(dest, tmp)
        step_product_handoff_flow(dest, tmp)
    step_sync_coverage(dest)
    step_sync_self_guard()
    step_sync_safety(tmp)
    step_misc(dest, work)
    step_flow_contract(dest, tmp)
    step_core_priority(dest, tmp)
    step_coordination(dest)
    step_skill_split(dest)
    step_shared_rules(dest)
    step_skill_rule_map(dest)
    step_sync_skill_parts(dest, tmp)
    step_sync_shared_section(dest, tmp)
    step_sync_scope(dest, tmp)
    step_sync_mode(dest, tmp)
    step_architecture_summary(dest)
    step_deployment_lifecycle(tmp)
    step_tests(collect())
    step_dev_layout()
    step_kit_source()
    step_global_skill()


# 鎖檔裡的套件名 → import 名，名字不一樣的才列
DEV_IMPORT_NAMES = {'attrs': ('attr', 'attrs'), 'markdown-it-py': ('markdown_it',),
                   'pytest': ('pytest', '_pytest'), 'rpds-py': ('rpds',)}
# A4 會跑到的程式：只能用標準函式庫，沒裝 uv 的機器也要能驗
DEV_STDLIB_ONLY = ('tools', 'src/project_bootstrap')
# 只有這幾支可以用鎖檔裡的套件。其他程式不能 import 它們（A4 才碰不到），
# import 它們的測試要以 raise unittest.SkipTest('needs …') 開頭：run_tests 憑這個標記不跑它們並在報告列出。
# 要多一支就加在這裡，這是刻意留的關卡。
DEV_EXTRAS = ('src/project_bootstrap/mdlinks.py', 'src/project_bootstrap/schema_check.py')


def p1_imports(text):
    """頂層 import 的完整模組名；相對 import 不算。"""
    ast = __import__('ast')
    names = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            module = node.module or ''
            names.append(module)
            names += ['%s.%s' % (module, alias.name) for alias in node.names]
    return names


def dev_layout_problems(pyproject, lock, sources, tests=None, extras=DEV_EXTRAS):
    """開發骨架的鎖定與 A4 免安裝。

    只查：最低版本是 3.12、還不是可安裝的包；pyproject 宣告的每個依賴都在 uv.lock；
    鎖檔每個外部套件都有 sha256 與授權；A4 會跑到的程式不 import 鎖檔裡的套件。
    `extras` 列的模組可以用鎖檔套件，但別的程式不能 import 它們，import 它們的測試要在缺套件時
    SkipTest。授權字串對不對、鎖檔是不是最新（用 uv lock --check）、importlib 動態載入，這裡看不出來。
    """
    import tomllib  # 標準庫，3.11 起有；放這裡，舊版 Python 才看得到檔頭的版本訊息
    try:
        meta, locked = tomllib.loads(pyproject), tomllib.loads(lock)
    except tomllib.TOMLDecodeError as exc:
        return ['pyproject.toml 或 uv.lock 不是合法的 TOML：%s' % exc]
    bad = []
    project = meta.get('project', {})
    if project.get('requires-python') != '>=3.12':
        bad.append('pyproject 的 requires-python 不是 >=3.12')
    if meta.get('tool', {}).get('uv', {}).get('package') is not False:
        bad.append('pyproject 沒寫 [tool.uv] package = false（打包屬 P2）')
    wanted = project.get('dependencies', []) + [d for group in meta.get('dependency-groups', {}).values()
                                                  for d in group]
    declared = {re.match(r'[A-Za-z0-9_.-]+', d).group(0) for d in wanted}
    packages = {p['name']: p for p in locked.get('package', [])}
    if not declared:
        bad.append('pyproject 沒有宣告任何依賴')
    for name in sorted(declared - set(packages)):
        bad.append('依賴沒進 uv.lock：' + name)
    licenses = meta.get('tool', {}).get('project-bootstrap', {}).get('licenses', {})
    external = {name: p for name, p in packages.items() if 'registry' in p.get('source', {})}
    if 'project-bootstrap' not in packages:
        bad.append('uv.lock 沒有本專案自己')
    for name, p in sorted(external.items()):
        artifacts = p.get('wheels', []) + ([p['sdist']] if 'sdist' in p else [])
        if not artifacts or not all(a.get('hash', '').startswith('sha256:') for a in artifacts):
            bad.append('鎖檔套件沒有 sha256：' + name)
        if name not in licenses:
            bad.append('鎖檔套件沒登記授權：' + name)
    for name in sorted(set(licenses) - set(external)):
        bad.append('授權表有鎖檔沒有的套件：' + name)
    forbidden = set()
    for name in packages:
        forbidden.update(DEV_IMPORT_NAMES.get(name, (name.replace('-', '_'),)))
    forbidden.discard('project_bootstrap')
    extra_modules = {path[len('src/'):-len('.py')].replace('/', '.') for path in extras}
    for path in extras:
        if path not in sources:
            bad.append('DEV_EXTRAS 列的模組不存在：' + path)
    for kind, files in (('程式', sources), ('測試', tests or {})):
        for path, text in sorted(files.items()):
            try:
                names = p1_imports(text)
            except SyntaxError:
                bad.append('解析失敗：' + path)
                continue
            reaches = sorted({n for n in names if n in extra_modules or n.rsplit('.', 1)[0] in extra_modules})
            if kind == '程式' and path not in extras:
                for name in names:
                    if name.split('.')[0] in forbidden:
                        bad.append('A4 會跑到的程式 import 了外部套件：%s（%s）' % (path, name))
                if reaches:
                    bad.append('A4 會跑到的程式 import 了用外部套件的模組：%s（%s）' % (path, '、'.join(reaches)))
            if kind == '測試' and reaches and "raise unittest.SkipTest('needs " not in text:
                bad.append('測試 import 用外部套件的模組卻沒有缺套件時 SkipTest：' + path)
    return bad


def step_dev_layout():
    try:
        pyproject = read_lf(ROOT / 'pyproject.toml')
        lock = read_lf(ROOT / 'uv.lock')
    except OSError as exc:
        record('FAIL', '開發骨架', '讀不到 pyproject.toml 或 uv.lock：%s' % exc)
        return
    sources = {}
    for folder in DEV_STDLIB_ONLY:
        for path in sorted((ROOT / folder).glob('*.py')):
            if not path.name.startswith('test_'):
                sources[path.relative_to(ROOT).as_posix()] = read_lf(path)
    tests = {path.relative_to(ROOT).as_posix(): read_lf(path) for path in sorted((ROOT / 'tests').glob('test_*.py'))}
    bad = dev_layout_problems(pyproject, lock, sources, tests)
    cases = []
    if not bad:
        first = sorted(path for path in sources if path not in DEV_EXTRAS)[0]
        skip_test = next(path for path, text in tests.items() if 'project_bootstrap.mdlinks' in text)

        def lock_block(name, change):
            start = lock.index('\n[[package]]\nname = "%s"\n' % name)
            end = lock.find('\n[[package]]\n', start + 1)
            end = len(lock) if end == -1 else end
            return lock[:start] + change(lock[start:end]) + lock[end:]
        cases = [
            ('依賴沒進鎖檔', dev_layout_problems(pyproject, lock_block('jsonschema', lambda b: ''), sources)),
            ('鎖檔少 sha256', dev_layout_problems(pyproject, lock_block(
                'attrs', lambda b: b.replace('sha256:', 'md5:')), sources)),
            ('授權表少一個', dev_layout_problems(pyproject.replace('\npytest = "MIT"\n', '\n', 1), lock, sources)),
            ('最低版本改 3.11', dev_layout_problems(pyproject.replace('">=3.12"', '">=3.11"', 1), lock, sources)),
            ('拿掉 package = false', dev_layout_problems(pyproject.replace('package = false', '', 1), lock, sources)),
            ('驗證器 import jsonschema', dev_layout_problems(pyproject, lock, dict(
                sources, **{first: sources[first] + '\nimport jsonschema\n'}))),
            ('驗證器 from markdown_it import', dev_layout_problems(pyproject, lock, dict(
                sources, **{first: sources[first] + '\nfrom markdown_it.token import Token\n'}))),
            ('一般模組 import 用外部套件的模組', dev_layout_problems(pyproject, lock, dict(
                sources, **{first: sources[first] + '\nfrom project_bootstrap import mdlinks\n'}), tests)),
            ('測試沒有缺套件時 SkipTest', dev_layout_problems(pyproject, lock, sources, dict(
                tests, **{skip_test: tests[skip_test].replace("raise unittest.SkipTest('needs ", "raise unittest.SkipTest('x ")}))),
            ('DEV_EXTRAS 列了不存在的模組', dev_layout_problems(pyproject, lock, sources, tests,
                                                         DEV_EXTRAS + ('src/project_bootstrap/gone.py',))),
        ]
        for name, problems in cases:
            if not problems:
                bad.append('負向測試未擋：' + name)
    record('FAIL' if bad else 'OK', '開發骨架', '；'.join(bad) if bad else
           'pyproject 依賴都在 uv.lock、%d 個外部套件都有 sha256 與授權、最低 Python 3.12；'
           '%d 支程式除 %d 支指定模組外只用標準函式庫，且不 import 那幾支；import 它們的測試缺套件時 SkipTest；'
           '%d 個負向測試（鎖檔是否最新要另跑 uv lock --check，本項不需要 uv）' % (
               len(re.findall(r'source = \{ registry = ', lock)), len(sources), len(DEV_EXTRAS), len(cases)))


def bootstrap_source_problems(build_kit, files, installer, sync, current):
    """bootstrap.py 必須等於 build_kit 的生成結果（v3 Q49）。

    來源有三個：src/kit 的範本與 owners.json、src/project_bootstrap/installer.py、
    tools/sync_project.py 的合併函式。任何一個改了沒重生都要擋，手改產物也要擋。
    """
    owners = json.loads(read_lf(ROOT / 'src/kit/owners.json'))['files']
    try:
        built = build_kit.build_bootstrap(files, installer, sync, owners)
    except (build_kit.KitError, SyntaxError) as exc:
        return ['生不出 bootstrap.py：%s' % exc]
    if built != current:
        return ['bootstrap.py 與來源生成結果不同；改來源後跑 python3 -X utf8 tools/build_kit.py，不要手改 bootstrap.py']
    return []


def kit_source_problems(build_kit, prose, files, retired_exists):
    """src/kit 生得出部署包全文、範本集合等於 EXPECTED，而且 PROJECT-BOOTSTRAP.md 沒被放回來。

    部署包全文只在記憶體生成（kit_text，v3 Q50）；那個檔放回來就多一份會過期的範本副本。
    範本內容對不對由本檔其他各項驗。
    """
    try:
        build_kit.build(prose, files)
    except build_kit.KitError as exc:
        return ['src/kit 生不出部署包：%s' % exc]
    bad = []
    if retired_exists:
        bad.append('PROJECT-BOOTSTRAP.md 已退休（v3 Q50），不要提交回來；說明在 src/kit/kit.md')
    if set(files) != EXPECTED:
        bad.append('src/kit/files 的範本與 EXPECTED 不同：缺 %s 多 %s'
                   % (sorted(EXPECTED - set(files)), sorted(set(files) - EXPECTED)))
    return bad


def step_kit_source():
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_kit
        prose, files = build_kit.load_source()
    except (ImportError, OSError) as exc:
        record('FAIL', '部署包由來源生成', '讀不到 tools/build_kit.py 或 src/kit：%s' % exc)
        return
    except Exception as exc:  # build_kit.KitError（例如範本少了 .tmpl）
        record('FAIL', '部署包由來源生成', str(exc))
        return
    finally:
        sys.path.remove(str(ROOT / 'tools'))
    retired = KIT.exists()
    bad = kit_source_problems(build_kit, prose, files, retired)
    cases = []
    if not bad:
        name = 'AGENTS.md'
        directive = '<!-- kit-file: %s -->' % name
        cases = [
            ('部署包又被放回來', kit_source_problems(build_kit, prose, files, True)),
            ('多一個沒用到的範本', kit_source_problems(build_kit, prose, dict(files, **{'extra.md': 'x\n'}), retired)),
            ('kit.md 指到不存在的範本', kit_source_problems(build_kit, prose.replace(
                directive, '<!-- kit-file: missing.md -->', 1), files, retired)),
            ('同一個範本用兩次', kit_source_problems(build_kit, prose.replace(
                '<!-- kit-file: CLAUDE.md -->', directive, 1), files, retired)),
            ('範本少了結尾換行', kit_source_problems(build_kit, prose, dict(files, **{name: files[name][:-1]}), retired)),
            ('範本含收尾圍籬', kit_source_problems(build_kit, prose, dict(
                files, **{'.gitattributes': files['.gitattributes'] + '````\n'}), retired)),  # 3.13 用四個反引號圍
            ('範本集合少一個', kit_source_problems(build_kit, prose.replace(
                '<!-- kit-file: .gitattributes -->\n', '', 1),
                {k: v for k, v in files.items() if k != '.gitattributes'}, retired)),
        ]
        for label, problems in cases:
            if not problems:
                bad.append('負向測試未擋：' + label)
    record('FAIL' if bad else 'OK', '部署包由來源生成', '；'.join(bad) if bad else
           'src/kit（kit.md＋%d 個 .tmpl 範本）生得出部署包全文，PROJECT-BOOTSTRAP.md 沒被放回來；'
           '%d 個負向測試（只證明全文生得出來，範本內容由其他各項驗）' % (len(files), len(cases)))
    installer = read_lf(ROOT / 'src/project_bootstrap/installer.py')
    sync = read_lf(ROOT / 'tools/sync_project.py')
    current = read_lf(ROOT / 'bootstrap.py') if (ROOT / 'bootstrap.py').exists() else ''
    bad = bootstrap_source_problems(build_kit, files, installer, sync, current)
    cases = []
    if not bad:
        cases = [
            ('手改 bootstrap.py', bootstrap_source_problems(build_kit, files, installer, sync,
                                                           current.replace('不碰網路', '不碰網際網路', 1))),
            ('改範本沒重生', bootstrap_source_problems(build_kit, dict(files, **{'CLAUDE.md': files['CLAUDE.md'] + 'x\n'}),
                                                    installer, sync, current)),
            ('改 installer.py 沒重生', bootstrap_source_problems(build_kit, files, installer + '\n# x\n', sync, current)),
            ('改 sync_project.py 的合併函式沒重生', bootstrap_source_problems(
                build_kit, files, installer, sync.replace("BUSY_FIELD = '", "BUSY_FIELD = ' ", 1), current)),
            ('sync_project.py 少一個共用函式', bootstrap_source_problems(
                build_kit, files, installer, sync.replace('def ensure_claude_import(', 'def ensure_claude_import_x(', 1), current)),
        ]
        bad = ['bootstrap.py 負向測試未擋：' + label for label, problems in cases if not problems]
    record('FAIL' if bad else 'OK', '安裝程式由來源生成', '；'.join(bad) if bad else
           'bootstrap.py 與 src/kit、installer.py、sync_project.py 的生成結果逐位元組相同；%d 個負向測試'
           '（安裝、更新與換行的行為由 tests/test_bootstrap_repo.py 實跑）' % len(cases))


GLOBAL_SKILL_DIRS = ('.claude/skills/handoff', '.codex/skills/handoff')


def global_skill_problems(home, templates):
    """家目錄的兩份全域 handoff skill 跟部署包範本比對（2026-11-18 使用者指定）。

    回傳 (已安裝的目錄, 問題)。templates 是 {檔名: 內容}，取自 src/kit 的
    `.claude/skills/handoff/*.tmpl`（這七個範本沒有佔位符，部署出去就是原文）。
    比對整份內容而不只看 `source:` 版本號：同版號但內容不同也算過期。
    """
    installed, problems = [], []
    for rel in GLOBAL_SKILL_DIRS:
        folder = home / rel
        if not folder.is_dir():
            continue
        installed.append('~/' + rel)
        stale = []
        for name, text in sorted(templates.items()):
            try:
                same = (folder / name).read_text(encoding='utf-8') == text
            except (OSError, UnicodeDecodeError):
                same = False
            if not same:
                stale.append(name)
        if stale:
            found = re.search(r'source: PROJECT-BOOTSTRAP\.md v([0-9][0-9.-]*)',
                              (folder / 'SKILL.md').read_text(encoding='utf-8', errors='replace')
                              if (folder / 'SKILL.md').is_file() else '')
            problems.append('~/%s 是 %s，跟部署包不同的檔：%s' % (
                rel, found.group(1) if found else '版本不明', '、'.join(stale)))
    return installed, problems


def step_global_skill():
    """只提醒、不影響結束碼（使用者 2026-11-18 選定）；兩份都沒裝印 skip。"""
    title = '全域 handoff skill 跟部署包同版'
    folder = ROOT / 'src/kit/files/.claude/skills/handoff'
    templates = {p.name[:-len('.tmpl')]: p.read_text(encoding='utf-8')
                 for p in sorted(folder.glob('*.tmpl'))}
    with tempfile.TemporaryDirectory() as raw:
        fake = pathlib.Path(raw)
        good = fake / GLOBAL_SKILL_DIRS[0]
        good.mkdir(parents=True)
        for name, text in templates.items():
            (good / name).write_bytes(text.encode('utf-8'))
        cases = [('同內容被當成過期', global_skill_problems(fake, templates)[1] == [])]
        (good / 'env.md').write_bytes((templates['env.md'] + '\n舊內容\n').encode('utf-8'))
        cases.append(('同版號但內容不同沒抓到', global_skill_problems(fake, templates)[1] != []))
        (good / 'env.md').unlink()
        cases.append(('少一個檔沒抓到', global_skill_problems(fake, templates)[1] != []))
        empty = fake / 'empty'
        empty.mkdir()
        cases.append(('沒裝被當成已裝', global_skill_problems(empty, templates)[0] == []))
    bad = [label for label, ok in cases if not ok]
    if bad:
        record('FAIL', title, '負向測試未擋：' + '、'.join(bad))
        return
    installed, problems = global_skill_problems(pathlib.Path.home(), templates)
    if not installed:
        record('SKIP', title, '本機沒有 ~/%s 也沒有 ~/%s' % GLOBAL_SKILL_DIRS)
    elif problems:
        record('NOTE', title, '；'.join(problems) + '。要重裝：把 src/kit/files/.claude/skills/handoff/ '
               '的七個範本去掉 .tmpl 覆蓋過去（%d 個負向測試）' % len(cases))
    else:
        record('OK', title, '%s 七個檔跟部署包逐字相同；%d 個負向測試' % ('、'.join(installed), len(cases)))


def main():
    global QUIET
    ap = argparse.ArgumentParser()
    ap.add_argument('--quiet', action='store_true',
                    help='只印摘要及 FAIL／SKIP；仍執行全部檢查，結束碼不變')
    ap.add_argument('--staged', action='store_true',
                    help='B7 提交前拒絕未暫存或未追蹤檔，驗證實際 staged 候選')
    ap.add_argument('--keep', action='store_true', help='保留產生的骨架，印出路徑')
    args = ap.parse_args()
    QUIET = args.quiet
    results.clear()

    if not (ROOT / 'src/kit/kit.md').exists():
        print('找不到 src/kit/kit.md——請在本 repo 根目錄執行')
        return 2

    if args.staged:
        problems = source_staged_problems(ROOT)
        if problems:
            print('[index] 🔴 ' + '；'.join(problems))
            return 2
        print('[index] staged 提交候選與工作樹一致，無未追蹤檔')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='verify-bootstrap-'))
    dest = tmp / 'gen'
    dest.mkdir()
    print(f'重生骨架於 {dest}\n')
    try:
        run_checks(dest, tmp)
    finally:
        if args.keep:
            print(f'\n（--keep）骨架保留在 {dest}')
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    failed = [t for s, t, _ in results if s == 'FAIL']
    skipped = [t for s, t, _ in results if s == 'SKIP']
    noted = [t for s, t, _ in results if s == 'NOTE']
    print()
    if noted:
        print(f'提醒：{len(noted)} 項（不影響結束碼）—— {"、".join(noted)}')
    if failed:
        print(f'FAIL：{len(failed)} 項未通過 —— {"、".join(failed)}')
        return 2
    if skipped:
        print(f'SKIP：{len(skipped)} 項未驗證 —— {"、".join(skipped)}')
        return 1
    print('OK：部署包驗證全數通過（%d 項）' % len(results))
    return 0


if __name__ == '__main__':
    sys.exit(main())
