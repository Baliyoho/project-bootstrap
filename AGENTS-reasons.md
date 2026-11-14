# AGENTS 規則的理由與事故

> 最後更新：2026-11-14（新增「共用制度副本」一段）；前次 2026-11-11（F22 第二輪：每段末尾補入口壓縮前的完整措辭）
> 這裡是 [AGENTS.md](AGENTS.md) 每條規則的完整原文、理由與事故。2026-11-10（F22）從 AGENTS.md 逐字搬來：規則留在入口，理由住這裡，由入口的「為什麼」連結指過來。**不是每輪必讀**；要改、要質疑或想繞過某條規則之前先讀對應那一段。
> 這裡的段落保存搬家當時的完整措辭；之後規則有變，先改 AGENTS.md，再在這裡對應段落補帶日期的理由，不要刪舊事故。

<a id="shared"></a>

## 共用制度副本

2026-11-14 使用者決定把部署包的共用制度逐字貼進本 repo 的 AGENTS.md。起因：各專案升到 v3 之後，全域 `~/.claude/skills/handoff/` 也得換成 v3，否則 Claude Code 在那些專案裡載入的是家目錄的 v2 skill（家目錄蓋過專案那份，2026-11-12 實測）。但 v3 skill 把必守條件與 session 命名都指向 `AGENTS.md` 的共用制度，而本 repo 刻意沒有專案層 skill、`AGENTS.md` 也沒有那一節——換掉全域就等於這裡接棒時找不到命名規則。選項裡只加一行指標太依賴模型自己去讀，所以選了貼入：`CLAUDE.md` 的 `@AGENTS.md` 會把它自動載入。

代價與守門：`sync_project.py` 拒絕本 repo，副本只能手動重貼；`verify_bootstrap.py` 的「規則理由連結」要求它跟 `src/kit/files/AGENTS.md.tmpl` 逐字相同（有負向測試），同時對這段跳過死連結與理由連結兩項檢查——副本連到部署後才存在的 `.claude/skills/handoff/`，章節也沒有本 repo 的理由連結；那幾條條件的理由在需求決策書 v3。跳過的範圍只限兩個標記之間，標記壞掉就不跳。

<a id="start"></a>

## 開工第一件事

**先走接棒程序的 A 模式，A 沒跑完之前不要改任何檔案**；收工走 B 模式，中途要拉最新或推一個安全點走 C 模式。

程序檔在**全域**副本：`~/.claude/skills/handoff/SKILL.md`（Codex 是 `~/.codex/skills/handoff/SKILL.md`）——**這個 repo 刻意沒有專案層的那一份**（理由見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」）。工具不會自動載入 skill 的時候就直接開那個檔讀，它是純 Markdown。**這台機器沒有全域副本（例如乾淨的新機器）時，程序在 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的「3.8」節，那段就是同一份 `SKILL.md`**；照讀它，不要從別台機器搬檔或憑記憶重刻。（2026-11-10／F16a：舊句在沒有全域副本時叫人開一個不存在的檔，乾淨 clone 加空家目錄實測找不到程序。）

**下一輪接棒完成 A 模式後，開始任務前先讀 [project-bootstrap-reaudit-2026-11-03.md](project-bootstrap-reaudit-2026-11-03.md)**（2026-11-03 使用者明確要求）。這是第二輪複審快照，列出 R01–R09、重現證據與驗收門檻。先讀它才能分清「舊反例已修」與「修正邊界仍有缺口」，不能只看到前輪結案就當作沒有待辦。報告不累積實作進度，當下狀態看 HANDOFF。

**接著要動原查核報告那 16 條的話，再讀 [project-bootstrap-audit-progress.md](project-bootstrap-audit-progress.md)**：每一條的狀態、已修的那幾條守門人是哪一項、沒修的那幾條的建議作法與驗收門檻都在那裡。它 2026-11-02 在使用者要求「下一輪交棒給另一個模型」時產出，所以寫給**沒有那段對話記憶的接手者**；查核報告本身是凍結快照，狀態不寫進它裡面。

**現行需求唯一權威是 [需求決策書](project-bootstrap-requirements-decision.md)**：D1–D8、51 個穩定需求 ID（含 F50 session 改名）、最低強度與驗收條件。討論需求、驗收或替代工具前讀它；決策定稿不等於實作完成，逐 ID／子項實作狀態已移交 [v2 現況索引](experiments/v2/status.json)，HANDOFF 只留停點與行動。待決事項唯一入口是決策書第 6 節。本輪整理新增的成本基準與授權界線見第 7 節。

