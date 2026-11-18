# PROJECT-BOOTSTRAP.md — AI 協作專案管理骨架（部署包）

> **本檔不是安裝途徑（2026-11-18 起，需求決策書 v3 Q49）。** 新專案跑 project-bootstrap repo 根目錄的 `bootstrap.py`：
>
> ```text
> python3 bootstrap.py --target <新專案資料夾>
> ```
>
> 它問完第 1 節的訪談，把第 3 節的每個檔寫進去（已存在的同名檔不覆寫，新內容寫成 `<路徑>.bootstrap-new`），逐檔比對雜湊，再把安裝後要由 agent 做的第一批工作寫進 `HANDOFF.md`。之後在那個資料夾開 Claude Code 或 Codex 說「接棒」即可。已部署的專案升級跑 `python3 bootstrap.py update --target <專案>`（先預演，加 `--write` 才寫入）。
> 本檔（`src/kit/kit.md`）是部署包的說明，範本全文在 `src/kit/files/`。2026-11-18 起不再生成成 `PROJECT-BOOTSTRAP.md` 提交（需求決策書 v3 Q50）：驗證器與同步器需要全文時，由 `tools/build_kit.py` 在記憶體把兩者組起來；下面的「第 N 節」「3.x」指的就是組出來的全文。不複製進專案。
> 版本：**2026-11-18.3**（zsh 跟 bash 不同的三種寫法（管線結束碼用 `${pipestatus[1]}`、`echo =====` 被當成檔名展開、未加引號的 `$變數` 不拆字）從本 repo 的維護手冊上移到 handoff skill 的 `env.md`「macOS」一節，因為部署出去的專案在 macOS 上一樣會踩到。七個 skill 檔與共用制度標記同版。）
> 更早的版本與每一版的理由在 project-bootstrap repo 的 `CHANGELOG.md`（2026-11-17 起從本檔開頭搬出，逐字不改；部署後用不到）。
> 萃取自兩個實際運行的專案：一個是表單資料庫＋NAS＋custom widget 的案件審核工作流，一個是文本識別系統。兩個都是多模型、多機器協作。

## 交接自動化怎麼運作（本骨架的核心）

制度寫成文件，agent 不一定會照做。本骨架用三層把**漏做的機會壓低**（不是讓它保證發生——**載入、遵循、執行是三種不同的證據**，見「跨工具與跨平台」的可攜層那一段）：

| 層 | 檔案 | 什麼時候動 |
|---|---|---|
| **事實** | `.claude/hooks/git-freshness.sh`（SessionStart hook） | 每次 session 開始自動 fetch 一次，印出最多五行 `[facts]`：時間、與 origin 的落後與領先、未提交檔數、origin 的「工作中」原文。**只報事實，不下指示**（2026-11-13 起，v3 D12） |
| **參考** | `.claude/skills/handoff/SKILL.md` | 碰到才讀：異常判讀、交棒步驟、建制、理由。必守的條件在 `AGENTS.md` 的共用制度一節（2026-11-13 起，v3 第 5 節） |
| **AI push 提醒** | `.claude/hooks/pre-push-handoff.sh`（PreToolUse hook） | 有限字面判讀，缺已提交 HANDOFF 差異時提醒並阻擋；保障範圍見 3.11 |

**分工**：`AGENTS.md` 的共用制度＝必守條件；skill＝**怎麼做**（指令、判讀表、模板）與理由（`reasons.md`）；專案自己的 override 寫在 `AGENTS.md` 共用制度標記外的鐵律，只可加嚴。
2026-11-17 起不再部署 `docs/ai-notes/handover-protocol.md`（v3 Q41）；舊專案留著的那一份是不同步的實例，程序細節上以同步的 skill 為準，這樣不同步的舊實例才不會推翻已升級的制度（2026-11-02／F10）。

**還沒有這套制度的資料夾走 skill 的模式 0（建制）**：使用者講一句「幫我把交接機制建起來」，agent 就跑 `bootstrap.py`（2026-11-18 起，決策書 v3 Q49），再處理它寫進 `HANDOFF.md` 的第一批工作，而不是憑印象重刻——憑印象生出來的版本缺的永遠是最貴的那部分（每條規則後面的「為什麼」、hook 的邊界條件），看起來像那套制度，實際擋不住任何事。2026-11-18 以前這一步是讓 agent 照本部署包逐檔照抄；輸出二十幾個檔最貴也最容易抄錯，所以改由程式寫檔。
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
- `project_doc_max_bytes` 會截 `AGENTS.md`，所以**共用制度那一節必須待在 `AGENTS.md` 最上面**（2026-11-14 前這裡寫「開工第一件事」，那一節 v3 起已併進共用制度）。

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

