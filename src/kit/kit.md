# PROJECT-BOOTSTRAP.md — AI 協作專案管理骨架（部署包）

> 把這一份檔案複製到**新專案的空資料夾**，然後開一個 AI session 貼上：
>
> ```text
> 請完全依照本資料夾的 PROJECT-BOOTSTRAP.md 建立本專案的管理骨架：先做第 1 節訪談問我問題，
> 拿到答案後照第 3 節逐檔建立（內容照抄、只替換佔位符），依第 4 節先完成本機驗收才首次發布，再跑第 5 節遠端與工具驗收並回報。
> 過程中不要自行增刪制度，也不要把佔位符留在檔案裡。
> ```
>
> 也可以完全手動：照第 3 節把每個檔案自己建出來，效果一樣。
> 骨架建好後，**這份 PROJECT-BOOTSTRAP.md 就可以刪掉**（內容已分散進 AGENTS.md／handover-protocol.md／`handoff` skill）。
> 版本：**2026-11-14**（**session 名稱開頭的時間改成 `MM.DD.HH`**（使用者 2026-11-14 指定，例：`㊣　11.14.06｜主題｜工作中｜交棒0次`），取代 `YYMMDDHH`：同一年內不需要年份，加點分隔比八位數字好認。3.1 共用制度的「session 名稱」、3.8 handoff skill 各檔的格式與範例、3.10 開場 hook 第一行（`date +%m.%d.%H`）一起改；`VERSION` 與六個 skill 檔、共用制度標記、3.10 的 `source:` 跳到 `v2026-11-14`。已經用舊格式命名的 session 不必改名，「工作中」欄位的判讀靠全形豎線，新舊兩種都讀得懂。同日稍晚：「跨工具與跨平台」的能力矩陣拿掉 Antigravity 欄（v3 D8 已放棄，`capabilities.json` 那幾格留狀態不渲染），使用者 2026-11-14 定案；skill 沒動，`VERSION` 不跳。）
> 前一版 **2026-11-13**（**需求決策書 v3 第 1 期：共用制度縮成 `AGENTS.md` 裡的一節，開場 hook 只報事實，handoff skill 降為碰到才讀的參考，Antigravity 移出部署包**。3.1 `AGENTS.md` 範本的共用制度夾在開始與結束標記之間，32 行（v3 D11 上限 40），起點是 handoff-ab 的極簡版，補上「待續分支」、不提交祕密與不整批加入、F50 session 命名三條。3.10 `git-freshness.sh` 檔名不變（Codex 與 Windows 接線不用動），內容改成最多五行 `[facts]`：時間與 `YYMMDDHH`、與 origin 的落後與領先、未提交檔數、origin 的「工作中」原文，有差異才印的共用制度版本與家目錄 skill 差異；判讀表、全綠行、工具身分猜測與「先走 skill」的提醒移除。共用制度版本改從 `AGENTS.md` 開始標記讀。3.8 入口與 `mode-a.md` 改寫成參考，其餘四個檔只加一段 2026-11-13 註記。舊 3.18–3.20（Antigravity 轉接層、Windows shim、`.agents/hooks.json`）移除。同日補一句（F50 互動驗證重現：用選項卡片停下時漏了 `session：` 行）：共用制度的「session 名稱」加「用選項卡片發問也算停下來等決定，卡片之前先寫這一行」；這一版還沒發布到任何專案，所以版本號不跳。handoff-ab 兩輪 18／18 與 v2 完整版相同，結果在 `experiments/handoff-ab/RESULTS.md`；F50 在 `experiments/handoff-ab/F50.md`。）
> 前一版 **2026-11-12.4**（**交棒只在使用者要求時做**，決策書 Q31 (a)：入口模式表的 B 改成「使用者要求交棒／收工／換人接手」，告一段落走 C、commit／push 時機由 agent 判斷；C 的 push 在 origin「工作中」仍是本 session 時不必更新 HANDOFF；一段工作做完時讀得到上下文用量就讀，70% 建議交棒一次、85% 再一次，讀不到不估算；3.11 push 提醒在 origin「工作中」不是「無（已交棒）」時放行。守門人：入口必備句加「使用者沒要求就不得自行交棒」，「AI push 提醒情境」加放行、已交棒仍擋、沒有欄位仍擋與拿掉放行的負向測試。六個檔、3.11 與 3.16 指標一起跳到 `v2026-11-12.4`。**沒有驗證的**：模型會不會照著只建議不交棒。）
> 前一版 **2026-11-10.2**（**handoff skill 的 `reasons.md` 末尾加一張「規則 → 理由在哪」對照表**，決策書 Q17 (b)：入口與 `mode-a.md` 不逐條加連結（常態必讀不增加），改由對照表列出入口與四個模式檔每個段落的理由在哪；拆分前就沒寫理由的段落照實標「沒有寫下理由」。守門人：`verify_bootstrap.py` 的「skill 規則對照表」（每個段落標題都在左欄、右欄指到的段落存在，附負向測試；不判斷理由內容）。六個檔一起跳到 `v2026-11-10.2`。）
> 前一版 **2026-11-10**（**handoff skill 從單檔拆成一個目錄、六個檔**，決策書 F22／Q9：單檔 22,040 字元，正常接棒只需要其中一小部分。3.8 現在產出入口 `SKILL.md`、`mode-a.md`（正常接棒）、`mode-a-stop.md`（完整判讀表與異常）、`mode-b.md`（交棒與中途同步）、`mode-0.md`（建制）、`reasons.md`（理由、事故與命名細則）；入口與 `mode-a.md` 是新寫的摘要，合計 5,380 字元，其餘四個檔逐字搬自單檔。3.10 `git-freshness.sh` 在 fetch 成功、不是 detached、upstream 是 `origin/<當前分支>`、沒有領先落後、工作樹乾淨、origin 的「工作中」是 `無（已交棒）` 全部成立時多印一行「全綠」，少一項就不印並指向 `mode-a-stop.md`。守門人：`verify_bootstrap.py` 新增「skill 拆分」（檔案齊全、六檔同版本、常態必讀 ≤6,000、入口與 mode-a 必備句、拆分前每一行逐字留存或列入已改寫清單）與「全綠行」（真 Git fixture 逐項打破條件）。`sync_project.py` 會替已有入口的專案補上五個新檔，並列出 skill 目錄裡不認得的檔。**沒有驗證的**：模型會不會真的從入口走到模式檔。）
> 再前一版 **2026-11-03**（複審 R04／R07–R09：先遮罩再摘要；先 stage 並拒絕文件／檢查器部分 stage；空工具欄與角括號 title 組合修正。R03 同步資格檢查在維護工具，依 README 逐專案 A1–A5。）
> 2026-11-12 第三次（**刻意不跳版**：`.claude/skills/handoff/` 一個字沒動，所以 `VERSION` 不動；3.10 改了，`source:` 標記跳到 `v2026-11-12.3`）：**3.10 `git-freshness.sh` 在家目錄 `~/.claude/skills/handoff/` 跟專案那份不同時印一行 🟡**（決策書 Q28 (a)）。2026-11-12 在 Claude Code 2.1.321 實測：兩處都有同名 skill 時，Claude Code 載入的是家目錄那份，專案那份被蓋掉；全域副本若舊到沒有「專案有就讀那裡」那句，Claude Code 就照舊程序做，而 Codex 照專案那份做。逐檔比內容（含只有一邊有的檔），相同或沒有全域副本就安靜。3.8 同步規則照實補上這件事。🔴 **代價**同前兩條：各專案要逐專案跑 `sync_project.py` 才拿得到，另行授權。
> 2026-11-12 第二次（**刻意不跳版**：`.claude/skills/handoff/` 一個字沒動，所以 `VERSION` 不動；3.16 指標改了，`source:` 標記跳到 `v2026-11-12.2`）：**`.agents/skills/handoff/SKILL.md` 指標的 `description` 補回權威版後來加的模式 0 句子與三個觸發詞**（建立交接機制、幫我建 HANDOFF、新專案骨架）。Codex 與 Antigravity 的 skill 載入器看的是這份指標的 `description`，權威版加了觸發詞、指標沒跟，同一句話在 Claude Code 會載入程序、在另外兩個工具不會。現在指標的 `description` 一律是「指標檔，權威版在 …——」加上權威版的原文，F14 的程序入口等價案例（`surfaces.compare_procedure`）會擋兩者分岔。🔴 **代價**同上一條：各專案要逐專案跑 `sync_project.py` 才拿得到，另行授權。
> 2026-11-12（**刻意不跳版**：`SKILL.md` 一個字沒動，所以 `VERSION` 不動；3.11 範本改了，`source:` 標記跳到 `v2026-11-12`）：**3.11 `pre-push-handoff.sh` 只看殼層指令（`tool_input.command`），不再拿整段 payload 找 `git push`**（決策書 Q27 (a)）。Codex 的 `PreToolUse` 沒有 matcher（3.17 刻意不加），每個工具呼叫都會跑到這支；舊版在 main 上有未推 commit、已提交差異沒動 HANDOFF 時，編輯工具的內容只要提到 `git push` 就被擋，Claude Code（matcher 只放殼層工具）卻不會——同一個動作在兩個工具結果不同，3.17 寫的「功能上沒問題」在這個情境不成立。`command` 的值是字串或字串陣列都收，不用 python。殼層指令裡只是提到 `git push`（例如 `echo`）仍會誤擋，跟以前一樣。🔴 **代價**：`VERSION` 沒跳，各專案的落後偵測不會提醒這件事；要讓專案拿到新版得逐專案跑 `sync_project.py`，這一步另行授權。
>
> 2026-11-06（**刻意不跳版**：`SKILL.md` 一個字沒動）：**3.10 `git-freshness.sh` 與 3.18 `ag-wrap.sh` 的訊息裡，`$變數` 後面緊接中文或全形標點的地方一律改成 `${變數}`**。macOS 內建的 `/bin/bash` 是 3.2，在 UTF-8 語系（`LANG=zh_TW.UTF-8` 之類，或 Python 3.7+ 對 C 語系的 locale coercion 把子程序設成 `C.UTF-8`）下，它會把緊接的多位元組字元的第一個位元組吃進變數名：`（branch=$branch）` 印成 `（branch=��`，「`$tool`」整個消失，`ag-wrap.sh` 找不到腳本時連 JSON 都吐不出來。判斷邏輯沒有壞（參數展開、`case`、`grep` 對中文都正常），壞的是每一句給人與模型看的結論。2026-11-06 第一次在 Mac 上跑 `verify_bootstrap.py` 時三項 FAIL 才發現——之前所有驗證都在 Windows 的 Git Bash（bash 5）上跑，那裡不會重現。兩檔 `source:` 標記更新為 `v2026-11-06`；`verify_bootstrap.py` 加「bash 3.2 多位元組變數」靜態檢查與負向測試，因為只有在 Mac 上實跑才看得到的錯，Windows 上的驗證永遠是綠的。
>
> 前一版 **2026-11-02.8**（2026-11-02／F16：自訂 ignore 規則進範本，本機驗收與 executable index mode 先於首 commit／發布；新增 local bare remote 部署生命週期測試。前一步 F12 完成協調邊界文件，原子 claim 依使用者決定留待另案；F13 同步範圍與 preflight 完成。）
>
> 前一版 **2026-11-02.7**（2026-11-02／F12：明列接力式 single-writer 的協調邊界、觀測 SHA 比對與失敗停止；原子 claim 未實作，沒有並行互斥保證。）
>
> 前一版 **2026-11-02.6**（2026-11-02／F10：共用核心優先於不同步的協定實例，明列 override 範圍與人工遷移需求；不在單一專案就地改 skill。）
>
> 前一版 **2026-11-02.5**（2026-11-02／F11：補 A／B／C 狀態表、ahead-only 與 fetch 失敗判讀、切分支後重驗；A4 只記差異，B7 驗最終快照；A5／C push 明列例外，hook 分岔提示改為停下等待指示。skill 與兩支 hook 標記更新至 .5。）
>
> 前一版 **2026-11-02.4**（2026-11-02／F06：AI push 提醒移除未提交 HANDOFF 放行；明列命令／remote／refspec 邊界，擴充情境與舊捷徑負向測試。skill 的過度保證一併修正，因此 VERSION 與 skill／3.11 標記更新至 .4。）
>
> 前一版 **2026-11-02**（**兩支部署後腳本的錯誤訊號與保障範圍修掉了：`verify_state.py` 不再把失敗吞成 exit 0，`check_docs.py` 補上交接快照檢查並停止把程式碼範例報成死連結。**這一輪動到 3.14 與 3.15 兩個範本，所以它們的 `source:` 標記跳到 `v2026-11-02.3`（今天第三個帶標記的改動）；`SKILL.md` 一個字沒動，`VERSION` 與版本行照鐵律 1 不跳。
> **F04（服務失敗仍回傳成功碼）**：舊版 `verify_state.py` **每一種情況都 `return 0`**——在檢查裡放一個 exit 7 的命令，畫面印著 `boom=rc7`，結束碼仍是 0（修正前實跑確認）。而這支腳本存在的理由正是「把接手查證壓成一個回合」，也就是說**它的結束碼本來就會被當成結論用**。現在每項檢查只回 PASS／FAIL／ERROR／SKIP／NOT_CONFIGURED 五種之一，最後印一行彙總：FAIL／ERROR→exit 2；SKIP 獨立列出（缺配置不等於通過），`--strict` 時 exit 3，真正可選的項目寫進 `OPTIONAL`；`NOT_CONFIGURED` 仍回 0（骨架還沒填不是故障，這是刻意保留的明示選擇）。另外兩件報告點到的事：HTTP 檢查可以填 `expect`（狀態碼或回應裡該出現的字），因為**只把「有回應」當成正常是不夠的**——200 配一個空的錯誤頁照樣會過；以及所有輸出都過一層遮罩，命令的 stdout／stderr 與例外訊息都不在我們控制下，而交接快照會被貼進 HANDOFF、對話與 issue。
> **F08（文件檢查器的保障範圍不足）**：三件事。①**第 6 項「工作中」欄位是「HANDOFF.md 有出現在輸入清單裡才驗」**，所以整份被刪掉或改名時它回報乾淨——那一刀正好把跨機器誤接棒防呆連根拔掉。新增第 7 項「交接快照」：`HANDOFF.md` 必須存在，必要欄位與章節齊備、不超過 80 行（那是 skill B6 的規則，在此之前**只有骨架自己這個 repo 在驗**，使用者的專案拿不到）。⚠️ 修正前實跑時發現「刪掉整份」在標準骨架上其實會 exit 2，但那是**別的文件指向它的連結斷了**——訊息叫你去修連結，不是叫你把快照補回來，而不互相連結的專案連這個副作用都沒有。②連結檢查把圍欄與行內程式碼先塗白，並正確解析`[x](path "title")` 與角括號寫法：舊版會把文件裡的程式碼範例報成死連結，而「這支腳本的 FAIL 可以無視」一旦被學會，真的死連結也跟著被無視。③**名字改成實際範圍**：它查機械可判定的腐化模式，不是完整的 Markdown 驗證器，也不判斷待辦是否真的完成（那是 B6）——舊名「文檔一致性檢查」聽起來像驗過全部，於是「通過」被讀成「文件沒問題」。`--docs-only` 可以只查文件。
> 守門人：新增第 42 項「verify_state 失敗訊號」（十個情境**全部實跑**：命令非零退出、HTTP 500、連不上、200 但內容不對、全綠、缺憑證的三種處置、未填、祕密遮罩）與第 43 項「交接快照檢查」（刪檔／超 80 行／缺章節／欄位重複都要 exit 2，`--docs-only` 要真的關得掉，連結誤報的 fixture 要 exit 0 而真的死連結仍要 exit 2——不誤報不能靠什麼都不報換）。**兩項都拿 `HEAD` 的舊範本實跑比對過**：舊 `verify_state` 兩個失敗情境都 exit 0，舊 `check_docs` 超 80 行 exit 0 且把 fixture 誤報成死連結，新版反過來。🔴 **代價要寫明：3.14 是 `sync_project.py` 的同步對象，而 `VERSION` 沒跳，所以各專案的落後偵測不會替你講這件事**——這一輪要手動同步，六個專案又多一個檔。寫這兩個測試時自己踩到兩次 fixture 的錯（把 fixture 放進 `docs/ai-notes/` 害它指向的 `README.md` 解析不到、拿「刪檔」去驗 `--docs-only` 而刪檔本身會製造真的死連結），都是**測試自己壞掉而畫面上像受測物壞掉**那一類。原始缺陷與證據見 [project-bootstrap-audit.md](project-bootstrap-audit.md) 的 F04／F08。）
> 前一版 **2026-11-02**（**維護工具的 Python 下限，以及五處「已修正的主張又在範本裡復活」，一起修掉了。這一輪沒有動 `SKILL.md`、也沒有動任何帶 `source:` 標記的範本，所以 `VERSION` 與那些標記都不跳（鐵律 1、2）、`sync_project.py` 零改動、六個專案沒有新的同步債。**
> **F14（Python 相容性前提未宣告）**：`verify_bootstrap.py` 用 `Path.read_text(..., newline='')`，而那個參數官方標「Changed in 3.13」；`write_text` 的 `newline` 也要 3.10。文件卻只說「`python` 不存在就用 `python3`」——**失敗的形狀是最壞的那一種**：舊版不會在啟動時說「版本太舊」，而是執行到那一行才炸成 TypeError，沒人會把它聯想到版本。兩支維護工具改用包著 `open(..., newline='')` 的 `read_lf`／`write_lf`，檔頭加 `MIN_PY = (3, 8)` 守門並清楚報錯；部署後兩支腳本本來就只用到 3.8 就有的 API，下限寫進 3.4 README 範本「`python` 不存在就用 `python3`」那一句旁邊。**部署後那兩支刻意不加守門**：`tools/check_docs.py` 是 `sync_project.py` 的同步對象，動它就得跳 `source:` 標記再把六個專案同步一輪，而 `VERSION` 不跟著動、落後偵測不會替你講——為一個「本來就跑得動」的版本宣告製造一筆無聲的同步債並不划算。下限是「不使用更新的 API」的**靜態擔保**，不是「在 3.8 上跑過」：這台機器只有 3.13，要變成實測得先有 CI。
> **F15（已修正的主張在範本／操作卡復活）**：五處一起修。①3.4 README 範本寫著「其他工具（Gemini／Codex）沒有 skill 機制」，而能力表那一格 2026-10-30 就實測成 ✅（Codex 讀 `~/.codex/skills/` 與 repo 的 `.agents/skills/`，Antigravity 原生讀 `.agents/skills/`）——**新部署的專案第一眼讀到的就是那一句**。②第 6 節說序號算「部署包當天的第幾次修改（跟版本行同一個號）」，`AGENTS.md` 鐵律 2 說算「帶 `source:` 標記的改動」，**兩種說法都不對**，而且今天就有反例（標記到 `.2`、版本行是裸的 `2026-11-02`）；兩邊一起改成「當天第幾個帶標記的改動，跟版本行**不保證同號**——版本行與 `VERSION` 只跟著 `SKILL.md` 走」。③協定範本與接棒 prompt 把 `verify_state` 寫成「有憑證才跑」，那會讓**不需要憑證的本機與公開檢查整批漏掉**，而缺憑證本來只該讓個別層級記 SKIPPED。④README 範本的 prompt A＝交棒、B＝接棒，跟 skill 的 A 接棒／B 交棒**正好相反**，於是每次指路都要先做一次字母翻譯、而翻錯沒有徵兆；字母直接取消，標題改成「收工時／開工時」並寫出它跑哪個模式。⑤「可攜層到哪都成立」「三層自動發生」兩句過度保證改成「不需要任何設定就讀得到」「把漏做的機會壓低」，並寫明**載入、遵循、執行是三種不同的證據**——遵循那一種目前唯一的量測是 2026-11-01 的六個收尾 session，git 結果全對、其中兩個仍然漏了改 session 名稱。
> 守門人：新增第 40 項「Python 版本下限」與第 41 項「已修正的主張沒復活」。後者**刻意不是一張禁句表**（F15 的改善建議明寫「新的措辭會再次繞過」）：每一項都綁在一個結構上——能力表的那一格、skill 的字母對應、同一條規則的單一定義；而「」裡的引用不算主張，因為鐵律 3 要求保留為什麼，而「為什麼」幾乎一定要引用被改掉的舊說法。**兩項都拿 `HEAD`（修正前）的內容實跑過：17 處矛盾與 3 處版本地雷全部判出來。**兩個踩到才知道的點：①掃 API 之前必須把註解與字串塗白，否則 `read_lf` 的 docstring 裡那句「不要改回 `Path.read_text(..., newline='')`」會被判成用法，而那種假陽性會逼下一棒把理由刪掉；②第一版的例外寫成「整行含 `handoff skill` 就放行」，而要擋的那一句所在的那一行開頭正好是「程序已經寫成 **handoff skill** 那個連結」——例外吃掉了唯一的目標，畫面上卻是 ok，所以例外縮到「命中的那一段」。原始缺陷與證據見 [project-bootstrap-audit.md](project-bootstrap-audit.md) 的 F14／F15。）
> 前一版 **2026-11-02**（**同步器的資料保全與失敗訊號修掉了。`sync_project.py` 只住在權威 repo、不部署，所以這一輪沒有任何 `source:` 標記要跳、也沒有副本同步義務——`VERSION` 與下面那條一樣不動。**
> **F02（同步刪掉同組的自訂 hook）**：舊版 `cur[at] = copy.deepcopy(g)` 把「含骨架 handler 的那一組」整組當成骨架的，於是專案把自己的 hook 加在同一組裡（`hooks` 陣列本來就放得下多個，完全合法的形狀）就會被**靜默刪掉**，而輸出還寫著「專案其他設定原樣保留」——一句主動的錯誤保證。所有權改到 **handler** 層：只換指向骨架腳本的那幾個handler，專案自己的留下；組層設定（`matcher`）仍歸骨架，但如果同一組裡有專案的 handler 而權威版要改 `matcher`，就**拒絕並印出新舊值**，不猜（改下去會連專案那個 handler 的觸發條件一起換）。另外兩種也拒絕：同一事件有兩組指向同一支腳本、分組方式跟權威版不同（舊版會在後面另外補一組，於是同一支腳本掛兩次——實測舊版真的讓 `pre-push-handoff.sh` 出現 2 次，開場印兩遍、防呆跑兩次）。`handler_scripts()` 連 `commandWindows` 一起看，否則 Codex 的 Windows 接線那種「只有 Windows 命令」的 handler 會被當成專案自己的而永遠不更新。
> **F03（失敗仍 exit 0，而且可能已部分寫入）**：舊版邊算邊寫，`WHOLE` 那一圈又在任何 JSON 驗證之前，所以一份壞掉的接線會在**覆蓋掉好幾個檔之後**才被發現；`FAIL` 只進訊息列、不影響結束碼，於是同步失敗一半照樣 exit 0，最後還印「全部都已經是 v…」。改成 `Plan` → preflight → `apply_plan`：任一項算不出來就整個目標跳過、**一個檔都不寫**；寫入逐檔走暫存檔 ＋ `os.replace`（半個 JSON 接線比舊接線更糟，它會讓整份設定失效）；中途失敗要列出已套用與未套用；目標不存在、是權威 repo 自己、或任何目標沒完成，都**非零退出**且不准宣稱最新版。舊版的實測：壞 JSON 加 `--write` 回 exit 0 而 `SKILL.md` 已經被覆蓋（查核報告只做到靜態確認，這次重現了），不存在的資料夾 exit 0 還印「全部都已經是最新版」。
> 守門人：新增第 38 項「同步安全」——F02 五種形狀（同組自訂 hook 要保留、matcher 衝突要拒絕且訊息要說出新舊值、重複組要拒絕、異常分組要拒絕、`commandWindows` 要認得）＋F03 四種（壞 JSON 零寫入、失敗非零、不存在目標非零、修好後照樣同步得動）。**逐項對舊實作跑過，九項全部是反的。** 原始缺陷見 [project-bootstrap-audit.md](project-bootstrap-audit.md) 的 F02／F03。）
> 前一版 **2026-11-02**（**占用判讀與版本方向兩個錯誤安全訊號修掉了，`SKILL.md` 一個字沒動、`VERSION` 刻意不跳**（鐵律 1），所以 3.10 `git-freshness.sh` 與 3.14 `check_docs.py` 的 `source:` 標記跳到 `v2026-11-02.2`——今天第一個帶標記的改動是 `SKILL.md` 的 `v2026-11-02`，這是第二個。🔴 **代價要寫明：`VERSION` 沒跳，所以各專案的落後偵測不會替你講這件事**，而這次落後的副本正好會印錯誤的綠燈，所以得手動跑一次 `sync_project.py`。
> **F01（占用誤判）**：兩支 hook 的 `case "$busy" in *無*)` 與 `check_docs.py` 的 `'無' in value` 都是子字串比對，於是**正常的任務名稱**就足以產生錯誤綠燈——標記寫著別台機器正在做、而 session 主題叫「修無效連結」，三處都會判成「無（已交棒）」。機器名比對有同一個洞：拿整列當乾草堆、`$me` 當針，所以 `desk` 與 `desk-win` 互為子字串時會讀成「同一台機器」，而那個方向的錯正好是放行。現在只有正規化後**完整等於**「無（已交棒）」才算空閒，其餘逐欄解析、機器欄要完整相等，欄位重複或解析不出機器欄都當成「有人在做」。`check_docs.py` 另外擋欄位重複與空機器欄。
> **F09（版本方向）**：偵測只比 `!=`，訊息卻寫死「落後」，所以本機比上游**新**的時候（權威版還沒 push，或有人就地改了副本）它會叫你跑 `sync_project.py`——那會把新的蓋成舊的。現在把序號補成三位數後用 `sort` 判方向，領先時改印「比上游新」並明寫不要同步。**同一個方向錯誤也在測試與第 5 節自檢清單裡**：兩處都拿 `1999-01-01` 當「上游最新版」來驗落後提示，而那是本機領先——那個 fixture 不但沒守住方向，還會把任何正確的修法判成 FAIL，所以修實作的人一定要連它一起改。
> 守門人：共用情境表加 4 個 F01 負向測試（主題含「無」、機器名含「無」、機器名互為子字串、欄位重複）＋1 個反向保險（已交棒前後有空白仍要 ✅），兩支 hook 同時套用；「工具欄（負向測試）」擴成「工作中欄位格式（負向測試）」共 4 種壞格式；版本偵測加「領先→不說落後」與「領先→勸退同步」。**退回舊實作實跑過，4 項確實 FAIL。**原始缺陷與證據見 [project-bootstrap-audit.md](project-bootstrap-audit.md) 的 F01／F09。）
> 前一版 **2026-11-02**（已交棒的 session 收到任何使用者新訊息，先恢復「工作中」，保留原時間與累計交棒次數；要改檔仍須重新走 A 模式。交棒次數記在 session 標題，只有 B 模式成功 push 才增加，不在 HANDOFF 累積 session 歷史。2026-11-02 使用者指出：agent 自主交棒後，同一 session 繼續對話卻留著「已交棒」，讓側欄狀態與實際活動不符。新增程序文字與入口觸發詞的負向測試；沒有新增逐訊息 hook 或模型探針。）
> 前一版 **2026-11-01.4**（Windows 的 Codex hook 改經 Git Bash 啟動器，保留 `.sh` 的判斷與結束碼；skill 的 B5 補上接線變更後必須重新審核、驗收實際執行的程序，所以 `VERSION` 同步跳版。）
> 前一版 **2026-11-01.3**（**把「改 session 名稱」寫進 A5 與 B9 的回報模板，變成必填的一行。**2026-11-01 量到：六個收尾 session（全 Sonnet）裡只有四個照「session 命名」改成 `↗　…｜已交棒`，另外兩個用的還是派工時給的標題；六個的 git 結果**全部正確**，漏的只有命名。**為什麼漏沒有量過**，所以這次不針對某個原因下藥——改的是「有沒有做」看不看得出來：改名發生在 session 的外殼上，repo 裡不留痕跡，`check_docs.py`、`git-freshness.sh`、pre-push 防呆三層**全都看不到它**，漏掉完全無聲，而無聲的漏跟「沒有這條規則」在畫面上一模一樣。回報那一行是它唯一能有的守門人：改了就寫改成什麼，工具沒有這個能力就寫 `不適用：<原因>`（仍然不必為此停下來問使用者）。B9 同時從散文改成有編號的三件事（改名→確認 origin 的「工作中」已清→回報）——漏掉的那兩個 session 把 B1–B8 **有編號**的步驟全做對了，而改名是整個 B 模式裡唯一沒有編號的動作。順手補掉一個讀文字就看得出來的洞：舊版 B9 寫「前面的 `YYMMDDHH｜<主題>` 原封不動」，那句話**預設 A5 已經改過名**，A5 漏掉時它無從執行，而那時候唯一拿得到的時間是「現在」——重算會寫出交棒的小時，正是同日把時間戳搬進 hook 要修掉的那種靜默錯誤；所以補一條恢復路徑：前綴從 `HANDOFF.md`「工作中」欄位抄（它記的就是開工時間與當時的 session 名）。守門人：`verify_bootstrap.py` 新增「改名寫進回報模板」，釘 A5／B9 兩個模板各有一行 `session：`、而且都留著「不適用」這個選項，附三個負向測試（刪 A5 那行、刪 B9 那行、拿掉「不適用」）。**為什麼跳版**：這次真的動到 `SKILL.md`，`VERSION` 要跟著走（鐵律 1）。**序號為什麼是 `.2` 而不是 `.4`**：序號算的是**當天第幾個帶 `source:` 標記的改動**，不是當天第幾次碰部署包——當天前兩次只改敘述、沒有任何標記動過，第三次改了 3.10 拿到 `v2026-11-01`，這是第二個。所以 `版本行` 從來沒有過裸的 `2026-11-01`，那不是漏編號，是當天第三次刻意不跳版的結果。另外，A5／B9 標題裡的行數**刻意沒跟著改**（A5 仍是「3–5 行」、B9 仍是「≤5 行」）：那兩個數字在 `README.md`、`handover-protocol.md`、3.10 的開場提醒等**六個地方**都有副本，其中兩處是 `sync_project.py` 的 `INSTANCE`、永遠不會同步——改一個數字就會製造一處無聲分岔，而模板現在剛好是 5 行、本來就落在原範圍內。下一棒看到「必填 5 行卻寫 3–5」不要去修它。**`.2` 是同一輪 15 分鐘前推出去的同一件事**，只差 A5／B9 標題的行數；因為那一版已經 push，而 `VERSION` 的同一個號不該對應兩份不同的 `SKILL.md`（那正是鐵律 2 寫下來要防的事），所以還原行數時一起跳到 `.3`。那 15 分鐘裡沒有任何副本同步過 `.2`——六個專案實測都還在 `v2026-10-31`，全域兩份當場重新覆蓋）
> 前一版 **2026-10-31**（「工作中」標記**加工具欄**，格式變成 `` `機器` ／ `工具` ／ `session 名`（可選） ``。舊格式只比機器名，於是**同一台機器換個工具**就落進「大概是你自己另一個視窗」的 🟡，而 A2.5 叫人去驗的那個證據（側欄有沒有 `㊣`）只有 Claude Code 有——同機器通常就是同一個工作樹，兩個 agent 會**即時互相覆寫**，比跨機器那個洞更貴（跨機器至少是兩份磁碟）。四處一起改，缺一處就白做：A5 寫標記時填工具名；A2.5 的「指向這台機器」拆成同工具／別的工具／沒有工具欄三列，判準不再綁側欄；`git-freshness.sh` 的同機器分支拆成同工具→🟡／不同工具→🔴；`check_docs.py` 第 6 項擋「標記在工作中卻沒有工具欄」——否則新格式會靜默退化回舊行為，而靜默退化跟「沒這個機制」在畫面上一模一樣。**工具名由寫標記的那一棒自己填**：模型知道自己是誰，三個平台一致；環境變數只拿來**加嚴**（偵測到的工具跟標記不符就 🔴），一致或認不出來都只給 🟡 並把問題丟回給模型答——跨工具啟動時變數會被繼承、會說謊（2026-10-31 實測，見「工具身分」一節）。新舊格式靠 session 名裡的全形豎線分辨，所以同一段邏輯讀得了還沒升級的專案，不必先問「這個專案升級了沒」）
> 再前一版 **2026-10-30.3**（`HANDOFF.md` 加**工作中標記**：接棒時（skill A5）確定要動手才把機器與 session 寫進 HANDOFF 並 push，交棒時（B6）改回「無（已交棒）」，下一棒接棒前（A2.5）先檢查。補的是跨機器接力的洞——A 機器忘記交棒就關掉，B 機器看到綠勾就接棒。既有三層防呆全都掛在「下一個動作」上，而**直接關掉視窗沒有下一個動作**；這個標記掛在「開工」，所以繞不過去。`git-freshness.sh` 同步讀它，並改掉那行誤導的 `✅ 與 origin 同步`——它只證明「本機沒落後」，不證明「沒有別台在做」，而一個綠勾會讓人直接往下做。`check_docs.py` 加第 6 項擋欄位不見，否則防呆會靜默失效。
> 同日第二件事：加 `VERSION` 檔 ＋ `tools/sync_project.py`，並讓 `git-freshness.sh` 比對上游版本。這之前「哪些專案裝了這套骨架」沒人記得住、也沒有任何東西負責把權威版發下去，所以同步一直是手工的——今天盤點就掃出 4 個專案留著上一輪沒 commit 的同步殘留。偵測放在開場這個必然發生的時刻，落後的專案會自己講；修則是一行指令。跟「工作中」標記同一招）。
> 同日第三件事（跳版 `.2`）：**改名與 git 解耦**。舊版 A5 把「改 session 名稱」排在「開工標記 push 成功」之後，於是沒有 `HANDOFF.md` 的專案（包括骨架自己這個 repo）、或這一輪只讀的 session，永遠到不了改名那一步——側欄上三個 session 全是 `↗ 已交棒`，一個 `㊣ 工作中` 都沒有過，正好是這條規則要解決的問題在它的老家失效。改名現在只看 session 狀態：回報完就 `㊣`、停下來等人就 `※`（不限「必須停下來問使用者」那張表），只有宣稱 git 事實的 `↗ 已交棒` 仍要等 push 成功。
> 同日第四件事（**刻意不跳版**，理由見下）：**修正「跨工具與跨平台」那張表的 Antigravity 一欄。**舊表寫「❌ 沒有 hook 機制」，那是 2026-08-05 的事實，重查官方文件已經不成立——它現在有 `.agents/hooks.json`，而且有 `SessionStart`。照舊表判斷會白白放棄一層防呆，而且錯得毫無徵兆：表上有查證日期，但**沒有人會因為日期舊就去重查**。`ARCHITECT.md` 與 `docs/ai-notes/handover-protocol.md` 兩份範本裡跟著錯的句子一併修掉。`.agents/hooks.json` 範本**刻意還沒附**，理由見那一節。**為什麼不跳版**：`VERSION` 不是「部署包的版本」，是**偵測器拿去跟 `SKILL.md` 的 `source:` 標記比對的那個值**（`git-freshness.sh` 的 `mine=` 那一行）。這次改的全是不同步的檔（兩份範本都在 `INSTANCE`），`SKILL.md` 一個字沒動——跳版就會讓每個專案永遠印「骨架落後」，而且跑 `sync_project.py` 修不掉（同步回去的 `SKILL.md` 標記還是舊的）。這個耦合 2026-10-30 當天就被 `verify_bootstrap.py` 的「同版→閉嘴」抓到，警告寫進 AGENTS.md 鐵律 1。
> 同日第五件事（**跳版 `.3`**，因為這次真的動到 `SKILL.md`）：**三個平台的能力全部重查一輪，修掉四個過期斷言、加一個保鮮期檢查。** ①**Codex 桌面 App 有 hooks**（App `26.506`／2026-05-08 起有 in-app 信任審核），舊表那句「沒有 hooks」是 2026-08-06 的實測——這是繼 Antigravity 之後**第二次**栽在同一種錯，所以這次不只改字：`verify_bootstrap.py` 加「跨工具表保鮮期」，查證日期超過 90 天就 fail。上一次的對策是一句警告，而**警告沒有擋住第二次**。②**`.agents/skills/` 不再只給 Antigravity**：`codex debug prompt-input` 印的 Skill roots 表證實 Codex 也讀 repo 的 `.agents/skills`，所以 3.16 那個指標檔的 `description` 從此必須寫滿觸發詞——那是它被發現的唯一依據，寫短就等於無聲地關掉一個入口。③**`CLAUDE.md` 改成只放 `@AGENTS.md` import**：Claude Code 從 v2.1.277 原生讀 `AGENTS.md`，但**有 `CLAUDE.md` 就不讀**，舊版那句「去讀 AGENTS.md」的指標反而壓掉了保證載入的機制，換來「它可能會去開那個檔」；順手把 `CLAUDE.md` 從 `sync_project.py` 的 `INSTANCE` 搬到 `PARTIAL`，否則這個修正只有新部署的專案拿得到。`extract()` 也跟著從「只取第一個區塊、事後改標題」改成「區塊依序對應檔名」，因為 3.2 從此是兩份不同的內容，而把其中一份合成在腳本裡就是讓範本有第二個家。④**`SessionEnd` 存在**（Claude Code 與 Codex 都有，Codex 的還會在閒置 30 分鐘觸發；Antigravity 沒有），所以「直接關掉視窗沒有下一個動作」只對一半的工具成立。結論沒變（標記還是寫在開工），但**理由改掉了**——鐵律 3 的重點是理由，理由錯了下一棒就會為了錯的原因重開一個已經定案的決定。⑤Antigravity 的兩個未知查清了：stdout 必須是 JSON `injectSteps`（裸 `echo` 會被丟掉），cwd 官方仍然沒寫、但可以用 stdin 的 `workspacePaths[0]` 繞過，所以「不附 `.agents/hooks.json` 範本」的理由從「查不到」換成「要先寫一層只做管線的轉接並實測」。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動，理由同上一條）：新增「工具身分：靠環境變數認得出『現在是哪個工具』嗎」一節。起因是「工作中」標記只比機器名，**同一台機器換個工具**就落進「大概是你自己另一個視窗」的 🟡，而 A2.5 叫人去驗的那個證據（側欄的 `㊣`）只有 Claude Code 有——同機器通常就是同一個工作樹，兩個 agent 會即時互相覆寫，比跨機器那個洞更貴。實測結論是**沒有跨廠商的共同變數**，而且在一個工具的殼層裡啟動另一個工具時變數會被繼承、會說謊，所以身分的權威來源只能是標記裡自己填的工具名。**修法 2026-10-31 已落地**（跳版 `2026-10-31`，四處一起改，見本檔最上面那行版本說明）。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動，理由同上一條。但這是部署包當天的**第二次**修改，所以新增那兩個檔的 `source:` 標記寫 `v2026-10-31.2`——標記算的是「這份副本來自部署包的哪一版」，`VERSION` 算的是「`SKILL.md` 的版本」，兩個號會這樣岔開是正常的，鐵律 1 要的就是別讓後者跟著前者動）：**補上 Antigravity 的 hook 接線**——`.claude/hooks/antigravity-wrap.sh`（3.18）＋ `.agents/hooks.json`（3.19）。這之前四個平面裡有一個完全沒有觸發層，而「不附」的理由已經在 2026-10-30 從「查不到」降級成「要先寫一層轉接」。轉接層只做管線：取 `workspacePaths[0]`、`cd` 過去、跑**同一支** `git-freshness.sh`、把它的 stdout 包成 `{"injectSteps":[{"ephemeralMessage":"…"}]}`。裡面沒有任何判斷規則可以跟權威版分岔，所以它只會在管線上壞掉——而管線是驗得出來的：`verify_bootstrap.py` 加「Antigravity 轉接層」六情境（正常注入、escaping 原樣還原、`cd` 真的進到 `workspacePaths[0]`、少參數、腳本不存在、stdin 不是 JSON），全部要求合法 JSON ＋ exit 0。**還沒驗到的是「Antigravity 真的會觸發它、而且吃這個設定檔形狀」**：官方只寫了檔案位置、事件名與 stdout 契約，沒有列設定檔欄位，而它沒有 headless 模式，要在 IDE 裡開一個 session 才看得到。所以第 5 節那一項**不是可選的驗收，是這兩個檔能不能留下來的條件**——沒看到訊息就把它們刪掉，一個不會觸發的 hook 比沒有更糟（它看起來像有防護）。失敗也刻意做成**吵的**：拿不到工作區或找不到腳本時注入一句 `[ag-wrap] ⚠️`，而不是安靜地什麼都不做。
> 2026-11-01（**刻意不跳版**：`SKILL.md` 一個字沒動，範本一個字也沒動，所以 `sync_project.py` 零改動。部署包當天**第二次**修改）：**`statusMessage` 那個未知量完了，而量的過程推翻了同一節裡另一句沒人懷疑過的話。** ①**互動 TUI 會顯示 `statusMessage`**（`0.166.0`）：它接在狀態行後面，畫面上是 `Working (1s • esc to interrupt) · <字串>`。配上「純文字 stdout 只進 agent 的 context、不給人看」那條，這個鍵在互動模式下是**使用者唯一看得到的那行字**，不是裝飾。②**互動 TUI 開場不跑 `SessionStart`，它跟著第一個 turn 才跑。** 舊版 3.17 與第 5 節都寫著「你按下同意的那個 session 不會跑，要再開一個才算」——那是合理的推論，實測是反的，而且它教人用**保證看不到**的方式驗收（開一個新 session、然後盯著開場）。兩處一起改掉。③**互動 TUI 的 hook 失敗是吵的**（`• Hook failed` ＋ `└ hook exited with code 1`），跟 `codex exec` 的全程無聲相反——所以驗收本來就該在互動模式做。④留一個**未解**：那一輪 hook 退出碼 1，而六分鐘前同一支腳本在 `codex exec` 下成功。兩個很有說服力的理由都被量掉了（「`bash` 解析到 WSL」：同一條啟動鏈獨立跑是 exit 0；「殼層偵測不同」：兩次 rollout 都寫 `<shell>powershell</shell>`，**包括成功那次**），所以照鐵律 3 標成未解、不補第三個理由。⑤把「PATH 上的 `bash` 是 WSL 那支」從 Antigravity 那節的死結**延伸到 Codex 這一面**（事實不重寫，只加一條指標＋補量到的退出碼 1）：骨架兩份接線寫的都是 `bash .claude/hooks/<腳本>.sh`，哪一支 `bash` 被解析到就決定這層防呆在不在；Antigravity 靠 3.19 的 shim 解掉了，Codex 這邊還沒有對應解法。**方法論**：探針刻意做成「自己寫 log ＋ `sleep 20`」，那 20 秒是把「沒跑」與「跑了但訊息只閃一下」分開的唯一辦法；而唯一不花模型呼叫的那條路（`codex debug prompt-input`）**不跑 hook**，所以量不到——這一項非得花一個 turn，花之前要先問使用者（這個 repo 的設計前提是只用訂閱額度）。**本節開頭那個 `查證日期：` 刻意沒動**：這一輪沒重讀任何官方頁面，只在本機實測，歸零會把「沒查」謊報成「查過」。
> 2026-11-01（**刻意不跳版**：`SKILL.md` 一個字沒動，範本一個字也沒動，所以 `sync_project.py` 零改動）：**`README.md` 的跨工具表從此有守門人。**保鮮期檢查只讀本檔那一節，而 README 那張表是它的轉述——於是它可以無聲分岔，而 README 偏偏是**人的入口**。`verify_bootstrap.py` 新增「README 跨工具表一致性」：比對同名列的判定符號、查孤兒版本號、查指回部署包的指標，並附四種分岔的負向測試（一個永遠回「一致」的比對器跟沒有這項檢查在畫面上一模一樣）。**加的當下就抓到一處已經發生的分岔**：「自動載入程序檔」×「Codex CLI」2026-10-30 在本檔改成 ✅、README 還停在 ⬜，一個多月沒人發現；連帶修掉 README 那句「只有 Claude Code 與 Codex CLI 有自動關卡」（四個平面現在都接得上，只是各自帶條件）。順手把 `FRESHNESS_PAGES` 裡 Codex 那兩頁搬家後的網址補成跟本節一致——fail 訊息的用途就是「照著重查」，指著 308 等於每次重查都先撞一次牆。為什麼不給 README 自己一個「查證日期」：見「這張表的保鮮期」那一節。
> 2026-11-01（**刻意不跳版**：`SKILL.md` 一個字沒動，所以 `VERSION` 不動。但這次**動到了範本**（3.10），所以 `git-freshness.sh` 的 `source:` 標記跳到 `v2026-11-01`——當天前兩次改的都只是敘述，沒有任何標記寫過 `v2026-11-01`，所以這是當天第一個帶標記的改動、不加序號。部署包當天**第三次**修改）：**開工改名的時間戳改由 hook 算好，而骨架自己這個 repo 補上它一直缺的兩層。** ①**3.10 多印一行開工改名提示**（`㊣　$(date +%y%m%d%H)｜<主題>｜工作中`）。改名規則 2026-10-24 就有，但時間戳一直要 agent 自己去取，而**取錯的時候是靜默的**：拿系統提示裡的日期去推小時就會寫出一個不存在的時刻，而那個時間戳的唯一用途正是「讓使用者在側欄認出這是哪一次」。hook 跑在 `SessionStart`，所以它算的值本來就比「回報完才去 `date` 一次」更接近接棒那一刻。**只印、不改名**：沒有任何工具讓 hook 改 session 名稱，所以那句話明寫「有這個能力的工具才做」——否則在 Codex CLI 與 Gemini CLI 上它就是一個每次開場都在要求失敗動作的指令。②**骨架自己這個 repo 補 `.codex/hooks.json`**，指向它自己那支`repo-git-check.sh`（**不是 3.17 的副本**——3.17 掛的是 3.10／3.11，這裡沒有那兩個檔）。在此之前這個repo 只有 Claude Code 這一面有開場檢查。③**`AGENTS.md` 補「開工第一件事」**：範本 3.1 一直有這一節，缺的反而是制度的來源自己——而開場 hook 只在 Claude Code 與審核過的 Codex 上會跑，`AGENTS.md` 才是Antigravity／Gemini／未信任的 Codex 唯一保證讀到的入口。🔴 **代價要寫明：3.10 改了而 `VERSION` 沒跳，所以各專案的落後偵測不會替你講這件事**，`--all` 掃到 7 個專案，其中 **6 個只差 `git-freshness.sh` 這一個檔**（`序號卡` 已完結，不碰），得手動跑一次 `sync_project.py`。這正是 `ARCHITECT.md` 記的 2026-09-13 事故的形狀（3.9 的 matcher 補了卻沒發下去，三個專案一個半月沒有徵兆），只是這次是**有意識地**選的：跳版會讓每個專案永遠印「骨架落後」而且同步修不掉（鐵律 1）。④順手補兩個守門人：`sync_project.py` 現在**拒絕把本 repo 自己當目標**——它的兩份接線跟 `WIRING` 清單同名卻指向自己那支 hook，手打一次 `sync_project.py .` 就會把它們改成指向這裡不存在的 `git-freshness.sh`（加擋之前實測預演真的印出兩個 `UPDATE`）；`verify_bootstrap.py` 從 27 項變 29 項（「本 repo settings.json」擴成「本 repo 兩份接線」、新增「sync 拒絕本 repo」，開工改名提示則加進兩支 hook 共用的那張情境表）。三項新檢查都做過**負向測試**：拿掉提示行、把接線改成指向 `git-freshness.sh`、拿掉那道擋，三項各自 FAIL。⑤**這個 repo 從此也在「Codex 要各審一次」那張清單上**（信任綁 `hooks.json` 的絕對路徑），所以它跟那六個專案一樣，接線在、但還沒真的跑過。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動。部署包當天第九次修改，範本內容也沒動）：**Codex hook 那兩個「還沒實測」做完了，而且其中一個的前提本身是錯的。** ①**`statusMessage` 不是 Claude 專屬的 key**——官方把它列在 hook 定義的正式鍵裡，語意是「Optional UI message」，所以 3.17 舊版問的「這個 Claude 專屬的 key 會不會被忽略」**問錯了問題**；實測 `codex exec` 的 stdout／stderr 都不會出現它，互動 TUI 沒量。②**沒有 matcher 就是每次都觸發，而且不分工具名**（同一個 session 量到 `Bash`×2 ＋ `apply_patch`×1 全部觸發），所以那份接線的 `pre-push-handoff.sh` 會跟著**每一個**工具呼叫跑一次——這是設計意圖，不是疏漏，但成本要知道。③最值得記的是沒人問的第三件：**信任綁的是 `hooks.json` 的絕對路徑，不是內容。** 記在 `~/.codex/config.toml` 的 `[hooks.state.'<hooks.json 絕對路徑>:<事件>:<組>:<序>']`，值是 `trusted_hash`；拿一份**逐位元組相同**（兩個檔 sha256 都一致）的接線換個資料夾跑，完全不信任、靜默跳過。**所以六個專案要各審一次，不是審一次全通。**④「失敗是靜默的」要加條件：**互動模式開場會主動問**（「Hooks need review／2 hooks are new or changed」＋Review／Trust all／Continue without trusting 三選一），**只有 `codex exec` 全程不吭聲**。舊版那句沒分互動與非互動，會讓人以為非得自己去打 `/hooks`。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動。部署包當天第八次修改，三個範本的內容仍然沒動）：**Antigravity 2.0 `2.28.2` 實測完畢——它會讀專案層 `.agents/hooks.json`，而且接線端到端成立。** 四個 surface 裡現在只剩 IDE `1.107.0` 不觸發（原因仍未解，而且已決定不追）。2.0 沒有命令列入口，所以 session 是用桌面自動化開的，但**偵測器仍然是寫檔不是看畫面**；量到 `SessionStart`／`PreInvocation`／`PostInvocation`／`Stop` 四個事件，cwd 同樣是 `.agents/`，沒有任何信任提示。另外補一條方法論紅字：**先驗儀器再測受測物**——第一版探針的 `command` 被轉義吃掉一個字元，而那種壞法在已知會觸發的 CLI 上同樣一聲不響，直接拿去測 2.0 就會產出一個假陰性，形狀跟 IDE 前兩輪的誤判一模一樣。只改敘述：接線、`verify_bootstrap.py`、`sync_project.py` 都沒動。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動。部署包當天第七次修改，而且**三個範本的內容都沒動**，所以 `source:` 標記不變）：**把既有專案的 Antigravity 接線補上，並在 3.18 補一條「從 Windows 提交會掉執行位元」的陷阱。** `sync_project.py` 刻意不做補裝（專案缺哪個檔就 skip 哪個），所以補裝是一次性動作，而且清單要先給使用者看過——這台機器 7 個裝過骨架的專案裡，`序號卡`（已完結、main 上那個未推的 commit 是刻意留的）不補，其餘 6 個各補 3.18／3.19／3.20。陷阱本身見 3.18 那條紅字：Unix handler 直接跑 `.sh`，而 Windows 提交出來的是 `100644`，Unix clone 上那條 handler 會靜默不動。**IDE 這一面同日決定不再追**（使用者不再用這個 surface），所以 Antigravity 剩下的唯一未知是 2.0——它沒有 headless，要人開一次 session 才測得到。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動。部署包當天第六次修改，所以新增三個檔的 `source:` 標記寫 `v2026-10-31.2`）：**把 Antigravity CLI 的 hook 接線補上，而且這次是端到端實測過的。** 新增三節範本：3.18 `.claude/hooks/ag-wrap.sh`（轉接層，只做管線）、3.19 `.agents/ag-hook.cmd`（Windows shim，找 Git Bash）、3.20 `.agents/hooks.json`（接線，只接 `SessionStart`）；舊 3.18「其他 skills 慣例」順延成 3.21。驗收方式從「看畫面」換成**讓 agent 自己把開場訊息背出來**：在重生的骨架上跑 `agy -p`，`[git-check]` 那句原文被引用出來了。shim 的三個設計約束都是踩到才知道的：①**全檔 ASCII**——中文 `rem` 註解被 OEM code page 誤讀後**整段被當成指令執行**，stderr 噴三行 `is not recognized`；②**只用單行 `if`、不用括號區塊也不用 label**——檔案是 LF 行末（`.gitattributes` 強制），而 `cmd.exe` 讀 LF-only 檔案時多行區塊會出錯；③**路徑用 `%~dp0` 與 `$0` 推，不依賴 cwd**——雖然實測 cwd 就是 `hooks.json` 所在目錄，但多押一個假設沒有好處。`.agents/hooks.json` 放兩個 handler（Unix 一條、Windows 一條），不合用的那條失敗而無害（實測只噴 stderr、不產生 stdout）。`PreToolUse` **刻意不接**：實測不明確回 `{"allow_tool": true}` 就等於拒絕，接上之後轉接層任何一次失敗都會擋掉使用者全部的工具呼叫。`verify_bootstrap.py` 加「Antigravity 接線」情境（轉接層的 JSON 與 escaping、shim 全 ASCII 且無括號區塊、`hooks.json` 的 key 與事件），`sync_project.py` 的 `WHOLE` 多兩份、新增 `AG_WIRING` 只換 `handoff-git-check` 那一個頂層 key。**IDE `1.107.0` 為什麼沒觸發仍然沒有解釋**，刻意留成未解問題。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動。部署包當天第五次修改）：**在 Antigravity CLI `1.4.7` 上把 hook 實測完，結論反轉。** `agy` 有 `--print` headless 模式（IDE 沒有，那正是前兩次測不準的根因），所以這次量得到：**專案層 `.agents/hooks.json` 會被讀、六個事件（`SessionStart`／`PreInvocation`／`PreToolUse`／`PostToolUse`／`PostInvocation`／`Stop`）全部觸發**；cwd 是 `hooks.json` 所在目錄（`.agents/`），與官方契約一致；`PreInvocation` 在 CLI 沒失效。三個意外：①**相對路徑可用、絕對路徑才脆弱**——`command` 照空白切 token、不解析引號，實測只有「不含空白＋不加引號」的絕對路徑跑得起來（四種組合逐一驗證），所以**上一條那個「骨架的不變量可能害探針測不出東西」的推論被推翻**，鐵律 5 跟 Antigravity 沒有衝突，在 Windows 上甚至是唯一寫得出來的形式；②**`PreToolUse` 不明確回 `{"allow_tool": true}` 就等於拒絕**——回 `{}` 的那一輪 agy 把 `read_file` 與 `run_command` 全擋掉了，這比「hook 不跑」危險得多；③**Windows 上接不起來的真正原因是 shim**：`cmd /c` 跑不了 `.sh`，PATH 上的 `bash` 是 WSL 的（本機還壞的），而 Git Bash 在 `C:\Program Files\Git\bin\bash.exe`、路徑含空白——`command` 寫不出來。**骨架仍不附接線**，但理由從「入口不存在」換成「缺一層 `.cmd` shim，而且有三件事要先解決」（shim 怎麼跨機器找到 Git Bash、Unix 不需要 shim 會變成兩種形狀、`PreToolUse` 接上後 shim 失敗等於擋掉全部工具呼叫）。IDE `1.107.0` 為什麼沒觸發**仍然沒有解釋**，刻意留成未解問題。只改敘述：接線、`verify_bootstrap.py`、`sync_project.py` 都沒動。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動。部署包當天第四次修改）：**重新界定上一條那輪探針的範圍——結論從「Antigravity 沒有 hook 這一層」縮回「骨架還沒附接線，而探針只覆蓋 IDE」。** 起因是使用者指出 **Antigravity 與 Antigravity IDE 是不同產品**，查證後成立：官方 blog「Choosing your surface」並排列出 **Antigravity 2.0（獨立桌面 App，無編輯器）／Antigravity CLI（`agy`）／Antigravity IDE（VS Code fork）／Python SDK** 四個 surface，而上一輪的探針只跑在 IDE `1.107.0` 上。三個洞因此開著：①2.0 與 CLI 沒測（本機三個 surface 都裝著，`~/.gemini/` 下三個目錄並存，`agy 1.4.7` 在 PATH）；②探針的 `command` **必然是相對路徑**（鐵律 5「接線路徑一律相對」＋跨平台防呆主動擋絕對路徑，而那輪 exit 0 過），而第三方指南說 `command` 必須絕對——**骨架自己的不變量可能保證了那支探針測不出東西**；③有第三方可重現實測說工作區 `.agents/hooks.json` 在三個 flavour 都會觸發，且其 log 路徑指向 IDE。同時修掉一個被過度一般化的斷言：全域路徑 `~/.gemini/<applicationName>/hooks.json` 的 `applicationName` **跟著 surface 走**，`antigravity-ide` 那一份只是 IDE 的，不能推成「Antigravity 的 hook 是機器層設定」。**「不附接線」這個決定沒變，變的是理由與重開它的門檻**——不再需要「比那次探針更強的證據」，只需要在實際使用的 surface 上用絕對路徑再測一次。只改敘述：接線、`verify_bootstrap.py`、`sync_project.py` 都沒動。
> 2026-10-31（**刻意不跳版**：`SKILL.md` 一個字沒動。部署包當天第三次修改）：**移除 Antigravity 的 hook 接線（舊 3.18 轉接層 ＋ 舊 3.19 `.agents/hooks.json`），舊 3.20 遞補回 3.18。**同日補上的那兩節，隔了幾個小時就被自己的驗收條件判出局——那一項本來就寫著「不是可選的驗收，是這兩個檔能不能留下來的條件」，實測結果是**專案層 `.agents/hooks.json` 完全不被讀取**（Antigravity IDE `1.107.0`／Windows），所以它們留不下來。證據與完整契約記在「跨工具與跨平台」的 Antigravity 那一節，包含**怎麼測才測得準**：前兩次用「畫面上看不看得到訊息」當偵測器，混進了「沒跑」與「跑了但輸出被丟掉」兩種可能；第三次改成讓 hook 自己寫檔，才分得開。`verify_bootstrap.py` 的「Antigravity 轉接層」六情境一併移除（**管線本身是通過的**——被推翻的不是轉接層會不會動，是它有沒有機會被呼叫），`sync_project.py` 的 `WHOLE`／`WIRING` 各少一份。