**2026-11-13 起現行需求權威改為 [需求決策書 v3](project-bootstrap-requirements-decision-v3.md)**（使用者指示直接出 v3，並選「兩檔先並存」，v3 的 Q32 (b)）。v3 沿用同一組 51 個 ID，把制度的範圍收窄成「只負責模型不會自己知道的事」，新增 D9–D15、退役 D5，最低強度含阻擋的需求全部下修或委託給工具；依據是 handoff-ab 兩輪實測與 v3 第 2 節列的外部資料。上一段說的 v2 決策書沒有刪：驗證器、`test_trail_repo`、`test_registry`、一致性檢查與 v2 現況索引都讀它的檔名與結構，Q1–Q31 的逐條理由也只在那裡。兩檔衝突時以 v3 為準；v2 檔的第 6 節仍是那些工具認得的待決登記處，v3 新增的待決（Q32 起）登記在 v3 第 8 節。**為什麼不直接蓋掉**：蓋掉要在同一個 commit 改驗證器、測試與現況索引，使用者選擇先並存。

[需求歷史原件](project-bootstrap-requirements-history.md)保存 v3.10 與全部修訂理由，僅供追溯；其中舊的「權威版」「現在」「待決」不再指示現行操作。不要讓歷史段落覆蓋決策書，也不要把現行程序當成已符合新需求。

需求實現與開源技術棧選型見 [實現規劃](project-bootstrap-implementation-plan.md)（2026-11-06）：51 項需求映射、現有能力基準、候選比較、保障邊界與分期驗收。使用者已授權 v2 分支實作，未部署，不授權略過現行程序；實作進度看 v2 現況索引。處理選型或架構實作時再讀，不列常態接棒必讀。

效率改善的設計提案見 [project-bootstrap-efficiency-plan.md](project-bootstrap-efficiency-plan.md)（2026-11-03）。它尚未生效，不是每輪必讀文件，也不授權省略本檔或全域 skill 的現行程序；只有處理效率改造時才讀，實作進度仍看 HANDOFF。

照 A 模式做會踩到三處跟部署出去的專案不一樣的地方：

- **A4 的一鍵驗證不是 `verify_state.py`**（那是骨架的檔，不部署到自己身上），改跑 `python -X utf8 tools/verify_bootstrap.py`，**exit 0 才算改完**（鐵律 4）。
- **沒有 `check_docs.py`、沒有 pre-push 防呆**，所以 B4 與那層擋 push 的關卡都不存在；`.md` 的死連結與日期標頭由 `verify_bootstrap.py` 的「本 repo 自己的文件」那一項顧。
- **B7 提交前先明確 stage，再跑 `python -X utf8 tools/verify_bootstrap.py --staged`**；它拒絕未暫存與未追蹤檔，避免用工作樹檢查結果證明另一份提交候選。一般 A4 仍用不帶旗標的指令。
- **`HANDOFF.md` 是當下交接快照，也承載「工作中」標記**；A5 更新標記，B6 核對整份現況並覆寫，≤80 行、不累積歷史（見下方「本 repo 的交接快照」）。

**為什麼要在這裡再寫一次**：開場 hook 已經會講同樣的話，但它**只在 Claude Code、以及已經審核過 hook 的 Codex 上會跑**——Antigravity、Gemini CLI、還沒被信任的 Codex 都不會，而 `AGENTS.md` 是那些工具唯一保證會讀到的入口。把開工義務只放在 hook 裡，等於讓它在一半的平面上無聲消失。（2026-11-01 補。部署包範本 3.1 一直有這一節，缺的反而是骨架自己這個 repo——制度的來源比它的產物少一層保護，而且沒有任何徵兆。）

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> **先走接棒程序的 A 模式，A 沒跑完之前不要改任何檔案**；收工走 B 模式，中途要拉最新或推一個安全點走 C 模式。
>
> - 程序檔在**全域**副本 `~/.claude/skills/handoff/SKILL.md`（Codex 是 `~/.codex/skills/handoff/SKILL.md`）；這個 repo 刻意沒有專案層的那一份。工具不會自動載入 skill 就直接開那個檔讀。**這台機器沒有全域副本時，程序在 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的「3.8」節**；不要從別台機器搬檔或憑記憶重刻。
> - 部署包 `2026-11-10` 起 skill 是一個目錄：`SKILL.md` 是入口，再照它讀同目錄的模式檔；這台 Mac 的全域副本 2026-11-10 已換成六檔版（決策書 Q11 (a) 試用）；**別台還沒換的仍是單檔**，照單檔走。本 repo 的「全綠」行由 `.claude/hooks/repo-git-check.sh` 印（前綴 `[repo-check]`），要重跑就跑它。
> - **A4 改跑 `python -X utf8 tools/verify_bootstrap.py`**（不是 `verify_state.py`），**exit 0 才算改完**。
> - 沒有 `check_docs.py`、沒有 pre-push 防呆，所以 B4 與擋 push 的關卡不存在；文件檢查由 `verify_bootstrap.py` 顧。
> - **B7 先明確 stage，再跑 `python -X utf8 tools/verify_bootstrap.py --staged`。**
> - **`HANDOFF.md` 是當下交接快照，也承載「工作中」標記**：A5 更新標記，B6 核對整份現況並覆寫，≤80 行、不累積歷史。
>
> 這些義務寫在這裡而不只放 hook，是因為有些工具不跑 hook。
>
> （「碰到才讀」的文件對照表原樣搬到 ARCHITECT.md「碰到才讀的文件」。）