- 標記格式 `` `機器` ／ `工具` ／ `session 名`（可選） ``，由 skill **A5** 寫；工具名用慣用寫法（`Claude Code`／`Codex CLI`），因為 hook 比的是這個字串。
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

跨 session、跨模型（Claude／Codex）、跨機器（PC↔Mac）協作時，反覆出現的失效模式與對策：

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

## 1. 部署前訪談（安裝程式問，一次問完）

`bootstrap.py` 用 `input()` 一次問完下表（2026-11-18 起，決策書 v3 Q49），把答案換進佔位符；**寫出去的檔案裡不會留下任何 `{{...}}`**。不能互動時用 `--answers <檔案.json>`、`--set KEY=VALUE` 與 `--non-interactive`。答案存成專案裡的 `.bootstrap/answers.json`，日後 `update` 用；答案裡不得有祕密，看到金鑰樣式會拒絕。可以留空的題目留空時寫成 `<部署後填>`，列進 `HANDOFF.md` 的第一批工作；`{{TODAY}}` 由程式填當天日期，不問。

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
| `{{STACK_DIRS}}` | 專案主要程式目錄（寫進 ARCHITECT 的結構） | `src/`、`migrations/` |
| `{{VERIFY_TARGETS}}` | 「一鍵驗證」該查什麼（沒有就先留空） | 健康檢查 API、docker 容器狀態 |

最後一題問：**「這個專案有沒有已知的『絕對不能做』的操作？」**（例：不能直接改資料庫檔、不能在正式環境跑 migration）。它跟 `{{VERIFY_TARGETS}}` 一樣有判斷空間，程式只記下原話：怎麼寫成 AGENTS.md 鐵律（第 4 條之後）、怎麼寫成 `verify_state.py` 的檢查項，列進安裝後 agent 的第一批工作；沒有就先放空著，日後踩到再補。

---

## 2. 要建立的檔案結構

```text
{{GH_REPO}}/
├─ README.md                        ← 專案介紹：是什麼、為什麼做、怎麼連、怎麼跑
├─ AGENTS.md                        ← AI 開工時自動讀：共用制度一節（≤40 行）＋專案鐵律
├─ CLAUDE.md                        ← 指標，指向 AGENTS.md
├─ HANDOFF.md                       ← 當下工作狀態（≤80 行，不累積歷史）
├─ ARCHITECT.md                     ← 專案結構的唯一權威（只有結構變動才改）
├─ .bootstrap/answers.json          ← 訪談答案（安裝程式寫，update 用；不含祕密）
├─ .gitignore
├─ .gitattributes
├─ .claude/                         ← Claude Code 讀這裡
│   ├─ settings.json                ← hook 設定（進 Git）
│   ├─ settings.local.json          ← 各機器本地設定（不進 Git）
│   ├─ hooks/git-freshness.sh       ← SessionStart：fetch 一次，只報事實（最多五行 [facts]）
│   ├─ hooks/pre-push-handoff.sh    ← PreToolUse：AI push 提醒（有限覆蓋，見 3.11）
│   ├─ hooks/codex-hook.cmd         ← Codex 的 Windows 啟動器：找 Git Bash、加純文字標頭、保留結束碼
│   ├─ skills/handoff/SKILL.md      ← 交接程序的參考入口（碰到才讀；必守條件在 AGENTS.md）
│   ├─ skills/handoff/mode-*.md、reasons.md、env.md ← 參考檔：模式步驟、理由與環境差異（共六個，與入口同版本）
│   └─ skills/<其他>/SKILL.md       ← 需要時才建：可重複使用的操作食譜（權威版）
├─ .codex/hooks.json                ← Codex 讀這裡：掛上面同樣那兩個腳本，不另寫一份
├─ .agents/skills/handoff/SKILL.md  ← Codex 讀 .agents/skills/：指向權威版的指標
├─ .agents/skills/<其他>/SKILL.md   ← 需要時才建：同樣只放指標，不複製內容
├─ docs/
│   ├─ ai-notes/
│   │   └─ roadmap.md               ← 持久待辦總表
│   └─ mockups/                     ← 選用：與使用者定案的 UI 規格
└─ tools/
    ├─ check_docs.py                ← 文件與交接快照的機械檢查
    └─ verify_state.py              ← 一鍵現況查證（骨架，依專案填）
```