> 前幾版——
> 2026-10-24：版本號加序號（同一天改第二次起在日期後面加 `.2`、`.3`，因為日期粒度只能證明「不早於那一天」——當天改第三次時，三份副本的標記長得一模一樣，落後的那份看不出來）；handoff skill 加 **session 命名**：接棒／交棒／踩到「必須停下來問使用者」時各改一次 session 名稱。側欄上十幾個 session 全叫「接棒」認不出哪個是哪個，而其中「停在等人回答」的那個最需要被一眼看見。
> 2026-09-30：兩個 hook 腳本補上 `source:` 版本標記——鐵律第 2 條的作用是一眼認出落後的副本，而最無從用肉眼辨識新舊的正好是這兩支 `.sh`。
> 2026-09-20：handoff skill 加 **A6 回推補交接**，協定範本加對應的「漏交棒的補救」一節——三層防呆全都掛在「下一個動作」上，**直接關掉視窗沒有下一個動作**，所以這是程序責任不是工具責任。
> 2026-09-07：加入 `ARCHITECT.md`＝結構的唯一權威，以及 handoff skill 的**模式 0 建制**——在還沒有這套制度的資料夾裡，由 agent 照本部署包把骨架生出來，而不是憑印象重刻一份。
> 2026-08-05：加入 `handoff` skill、push 前防呆 hook，並把「殘留佔位符」從人工核取方塊改成 `check_docs.py` 的第 5 項檢查。
> 萃取自兩個實際運行的專案：一個是表單資料庫＋NAS＋custom widget 的案件審核工作流，一個是文本識別系統。兩個都是多模型、多機器協作。