<a id="what"></a>

## 這個 repo 是什麼

**AI 協作專案管理骨架的權威版。** 唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)——一份自帶所有檔案範本的部署包，複製到新專案資料夾就能生出整套制度。用法見 [README.md](README.md)。

**結構問題（有哪些檔、部署包各節產出什麼、副本存在於哪些地方）看 [ARCHITECT.md](ARCHITECT.md)**——動到結構就跟它同一個 commit 改；本檔只放規則。

**這裡不是知識庫。** 不要在本 repo 累積專案知識、踩坑紀錄或狀態；那些屬於各自的專案 repo。

唯一的例外是 `tools/verify_bootstrap.py`——它是**部署包的測試**，不是骨架的一部分，也不會被部署出去。

**v2 實作例外（2026-11-06）**：`experiments/v2/` 保存本骨架的隔離原型、負向測試與逐 ID 現況；`tools/verify_v2.py` 是實驗入口。只使用合成 fixture，不保存其他專案資料，不部署。現行 22 檔仍以部署包為權威；原型通過不授權切換程序或宣稱跨工具強保障。實驗用法與限制見 [v2 原型說明](experiments/v2/README.md)。

另一個例外是 [HANDOFF.md](HANDOFF.md)：2026-10-30 起這個 repo 多機維護，所以補上跨機器「工作中」標記（`.claude/hooks/repo-git-check.sh` 開場讀 origin 那一份）。**它同時必須是可信的當下交接快照**；只保留現況、未完成事項與接手限制，事故史與規則仍放回各自的家。本 repo 依然刻意沒有 handoff skill、沒有 `pre-push-handoff.sh`、沒有 `check_docs.py`——它是制度的**來源**，不是一個交接中的工作專案（理由見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」）。⚠️ **2026-11-06 起這三項是「已宣告的例外」，不是空白**：需求 v3.10 新增的 F46 要求來源自身的保護不低於產物，使用者當天選了 D4／F34 的宣告路線而非補裝，正式宣告寫在 ARCHITECT 那一節的開頭。**但宣告不等於 F46 已達成**——F46 的強度是偵測。2026-11-08 起驗證器會逐項印出這三項來源例外；來源與產物的接手、占用、文件檢查尚未全部用同組情境驗收，所以 F46 仍未整項通過。要撤銷宣告改成補裝，是改使用者的決定。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **AI 協作專案管理骨架的權威版。** 唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)：自帶所有檔案範本的部署包。用法見 [README.md](README.md)。
> - **這裡不是知識庫**：不累積專案知識、踩坑紀錄或狀態，那些屬於各自的專案 repo。
> - 不部署的例外：`tools/verify_bootstrap.py`（部署包的測試）；`src/project_bootstrap/`、`tests/`、`experiments/v2/`（說明與現況索引）與 `tools/verify_v2.py`（隔離原型，只用合成 fixture，不保存其他專案資料；**原型通過不授權切換程序或宣稱跨工具強保障**）；`pyproject.toml`／`uv.lock`（P1 開發骨架，A4 不需要）；`tools/build_kit.py`（由 `src/kit/` 生成部署包）；[HANDOFF.md](HANDOFF.md)；本檔的理由檔。
> - 刻意沒有 handoff skill、`pre-push-handoff.sh`、`check_docs.py`。這是**已宣告的例外**，不是空白；宣告不等於 F46 已達成；撤銷宣告改成補裝是使用者的決定。


<a id="rule-1"></a>

## 鐵律 1

1. **`PROJECT-BOOTSTRAP.md` 是權威版。** 制度要改就改它，再用 `python -X utf8 tools/sync_project.py <專案路徑> --owner '<本 session 工作中欄位完整值>' --write` 覆蓋到各專案（先在目標完成 A1–A5；`--all` 可批次預演、寫入須逐專案；它會保留 `check_docs.py` 的專案設定區塊與兩份 hook 接線裡專案自己加的設定，而且只改檔案、不 commit）；**不要**在單一專案裡就地改 skill 或 hook——那正是「同一個事實有多個家」的失控起點。改完版本也要更新 `VERSION`，各專案的開場檢查靠它才知道自己落後。⚠️ **但它不會立刻講**：`git-freshness.sh` 把上游版本快取 720 分鐘，所以跳版後各專案最多要 12 小時才會印「骨架落後」。要它下一次開場就講，就刪掉那個專案的 `.claude/.bootstrap-version`（gitignored，下次開場自己重寫）。2026-11-01 踩到：決定「讓開場檢查自己講」之後才發現六個專案的快取全停在當天 13:2x 的舊版本，不刪的話那個決定整晚不會生效，而且完全沒有徵兆。⚠️ **但只有在 `.claude/skills/handoff/SKILL.md` 真的改了內容時才跳 `VERSION`。** `VERSION` 實際上是「`SKILL.md` 的版本」：偵測器比的是該檔的 `source:` 標記與上游 `VERSION`（`git-freshness.sh` 的 `mine=`）。只改了不同步的範本（`sync_project.py` 的 `INSTANCE`，例如 `ARCHITECT.md`、`handover-protocol.md`）或部署包自己的敘述就跳版，每個專案會**永遠**印「骨架落後」，而且同步修不掉——同步回去的 `SKILL.md` 標記沒變。2026-10-30 修 Antigravity 那張表時踩到，被 `verify_bootstrap.py` 的「同版→閉嘴」擋下。