**選用目錄**（有需要再建，不要為了對齊而空建）：`tests/`、`deploy/`、`apps/`、`archive/`。

---

## 3. 各檔案內容（範本全文；安裝程式寫檔時換佔位符）

### 3.1 `AGENTS.md`

> **2026-11-13 起（v3 D11、D12）**：開始與結束標記之間是共用制度，由部署包管理，≤ 40 行；專案只能在標記外面加自己的鐵律（連線資料 2026-11-17 起在 README，v3 Q40），全檔 ≤ 100 行。共用制度只寫目標、模型不會自己知道的事與不可違反的條件，不寫逐步程序；開始標記裡的 `source:` 版本給開場 hook 比對上游用。

````markdown
<!-- kit-file: AGENTS.md -->
````

### 3.2 `CLAUDE.md`

> **`CLAUDE.md` 只放一行 import，不要寫「去讀 AGENTS.md」那種句子。** Claude Code 從 v2.1.277 起原生讀 `AGENTS.md`，但**有 `CLAUDE.md` 就不讀**；而用文字叫它去讀，官方的說法是 Claude 只有在它決定開那個檔的時候才看得到。`@AGENTS.md` 是 import，內容保證進 context，而且在不支援原生讀取的 session（舊版 Bedrock、關閉 telemetry、使用者關掉內建 plugin）也成立——所以不是「刪掉 `CLAUDE.md` 就好」，留著 import 版比刪掉更穩。理由全文見開頭「跨工具與跨平台」。

````markdown
<!-- kit-file: CLAUDE.md -->
````

> **2026-11-17 起不再產出 `GEMINI.md`**：本專案明確不支援 Gemini（需求決策書 v3 第 1 節只認 Claude Code 與 Codex）。已部署專案裡那一份是專案自己的檔，同步不改寫也不刪，刪不刪由使用者決定。

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

### 3.6（2026-11-17 移除）

原本是 `docs/ai-notes/handover-protocol.md`（交接協定：規則、理由與專案 override）。需求決策書 v3 Q41 把它移出部署包：它大半在重述 handoff skill 與 `AGENTS.md` 共用制度，v3 第 5 節的目標形狀也沒有它。只有它才有的分支模型搬進 skill `mode-b.md` 的 B1，「漏交棒的補救」的理由搬進 `reasons.md`，「verify_state 一律跑」寫進 `mode-a-stop.md` 的 A4；專案自己的 override 改寫在 `AGENTS.md` 共用制度標記外的鐵律。編號保留，免得舊紀錄裡的「3.6」指到別的東西。已部署專案裡的那一份不會被同步工具改寫或刪掉（同步時列 MIGRATE），裡面若有專案 override，搬進 `AGENTS.md` 之後刪不刪由使用者決定。

### 3.7 `docs/ai-notes/roadmap.md`

````markdown
<!-- kit-file: docs/ai-notes/roadmap.md -->
````

### 3.8 `.claude/skills/handoff/SKILL.md`、`.claude/skills/handoff/mode-a.md`、`.claude/skills/handoff/mode-a-stop.md`、`.claude/skills/handoff/mode-b.md`、`.claude/skills/handoff/mode-0.md`、`.claude/skills/handoff/reasons.md`、`.claude/skills/handoff/env.md`（交接程序，本骨架的核心）

> **這一份就是「教 agent 自動交接同步」的東西。** 內容不要改（安裝程式與 update 原樣寫入），包含檔頭的 `source:` 版本標記——它讓你日後能一眼看出某個專案的副本是不是落後了。
> **2026-11-10 起這支 skill 是一個目錄，2026-11-16.4 起七個檔（加 `env.md`）**（決策書 F22：單檔 22,040 字元，正常接棒只需要其中一小部分）。入口與 `mode-a.md` 是新寫的摘要，其餘四個檔是從單檔逐字搬來的；六個檔的 `source:` 標記必須是同一個版本，同步時整個目錄一起覆蓋。下面六個區塊依序對應標題上的六個檔名。

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

**`.claude/skills/handoff/env.md`**——工具與平台差異（2026-11-16.4 起，決策書 v3 Q35）。在 Codex 或 Windows 上碰到對應狀況才讀；只寫環境怪癖與操作提醒，不改變共用狀態的判讀，要加會讓交接結果不同的規則就不放這裡。