## 交接自動化怎麼運作（本骨架的核心）

制度寫成文件，agent 不一定會照做。本骨架用三層把**漏做的機會壓低**（不是讓它保證發生——**載入、遵循、執行是三種不同的證據**，見「跨工具與跨平台」的可攜層那一段）：

| 層 | 檔案 | 什麼時候動 |
|---|---|---|
| **事實** | `.claude/hooks/git-freshness.sh`（SessionStart hook） | 每次 session 開始自動 fetch 一次，印出最多五行 `[facts]`：時間、與 origin 的落後與領先、未提交檔數、origin 的「工作中」原文。**只報事實，不下指示**（2026-11-13 起，v3 D12） |
| **參考** | `.claude/skills/handoff/SKILL.md` | 碰到才讀：異常判讀、交棒步驟、建制、理由。必守的條件在 `AGENTS.md` 的共用制度一節（2026-11-13 起，v3 第 5 節） |
| **AI push 提醒** | `.claude/hooks/pre-push-handoff.sh`（PreToolUse hook） | 有限字面判讀，缺已提交 HANDOFF 差異時提醒並阻擋；保障範圍見 3.11 |

**分工**：`docs/ai-notes/handover-protocol.md`＝**規則與理由**（為什麼、什麼算對）；skill＝**怎麼做**（指令、判讀表、模板）。
共用交接制度衝突時以同步的 skill 為準；協定保存理由與明確的專案 override，不覆蓋核心程序。這樣才不會讓不同步的舊實例推翻已升級的制度（2026-11-02／F10）。