2026-11-10（決策書 Q9／F22）：handoff skill 從單檔拆成一個目錄、六個檔（入口 `SKILL.md`、`mode-a.md`、`mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md`）。上面寫「只有 `SKILL.md` 改了才跳 `VERSION`」的地方，現在指的是這個目錄裡任何一個檔：規則的理由沒變（版本號要回答的是「這個專案的交接程序是不是舊的」），變的只是程序住在幾個檔裡。六個檔的 `source:` 標記要同一個版本——各專案的開場檢查只讀入口那一行，模式檔落後而入口是新的時候不會有任何提示，所以由 `verify_bootstrap.py` 的「skill 拆分」擋。

2026-11-11（P1 第三片，使用者在聊天中說「Start slice 3」，前一輪已說明這片會改鐵律 1）：權威來源從手改的 `PROJECT-BOOTSTRAP.md` 搬到 `src/kit/`。理由：實現規劃第 7 節 P1 要求「來源權威切換同批改文件」，效率計畫也主張來源與部署產物分離；一份 28 萬位元組的檔案裡夾著 27 個範本，改一個 hook 就要在散文中間找圍籬，範本也無法單獨 diff 或測試。做法：`tools/build_kit.py` 把 `kit.md` 裡的 `<!-- kit-file: 路徑 -->` 換回範本內容，第一次拆出時逐位元組重建、`extract()` 取出的 27 檔與範本相同；範本加 `.tmpl` 是為了不讓範本 `.gitignore`／`.gitattributes`／skill／hook 接線在本 repo 生效。`PROJECT-BOOTSTRAP.md` 仍然提交：各專案複製它、`sync_project.py` 讀它與它的 Git 歷史；所以它是產物不是第二個家，手改會被「部署包由來源生成」擋下。部署出去的內容這次沒有改，`VERSION` 不跳、不同步專案；範本檔頭的 `source: PROJECT-BOOTSTRAP.md` 標記照舊，從專案那一端看，權威仍是部署包。上面原文「改它」自這一天起讀成「改 `src/kit` 再重生」。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> 1. **制度的權威來源是 `src/kit/`；`PROJECT-BOOTSTRAP.md` 是由它生成、發給各專案的部署包。** 制度要改就改 `src/kit/kit.md`（散文）或 `src/kit/files/<部署路徑>.tmpl`（範本），跑 `python3 -X utf8 tools/build_kit.py` 重生部署包，來源與部署包同一個 commit；**不要手改 `PROJECT-BOOTSTRAP.md`**（`verify_bootstrap.py`「部署包由來源生成」會擋）。之後用 `python -X utf8 tools/sync_project.py <專案路徑> --owner '<本 session 工作中欄位完整值>' --write` 覆蓋到各專案（先在目標完成 A1–A5；`--all` 只能批次預演，寫入逐專案；它只改檔、不 commit）。**不要**在單一專案就地改 skill 或 hook。**只有 `.claude/skills/handoff/` 目錄裡的檔（入口 `SKILL.md` 與五個模式／理由檔）真的改了內容才跳 `VERSION`**，而且六個檔的 `source:` 標記要同一個版本；跳版後要某專案下一次開場就提示，刪掉它的 `.claude/.bootstrap-version`。


<a id="rule-2"></a>

## 鐵律 2

2. **改動 skill／hook 內容時，同步更新檔頭的 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->` 標記**，否則沒人分得出哪份副本落後。格式是 `v<日期>`，**同一天改第二次起在日期後面加序號**（`v2026-10-24.2`、`.3`），當天第一次不加；序號算的是**當天第幾個帶 `source:` 標記的改動**，不是單一檔案的、也不是當天第幾次碰部署包——只改敘述而沒有任何 `source:` 動過的那幾次不算。⚠️ **序號跟部署包開頭的「版本」行不保證同號**（2026-11-02／F15 改，舊版這裡寫「同一個號」而部署包第 6 節寫「算當天第幾次修改」，兩種說法都不對）：版本行與 `VERSION` 只跟著 `SKILL.md` 走（鐵律 1），所以當天後續不含 `SKILL.md` 的改動會讓標記**超前**版本行——2026-11-02 標記到 `.2`、版本行仍是裸的 `2026-11-02`。有 `SKILL.md` 的那幾次兩邊才同號，所以版本行會跳號（2026-11-01 就直接是 `.2`，裸的 `2026-11-01` 從來沒存在過，因為當天第三次改動只動了 3.10、刻意沒跳 `VERSION`）。2026-10-24 當天改了三次而標記三次相同，副本落後卻顯示一樣新，誤判成同步漏掉白查一輪。

2026-11-10：上面的「`SKILL.md`」自這一天起讀成「handoff skill 目錄」（見鐵律 1 的同日註記）；跳號與超前的例子是拆分前的歷史，照原樣保留。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> 2. **改 skill／hook 內容時，同步更新檔頭的 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->` 標記。** 同一天改第二次起在日期後面加序號（`.2`、`.3`）；序號算的是**當天第幾個帶 `source:` 標記的改動**。序號跟部署包開頭的「版本」行**不保證同號**：版本行與 `VERSION` 只跟著 handoff skill 目錄走。