````markdown
<!-- kit-file: .claude/skills/handoff/env.md -->
````

**同步規則（重要）**：這個 skill 目錄（七個檔）會同時存在於 ①本部署包 ②每個專案的 `.claude/skills/handoff/` ③（選用）全域 `~/.claude/skills/handoff/`。
⚠️ **在 Claude Code 裡，③ 會蓋掉 ②**（2026-11-12 在 2.1.321 實測，決策書 Q28）：兩處都有同名 skill 時，skill 清單與 Skill 工具用的是家目錄那份，專案那份只靠入口一句「專案有就讀那裡」救回來。所以全域副本一定要跟部署包同版；不同時 3.10 的開場 hook 會印一行 🟡 列出哪些檔不一樣。
**權威版是本部署包**；要改就改這裡，再覆蓋下去，不要在單一專案裡就地改——那正是「同一個事實有多個家」的典型失控起點。

### 3.9 `.claude/settings.json`

````json
<!-- kit-file: .claude/settings.json -->
````

> Codex 的接線見 3.17——它掛的是**同樣這兩個 `.sh`**，不要複製第二份腳本進 `.codex/`。兩份各自演化就會出現「Claude 端會擋、Codex 端不會擋」的不對稱。

> 🔴 **腳本路徑前面那個 `$(git rev-parse --show-cdup)` 不是裝飾，拿掉就只有「從 repo 根目錄開的 session」才有防護。** hook 的 `command` 以 **session 的 cwd** 執行（Claude Code 的 handler「runs in the current directory」；Codex 官方文件同樣明寫，並直接建議改從 Git root 解析 repo hook），而人會從子目錄開 session——`cd tools && claude`。那時候 `bash .claude/hooks/git-freshness.sh` 是 **exit 127、No such file**，而 **SessionStart 失敗跟「檢查過了沒事」在畫面上一模一樣**：落後的本機、別台機器的「工作中」標記、骨架落後提醒三件事同時無聲消失。`--show-cdup` 回傳的是**到 repo 根目錄的相對路徑**（根目錄是空字串、子目錄是 `../`），所以修掉這個洞之後接線裡**仍然沒有任何絕對路徑**，鐵律 5 原封不動；不在 git repo 裡時它是空字串，行為退回跟舊版一樣（多一行 git 的 fatal 到 stderr，刻意不消音——這套骨架的失效一向是太安靜而不是太吵）。2026-11-02 在 `tools/` 下重現 exit 127，修完在 root／`tools/`／`docs/ai-notes` 三處都正常；`verify_bootstrap.py` 的「接線 cwd 定位」把這三處、Windows 啟動鏈與兩個負向測試（舊形式、混合斜線）一起釘住（F05）。

### 3.10 `.claude/hooks/git-freshness.sh`

> **2026-11-13 起只報事實（v3 D12）**：fetch 一次，把最多五行 `[facts]` 放入 SessionStart 的 `hookSpecificOutput.additionalContext`，不下指示、不判讀。2026-11-14 實測 Codex 0.169.0 會把裸的 `[facts]` 開頭輸出誤認為壞 JSON，丟掉整段 context；改用兩個工具都支援的 JSON 外殼。檔名沿用 `git-freshness.sh`，3.9 與 3.17 的接線因此不必改。
>
> Windows 需要 Git for Windows 附的 bash（Claude Code 內建可用）。建立後在 macOS／Linux 上加執行權限：`chmod +x .claude/hooks/git-freshness.sh`。

````bash
<!-- kit-file: .claude/hooks/git-freshness.sh -->
````

### 3.11 `.claude/hooks/pre-push-handoff.sh`（AI push 提醒）