**還沒有這套制度的資料夾走 skill 的模式 0（建制）**：使用者講一句「幫我把交接機制建起來」，agent 就照本部署包逐檔生成，而不是憑印象重刻——憑印象生出來的版本缺的永遠是最貴的那部分（每條規則後面的「為什麼」、hook 的邊界條件），看起來像那套制度，實際擋不住任何事。
這裡有個雞生蛋問題：skill 是部署**之後**才存在於專案裡的。所以模式 0 真正會被載入的地方是**全域副本**（`~/.claude/skills/handoff/`、`~/.codex/skills/handoff/`）；專案內那份仍保留模式 0，是為了讓副本可以無腦整份覆蓋，不必維護兩種版本。

## 跨工具與跨平台

> **查證日期：2026-10-30**（三邊官方文件全部重查，另在本機實測 Codex CLI `0.164.0`）。
> **這張表有 90 天保鮮期**：`verify_bootstrap.py` 的「跨工具表保鮮期」檢查超過就 fail，理由見本節最後一段。

**把三層拆成兩種可靠度**，不要假設哪個工具一定有自動化：

- **可攜層——不需要任何設定就讀得到**：`AGENTS.md` ＋ 純 Markdown 的程序檔。就算一個 hook 都沒掛，agent 讀 `AGENTS.md` 開頭那段就知道要先走交接程序。**正確性靠這一層，不靠 hook。**
  ⚠️ **但它保證的是「讀得到」，不是「做得到」**（2026-11-02／F15 加）：**載入、遵循、執行是三種不同的證據**，而下面那張表量到的只有第一種。遵循那一種目前唯一的量測是 2026-11-01 的六個收尾 session——git 結果全部正確，其中兩個仍然漏了改 session 名稱。所以這一層的正確說法是「到哪都**讀得到**、而且不必信任任何腳本」，不是「到哪都成立」；舊版那句「到哪都成立」把三種證據講成一種。