<a id="rule-3"></a>

## 鐵律 3

3. **保留每條規則的「為什麼」**。這份骨架的價值不在條文，在條文背後的事故；砍掉理由，下一棒就會繞過規則。（2026-08-05 隨首版 `1fa96a2` 寫入；日期取自 git 首次出現，當時沒有另外記錄理由）

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> 3. **保留每條規則的「為什麼」。** 理由可以搬到理由檔，不能刪；`verify_bootstrap.py` 的「規則理由連結」會擋沒有理由的規則。


<a id="rule-4"></a>

## 鐵律 4

4. **改完要驗證**：跑 `python -X utf8 tools/verify_bootstrap.py`，**exit 0 才算改完**。它會重生骨架比對檔案清單、模擬部署填佔位符、跑 `check_docs.py`、負向測試佔位符檢查與 `ARCHITECT.md` 日期標頭檢查真的擋得住、掃絕對路徑與缺 `python3` 退路的跨平台地雷、測 pre-push hook 五情境、從子目錄實跑兩份接線的原始命令、查全檔 LF 與兩份 JSON 設定，也查本 repo 自己的 `.md` 死連結、`.claude/settings.json` 與本 repo 那支 hook 的「工作中」判讀，還查兩支部署後腳本的失敗訊號與交接快照檢查、四支 `.py` 有沒有用到高於宣告下限的 Python API、以及已修正的主張有沒有在範本、操作卡與入口文件裡復活（這個 repo 沒有部署 `check_docs.py`，否則那就成了要跳版同步的副本）。2026-08-05 之前這段是要人照著手刻的敘述，每一棒都得重刻一次，於是實務上常被跳過——所以固化成一個指令。跳過的項目（例如機器上沒有 bash）腳本會印 `skip` 並回傳 1，回報時要照實寫。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> 4. **改完要驗證**：跑 `python -X utf8 tools/verify_bootstrap.py`，**exit 0 才算改完**。印 `skip` 的項目會回傳 1，回報時照實寫。


<a id="rule-5"></a>

## 鐵律 5

5. **不要塞專案專屬內容**（網址、docId、憑證檔名、業務規則）。部署包只放通用制度與佔位符。（2026-08-05 隨首版 `1fa96a2` 寫入；日期取自 git 首次出現，當時沒有另外記錄理由）

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> 5. **不要塞專案專屬內容**（網址、docId、憑證檔名、業務規則）。部署包只放通用制度與佔位符。


<a id="rule-6"></a>

## 鐵律 6

6. **這是公開 repo**（2026-09-07 起公開，MIT 授權）。任何人都看得到**全部 Git 歷史**，所以文件裡不要寫客戶／單位名稱、內部專案代號、本機絕對路徑——`README.md` 的「來源」那節就是為此改成不點名的中性描述。要補來源或舉例時照樣寫成中性描述；已經進歷史的東西刪不掉，所以是提交前擋，不是事後補救。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> 6. **這是公開 repo**（MIT）。不寫客戶／單位名稱、內部專案代號、本機絕對路徑；提交前擋，進了 Git 歷史刪不掉。


<a id="copy-1"></a>

## 副本規則 1

- **改完部署包，把所有副本一起覆蓋**，包括選用的全域 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/`（2026-10-30 實測 Codex CLI `0.164.0` 仍讀後者，雖然官方文件已經不列這個路徑）。漏掉一份，那台機器就繼續照舊制度做事。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **改完部署包，把所有副本一起覆蓋**，包括選用的全域 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/`。


<a id="copy-2"></a>

## 副本規則 2

- **Codex 的 hook 與 Claude Code 同格式同語意**，所以兩邊掛的是同樣那兩個 `.sh`——不要複製第二份腳本進 `.codex/`。兩份各自演化就會出現「Claude 端會擋、Codex 端不會擋」的不對稱。 Windows 的 Codex 接線另用 `commandWindows` 經 3.17 的 `.claude/hooks/codex-hook.cmd` 尋找 Git Bash；它只做管線、保留 stdin 與結束碼，沒有規則。2026-11-01 真部署重現 PATH 的 `bash` 是 WSL、缺 `/bin/bash` 而 exit 1。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **Codex 與 Claude Code 掛同樣那兩個 `.sh`**，不要複製第二份腳本進 `.codex/`。Windows 的 Codex 接線用 `commandWindows` 經 3.17 的 `.claude/hooks/codex-hook.cmd` 找 Git Bash；它只做管線，沒有規則。