> **AI push 提醒，不是 Git 原生 pre-push 或發布保證。** 只對殼層指令（payload 的 `command` 欄位）含字面 `git push` 的呼叫，依目前分支與本機 `origin` 追蹤 ref 判斷；不解析 shell、選項、實際 remote 或 refspec。`git -c … push`、GUI、間接執行的 script 可能漏判，指令裡只是提到 `git push`（例如 `echo`）也可能誤擋；編輯檔案等非殼層工具的內容提到它不算（2026-11-12，決策書 Q27）；feature 分支與判斷不了時放行。需要硬閘門時另評估 Git 原生 pre-push 與伺服器保護。
> 2026-11-16：2026-11-16.2 曾在這裡加 session ID 占用核對（釋回或替換標記時比對工具送來的 session ID），同日由 2026-11-16.3 撤回：缺資訊就擋，違反本段「判斷不了時放行」與 D1「標記是訊號不是鎖」，也沒有使用者定案。要重新加入，先依 D14 對照、由使用者決定，而且四種工具／平台組合用同一條規則。
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
> 🔴 **要兩道信任，而且失敗是靜默的。** ①專案的 `.codex/` 整層要先被信任（記在 `~/.codex/config.toml` 的 `[projects.'<路徑>'] trust_level`）；②每一支非 managed 的 hook 還要按**當前雜湊**逐一審核（CLI 打 `/hooks`），所以改過接線定義要重新審核。2026-10-30 實測：在未信任的資料夾跑 `codex exec`，hook 完全沒跑，而且 **stderr 一個字都沒有**。所以部署完**一定要照 `mode-0.md` 的 0-6 真的開一個 session**，不能看到檔案在就算裝好了。⚠️ **而且要在互動模式、而且要送出一句話**：2026-11-01 實測互動 TUI 開場不跑 `SessionStart`（跟著第一個 turn 才跑），所以盯著開場看是假陰性。互動模式的補償是 hook 失敗會印 `• Hook failed`，而 `codex exec` 連失敗都不吭聲。
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

**Windows 工作區沙箱下的 Git 更新**：執行時要知道的作法在 3.8 的 `env.md`「Windows」一節（2026-11-16.4 起；以前只寫在這裡，不會部署到專案）。

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

2026-11-18 起（決策書 v3 Q49）這一步是安裝後 agent 的第一批工作，做法在 3.8 的 `mode-0.md`「0-5 本機驗收後才首次發布」：`.gitignore` 先就位再逐檔 `git add`、`git check-ignore` 逐一確認憑證與運行路徑、`check_docs.py` 與 `verify_state.py` 通過才第一個 commit，建 GitHub repo 前先問使用者。安裝程式本身不 add、不 commit、不碰網路。原本寫在這裡的指令搬進了 `mode-0.md`：部署包不在專案裡，專案裡讀得到的只有 skill。

---

## 5. 部署後自檢清單

2026-11-18 起（決策書 v3 Q49）原本這一節的清單逐字搬進 3.8 的 `mode-0.md`「0-6 遠端與工具驗收」，理由同第 4 節。安裝程式寫完會逐檔比對雜湊，但遠端、runtime 與工具實際注入仍要照那份清單驗，未驗證不能宣稱通過。

---

## 6. 之後怎麼維持（一頁操作卡）

**每次開工／收工**：跟 AI 說「接棒」或「交棒」（Claude Code 也可以打 `/handoff`）；工具沒自動找到 skill 時，指它讀 `.claude/skills/handoff/SKILL.md` 的 A 或 B 模式。**順序永遠是先交棒、後接棒**（舊 session 先把狀態寫進 `HANDOFF.md` 並 push，新 session 才讀得到）。

**改到 skill 或 hook 時**：權威版在本部署包 → 改這裡 → 覆蓋各專案 `.claude/skills/handoff/` 整個目錄（七個檔一起，與選用的全域副本）→ 檔頭 `source:` 標記跳版。專案那一端用 `python3 bootstrap.py update --target <專案>`：只換 core 與 adapter 擁有的部分（`owners.json`），專案自己的內容不動。

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
| 專案的目的、網址、連線資料、怎麼跑起來 | `README.md` |

**開新的 ai-notes 檔案時**：回頭在 `ARCHITECT.md` 補上一列，否則沒人會找到它。

**已知的腐化模式與對策**：

| 症狀 | 對策 |
|---|---|
| HANDOFF 超過 80 行 | 把持久內容搬進 ai-notes，只留當下狀態 |
| 同一件事在兩份文件都寫了 | 留一份權威版，另一份改成指標並說明為什麼（避免下一棒又複製回去） |
| `ARCHITECT.md` 開始出現「正在做 X」「預計改成 Y」 | 那是 HANDOFF 與 roadmap 的內容，搬走；本檔只寫現在的結構 |
| 文件寫「共 N 份」「目前 12 個」 | `check_docs.py` 會提醒；改成不寫數字 |
| 換了網址／改了名稱 | 把舊值加進 `check_docs.py` 的 `STALE_PATTERNS`，讓工具替你抓殘留 |
| 兩台機器同時動 main | 恢復 single writer；分岔了就先整合，**禁止 force push** |