- **工具層——有就更省事**：hooks。它只是讓人不必記得，不是制度成立的前提。

**2026-10-30 的實測給了這個分層一個硬證據**：在一個 Codex 沒有信任過的資料夾裡，`AGENTS.md` 照樣被讀進 prompt（`codex debug prompt-input` 看得到），但 `.codex/hooks.json` 整層被跳過，**而且 stderr 一個字都沒有**。可攜層在未信任的專案成立，工具層不成立。這不是哪一家的實作瑕疵，是信任模型的必然——讀一份 Markdown 沒有風險，跑一支腳本有。

<!-- kit-table: tools -->

### Claude Code：`CLAUDE.md` 會擋住 `AGENTS.md`

Claude Code 從 v2.1.277 起原生讀 `AGENTS.md`，但預設值 `claude-md-or-agents-md` 的意思是：**工作目錄或其上只要有 `CLAUDE.md`／`.claude/CLAUDE.md`／`CLAUDE.local.md`，就不讀 `AGENTS.md`**。

所以「用一句話叫 Claude 去讀 `AGENTS.md`」的指標檔是最壞的組合——它壓掉了保證載入的機制，換來「它可能會去開那個檔」。官方文件直接點名這一種寫法：Claude 只有在它決定開那個檔的時候才看得到。2026-10-30 在骨架自己的 repo 上就是這樣——session 開場只拿到 `CLAUDE.md` 那三行，`AGENTS.md` 是後來照交接程序手動讀進來的。

修法在 3.2：`CLAUDE.md` 只放一行 `@AGENTS.md` import。它保證注入，而且在**不支援原生讀取的 session 也成立**（v2.1.281 之前的 Bedrock、關閉 telemetry 的 session、使用者把內建 plugin 關掉的情況）。所以不是「刪掉 `CLAUDE.md` 就好」——留著 import 版比刪掉更穩，而且官方說保留 import 永遠不會讓它讀兩次。

兩個附帶事實要記住：經設定讀進來的 `AGENTS.md` **不會觸發 `InstructionsLoaded` hook**，經 `CLAUDE.md` import 的會；`.claude/rules/*.md` **不計入**上面那個「有沒有 `CLAUDE.md`」的判定，會跟 `AGENTS.md` 並存，所以 Claude 專屬的細則放那裡，不要塞回 `CLAUDE.md`。

### Codex：CLI 與桌面 App 能力相同，差的是信任

**「桌面 App 沒有 hooks」是錯的，而且錯了快半年。** 舊表的依據是 2026-08-06 在 App `26.721.41059` 實測 `/hooks` 打不出來，但 App `26.506`（2026-05-08）就加了 hooks 的 in-app 信任審核流程，本機 App 版本已經是 `26.1023.51421`。這是**第二次**踩同一種坑（第一次是 Antigravity 那一欄），所以這次連帶加了工具檢查，見本節最後。

- **hooks 預設開啟**：`codex features list` 顯示 `hooks  stable  true`；要關是 `[features] hooks = false`（`codex_hooks` 是棄用別名）。
- **來源全部合併、不互相覆蓋**：`~/.codex/hooks.json`、`~/.codex/config.toml` 的 `[hooks]`、`<repo>/.codex/hooks.json`、`<repo>/.codex/config.toml`、plugin。同一層同時用兩種寫法會在啟動時警告。
- **兩道信任；非互動時失敗是靜默的，互動時會主動問**：專案的 `.codex/` 整層要先被信任（記在 `~/.codex/config.toml` 的 `[projects.'<路徑>'] trust_level`），每一支非 managed 的 hook 還要逐一審核。2026-10-30 實測：未信任的資料夾跑 `codex exec`，hook 完全沒跑而且沒有任何訊息。
  2026-10-31 把第二道閘量完（`0.164.0`）：**審核記在 `~/.codex/config.toml` 的 `[hooks.state.'<hooks.json 絕對路徑>:<事件>:<組>:<序>']`，值是 `trusted_hash = "sha256:…"`。**鍵裡含絕對路徑，所以**信任不隨內容轉移**——逐位元組相同的接線換個資料夾就要重審，**每個專案都得各審一次**。改過內容也要重審（雜湊變了）。
  互動模式**開場自己會問**（「Hooks need review／N hooks are new or changed」，三選一：Review hooks／Trust all and continue／Continue without trusting），所以一般不必自己打 `/hooks`；`codex exec` 則永遠不問、不印、直接跳過。🔴 **這句舊話被實測推翻了（2026-11-01／`0.166.0`）**：互動 TUI **開場根本不跑 `SessionStart`**，它跟著**第一個 turn** 才跑（`source` 仍是 `startup`）。所以按下同意的那個 session **跑得到**，只要你送出一句話；反過來說，開一個新 session 然後盯著開場看，是**保證**看不到的。舊話是個合理的推論，不是測量——而它教人用一種永遠不會成功的方式驗收（見第 5 節那一項）。
  自動化要繞過第二道閘只有 `--dangerously-bypass-hook-trust`（單次有效）；`requirements.toml` 與 `managed_dir`／`windows_managed_dir` 是企業／MDM 管的 managed 來源，不是給個人用的。
- 事件：`SessionStart`、`SessionEnd`、`PreToolUse`、`PermissionRequest`、`PostToolUse`、`PreCompact`、`PostCompact`、`UserPromptSubmit`、`SubagentStart`、`SubagentStop`、`Stop`、`Interrupt`。
- **`SessionStart` 的純文字 stdout 進的是模型的 context，不是畫面**（官方：plain text on stdout 「is added as extra developer context」；`UserPromptSubmit`、`SubagentStart` 同理，`PreToolUse` 等則**直接忽略**，`Stop`／`Interrupt`／`SubagentStop` 更是「invalid for this event」）。所以 Codex 這一面**使用者看不到 `[git-check]`，agent 看得到**——對骨架的用途（提醒 agent 走交接程序）剛好夠，但**驗收時不要去畫面上找那行字**，找不到不代表沒跑。要給人看的訊息得用 `systemMessage`。
- **量到的 payload（`0.164.0`／Windows）**：共同欄位 `session_id`、`transcript_path`、`cwd`、`hook_event_name`、`model`、`permission_mode`；`SessionStart` 多一個 `source`（實測值 `startup`），`PreToolUse` 多 `turn_id`、`tool_name`、`tool_use_id`、`tool_input`。指令在 `tool_input.command`，**所以 `pre-push-handoff.sh` 從 stdin 取 `command` 欄位比對 `git push` 的作法在 Codex 上成立**（不必為 payload 形狀另寫一份；2026-11-12 以前是拿整份 stdin 比對）。Windows 上殼層是 pwsh，但 `tool_name` 仍是 `Bash`。
- **`statusMessage` 在互動 TUI 真的會顯示（2026-11-01 實測，`0.166.0`）**：它接在狀態行後面——畫面上是 `Working (1s • esc to interrupt) · <statusMessage 的字串>`。`codex exec` 不顯示（非互動沒有 UI），這一點 `0.164.0` 與 `0.166.0` 一致。所以這個鍵在骨架的接線裡**不是裝飾**：配上上面那條（純文字 stdout 只進 agent 的 context、不給人看），互動模式下它是**使用者唯一看得到的那行字**。
- **互動 TUI 的 hook 失敗是吵的，不是靜默的**（同一輪實測）：畫面上出現 `• Hook failed` ＋ `└ hook exited with code 1`。這跟 `codex exec` 的「全程不吭聲」正好相反，所以**驗收要在互動模式做**——非互動模式連失敗都看不到。
- 🔴 **未解：同一支 hook 在互動 TUI 退出碼 1，而六分鐘前在 `codex exec` 下跑得好好的。** 同一個資料夾、同一份已信任的 `hooks.json`、同一支腳本；exec 那次寫出了 log，TUI 那次一行都沒寫，所以腳本的第一個指令都沒跑到。兩個看起來很有說服力的理由**都被量掉了**：①「`bash` 解析到 WSL」——把同一條啟動鏈（PowerShell → `bash -lc`）拿來獨立跑同一支腳本，exit 0 成功；②「codex 偵測到的殼層不同」——兩次 session rollout 的 `<environment_context>` 都寫 `<shell>powershell</shell>`，**包括成功那次**。照鐵律 3，這裡刻意不補第三個理由。要重開這題，先讓探針印出 hook 自己看到的 `PATH` 與 cwd，再比對兩次。
- **Windows 的 Codex 接線已補 Git Bash 啟動器（2026-11-01）**：真 repo 上實跑舊接線，互動 TUI 報 exit 1、context 沒收到訊息；同一支腳本經 PATH 的 WSL `bash` 報缺 `/bin/bash`，經 Git Bash 則 exit 0。新接線用 `commandWindows` 指向 3.17 的 `.cmd`，只做管線；另對 stdout 加純文字標頭，避開本版把 `[` 開頭當 JSON 的實測問題。修正後 CLI `0.166.0` 與桌面 App 內附 runtime `0.166.0-alpha.5.1` 的互動測試都收到 `HOOK_PRESENT`（後者是以該 binary 的 TUI 驗收，不冒充 App UI 已驗）。**稍早那組 exec／TUI 探針的差異仍未回溯查明，不能用新案例替它補原因。**
- 🔴 **「叫 agent 把注入背出來」這個測法在 Codex 上不成立。** 2026-10-31 實測：它回「I can't repeat hidden system or developer instructions」**直接拒絕複述**（Antigravity 那一面可以，見下）。要量注入有沒有到，就讓 hook 自己寫檔，或問一個不必複述的是非題（「只回 YES／NO：你的 context 裡有沒有以 `[git-check]` 開頭的行」）。**拿複述當儀器會得到假陰性，而假陰性長得就跟「hook 沒跑」一模一樣。**
- **skill 來源看得到，不必猜**：`codex debug prompt-input` 會印一張「Skill roots」表。2026-10-30 實測 0.164.0 列出 `~/.codex/skills`（**官方文件已經不列這個路徑，但實際仍然讀**）**與 repo 的 `.agents/skills`**。官方另外列 `$CWD/../.agents/skills`、`$HOME/.agents/skills`、`/etc/codex/skills`。
- `project_doc_max_bytes` 會截 `AGENTS.md`，所以**「開工第一件事」那一段必須待在 `AGENTS.md` 最上面**。

### Antigravity：2026-11-13 起不支援

需求決策書 v3 的 D8 放棄 Antigravity：轉接層、Windows shim 與 `.agents/hooks.json`（舊 3.18–3.20）移出部署包。2026-10-31 量到的 hook 契約、四個 surface 的差異與 Windows 死結的解法留在本檔 Git 歷史（`2026-11-12.4` 以前的版本），要重新支援時從那裡讀起，不要憑記憶重刻。

當時量到的專案層 hook 觸發情況（只作紀錄，部署包已不附接線）：

<!-- kit-table: antigravity-hooks -->

### `SessionEnd`：「關掉視窗就沒有下一個動作」現在只對一半的工具成立

Claude Code 與 Codex 都有 `SessionEnd`，Codex 的還會在**閒置 30 分鐘且沒有連線的 client** 時觸發——那正是「A 機器關掉視窗就消失」的場景。Antigravity 沒有這個事件。

**結論沒有變：「工作中」標記還是寫在開工（skill A5），不是收工。** 但理由要換掉一半：

- Claude Code 的 `SessionEnd` **不能擋下結束**，JSON 輸出被丟掉，整體預算預設只有 **1.5 秒**（可用單 hook 的 `timeout` 或 `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` 拉到最多 60 秒）。1.5 秒做不完一次 `git push`。
- 所以它能做的是**提醒離場的那一個人**（寫本機麵包屑、或 exit 2 把 stderr 給使用者看），救不了**下一棒**——下一棒靠的仍然是 A5 已經推到 origin 的那個標記。
- 而且四個平面有一個根本沒有這個事件。制度不能押在只有一部分工具有的東西上。

⚠️ **真要加 `SessionEnd` hook，1.5 秒那個預算就是陷阱**：一支被砍掉的 hook 看起來像防護、實際上不會完成，正是這份骨架最討厭的那一類。要加就把 `timeout` 明確寫上去，而且只做純本機寫檔／stderr，不碰網路。

### 工具身分：靠環境變數認得出「現在是哪個工具」嗎

> **實測日期：2026-10-31。** 這一節刻意不用本節開頭那個 `查證日期：` 字串——保鮮期檢查只讀全檔第一個，寫在這裡會被誤當成重查而把時鐘歸零。

要讓 hook 自動判斷「現在是哪個工具在跑」，前提是有一個共同欄位。**沒有。**

| 工具 | 自報的變數 | 證據強度 |
|---|---|---|
| Claude Code 2.1.309 | `CLAUDECODE=1`、`AI_AGENT=claude-code_2-1-309_agent` | session 內直接讀 env |
| Codex CLI 0.164.0 | `CODEX_VERSION`、`CODEX_SESSION_ID`、`CODEX_THREAD_ID`、`CODEX_TOOL_CALL_ID`（另有 `CODEX_CI=1`、`CODEX_SANDBOX_NETWORK_DISABLED=1`）；**沒有 `AI_AGENT`** | 實跑 `codex exec`，先把 `CLAUDE*`／`AI_AGENT` 全部 unset 並確認殘留 0 |
| Gemini CLI | `GEMINI_CLI=1` | **僅靜態**：bundle 內自述「`shell_command` 執行指令時會設」，沒實跑 |
| Antigravity IDE 1.107.0 | 未測 | 它**有** CLI：`antigravity-ide`（在 PATH，執行檔不叫 `antigravity`），`chat --mode agent` 可從命令列起一個 agent，但沒有 headless 列印模式，要在 IDE 裡跑指令才讀得到。**別跟 Antigravity CLI 搞混**——那是另一個 surface |
| Antigravity CLI 1.4.7（`agy`） | ✅ `agy -p "<prompt>"` | 真正的 headless：`--print`／`-p` 單輪、`--output-format json`／`stream-json`、`--print-timeout`。**hook 實測就是靠它做的**——IDE 那一面測不準的根因就是沒有這個模式 |

三個限制，寫進來是因為它們決定這件事能不能自動化：

1. **`AI_AGENT` 不是跨廠商慣例**，只是名字看起來像——Codex 一個字都沒有。所以偵測只能寫成逐家允許清單＋`unknown` 落底，而不是讀一個通用欄位。
2. **量到的是 shell tool 的環境，不是 hook 的環境**，而要判斷的那段邏輯住在 hook 裡。Codex 的 hook 環境沒量到：要過兩道信任（專案信任＋`/hooks` 逐一審核當前雜湊），而繞過它的旗標語意就是「跑沒審過的 hook」。合理的推論是 hook 作為子進程拿到原始 env、shell tool 那層還額外被 `shell_environment_policy` 過濾過，所以 hook 不會看到更少——但**那是推論不是測量**（鐵律 3）。
3. **跑的是 `codex exec`（非互動）**，`CODEX_CI=1` 很可能只有非互動才有，不要拿它當判準。像穩定身分標記的是 `CODEX_VERSION` 與 `CODEX_SESSION_ID`，但互動 session 同樣沒量。