<a id="copy-3"></a>

## 副本規則 3

- **Antigravity 的 hook 要分 surface 看，不要寫成整個產品的性質。** 它是四個獨立 surface（Antigravity 2.0 桌面 App／Antigravity CLI／Antigravity IDE／Python SDK，官方 blog 並排列出）。2026-10-31 實測：**CLI（`1.4.7`／`1.4.12`）與 2.0（`2.28.2`）都會讀專案層 `.agents/hooks.json` 並觸發**（CLI 靠 `agy -p` headless；2.0 沒有命令列入口，改成桌面自動化開 session ＋ 寫檔探針，再到真專案上確認注入進了 context），**接線已經端到端跑通並附進骨架**（3.18 轉接層 ＋ 3.19 Windows shim ＋ 3.20 接線）；**四個 surface 裡只剩 IDE `1.107.0` 沒觸發，原因仍未解釋**。**IDE 這一面 2026-10-31 決定不再追**（使用者不再用這個 surface，未解問題沒有讀者）——量到的事實照留，收掉的只是「去 IDE 重跑一次」那個下一步，掃到別再重提。改這三個檔之前先讀部署包「跨工具與跨平台」的 Antigravity 那一節——裡面有四個踩到才知道的約束：`.cmd` **必須全 ASCII**（中文註解會被 OEM code page 誤讀成指令執行）、**不能有多行括號區塊或 label**（LF 行末的 batch 會壞）、**路徑用 `%~dp0`／`$0` 推不靠 cwd**、**從 Windows 提交 `ag-wrap.sh` 要補 `git update-index --chmod=+x`**（Windows 不帶執行位元，而 Unix handler 直接跑這支 `.sh`，記成 `100644` 的話 Unix clone 上它靜默不動；2026-10-31 補裝六個專案時就是從 Windows 做的）。另外兩個反直覺的點：相對路徑可用而絕對路徑才脆弱（所以鐵律 5 跟它**沒有**衝突，在 Windows 上甚至是唯一寫得出來的形式）；`PreToolUse` 不明確回 `{"allow_tool": true}` 就等於**拒絕**，會擋掉使用者全部的工具呼叫——所以骨架**刻意只接 `SessionStart`**。
  要重開這個決定，門檻是比那次探針更強的證據——那次是讓 hook 自己寫檔，連 Hooks UI 自己列得出來的 `PreToolUse` 都沒觸發。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **Antigravity 只接 `SessionStart`；改 3.18–3.20 之前先讀部署包「跨工具與跨平台」的 Antigravity 那一節。** 四個約束：`.cmd` 全 ASCII；不能有多行括號區塊或 label；路徑用 `%~dp0`／`$0` 推、不靠 cwd；從 Windows 提交 `ag-wrap.sh` 要補 `git update-index --chmod=+x`。IDE 那一面已決定不再追，掃到別重提。


<a id="copy-4"></a>

## 副本規則 4

- **接線路徑一律相對**：寫死絕對路徑換機器就靜默失效（真的發生過），`verify_bootstrap.py` 的「跨平台防呆」會擋。⚠️ **但「相對」不等於「可以假設 cwd 是 repo 根目錄」**：hook 的 `command` 以 **session 的 cwd** 執行，從子目錄開 session（`cd tools && claude`）時 `bash .claude/hooks/git-freshness.sh` 是 exit 127，而 SessionStart 失敗跟「檢查過了沒事」在畫面上一模一樣——落後提醒、「工作中」標記、骨架落後三件事同時無聲消失。所以 3.9／3.17 的路徑前面掛 `$(git rev-parse --show-cdup)`（回傳的是**到根目錄的相對路徑**，所以這條規則本身不必改），Windows 那一欄再用 PowerShell 的 `-replace '/','\'` 正規化斜線（`cmd` 吃不下 `../.claude\hooks\...` 的混合斜線，實測 `'..' is not recognized`）。**Antigravity（3.20）刻意不跟**：它的 `command` 不經 shell、cwd 是 `.agents/`，基準不同（2026-11-02／F05）。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **接線路徑一律相對，但不能假設 cwd 是 repo 根目錄**：3.9／3.17 的路徑前面掛 `$(git rev-parse --show-cdup)`，Windows 那一欄再用 PowerShell 的 `-replace '/','\'` 正規化斜線；Antigravity（3.20）刻意不跟。


<a id="copy-5"></a>

## 副本規則 5