🔴 **最重要的坑是反過來的：在一個工具的殼層裡啟動另一個工具，變數會被繼承。** 從 Claude Code 的殼層跑 `codex sandbox cmd /c set`，112 個變數裡 `CLAUDECODE=1` 與 `AI_AGENT=claude-code_…` 整批都在——Codex 的 session 會自稱 Claude Code。而 agent 互相呼叫正是最容易發生這件事的場景，也就是說這個誤判不是邊角案例。

所以結論：**環境變數只能用來加嚴，不能用來放寬。** 身分的權威來源是寫「工作中」標記的那一棒自己填的工具名（模型知道自己是誰，三個平台一致，不依賴任何變數）；變數只拿來交叉檢查「標記說是 A、但我看到 B」這種不一致，而且偵測不出來就退回只比機器名，**永遠不因為偵測失敗而放行**。

> 2026-11-13：開場 hook 不再解析「工作中」也不猜工具身分，只印原文，由模型判讀（v3 D12）。下面這段是 2026-10-31 的落地紀錄，保留作為「環境變數只能加嚴」的理由。

**落地在哪（2026-10-31，跳版 `2026-10-31`）**：

- 標記格式 `` `機器` ／ `工具` ／ `session 名`（可選） ``，由 skill **A5** 寫；工具名用慣用寫法（`Claude Code`／`Codex CLI`／`Gemini CLI`／`Antigravity`），因為 hook 比的是這個字串。
- 判讀表在 **A2.5**：同機器同工具→往下走（但要核對 session 名／開工時間）、同機器別的工具→停、同機器沒有工具欄→**當成別的工具處理**。分不出來的時候不往放行的方向猜。
- `git-freshness.sh`（3.10）的同機器分支依工具欄拆成 🟡／🔴。變數偵測只在「偵測到的工具跟標記不符」時加嚴，而且**兩家以上的簽章同時在場就不猜**——那正是被繼承的樣子。偵測一致或認不出來都只印 🟡，並把「你自己是不是 X」這一句明文丟給模型答：模型知道答案，hook 不知道。
- `check_docs.py` 第 6 項擋「標記在工作中卻沒填工具欄」，判別子是 session 名裡的全形豎線（`｜`）——`機器` ／ `工具` 的第二欄不會有它，`機器` ／ `session 名` 的第二欄一定有。

### 這張表的保鮮期（為什麼要用工具擋）

兩次踩同一種坑：Antigravity 的 hooks（2026-08-05 的事實，2026-10-30 才發現過時）、Codex 桌面 App 的 hooks（2026-08-06 的實測，同樣到 2026-10-30 才發現）。第一次之後加的對策是一句警告——**而警告沒有擋住第二次**。原因很直白：表上一直都有查證日期，但沒有人會因為日期舊就主動重查。

所以 2026-10-30 起改用工具：`verify_bootstrap.py` 的「跨工具表保鮮期」會讀本節開頭那個 `查證日期：`，**超過 90 天就 fail**（鐵律 4 要求 exit 0 才算改完，所以它擋得住）。要暫時跳過是 `BOOTSTRAP_FRESHNESS=off`。重查就是這幾頁：`code.claude.com/docs/en/hooks`、`code.claude.com/docs/en/memory`、`learn.chatgpt.com/docs/hooks`、`learn.chatgpt.com/docs/build-skills`、`antigravity.google/docs/hooks`、`antigravity.google/docs/rules`。⚠️ **Codex 那兩頁 2026-10-31 搬家了**：舊網址 `developers.openai.com/codex/hooks`／`/codex/skills` 回 308，而且 skills 那頁連路徑名都換了（`build-skills`），所以**不能只換網域**。轉址還在，所以舊連結不算壞——但清單的用途是「下一棒照著重查」，指著轉址就等於每次重查都先撞一次牆。

為什麼這次不怕變成「bump 一個欄位就能過」（那正是 `pre-push-handoff.sh` 被否決的理由之一）：**頻率差了兩個數量級**。pre-push 是每次推進度都誤報，`off` 會變成反射動作；90 天一次、一年看到四次，反射形不成，而且每一次都伴隨一個真正該做的動作。但天花板要講明白：**這個檢查只能保證有人看過日期，不能保證有人真的重查。** 它買到的是「必須有意識地決定」，不是正確性。

**`README.md` 那張表由一致性綁住，不另給一個時鐘**（2026-11-01 加）：它是這張表的轉述，而保鮮期只讀這一份，所以它可以無聲分岔——事實在這裡被重查、改對，入口文件留在舊事實上。`verify_bootstrap.py` 的「README 跨工具表一致性」比對兩張表**同名列的判定符號**，再查 README 有沒有寫出這一節已經沒有的版本號、有沒有留著指回部署包的指標。**不給 README 自己的「查證日期」**：那是同一個事實的第二個時鐘，兩個時鐘一定會分岔（本節的 Antigravity 那段就為此刻意把字串寫成 `實測日期：`，避開保鮮期只讀全檔第一個 `查證日期：` 的行為）。綁住一致性之後，單一時鐘同時罩得住兩張表。加這一項的當下就抓到一處已經發生的分岔：「自動載入程序檔」×「Codex CLI」這一格 2026-10-30 在這裡改成 ✅，README 還停在 ⬜。天花板一樣要講明白：**它守判定符號、版本號與指標，守不了散文**。

**共同前提**：兩個 hook 是 bash 腳本，macOS／Linux 內建；Windows 需要 Git for Windows 附的 bash。Python 腳本在 macOS 上常常只有 `python3` 沒有 `python`——所有文件一律寫「`python` 不存在就用 `python3`」。

---

## 0. 這套骨架在解決什麼問題

跨 session、跨模型（Claude／Gemini／Codex）、跨機器（PC↔Mac）協作時，反覆出現的失效模式與對策：

| 失效模式（都真的發生過） | 對策（本骨架的組成） |
|---|---|
| AI 對著**過期的本機快照**工作數小時，最後 commit 造成分岔 | `.claude/hooks/git-freshness.sh`：session 一開始自動 fetch 並把落後／分岔警告注入對話 |
| 交接文件愈寫愈長，接手者要讀 20 分鐘才知道現在做到哪 | **三層分工**：持久知識→`docs/ai-notes/`；當下狀態→`HANDOFF.md`（≤80 行、不累積歷史）；歷史→Git |
| 同一個事實散在三個檔案，各自演進到互相矛盾 | **每個事實只有一個家**：其他地方只放指標，不複製內容 |
| 文件說 A、實際是 B，AI 照文件做就炸 | **以實況為準**＋`tools/verify_state.py` 一鍵查證＋`tools/check_docs.py` 查死連結／過期網址／缺日期 |
| 純文件修正被「等功能驗收」擋住，接手者拿到過期文檔集 | **兩類分支**：功能分支需驗收才併；文件／基建分支驗證過就能併 `main` |
| 連線失敗被誤判成「本機沒有憑證」，寫下錯誤結論 | **SKIPPED 判準**：先排除「設定沒帶到」才能標 SKIPPED；禁止自行挖憑證 |
| 祕密／運行資料被推上 GitHub | 鐵律＋`.gitignore`＋提交前固定檢查 staged 清單 |
| 交接品質看 agent 心情：有時漏驗證、有時忘了寫 HANDOFF 就 push | `handoff` skill 把協定變成**可執行程序**（判讀表、指令、停止判準）；SessionStart hook 自動提醒，AI push 提醒檢查已提交 HANDOFF 差異（有限覆蓋，見 3.11） |

**保留「為什麼」**：每條規則後面都有一次實際事故。移植時不要把理由砍掉——理由沒了，下一棒就會覺得規則是多餘的而繞過它。

---

## 1. 部署前訪談（AI 執行時必做，一次問完）

把答案填進下列佔位符；**檔案裡不能留下任何 `{{...}}`**。

| 佔位符 | 意義 | 例 |
|---|---|---|
| `{{PROJECT_NAME}}` | 專案中文名 | 客戶報價系統 |
| `{{ONELINER}}` | 一句話說明它是什麼、給誰用 | 業務用的報價單產生與追蹤系統，資料在 Postgres，介面是 Next.js |
| `{{GH_OWNER}}` / `{{GH_REPO}}` | GitHub 帳號／repo 名 | `Baliyoho` / `quote-system` |
| `{{GH_VISIBILITY}}` | `private` 或 `public` | private |
| `{{LANG}}` | 使用者溝通語言 | 繁體中文 |
| `{{TZ}}` | 時區（HANDOFF 時間戳用） | Asia/Taipei |
| `{{TODAY}}` | 部署當天日期（絕對日期，YYYY-MM-DD） | 2026-07-26 |
| `{{SECRETS}}` | 絕不進 Git 的憑證檔 | `.env`、`*.pem` |
| `{{RUNTIME_DIRS}}` | 絕不進 Git 的運行／資料目錄 | `data/`、`backups/`、`uploads/` |
| `{{STACK_DIRS}}` | 專案主要程式目錄（寫進 README 檔案結構） | `src/`、`migrations/` |
| `{{VERIFY_TARGETS}}` | 「一鍵驗證」該查什麼（沒有就先留空） | 健康檢查 API、docker 容器狀態 |

追問一句就好：**「這個專案有沒有已知的『絕對不能做』的操作？」**（例：不能直接改資料庫檔、不能在正式環境跑 migration）。有的話寫進 AGENTS.md 鐵律第 4 條之後；沒有就先放空著，日後踩到再補。

---

## 2. 要建立的檔案結構

```text
{{GH_REPO}}/
├─ README.md                        ← 人的入口（第一次接觸專案看這份）
├─ AGENTS.md                        ← AI 的入口：共用制度一節（≤40 行）＋專案鐵律與連線資料
├─ CLAUDE.md                        ← 指標，指向 AGENTS.md
├─ GEMINI.md                        ← 指標，指向 AGENTS.md
├─ HANDOFF.md                       ← 當下工作狀態（≤80 行，不累積歷史）
├─ ARCHITECT.md                     ← 專案結構的唯一權威（只有結構變動才改）
├─ .gitignore
├─ .gitattributes
├─ .claude/                         ← Claude Code 讀這裡
│   ├─ settings.json                ← hook 設定（進 Git）
│   ├─ settings.local.json          ← 各機器本地設定（不進 Git）
│   ├─ hooks/git-freshness.sh       ← SessionStart：fetch 一次，只報事實（最多五行 [facts]）
│   ├─ hooks/pre-push-handoff.sh    ← PreToolUse：AI push 提醒（有限覆蓋，見 3.11）
│   ├─ hooks/codex-hook.cmd         ← Codex 的 Windows 啟動器：找 Git Bash、加純文字標頭、保留結束碼
│   ├─ skills/handoff/SKILL.md      ← 交接程序的參考入口（碰到才讀；必守條件在 AGENTS.md）
│   ├─ skills/handoff/mode-*.md、reasons.md ← 參考檔：模式步驟與理由（共五個，與入口同版本）
│   └─ skills/<其他>/SKILL.md       ← 需要時才建：可重複使用的操作食譜（權威版）
├─ .codex/hooks.json                ← Codex 讀這裡：掛上面同樣那兩個腳本，不另寫一份
├─ .agents/skills/handoff/SKILL.md  ← Codex 讀 .agents/skills/：指向權威版的指標
├─ .agents/skills/<其他>/SKILL.md   ← 需要時才建：同樣只放指標，不複製內容
├─ docs/
│   ├─ ai-notes/
│   │   ├─ handover-protocol.md     ← 交接協定（接棒／交棒／分支模型）
│   │   └─ roadmap.md               ← 持久待辦總表
│   └─ mockups/                     ← 選用：與使用者定案的 UI 規格
└─ tools/
    ├─ check_docs.py                ← 文件與交接快照的機械檢查
    └─ verify_state.py              ← 一鍵現況查證（骨架，依專案填）
```

**選用目錄**（有需要再建，不要為了對齊而空建）：`tests/`、`deploy/`、`apps/`、`archive/`。

---

## 3. 各檔案內容（照抄，只換佔位符）

### 3.1 `AGENTS.md`

> **2026-11-13 起（v3 D11、D12）**：開始與結束標記之間是共用制度，由部署包管理，≤ 40 行；專案只能在標記外面加自己的鐵律與連線資料，全檔 ≤ 100 行。共用制度只寫目標、模型不會自己知道的事與不可違反的條件，不寫逐步程序；開始標記裡的 `source:` 版本給開場 hook 比對上游用。

````markdown
<!-- kit-file: AGENTS.md -->
````

### 3.2 `CLAUDE.md` 與 `GEMINI.md`（2026-10-30 起兩檔內容不同，下面兩個區塊依序對應）

> **`CLAUDE.md` 只放一行 import，不要寫「去讀 AGENTS.md」那種句子。** Claude Code 從 v2.1.277 起原生讀 `AGENTS.md`，但**有 `CLAUDE.md` 就不讀**；而用文字叫它去讀，官方的說法是 Claude 只有在它決定開那個檔的時候才看得到。`@AGENTS.md` 是 import，內容保證進 context，而且在不支援原生讀取的 session（舊版 Bedrock、關閉 telemetry、使用者關掉內建 plugin）也成立——所以不是「刪掉 `CLAUDE.md` 就好」，留著 import 版比刪掉更穩。理由全文見開頭「跨工具與跨平台」。

````markdown
<!-- kit-file: CLAUDE.md -->
````

> `GEMINI.md` **不改成 import**，維持指標寫法：Antigravity 原生讀 `AGENTS.md`，這一份只是給還不會讀 `AGENTS.md` 的舊版工具的保險，而它支不支援 `@` import 沒有文件可查——猜錯的話會是靜默失效。若也用其他工具，比照再加一份指標檔即可，**內容永遠只是指標**。

````markdown
<!-- kit-file: GEMINI.md -->
````

### 3.3 `HANDOFF.md`（初始狀態，之後每次交棒覆寫）

````markdown
<!-- kit-file: HANDOFF.md -->
````

### 3.4 `README.md`

````markdown
<!-- kit-file: README.md -->
````

### 3.5 `ARCHITECT.md`（結構的唯一權威）

> **為什麼要有這一份**：結構問題（「這個東西放哪」「哪一份是權威版」「資料從哪進來」）本來散在 README 的檔案結構、AGENTS.md 的知識庫地圖與每個人腦袋裡，於是每一棒都要重新拼一次，拼錯了就照著不存在的路徑動手。
> 它與 `HANDOFF.md` 是**故意相反的節奏**：HANDOFF 每次交棒都覆寫，本檔只有結構真的變了才動——一份會頻繁改的結構圖，接手者遲早不會再相信它。

````markdown
<!-- kit-file: ARCHITECT.md -->
````

### 3.6 `docs/ai-notes/handover-protocol.md`

````markdown
<!-- kit-file: docs/ai-notes/handover-protocol.md -->
````

### 3.7 `docs/ai-notes/roadmap.md`

````markdown
<!-- kit-file: docs/ai-notes/roadmap.md -->
````

### 3.8 `.claude/skills/handoff/SKILL.md`、`.claude/skills/handoff/mode-a.md`、`.claude/skills/handoff/mode-a-stop.md`、`.claude/skills/handoff/mode-b.md`、`.claude/skills/handoff/mode-0.md`、`.claude/skills/handoff/reasons.md`（交接程序，本骨架的核心）

> **這一份就是「教 agent 自動交接同步」的東西。** 內容照抄不要改，包含檔頭的 `source:` 版本標記——它讓你日後能一眼看出某個專案的副本是不是落後了。
> 檔案裡的 `docs/ai-notes/handover-protocol.md` 刻意寫成純路徑而非連結，這樣同一份文字放進全域 `~/.claude/skills/` 也不會產生死連結。
> **2026-11-10 起這支 skill 是一個目錄、六個檔**（決策書 F22：單檔 22,040 字元，正常接棒只需要其中一小部分）。入口與 `mode-a.md` 是新寫的摘要，其餘四個檔是從單檔逐字搬來的；六個檔的 `source:` 標記必須是同一個版本，同步時整個目錄一起覆蓋。下面六個區塊依序對應標題上的六個檔名。

**`.claude/skills/handoff/SKILL.md`**——參考檔入口：碰到才讀（2026-11-13 起，v3 第 5 節）。適用判斷、要細節時讀哪個檔、全程禁令、必須停下來問人的清單；session 命名指回 `AGENTS.md`。

````markdown
<!-- kit-file: .claude/skills/handoff/SKILL.md -->
````

**`.claude/skills/handoff/mode-a.md`**——接棒的正常路徑。**新寫的摘要**；跟下一份衝突時以下一份為準。

````markdown
<!-- kit-file: .claude/skills/handoff/mode-a.md -->
````

**`.claude/skills/handoff/mode-a-stop.md`**——接棒的完整判讀表與異常處理（狀態轉移、A1–A6 原文）。開場 `[facts]` 有不正常的值時才讀。

````markdown
<!-- kit-file: .claude/skills/handoff/mode-a-stop.md -->
````

**`.claude/skills/handoff/mode-b.md`**——交棒 B1–B9、中途同步 C、交棒計數（原文）。

````markdown
<!-- kit-file: .claude/skills/handoff/mode-b.md -->
````

**`.claude/skills/handoff/mode-0.md`**——建制 0-1–0-8（原文）。

````markdown
<!-- kit-file: .claude/skills/handoff/mode-0.md -->
````

**`.claude/skills/handoff/reasons.md`**——理由、事故與 session 命名細則（原文）。要改、質疑或想繞過規則之前才讀。

````markdown
<!-- kit-file: .claude/skills/handoff/reasons.md -->
````

**同步規則（重要）**：這個 skill 目錄（六個檔）會同時存在於 ①本部署包 ②每個專案的 `.claude/skills/handoff/` ③（選用）全域 `~/.claude/skills/handoff/`。
⚠️ **在 Claude Code 裡，③ 會蓋掉 ②**（2026-11-12 在 2.1.321 實測，決策書 Q28）：兩處都有同名 skill 時，skill 清單與 Skill 工具用的是家目錄那份，專案那份只靠入口一句「專案有就讀那裡」救回來。所以全域副本一定要跟部署包同版；不同時 3.10 的開場 hook 會印一行 🟡 列出哪些檔不一樣。
**權威版是本部署包**；要改就改這裡，再覆蓋下去，不要在單一專案裡就地改——那正是「同一個事實有多個家」的典型失控起點。

### 3.9 `.claude/settings.json`

````json
<!-- kit-file: .claude/settings.json -->
````

> Codex 的接線見 3.17——它掛的是**同樣這兩個 `.sh`**，不要複製第二份腳本進 `.codex/`。兩份各自演化就會出現「Claude 端會擋、Codex 端不會擋」的不對稱。

> 🔴 **腳本路徑前面那個 `$(git rev-parse --show-cdup)` 不是裝飾，拿掉就只有「從 repo 根目錄開的 session」才有防護。** hook 的 `command` 以 **session 的 cwd** 執行（Claude Code 的 handler「runs in the current directory」；Codex 官方文件同樣明寫，並直接建議改從 Git root 解析 repo hook），而人會從子目錄開 session——`cd tools && claude`。那時候 `bash .claude/hooks/git-freshness.sh` 是 **exit 127、No such file**，而 **SessionStart 失敗跟「檢查過了沒事」在畫面上一模一樣**：落後的本機、別台機器的「工作中」標記、骨架落後提醒三件事同時無聲消失。`--show-cdup` 回傳的是**到 repo 根目錄的相對路徑**（根目錄是空字串、子目錄是 `../`），所以修掉這個洞之後接線裡**仍然沒有任何絕對路徑**，鐵律 5 原封不動；不在 git repo 裡時它是空字串，行為退回跟舊版一樣（多一行 git 的 fatal 到 stderr，刻意不消音——這套骨架的失效一向是太安靜而不是太吵）。2026-11-02 在 `tools/` 下重現 exit 127，修完在 root／`tools/`／`docs/ai-notes` 三處都正常；`verify_bootstrap.py` 的「接線 cwd 定位」把這三處、Windows 啟動鏈與兩個負向測試（舊形式、混合斜線）一起釘住（F05）。

### 3.10 `.claude/hooks/git-freshness.sh`

> **2026-11-13 起只報事實（v3 D12）**：fetch 一次，印出最多五行 `[facts]`，不下指示、不判讀。檔名沿用 `git-freshness.sh`，3.9 與 3.17 的接線因此不必改。
>
> Windows 需要 Git for Windows 附的 bash（Claude Code 內建可用）。建立後在 macOS／Linux 上加執行權限：`chmod +x .claude/hooks/git-freshness.sh`。

````bash
<!-- kit-file: .claude/hooks/git-freshness.sh -->
````

### 3.11 `.claude/hooks/pre-push-handoff.sh`（AI push 提醒）

> **AI push 提醒，不是 Git 原生 pre-push 或發布保證。** 只對殼層指令（payload 的 `command` 欄位）含字面 `git push` 的呼叫，依目前分支與本機 `origin` 追蹤 ref 判斷；不解析 shell、選項、實際 remote 或 refspec。`git -c … push`、GUI、間接執行的 script 可能漏判，指令裡只是提到 `git push`（例如 `echo`）也可能誤擋；編輯檔案等非殼層工具的內容提到它不算（2026-11-12，決策書 Q27）；feature 分支與判斷不了時放行。需要硬閘門時另評估 Git 原生 pre-push 與伺服器保護。
> 2026-11-02／F06：移除「工作樹正在改，等一下會提交」的放行假設。staged／unstaged 修改都不會隨 push 上傳，只有已提交的 HANDOFF 差異才算；開工標記與交棒快照都能通過，**不代表內容已驗證或已交棒**。
> 退出碼 2 會擋下該次 Bash 呼叫並把訊息交給模型——這是唯一能讓 agent「當場改走交棒程序」的機制，警告訊息模型不一定看得到。

````bash
<!-- kit-file: .claude/hooks/pre-push-handoff.sh -->
````

### 3.12 `.gitignore`

````gitignore
<!-- kit-file: .gitignore -->
````

> 上面兩個佔位符必須依訪談替換成 Git ignore patterns，**每行一個、不含 Markdown 反引號或頓號，不可用 `!` 反向納入祕密**；文件其他位置仍可用反引號列出檔名。不要只填文件卻漏掉這份範本（2026-11-02／F16：原先追加規則的指令在圍欄外，測試抽不到）。再加語言／框架專屬項目（`node_modules/`、`.venv/`、`dist/`、`.build/` …）。**寧可多擋不要少擋。**

### 3.13 `.gitattributes`

````gitattributes
<!-- kit-file: .gitattributes -->
````

### 3.14 `tools/check_docs.py`

````python
<!-- kit-file: tools/check_docs.py -->
````

### 3.15 `tools/verify_state.py`（骨架，部署後填 CHECKS）

````python
<!-- kit-file: tools/verify_state.py -->
````

### 3.16 `.agents/skills/handoff/SKILL.md`（給 Codex 的指標）

> **2026-10-30 起這個檔不再只給 Antigravity。** `codex debug prompt-input` 印的「Skill roots」表證實 Codex CLI `0.164.0` 也把 repo 的 `.agents/skills/` 當成 skill 來源（官方另外列 `$CWD/../.agents/skills`、`$HOME/.agents/skills`、`/etc/codex/skills`）。Antigravity 一樣原生辨識專案根目錄的 `.agents/skills/`。所以這一個檔現在同時是兩個工具的專案層入口。
> 仍然**只放指標、不放內容**——複製一份程序在這裡，兩份就會各自演化，最後一份說要先 fetch、另一份沒說。
> ⚠️ **但既然它會被自動發現，`description` 就必須保持完整的觸發詞**：agent 是看 `description` 決定要不要去開那個檔的，把它寫短就等於把這個入口關掉，而關掉的時候毫無跡象。2026-10-30 把舊版那句只有十幾個字的描述換成跟權威版同一套觸發詞，就是為此。
> 只用得到 Claude Code 的專案可以不建這個檔；建了也不影響其他工具。

````markdown
<!-- kit-file: .agents/skills/handoff/SKILL.md -->
````

### 3.17 `.codex/hooks.json`、`.claude/hooks/codex-hook.cmd`（給 Codex 的 hook 接線與 Windows 啟動器）

> **CLI 與桌面 App 都用得到這個檔。** 舊版這裡寫「桌面 App 沒有 hooks」，依據是 2026-08-06 在 App `26.721.41059` 打不出 `/hooks`——2026-10-30 重查已經不成立：App `26.506`（2026-05-08）就加了 hooks 的 in-app 信任審核流程。**對外部工具能力的斷言都有保鮮期**，拿它做「做不到所以不做」的決定之前先重查（保鮮期機制見開頭那一節）。
> hooks 與 Claude Code **同格式、同語意**：讀 `<repo>/.codex/hooks.json`，context 由 stdin 傳 JSON。所以這裡掛的是**同樣那兩個 `.sh`**，不要另外複製一份到 `.codex/hooks/`。
> 功能**預設開啟**（`codex features list` 可以確認 `hooks  stable  true`；要關是 `[features] hooks = false`）。來源不只這一個檔：`~/.codex/hooks.json`、兩層 `config.toml` 的 `[hooks]`、plugin 都會**合併**進來，同一層同時用兩種寫法會在啟動時警告。
> **路徑一律相對**——寫成 `C:\Users\...` 的絕對路徑，換到另一台機器或 macOS 必定失效，而且失效時是靜默的。
> **但「不寫死絕對路徑」跟「可以假設 cwd 是 repo 根目錄」是兩件事**——後者就是 F05，所以路徑前面要掛 `$(git rev-parse --show-cdup)`（它回的也是相對路徑，理由見 3.9 那一段）。
> 🔴 **要兩道信任，而且失敗是靜默的。** ①專案的 `.codex/` 整層要先被信任（記在 `~/.codex/config.toml` 的 `[projects.'<路徑>'] trust_level`）；②每一支非 managed 的 hook 還要按**當前雜湊**逐一審核（CLI 打 `/hooks`），所以改過接線定義要重新審核。2026-10-30 實測：在未信任的資料夾跑 `codex exec`，hook 完全沒跑，而且 **stderr 一個字都沒有**。所以部署完**一定要照第 5 節真的開一個 session**，不能看到檔案在就算裝好了。⚠️ **而且要在互動模式、而且要送出一句話**：2026-11-01 實測互動 TUI 開場不跑 `SessionStart`（跟著第一個 turn 才跑），所以盯著開場看是假陰性。互動模式的補償是 hook 失敗會印 `• Hook failed`，而 `codex exec` 連失敗都不吭聲。
> **2026-10-31 實測完畢（`0.164.0`／Windows），兩個未知都收掉了，其中一個是問錯問題。**
> ① **`statusMessage` 不是 Claude 專屬的 key**：官方把它列在 hook 定義的正式鍵裡（`type`／`command`／`commandWindows`／`timeout`／`statusMessage`／`additionalContextLimit`／`async`／`server`／`tool`／`input`），語意就是「Optional UI message」。所以它不會被當成雜訊，也不會讓設定失效。實測 `codex exec` 的 stdout／stderr **都不會出現它**（非互動沒有 UI 可顯示）；**互動 TUI 會顯示**——2026-11-01 在 `0.166.0` 量到它接在狀態行後面（`Working (1s • esc to interrupt) · <字串>`），所以互動模式下它是使用者唯一看得到的那行字。
> ② **`PreToolUse` 沒有 matcher＝每一次都觸發，而且不分工具名**：官方寫「省略、`""`、`"*"` 都等於比對該事件的每一次發生」，實測同一個 session 裡 `Bash`×2 ＋ `apply_patch`×1 全部觸發。所以 `pre-push-handoff.sh` 會跟著**每一個**工具呼叫跑一次——它自己對非 push 的呼叫是 `exit 0` 立刻收手（2026-11-12 起只看 `command` 欄位，編輯工具的內容提到 `git push` 也放行；在那之前會被擋，Claude Code 卻不會，見決策書 Q27），功能上沒問題，但**要知道這是「每次都跑」而不是「只在 push 時跑」**。要縮成只比對殼層工具就加 `"matcher": "Bash"`，但那是拿一次實測的工具名去賭所有情境（MCP 工具名長得完全不同），**這個取捨刻意留著不改**。
> ③ 順帶量到的第三件，比上面兩件重要：**信任綁 `hooks.json` 的絕對路徑，不是內容**，所以**每個專案都要各審一次**；而且只有互動模式會主動問你，`codex exec` 永遠靜默跳過。細節見「跨工具與跨平台」的 Codex 那節。
> `exit 2` 會擋下工具呼叫（官方：exit 2 加 stderr 理由即 block），所以 `pre-push-handoff.sh` 的擋法在 Codex 上**語意正確**，不必為它另寫 JSON 版的回應。

````json
<!-- kit-file: .codex/hooks.json -->
````

**Windows 用 `commandWindows` 經下面的啟動器找 Git Bash**，macOS／Linux 仍用原本的 `command`。它只處理管線，不複製任何 git 或交接判斷；stdin、stderr 與腳本結束碼原樣傳遞，否則 `PreToolUse` 的 exit 2 防呆會被吃掉；stdout 在原內容前加一行純文字標頭以免 JSON 誤判。接線自己先用 `$(git rev-parse --show-cdup)` 算出 repo 根目錄（2026-11-02／F05：舊版這裡寫「相對接線仍從 repo 根目錄啟動」，那是**假設**而不是事實，子目錄開的 session 直接 exit 127），啟動器再用 `%~dp0` 找腳本，兩層都不靠當下 cwd。⚠️ **Windows 這一欄要多做一次斜線正規化**：`--show-cdup` 回的是 `../`（正斜線），而 `cmd /d /c "../.claude\hooks\codex-hook.cmd"` 會死在 `'..' is not recognized`（2026-11-02 從子目錄實測），所以用 PowerShell 的 `-replace '/','\'` 先換成反斜線——`commandWindows` 本來就由 Codex 外層的 PowerShell 執行，用得上它。2026-11-01 在 Windows／CLI `0.166.0` 的真 repo 重現舊接線已信任卻 exit 1：PATH 的 `bash` 是 WSL，缺少 `/bin/bash`；直接改用 Git Bash 同一支 `.sh` 就成功。這是新的真部署案例，**不能倒推成稍早那組 exec／TUI 探針差異的原因**。

**`PreToolUse` 的 Windows 命令末尾必須保留 `; exit $LASTEXITCODE`。** 2026-11-01 補做真阻擋驗收時發現：只在原生 cmd 測到 exit 2 還不夠；Codex 外層的 PowerShell `-Command` 會把最後一個 native 命令的失敗折成 exit 1，於是畫面只報 Hook failed、工具仍被放行。加上明確 exit 才把 2 交回 Codex。驗證器同時測完整 PowerShell → cmd → Git Bash 啟動鏈與拿掉明確 exit 的負向情境，避免再用少一層的測試報成功。

保持 **ASCII、全 LF、單行 if、沒有 label 與多行括號區塊**。尋找順序是 PATH 上 `git.exe` 的安裝位置、兩種 Program Files、使用者安裝位置；刻意不執行 PATH 上未驗明來源的 `bash`，以免又選到 WSL。找不到 Git Bash 就在 stderr 明確報錯並 exit 1，不假裝驗收成功。另量到 `0.166.0` 對以 `[` 開頭的純文字 stdout 會報 `invalid session start JSON output`；同一支腳本只加上 `Git status check:` 標頭後，互動驗收由 `HOOK_ABSENT` 變成 `HOOK_PRESENT`。所以標頭留在啟動器，不改兩支共用 `.sh` 的既有標記。