- **`.agents/` 只放指標與接線**，不複製程序內容。2026-10-31 起它有 `hooks.json`（接線）與 `ag-hook.cmd`（Windows shim）——兩者都**不含任何判斷規則**，規則只在被包的那支 `.sh` 裡（權威版只有一份），所以它們跟「複製第二份腳本」不是同一種風險：裡面沒有東西可以跟權威版分岔，只會在管線上壞掉，而管線由 `verify_bootstrap.py` 的「Antigravity 接線」守著。2026-10-30 起它不只給 Antigravity——`codex debug prompt-input` 的 Skill roots 表證實 Codex 也把 repo 的 `.agents/skills/` 當 skill 來源。既然會被自動發現，**那份指標的 `description` 就必須寫滿觸發詞**：agent 是靠它決定要不要開檔的，寫短等於無聲地關掉一個入口。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **`.agents/` 只放指標與接線**，不複製程序內容；那份 skill 指標的 `description` 必須寫滿觸發詞。


<a id="copy-6"></a>

## 副本規則 6

- **Codex Windows 啟動器也要同步**：它是新增的部署包副本，來源在 3.17；本 repo 自己也有同一份。`sync_project.py --codex-only` 可只更新各專案的 Codex 接線與啟動器，不動 SKILL 與其他設定；已裝接線的專案會補齊新依賴，沒有接線的專案不補裝。接線改過要重新審核並驗收實際執行（skill B5），不能只看檔案存在。（2026-11-01 隨 `b04ecf4` 寫入；日期取自 git 首次出現）

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **Codex Windows 啟動器也要同步**：`sync_project.py --codex-only` 只更新各專案的 Codex 接線與啟動器。接線改過要重新審核並驗收實際執行（skill B5），不能只看檔案存在。


<a id="copy-7"></a>

## 副本規則 7

- **本 repo 自己的 `HANDOFF.md`、`.claude/hooks/repo-git-check.sh` 與兩份接線（`.claude/settings.json`、2026-11-01 起多一份 `.codex/hooks.json`）都不在副本拓撲裡**，`sync_project.py` 不要碰它們：`HANDOFF.md` 是範本 3.3 的*實例*；那支 hook 誰的副本都不是（檔頭寫了為什麼不抄 3.10）；兩份接線指向的是那支 hook，所以它們跟 3.9／3.17 只是**長得像**，不是副本。它們的檢查由 `verify_bootstrap.py` 顧。
  ⚠️ **但那兩份接線的路徑跟 `sync_project.py` 的 `WIRING` 清單同名**，所以 `sync_project.py <本 repo 路徑>` 會把它們改成指向這裡不存在的 `git-freshness.sh`，開場檢查就靜默失效——看起來有防護、實際上沒有。`--all` 本來就掃不到這個 repo（`discover()` 靠 handoff skill 發現專案，這裡刻意沒有），所以 2026-11-01 起改成**明確拒絕**把本 repo 自己當目標，而不是靠「記得不要這樣做」。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **本 repo 自己的 `HANDOFF.md`、`.claude/hooks/repo-git-check.sh`、`.claude/hooks/repo-action-rules.sh`、`.claude/settings.json`、`.codex/hooks.json` 不在副本拓撲裡**，`sync_project.py` 不要碰它們；它已明確拒絕把本 repo 當目標。


<a id="snapshot"></a>

## 本 repo 的交接快照

**A5 寫工作中標記；B6 必須核對並覆寫整份 `HANDOFF.md`，≤80 行。** 已完成的待辦從下一步移除，保留的未知必須分清「現行故障」與「歷史無法歸因」。版本與驗證結果要對實際執行結果，不抄上一輪；尚未做完就明記風險與可續作步驟。收工仍要清掉 origin 的工作中標記。

**為什麼不能只改標記（2026-11-01）**：2026-10-30 為減少維護成本，將這裡定義為標記載體；但檔案仍留著完整待辦。2026-11-01 `1875b00` 又把更新義務縮成兩個欄位，隨後 `1bca9c9`、`b04ecf4`、`f2f7c1f` 完成修正與同步時都只清標記，舊待辦原封不動留下。規則與檔案用途矛盾，不是 Git 沒同步。禁止累積歷史不等於禁止維護現況；不能要求接手者自行從多輪聊天重建狀態。

`verify_bootstrap.py` 的「本 repo 交接狀態」守住必要欄位、80 行上限、`VERSION` 一致與這次已知過期待辦，並檢查入口不再教人只改兩欄。**它不能判斷任意待辦是否真的完成**，B6 仍須逐項核對證據；驗證全過不等於狀態一定正確。

需要額外模型呼叫的探針先取得使用者授權，且只用訂閱額度；不能因為驗證器沒有涵蓋就自行呼叫模型。新增守門檢查必須附負向測試，否則永遠回 `ok` 也看不出來。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **A5 寫工作中標記；B6 必須核對並覆寫整份 `HANDOFF.md`，≤80 行。** 已完成的待辦移除；保留的未知分清「現行故障」與「歷史無法歸因」；版本與驗證結果對實際執行結果，不抄上一輪；沒做完就明記風險與可續作步驟；收工清掉 origin 的工作中標記。
> - `verify_bootstrap.py` 的「本 repo 交接狀態」只守必要欄位、80 行上限、`VERSION` 一致與已知過期待辦，**不能判斷任意待辦是否真的完成**；B6 仍須逐項核對證據。
> - **需要額外模型呼叫的探針先取得使用者授權，且只用訂閱額度。**
> - **新增守門檢查必須附負向測試**，否則永遠回 `ok` 也看不出來。


<a id="pointer"></a>

## 這個 repo 自己的指標檔

`CLAUDE.md` 2026-10-30 改成只有一行 `@AGENTS.md` import。**不要改回「去讀 AGENTS.md」那種句子**：Claude Code 有 `CLAUDE.md` 就不原生讀 `AGENTS.md`，用文字請它去讀不保證它真的開檔（當天在這個 repo 上驗證過：session 開場只拿到 `CLAUDE.md` 那三行）。`GEMINI.md` 維持指標寫法——Antigravity 原生讀 `AGENTS.md`，而它支不支援 `@` import 沒有文件可查。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> `CLAUDE.md` 只有一行 `@AGENTS.md` import，**不要改回「去讀 AGENTS.md」那種句子**；`GEMINI.md` 維持指標寫法。


<a id="eol"></a>

## 行末

`.gitattributes` 強制 `eol=lf`。部署包全檔是 LF；用 Python 改寫時記得 `newline=''` 或事後正規化，否則 Windows 會把整份寫成 CRLF。（2026-08-05 隨首版 `1fa96a2` 寫入；日期取自 git 首次出現）

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> `.gitattributes` 強制 `eol=lf`。用 Python 改寫時記得 `newline=''` 或事後正規化。


<a id="hook-1"></a>

## 改兩支 hook 的訊息時 1

**反引號在雙引號裡是命令替換。** ``echo "格式是 `機器` ／ `工具`"`` 會讓 shell 真的去執行 `機器`，訊息變成空白再加一行 command not found——而那兩支 `.sh` 會被抄進每個專案，所以錯一次就是錯六份。欄位名用「」包，不要用反引號（註解裡用沒問題，註解不求值）。2026-11-02 修 F01 時當場踩到，改完才發現；`verify_bootstrap.py` 的共用情境表現在把那句訊息的字面寫法釘住了。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **雙引號裡不要寫反引號**（那是命令替換）；欄位名用「」包，註解裡才能用。


<a id="hook-2"></a>

## 改兩支 hook 的訊息時 2

**`$變數` 後面緊接中文或全形標點時一律寫成 `${變數}`。** macOS 內建的 `/bin/bash` 是 3.2，在 UTF-8 語系下會把緊接的那個字的第一個位元組吃進變數名：`（branch=$branch）` 印成 `（branch=��`，「`$tool`」整個消失，`ag-wrap.sh` 連 JSON 都吐不出來。判斷邏輯不受影響，壞的是每一句結論訊息，而 Windows 的 Git Bash（bash 5）完全不重現——2026-11-06 第一次在 Mac 上跑 `verify_bootstrap.py` 才以三項 FAIL 現形，修掉部署包 22 處、本 repo hook 17 處。`verify_bootstrap.py` 的「bash 3.2 多位元組變數」靜態掃描現在會擋。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **`$變數` 後面緊接中文或全形標點時一律寫成 `${變數}`**；macOS 的 bash 3.2 會吃掉緊接那個字的位元組。


<a id="hook-3"></a>

## 改兩支 hook 的訊息時 3

**用腳本改這些檔時，不要把 patch 從 heredoc 餵進 `python -`。** 轉義會被多解一層：反斜線 n 變成真的換行、反斜線 t 變成字面上的 TAB，於是 shell 範本裡的 `printf` 格式字串被切成三行、Python 的 `strip()` 參數裡塞進看不見的 TAB，而兩種壞法在 diff 上都很難看出來。把 patch 寫成檔案再執行，或用 `chr(10)` 組字串。2026-11-02 同日踩到三次，第三次就是在寫這一條的時候。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **用腳本改這些檔時，不要把 patch 從 heredoc 餵進 `python -`**；把 patch 寫成檔案再執行，或用 `chr(10)` 組字串。


<a id="hook-4"></a>

## 改兩支 hook 的訊息時 4

**用腳本改 `.md` 時不要手寫 `\u` 轉義。** 手寫碼點會靜默寫出異體字或錯字：2026-11-05 一天踩兩次——`盾`／`證`／`斷`／`裡` 寫成「矛皾」「証」「中断」，以及 `㊣` 寫成 U+321B（正確是 U+32A3）、`權` 寫成日文異體 `権`。兩次在 diff 上都看不出來。直接寫中文字面，或把內容另存成 UTF-8 檔再拼接；patch 腳本一律加「命中數 ≠ 1 就 abort」，第二次就是靠它擋下來的。

2026-11-11（F22 第二輪）：入口壓縮成短句，壓縮前在 AGENTS.md 的完整措辭照錄如下；之後以 AGENTS.md 現行短句為準，這段是原文備查。

> - **用腳本改 `.md` 時不要手寫 `\u` 轉義**，直接寫中文字面；patch 腳本一律加「命中數 ≠ 1 就 abort」。