````bat
<!-- kit-file: .claude/hooks/codex-hook.cmd -->
````

### 3.18–3.20（2026-11-13 移除）

原本是 Antigravity 的轉接層、Windows shim 與 hook 接線。需求決策書 v3 的 D8 放棄 Antigravity，三個檔移出部署包；編號保留，免得舊紀錄裡的「3.18」「3.19」「3.20」指到別的東西。已部署的專案裡那三個檔不會被同步工具刪掉，要不要清掉由使用者決定。

### 3.21 其他 skills 慣例（有需要時才建，不要空建）

當某個操作**做過兩次以上、而且有踩過坑**（API 呼叫順序、部署步驟、前端框架陷阱），就把它寫成 skill：

- **權威版放 `.claude/skills/<slug>/SKILL.md`**（Claude Code 會自動載入這個路徑，內容必須實體存在那裡）。
- 若也想讓其他工具找到，在 `.agents/skills/<slug>/SKILL.md` 放**指標**，不要複製內容。

SKILL.md 開頭固定 frontmatter：

````markdown
---
name: <slug>
description: <什麼情況該讀這份，寫清楚觸發時機——這行決定模型會不會載入它>
---

# <標題>

（實測過的步驟與指令，附日期與踩坑理由）
````

指標檔內容：

````markdown
---
name: <slug>
description: Pointer to the authoritative copy in .claude/skills/. <一句話說明用途>
---

# 本檔只是指標，請讀權威版

**權威版：[`.claude/skills/<slug>/SKILL.md`](../../../.claude/skills/<slug>/SKILL.md)**

**請勿在此複製內容。** 兩份副本會各自演進並產生矛盾（曾發生：一份已更新成新網址、另一份停在舊位址，而入口文件指向舊的那份，照抄就失敗）。新知識一律寫進權威版。
````

---

## 4. 先本機驗收，再首次發布

### 4.1 本機驗收（第一個 commit 與 push 之前）

```bash
git init -b main
```

先確認 `.gitignore` 已就位再 `git add`（**順序不可反**，不然祕密會進第一個 commit）：

```bash
git status --porcelain
```

確認清單裡沒有憑證／運行資料後：

```bash
git add . && git diff --cached --name-only
```

依訪談逐一執行 `git check-ignore -- <憑證或運行路徑>`，必須列出該路徑；不要以檔案還沒建立為理由略過。核對 staged 清單沒有任何憑證或運行資料。關鍵字掃描只能降低風險，不能涵蓋所有祕密格式。

接著跑兩個本機檢查：

```bash
python -X utf8 tools/check_docs.py
python -X utf8 tools/verify_state.py
```

沒有 `python` 就用 `python3`。文件必須 exit 0；服務 FAIL／ERROR 不得當通過，SKIP／NOT_CONFIGURED 明列原因與待配置事項。核對 `ARCHITECT.md` 與 `HANDOFF.md` 是實況。這些本機驗收全部完成才可往下；遠端與工具注入尚未驗證，留到第 5 節，不可預先寫成通過。

### 4.2 首次發布（本機驗收完成後）

再次確認 staged 清單乾淨，然後提交並建 repo（需先裝好 `gh` 並登入）；owner／repo 名與 public／private 須先取得使用者確認：

```bash
git commit -m "chore: bootstrap project management skeleton"
```

```bash
gh repo create {{GH_OWNER}}/{{GH_REPO}} --{{GH_VISIBILITY}} --source=. --remote=origin --push
```

沒有 `gh` 就到 GitHub 網頁開一個空 repo，然後：

```bash
git remote add origin https://github.com/{{GH_OWNER}}/{{GH_REPO}}.git && git push -u origin main
```

最後確認 upstream 有對齊（hook 需要 upstream 才能比對）：

```bash
git status -sb
```

---

## 5. 部署後自檢清單

第 4.1 節已先完成本機驗收。這一節補遠端、runtime 與工具實際注入的驗收；逐項回報，全過或明列不適用／未配置才算交代完整，未驗證不能宣稱通過。

- [ ] `python -X utf8 tools/check_docs.py` → `OK`（一次涵蓋死連結與**殘留佔位符**；佔位符那一項掃 `.md`／`.py`／`.sh`／`.json`／`.gitignore`／`.gitattributes` 的 tracked 檔，所以要先 `git add`。本部署包自己被豁免——照最後一項刪掉它就好）
- [ ] `python -X utf8 tools/verify_state.py` → 可執行（尚未填檢查項時印 `NOT_CONFIGURED`，正常）
- [ ] `bash .claude/hooks/git-freshness.sh` → 印出三行 `[facts]`：時間（含 session 名用的 `MM.DD.HH`）與本機、落後 0 領先 0、origin 上「工作中」那一行的原文。印「origin 上沒有分支」表示第 4 節沒做完
- [ ] **子目錄也要有防護**（2026-11-02／F05）：`cd tools && sh -c 'bash "$(git rev-parse --show-cdup).claude/hooks/git-freshness.sh"'; cd ..` → 要印出跟在根目錄一樣的 `[facts]`。**要跑的是 `.claude/settings.json`／`.codex/hooks.json` 裡原始的那一串命令**，不是直接拿完整路徑跑腳本——後者在任何 cwd 都會過，測不到入口。hook 的 `command` 以 session 的 cwd 執行，而人會從子目錄開 session（`cd tools && claude`）；舊接線在那裡是 exit 127，而 **SessionStart 失敗跟「檢查過了沒事」在畫面上一模一樣**
- [ ] **工作中標記看得見**：把 `HANDOFF.md` 的「工作中」改成 `` `假機器名` ／ `Claude Code` ``，commit、push，再跑 `bash .claude/hooks/git-freshness.sh` → 第三行要印出那個值的原文；改回「無（已交棒）」、commit、push 後再跑 → 要印回 `無（已交棒）`。**驗完記得改回來**
- [ ] **共用制度版本提示**：`printf 2099-01-01 > .claude/.bootstrap-version && bash .claude/hooks/git-freshness.sh` → 要多印一行「共用制度落後」。快取裡放的是**上游最新版**，所以要餵一個比本機**新**的值。**驗完刪掉那個快取檔**（`rm .claude/.bootstrap-version`），否則 12 小時內都會拿到假答案
- [ ] `.claude/skills/handoff/SKILL.md` 存在，前三行是 `---` / `name: handoff` / `description: ...`（frontmatter 壞掉 skill 就不會被載入）；同目錄有 `mode-a.md`、`mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md` 五個檔，六個檔檔頭的 `source:` 版本相同（少一個，入口就會指向不存在的檔）
- [ ] **`CLAUDE.md` 只有 `@AGENTS.md` 這一行 import**，不是「去讀 AGENTS.md」那種句子——有 `CLAUDE.md` 時 Claude Code 不會自己讀 `AGENTS.md`，而用文字請它去讀不保證它真的開那個檔（理由見開頭「跨工具與跨平台」）。開一個 session 問它「`AGENTS.md` 的鐵律第 1 條是什麼」，答得出來才算接上
- [ ] `ARCHITECT.md` 存在且有「最後更新」標頭（`check_docs.py` 會擋），「專案本體」那節寫的是**實況**——還沒有程式碼就照實寫，不要先畫一個想像中的架構
- [ ] 在 Claude Code 打 `/handoff` 看得到這個 skill
- [ ] pre-push hook 會放行無關指令：`echo '{"tool_input":{"command":"git status"}}' | bash .claude/hooks/pre-push-handoff.sh; echo $?` → `0`
- [ ] `git log --stat -1` 確認第一個 commit **沒有**含憑證或運行資料
- [ ] 關掉 session 重開一次，確認 hook 在對話開頭自動跑

**跨工具（只驗你真的會用的那幾個，用不到的不必建檔）**

- [ ] **可攜層**：`AGENTS.md` 有共用制度一節（開始與結束標記之間 ≤ 40 行）——**這一項不能跳過**，它是唯一不需要任何設定就會被讀到的那一層（**「讀得到」不等於「照做」**，見開頭那一節），其餘都只是輔助
- [ ] **Codex CLI**：`.codex/hooks.json` 與 `.claude/hooks/codex-hook.cmd` 存在且接線路徑全是相對路徑（`grep -n ':[\\/]' .codex/hooks.json` 應無輸出——絕對路徑在別台機器會靜默失效）；**專案要先被信任**（否則整層 `.codex/` 被跳過）；Windows 的 `commandWindows` 要指向 `.claude/hooks/codex-hook.cmd`，該檔也必須在場；然後**開一次互動式 `codex`**——它開場就會問「Hooks need review」，選 `Trust all and continue`（想一條條看就選 `Review hooks`）。🔴 **這一項不能只看檔案在不在**，而且有三個會讓你誤判的點：①**信任綁 `hooks.json` 的絕對路徑，所以每個專案都要各做一次**，審過一個不會全通；②**在那個 session 裡送出一句話才驗得到**——2026-11-01 實測互動 TUI 開場不跑 `SessionStart`，它跟著第一個 turn 才跑；舊版這裡寫「你按下同意的那個 session 不會跑，要再開一個才算」，那是推論而實測是反的，而且它教人用**保證看不到**的方式驗收（再開一個、然後盯著開場）；③**不要去畫面上找 `[git-check]`**——Codex 把純文字 stdout 當 developer context 餵給模型、不顯示給人，所以要驗就問 agent 一個不必複述的是非題（「只回 YES／NO：你的 context 裡有沒有以 `[git-check]` 開頭的行」），或暫時讓 hook 自己寫一個檔。`codex exec` 從頭到尾不問也不印，**不能拿它當驗收手段**（2026-10-30／31 兩輪實測）
- [ ] **Codex skill 來源**：`codex debug prompt-input` 會印一張「Skill roots」表，確認裡面有 `~/.codex/skills`（全域副本放這裡）與本專案的 `.agents/skills`。這比問模型「你有哪些 skill」可靠，也不花一次模型呼叫
- [ ] **Codex 桌面 App**：它**有** hooks（App `26.506` 起有 in-app 信任審核，Settings 裡找 Hooks），而且跟 CLI 共用 `~/.codex`。舊版這裡寫「App 沒有 hooks」是 2026-08-06 的實測，已經過期。全域 skill 仍然放 `~/.codex/skills/handoff/SKILL.md`（2026-10-30 實測 CLI `0.164.0` 仍讀這個路徑，雖然官方文件已經不列它）
- [ ] **Codex 指標檔**：`.agents/skills/handoff/SKILL.md` 存在，內容只有指標、沒有複製程序內容（見 3.16）
- [ ] **共通的真正驗收**（不論哪個工具）：在專案裡講一句「我要接手這個專案」，agent 應該先 `git fetch`、讀 `AGENTS.md` ＋ `HANDOFF.md`，回報 3–5 行才動手。它直接開始翻程式碼就是沒接上——改用明講版：「請先讀 `.claude/skills/handoff/SKILL.md`，照 A 模式接棒」
- [ ] **另一台機器**：clone 後重跑上面「python 可執行」與「hook 自動跑」兩項。`python` 不存在就用 `python3`；Windows 需要 Git for Windows 附的 bash
- [ ] `HANDOFF.md` 的「本機能力」已填實際狀況
- [ ] 刪掉 `PROJECT-BOOTSTRAP.md`，以及用壓縮檔部署時附的 `讀我-先看這個.md`。前者的內容已分散進 AGENTS.md／handover-protocol.md，留著就是第二份會腐化的副本；後者的內容在部署完成的當下就是假的（它寫著「檔案都在，但裡面還有佔位符沒填」），下一棒讀到會以為部署沒做完而重跑一次訪談

---

## 6. 之後怎麼維持（一頁操作卡）

**每次開工／收工**：直接 `/handoff`（Claude Code），或用 README「換一個 AI 接手工作」的兩段 prompt 指路給其他模型。**順序永遠是先交棒、後接棒**（舊 session 先把狀態寫進 `HANDOFF.md` 並 push，新 session 才讀得到）。那兩段刻意沒有自己的字母編號（2026-11-02／F15）。

**改到 skill 或 hook 時**：權威版在本部署包 → 改這裡 → 覆蓋各專案 `.claude/skills/handoff/` 整個目錄（六個檔一起，與選用的全域副本）→ 檔頭 `source:` 標記跳版。

標記的格式是 **`v<日期>`，同一天改第二次起在日期後面加序號**（`v2026-10-24.2`、`.3`），當天第一次不加。序號算的是**當天第幾個帶 `source:` 標記的改動**，不是單一檔案的、也不是當天第幾次碰部署包——只改敘述而沒有任何標記動過的那幾次不算。標記寫的本來就是「這份副本來自部署包的哪一版」。⚠️ **它跟本檔開頭的「版本」行不保證同號**：那一行與 `VERSION` 只跟著 handoff skill 目錄走（鐵律 1；2026-11-10 起 skill 是 3.8 的六個檔，之前是單檔 `SKILL.md`），所以當天後續沒動到 skill 目錄的改動會讓標記序號**超前**版本行——2026-11-02 就是這樣，標記到 `.2` 而版本行仍是裸的 `2026-11-02`。舊版這裡寫「算的是部署包當天的第幾次修改（跟版本行同一個號）」，兩個斷言都不成立，而 `AGENTS.md` 鐵律 2 寫的是另一種算法——同一條規則兩個家、兩種說法（2026-11-02／F15 一起修）。2026-10-24 那天這份 skill 改了三次，三次的標記卻都是 `v2026-10-24`——副本明明落後，標記顯示一樣新，於是把「舊版 session 名稱少一個全形空格」誤判成同步漏掉，白查一輪。日期粒度只能證明「不早於那一天」，證明不了最新。

沒改內容的檔案不要跟著跳版——謊報一次「副本落後」之後，這個標記就沒人再信。

**新知識該寫哪一份**：

| 你剛剛得到什麼 | 寫進 |
|---|---|
| 一條「以後都要這樣做」的規則、一次踩坑 | `AGENTS.md` 鐵律（重大）或 `docs/ai-notes/<主題>.md`（細節），**附絕對日期** |
| 某個操作的可重複步驟（做過兩次以上） | `.claude/skills/<slug>/SKILL.md` |
| 「東西搬家了」「多了一個元件」「權威版換位置了」 | `ARCHITECT.md`，**跟該變動同一個 commit** |
| 「還有哪些事沒做」「這件事被否決了」 | `docs/ai-notes/roadmap.md` |
| 「現在做到哪、下一步」 | `HANDOFF.md`（覆寫，不累積） |
| 給人看的入口、網址、怎麼跑起來 | `README.md` |

**開新的 ai-notes 檔案時**：回頭把 `AGENTS.md` 的「知識庫地圖」補上一列，否則沒人會找到它。

**已知的腐化模式與對策**：

| 症狀 | 對策 |
|---|---|
| HANDOFF 超過 80 行 | 把持久內容搬進 ai-notes，只留當下狀態 |
| 同一件事在兩份文件都寫了 | 留一份權威版，另一份改成指標並說明為什麼（避免下一棒又複製回去） |
| `ARCHITECT.md` 開始出現「正在做 X」「預計改成 Y」 | 那是 HANDOFF 與 roadmap 的內容，搬走；本檔只寫現在的結構 |
| 文件寫「共 N 份」「目前 12 個」 | `check_docs.py` 會提醒；改成不寫數字 |
| 換了網址／改了名稱 | 把舊值加進 `check_docs.py` 的 `STALE_PATTERNS`，讓工具替你抓殘留 |
| 兩台機器同時動 main | 恢復 single writer；分岔了就先整合，**禁止 force push** |
