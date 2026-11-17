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
> 骨架建好後，**這份 PROJECT-BOOTSTRAP.md 就可以刪掉**（內容已分散進 AGENTS.md、ARCHITECT.md 與 `handoff` skill）。
> 版本：**2026-11-17.2**（交接協定 `docs/ai-notes/handover-protocol.md` 移出部署包（決策書 v3 Q41），3.6 保留編號、改成移除說明。只有它才有的內容搬進 skill：分支模型進 `mode-b.md` 的 B1，「漏交棒的補救」的理由進 `reasons.md`，「verify_state 一律跑」進 `mode-a-stop.md` 的 A4，`mode-a-stop.md` A6 的指標改指 `reasons.md`；入口的核心優先序改成專案 override 寫在 `AGENTS.md` 鐵律。已部署專案裡的舊協定不改寫也不刪，同步時列 MIGRATE。七個 skill 檔與共用制度標記同版。）
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

| | Claude Code | Codex CLI | Codex 桌面 App |
|---|---|---|---|
| 讀 `AGENTS.md` | ✅ 原生（v2.1.277 起），**但有 `CLAUDE.md` 就不讀**，見下 | ✅ 原生（未信任的專案也讀，2026-10-30 實測） | ✅ 原生（與 CLI 共用 `~/.codex`） |
| 自動載入程序檔 | ✅ `.claude/skills/`，可打 `/handoff` | ✅ `~/.codex/skills/` ＋ repo 的 `.agents/skills/`（2026-10-30 實測，見 3.16） | ✅ 同 CLI |
| Hooks | ✅ `.claude/settings.json` | ✅ `<repo>/.codex/hooks.json`，**2026-10-31 在 `0.164.0` 端到端實測過**；但要專案被信任＋**每個專案各審一次**（信任綁 `hooks.json` 絕對路徑，不是內容），見下 | ✅ **有**（App `26.506` 起有 in-app 信任審核） |
| 關閉 session 時有事件 | ✅ `SessionEnd`（不能擋、1.5 秒預算） | ✅ `SessionEnd`（含閒置 30 分鐘） | ✅ 同 CLI |

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

| Surface | 專案層 `.agents/hooks.json` | 證據 |
|---|---|---|
| **Antigravity CLI `1.4.7`／`1.4.12`** | ✅ **會讀、會觸發** | 2026-10-31 實測（`agy -p` headless），六個事件逐一確認，契約見下；`1.4.12` 上重跑同一份接線沒壞 |
| **Antigravity IDE `1.107.0`** | ❌ 沒觸發 | 2026-10-31 探針，四個事件都沒觸發、log 檔沒產生 |
| **Antigravity 2.0 `2.28.2`** | ✅ **會讀、會觸發** | 2026-10-31 實測：`SessionStart`／`PreInvocation`／`PostInvocation`／`Stop` 四個都進 log，cwd 同樣是 `.agents/`，而且沒有出現任何信任／審核提示。接著在裝了 3.18–3.20 的真專案上開一次 session，agent 把 `[git-check]` 開場原文背了出來——注入確實進到 context。測法見下 |

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

- 標記格式 `` `機器` ／ `工具` ／ `session 名`（可選） ``，由 skill **A5** 寫；工具名用慣用寫法（`Claude Code`／`Codex CLI`／`Gemini CLI`），因為 hook 比的是這個字串。
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
| `{{STACK_DIRS}}` | 專案主要程式目錄（寫進 ARCHITECT 的結構） | `src/`、`migrations/` |
| `{{VERIFY_TARGETS}}` | 「一鍵驗證」該查什麼（沒有就先留空） | 健康檢查 API、docker 容器狀態 |

追問一句就好：**「這個專案有沒有已知的『絕對不能做』的操作？」**（例：不能直接改資料庫檔、不能在正式環境跑 migration）。有的話寫進 AGENTS.md 鐵律第 4 條之後；沒有就先放空著，日後踩到再補。

---

## 2. 要建立的檔案結構

```text
{{GH_REPO}}/
├─ README.md                        ← 專案介紹：是什麼、為什麼做、怎麼連、怎麼跑
├─ AGENTS.md                        ← AI 開工時自動讀：共用制度一節（≤40 行）＋專案鐵律
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

## 3. 各檔案內容（照抄，只換佔位符）

### 3.1 `AGENTS.md`

> **2026-11-13 起（v3 D11、D12）**：開始與結束標記之間是共用制度，由部署包管理，≤ 40 行；專案只能在標記外面加自己的鐵律（連線資料 2026-11-17 起在 README，v3 Q40），全檔 ≤ 100 行。共用制度只寫目標、模型不會自己知道的事與不可違反的條件，不寫逐步程序；開始標記裡的 `source:` 版本給開場 hook 比對上游用。

````markdown
# AGENTS.md — 這個專案怎麼接續

現在做到哪、下一步是什麼，在 [HANDOFF.md](HANDOFF.md)。使用者用 **{{LANG}}** 溝通。
> 最後更新：{{TODAY}}（建立）

<!-- 共用制度開始 source: PROJECT-BOOTSTRAP.md v2026-11-17.2 — 到下方的結束標記為止由部署包管理；專案只能加嚴或填空，要改回部署包改再同步 -->
## 目標

這個專案由不同的 session、模型、機器輪流做。你要讓下一棒不必問任何人，就能從 origin 拿到最新成果、知道現況，而且不會跟別人互相覆寫。怎麼做到由你判斷。

## 你不會自己知道的事

- 本機的檔案可能是舊的。別台機器可能已經推了新東西到 origin，包含更新過的 `HANDOFF.md`。
- 主幹不一定是 `main`：`HANDOFF.md` 的「待續分支」寫了分支名，就在那條分支上做。
- 可能有另一個 session 正在同一條分支上工作。唯一的訊號是 origin 上 `HANDOFF.md` 的「工作中」那一行：`無（已交棒）` 表示沒人在做，其他值表示有人。
- session 開始時會自動 fetch 一次，印出 `[facts]` 開頭的幾行。那是當下的快照，之後會過期。
- 逐步程序、異常判讀與規則的理由在 [`.claude/skills/handoff/`](.claude/skills/handoff/SKILL.md)，是碰到才讀的參考。

## 不可違反的條件

1. 改任何檔案之前，本機要跟 origin 一致，而且 origin 上的「工作中」要先推成你自己（`機器 ／ 工具 ／ session 名`，加開工時間）。推不上去就不算。只讀、只回答問題的 session 不寫。
2. origin 上的「工作中」是別人時，不改檔、不推送，停下來告訴使用者。
3. 使用者要求交棒時才交棒。交棒前先 fetch，確認 origin 上的「工作中」標記確由本 session 推上。無法確認就停下回報，不改檔、不推送。交棒完成的定義：所有成果都在 origin 上；`HANDOFF.md` 整份覆寫成當下狀態（欄位照現有格式，80 行以內，不累積歷史）；「工作中」改回 `無（已交棒）`；本機沒有留下沒推的東西。使用者沒要求就保留你的「工作中」。
4. `main` 上的測試要一直是過的。沒做完的工作放分支推上去，在 `HANDOFF.md` 的「待續分支」寫明分支名。
5. 沒驗證過的事不寫成已驗證。
6. 不提交祕密或金鑰樣式的內容。提交前看 staged 清單，逐檔加入，不用 `git add -A` 或 `git add .`。
7. 不做這些事：`reset --hard`、force push、改寫已推送的歷史、刪分支、自行 stash、刪除不是你建立的檔案、提交 `.gitignore` 排除的東西。
8. 遇到本檔沒講、而且做錯無法復原的狀況（歷史分岔、fetch 失敗、來源不明的未提交變更），停下來告訴使用者。

## session 名稱（工具能改名才做）

格式 `<符號>　MM.DD.HH｜<主題>｜<狀態>｜交棒<N>次`，符號後接一個全形空格。三種狀態：`㊣` 工作中、`※` 待你決定、`↗` 已交棒。

- `MM.DD.HH` 用開場 `[facts]` 印的值，之後不改；主題 ≤10 字，還不知道寫 `待指派`；新 session 的 N 從 0 起算。
- 開始工作改 `㊣`；停下來等使用者決定改 `※`；交棒的 push 成功後才改 `↗`，N 加 1。是 `↗` 或 `※` 時收到任何新訊息，先改回 `㊣`，時間戳、主題與 N 不變。
- 接棒、交棒與停下來等決定的回覆各寫一行 `session：<實際標題>`；工具不能改名就寫 `session：不適用：<原因>；交棒<N>次`。用選項卡片發問也算停下來等決定，卡片之前先寫這一行。
<!-- 共用制度結束 -->

## 專案是什麼

{{ONELINER}}。repo 是 {{GH_VISIBILITY}} GitHub `{{GH_OWNER}}/{{GH_REPO}}`；連線方式與怎麼跑在 [README.md](README.md)，結構與每份檔案的權威在 [ARCHITECT.md](ARCHITECT.md)，持久待辦在 [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md)，碰到才讀。

## 鐵律（違反會造成實際損害）

1. **不提交祕密或運行資料**：{{SECRETS}}、API／SSH private key、{{RUNTIME_DIRS}} 都不可 commit 或 push；{{GH_VISIBILITY}} repository 也不例外。Git 存的是 source 與文件，**不是資料備份**。
2. **破壞性操作前先備份**：改 schema、批次改資料、刪檔、覆寫設定之前，先產出可還原的副本並說明放在哪。
3. **憑證原則**：憑證由使用者提供並存於 {{SECRETS}}，直接讀取即可；不從系統檔、其他主機、Git history 自行挖取或搬運憑證。文件裡只寫「key 在 {{SECRETS}} 的哪一項」，不寫值。
<!-- 4. 專案專屬鐵律寫在這裡：每一條附「為什麼」與發生日期，否則下一棒會繞過它。 -->
````

### 3.2 `CLAUDE.md` 與 `GEMINI.md`（2026-10-30 起兩檔內容不同，下面兩個區塊依序對應）

> **`CLAUDE.md` 只放一行 import，不要寫「去讀 AGENTS.md」那種句子。** Claude Code 從 v2.1.277 起原生讀 `AGENTS.md`，但**有 `CLAUDE.md` 就不讀**；而用文字叫它去讀，官方的說法是 Claude 只有在它決定開那個檔的時候才看得到。`@AGENTS.md` 是 import，內容保證進 context，而且在不支援原生讀取的 session（舊版 Bedrock、關閉 telemetry、使用者關掉內建 plugin）也成立——所以不是「刪掉 `CLAUDE.md` 就好」，留著 import 版比刪掉更穩。理由全文見開頭「跨工具與跨平台」。

````markdown
# CLAUDE.md

@AGENTS.md

<!-- 本檔刻意只有上面那一行 import。Claude Code 有 CLAUDE.md 就不會自己去讀 AGENTS.md，
     而「用文字叫它去讀」不保證它真的會開那個檔。Claude 專屬的細則請放 .claude/rules/，
     不要寫回這裡——那個目錄不計入上面那個判定，會跟 AGENTS.md 並存。 -->
````

> `GEMINI.md` **不改成 import**，維持指標寫法：它只是給還不會讀 `AGENTS.md` 的工具（例如舊版 Gemini CLI）的保險，而它支不支援 `@` import 沒有文件可查——猜錯的話會是靜默失效。若也用其他工具，比照再加一份指標檔即可，**內容永遠只是指標**。

````markdown
# GEMINI.md

本專案的 AI 協作指引統一放在 **[AGENTS.md](AGENTS.md)**——開工前先讀它（共用制度與專案鐵律）。本檔刻意保持極簡，請勿在此累積知識；新知識依 AGENTS.md 的規範寫進 `docs/ai-notes/` 或對應 SKILL.md。
````

### 3.3 `HANDOFF.md`（初始狀態，之後每次交棒覆寫）

````markdown
# HANDOFF — 工作交接狀態

- **交接時間**：{{TODAY}} HH:MM（{{TZ}}）
- **交棒者**：<模型／機器>（專案管理骨架部署完成）

## 任務目標

專案剛建立，管理骨架（AGENTS／HANDOFF／handoff skill／hook／驗證腳本）已就緒。下一步是定義專案本體的第一批工作。

## Git 狀態

- Repo：{{GH_VISIBILITY}} `{{GH_OWNER}}/{{GH_REPO}}`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- 本機能力：<作業系統；哪些憑證可用／未配置，不寫祕密值>

## 已完成

- 管理骨架部署：README／AGENTS／ARCHITECT／CLAUDE／GEMINI／HANDOFF／roadmap／`handoff` skill／兩個 `.claude` hook／`tools/check_docs.py`／`tools/verify_state.py`。
- `check_docs.py` 通過；首次 commit 已 push 到 `main`。

## 未完成／下一步

1. 填 README.md 的「為什麼做」「快速開始」與 AGENTS.md 的專案專屬鐵律。
2. 填 `tools/verify_state.py` 的檢查項目（目前是骨架）。
3. 把第一批工作寫進 [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md)。

## 地雷與注意事項

- 無。

## 服務查證與期望快照

`python -X utf8 tools/verify_state.py`（沒有 `python` 就用 `python3`）
<目前實際關鍵輸出；未能查的層級寫 SKIPPED 與原因>

## 懸置事項（AI 勿自行處理）

- <等使用者決定的事>
````

### 3.4 `README.md`

````markdown
# {{PROJECT_NAME}}

{{ONELINER}}

> 最後更新：{{TODAY}}（建立）

## 為什麼做

<部署後填：要解決什麼問題、給誰用；刻意不做什麼>

## 快速開始

| 用途 | 網址／指令 | 說明 |
|---|---|---|
| <主服務> | <部署後填> | <部署後填> |

| 連線項目 | 值 |
|---|---|
| 服務網址 | <部署後填> |
| 驗證方式 | <部署後填；只寫「key 在 {{SECRETS}} 的 XXX」，不要寫值> |
| 主要資源 ID | <部署後填> |

## 開發與驗證

```bash
python -X utf8 tools/verify_state.py
python -X utf8 tools/check_docs.py
```

`verify_state.py` 查服務現況，結束碼 0 表示沒有 FAIL／ERROR；`check_docs.py` 查死連結、日期標頭、殘留佔位符與交接快照的格式，`--docs-only` 只查文件。macOS／Linux 常常只有 `python3`，`python` 不存在就改用 `python3`。兩支腳本**需要 Python 3.8 以上**：它們只用到 3.8 就有的 API，這是靜態擔保，不是在 3.8 上實跑過（2026-11-02／F14）。

## 專案結構

結構、每份檔案的用途與哪一份是權威版，在 [ARCHITECT.md](ARCHITECT.md)。

## 協作方式

這個專案由不同的 AI session、模型與機器輪流做。開工時跟 AI 說「接棒」，收工時說「交棒」；要先讓舊 session 交棒，新 session 才讀得到最新狀態。目前做到哪在 [HANDOFF.md](HANDOFF.md)，在這裡工作要守的規矩在 [AGENTS.md](AGENTS.md)。

## 授權

<部署後填>
````

### 3.5 `ARCHITECT.md`（結構的唯一權威）

> **為什麼要有這一份**：結構問題（「這個東西放哪」「哪一份是權威版」「資料從哪進來」）本來散在 README 的檔案結構、AGENTS.md 的知識庫地圖與每個人腦袋裡，於是每一棒都要重新拼一次，拼錯了就照著不存在的路徑動手。
> 它與 `HANDOFF.md` 是**故意相反的節奏**：HANDOFF 每次交棒都覆寫，本檔只有結構真的變了才動——一份會頻繁改的結構圖，接手者遲早不會再相信它。

````markdown
# ARCHITECT — 專案結構

> **本檔＝結構的唯一權威**：這個專案由什麼組成、每樣東西的家在哪、哪一份是權威版。
> 最後更新：{{TODAY}}（建立）
>
> **什麼時候改**：只有**結構**變動才改——新增／刪除／搬移長期存在的目錄或檔案、換掉一個元件、改變資料流向、改變「哪一份是權威版」。
> 改功能、修 bug、更新進度**都不要動這一份**。它刻意比 [HANDOFF.md](HANDOFF.md) 慢：HANDOFF 每次交棒覆寫，本檔可能好幾個月不動。

## 這一份與其他檔案的分工（同一件事不要有兩個家）

| 你想知道 | 讀哪一份 |
|---|---|
| 專案由什麼組成、東西放在哪、誰是權威版 | **本檔** |
| 開工必守的條件與鐵律 | [AGENTS.md](AGENTS.md) |
| 這是什麼系統、為什麼做、怎麼連、怎麼跑起來 | [README.md](README.md) |
| 現在做到哪、下一步 | [HANDOFF.md](HANDOFF.md) |
| 還有哪些事沒做、什麼被否決 | [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md) |
| 交接怎麼做與為什麼（指令、判讀表、模板、理由） | [.claude/skills/handoff/SKILL.md](.claude/skills/handoff/SKILL.md) |

README 不另列檔案結構，只連到本檔；結構的細節與理由只寫在這裡。

## 全貌

```text
{{GH_REPO}}/
├─ 管理骨架     跨專案共通，部署時生成（見下表）
├─ 專案本體     {{STACK_DIRS}}（見下方「專案本體」）
└─ 不進 Git     {{SECRETS}}、{{RUNTIME_DIRS}}
```

## 管理骨架（部署時生成，跨專案共通）

| 檔案 | 是什麼 | 權威版在哪 | 什麼時候動 |
|---|---|---|---|
| [README.md](README.md) | 專案介紹：是什麼、為什麼做、怎麼連、怎麼跑 | 本專案 | 目的、連線或執行方式改變 |
| [AGENTS.md](AGENTS.md) | AI 開工時自動讀的條件：共用制度與專案鐵律 | 本專案（共用制度一節由部署包管理） | 多一條鐵律 |
| [CLAUDE.md](CLAUDE.md)、[GEMINI.md](GEMINI.md) | Claude 用 `@AGENTS.md` import；Gemini 用文字指標 | 指向 AGENTS.md | 幾乎不動 |
| [HANDOFF.md](HANDOFF.md) | 當下狀態（≤80 行、覆寫不累積） | 本專案 | **每次交棒** |
| 本檔 | 結構 | 本專案 | 只有結構變動 |
| [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md) | 持久待辦與決策記錄 | 本專案 | 有新待辦或決策 |
| [.claude/skills/handoff/SKILL.md](.claude/skills/handoff/SKILL.md)（入口）＋同目錄的 `mode-a.md`、`mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md`、`env.md` | 交接的可執行程序（0 建制／A 接棒／B 交棒／C 同步）；入口每次讀，其餘依模式才讀 | **部署包**（本專案這份是副本，檔頭 `source:` 標記可辨識落後） | 改制度先改部署包，再整份覆蓋下來 |
| [.claude/hooks/git-freshness.sh](.claude/hooks/git-freshness.sh) | SessionStart：自動 fetch、報告落後／分岔 | 同上 | 同上 |
| [.claude/hooks/pre-push-handoff.sh](.claude/hooks/pre-push-handoff.sh) | PreToolUse：AI push 提醒（有限覆蓋，見 3.11） | 同上 | 同上 |
| [.claude/settings.json](.claude/settings.json) | 上面兩個 hook 的接線（進 Git） | 本專案 | 加減 hook |
| `.claude/settings.local.json` | 各機器本地設定（**不進 Git**） | 各機器自己 | 換機器 |
| [.codex/hooks.json](.codex/hooks.json) | Codex CLI 的 hook 接線——掛的是上面**同樣那兩個 `.sh`**，不另存一份腳本 | 本專案 | 加減 hook |
| [.agents/skills/handoff/SKILL.md](.agents/skills/handoff/SKILL.md) | Codex 也讀 `.agents/skills/`：只放指向權威版的指標 | 指向 `.claude/` 那份 | 幾乎不動 |
| [tools/check_docs.py](tools/check_docs.py) | 文件與交接快照的機械檢查：死連結／過期字串／缺日期標頭／硬編數量／殘留佔位符／交接快照結構 | 部署包（「專案設定」區塊除外，那塊本來就該依專案調） | 專案設定要調 |
| [tools/verify_state.py](tools/verify_state.py) | 一鍵現況查證，輸出 key=value 事實快照 | 本專案（骨架來自部署包） | 服務或檢查項改變 |
| [.gitignore](.gitignore)、[.gitattributes](.gitattributes) | 排除祕密與運行資料；行末強制 LF | 本專案 | 新增祕密檔或運行目錄 |

**跨工具的可靠度不一樣**：`AGENTS.md` 與純 Markdown 的程序檔是**可攜層**（Claude Code／Codex 都原生讀得到）；hooks 已接 Claude Code、Codex CLI／桌面 App，而且**帶條件**——Codex 要專案被信任＋hook 經審核。正確性押在可攜層，不押在 hook 上：2026-10-30 在未信任的資料夾實測，`AGENTS.md` 照樣被讀進 prompt，`.codex/hooks.json` 整層被跳過而且沒有任何訊息。

## 專案本體

<還沒有程式碼就照實寫「尚未有程式碼」。**不要先畫一個想像中的架構**——想像的架構會被下一棒當成既成事實去對齊，然後花一整天把程式碼扭成文件的形狀。>

| 目錄／元件 | 職責 | 進入點 | 相依 |
|---|---|---|---|
| <{{STACK_DIRS}} 之一> | <做什麼> | <哪個檔或指令> | <依賴誰> |

## 資料流

<一段話講清楚：資料從哪裡進來、經過什麼、存到哪裡、誰讀它。部署後填。>

## 不在 Git 裡的東西

{{SECRETS}}、{{RUNTIME_DIRS}}——各機器保有自己的本地副本。**Git 存的是 source 與文件，不是資料備份。**
換機器時這些不會跟著過去，所以 `HANDOFF.md` 的「本機能力」要寫明這台有哪些、缺哪些。

## 改本檔的規矩

1. **跟結構變動同一個 commit**。分開改就會出現「文件說有 `foo/`、實際已經搬走」的空窗；接手者照結構圖找不到檔案時，通常不會回頭修文件，只會下次不再相信它。
2. **附絕對日期**（寫 `2026-09-07`，不要寫「今天」），並更新檔頭的「最後更新」。
3. **只寫結構，不寫進度**。「正在重構 X」屬於 `HANDOFF.md`；「打算重構 X」屬於 roadmap。
4. **每個事實只有一個家**：這裡只寫誰是權威版，不要把權威版的內容複製過來。
````

### 3.6（2026-11-17 移除）

原本是 `docs/ai-notes/handover-protocol.md`（交接協定：規則、理由與專案 override）。需求決策書 v3 Q41 把它移出部署包：它大半在重述 handoff skill 與 `AGENTS.md` 共用制度，v3 第 5 節的目標形狀也沒有它。只有它才有的分支模型搬進 skill `mode-b.md` 的 B1，「漏交棒的補救」的理由搬進 `reasons.md`，「verify_state 一律跑」寫進 `mode-a-stop.md` 的 A4；專案自己的 override 改寫在 `AGENTS.md` 共用制度標記外的鐵律。編號保留，免得舊紀錄裡的「3.6」指到別的東西。已部署專案裡的那一份不會被同步工具改寫或刪掉（同步時列 MIGRATE），裡面若有專案 override，搬進 `AGENTS.md` 之後刪不刪由使用者決定。

### 3.7 `docs/ai-notes/roadmap.md`

````markdown
# 待辦總表 / Roadmap（未完成工作盤點）

> **本檔＝狀態表**：有哪些事、做到哪、相依、優先、誰能動。
> **規格與實作細節不寫在這裡**，一律指回專門文件——本檔只記「狀態」與「決策」。
> 與只描述當下進度的 [HANDOFF.md](../../HANDOFF.md) 分工：roadmap 是持久清單，HANDOFF 是這一輪。
> 建立：{{TODAY}}。最後更新：{{TODAY}}。優先序為**建議值**，可隨時調整。

**優先**：P1 先做／解鎖其他／高風險 ｜ P2 次要 ｜ P3 之後 ｜ P4 不急
**誰能動**：🧑 使用者手動 ｜ 🤝 等使用者點頭後 AI 做 ｜ 🤖 AI 可做

## 一、<分類名稱>

| ID | 項目 | 狀態 | 相依 | 優先 | 誰 |
|---|---|---|---|---|---|
| R1 | <第一件事> | 未開始 | — | P1 | 🤝 |

## 決策記錄（做過但被否決／暫緩的，寫在這裡免得反覆重提）

| 日期 | 決策 | 理由 |
|---|---|---|
| {{TODAY}} | <例：先不做 X> | <理由> |

<!-- 完成的項目用 ~~R1~~ ✅ 標記並保留，狀態欄寫「YYYY-MM-DD 完成」＋指向細節文件的連結。 -->
````

### 3.8 `.claude/skills/handoff/SKILL.md`、`.claude/skills/handoff/mode-a.md`、`.claude/skills/handoff/mode-a-stop.md`、`.claude/skills/handoff/mode-b.md`、`.claude/skills/handoff/mode-0.md`、`.claude/skills/handoff/reasons.md`、`.claude/skills/handoff/env.md`（交接程序，本骨架的核心）

> **這一份就是「教 agent 自動交接同步」的東西。** 內容照抄不要改，包含檔頭的 `source:` 版本標記——它讓你日後能一眼看出某個專案的副本是不是落後了。
> **2026-11-10 起這支 skill 是一個目錄，2026-11-16.4 起七個檔（加 `env.md`）**（決策書 F22：單檔 22,040 字元，正常接棒只需要其中一小部分）。入口與 `mode-a.md` 是新寫的摘要，其餘四個檔是從單檔逐字搬來的；六個檔的 `source:` 標記必須是同一個版本，同步時整個目錄一起覆蓋。下面六個區塊依序對應標題上的六個檔名。

**`.claude/skills/handoff/SKILL.md`**——參考檔入口：碰到才讀（2026-11-13 起，v3 第 5 節）。適用判斷、要細節時讀哪個檔、全程禁令、必須停下來問人的清單；session 命名指回 `AGENTS.md`。

````markdown
---
name: handoff
description: 交接制度的參考檔（碰到才讀，不是必讀）：接棒時 git 狀態不正常（落後、領先、分岔、fetch 失敗、來源不明的未提交變更、別人的「工作中」標記）怎麼判讀與處理；交棒時 HANDOFF.md 怎麼覆寫、怎麼安全提交與 push；中途同步；在還沒有這套制度的資料夾裡把骨架建起來（模式 0 建制）；每條規則的理由與事故。規則本身在專案 AGENTS.md 的共用制度一節，衝突時以那裡為準。Triggers on 接手、接棒、交棒、收工、換機器、同步進度、建制、導入這套制度、建立交接機制、幫我建 HANDOFF、新專案骨架、handoff、hand off、resume work、bootstrap project、set up handoff。
---

<!-- source: PROJECT-BOOTSTRAP.md v2026-11-17.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 交接與同步程序（參考檔入口）

> **2026-11-13 起（需求決策書 v3 第 5 節）這個目錄是碰到才讀的參考，不是制度成立的前提。** 必守的條件在專案 `AGENTS.md` 的共用制度一節；本目錄的步驟與它衝突時以 `AGENTS.md` 為準，使用者明確指示仍優先。
>
> 在程序細節上，**核心優先序：SKILL.md**（含同目錄的模式檔）優先於專案實例。專案自己的 override 寫在 `AGENTS.md` 共用制度標記外的鐵律，只可加嚴；舊專案留著的 `docs/ai-notes/handover-protocol.md`（2026-11-17 起不再部署，v3 Q41）是不同步的專案實例，升級時須人工遷移。不得在單一專案就地修改共用 skill，回部署包修正再同步。模式 0 的權威是 `PROJECT-BOOTSTRAP.md` 部署包。

## 適用判斷（先做這一步）

| 專案根目錄的狀態 | 走哪裡 |
|---|---|
| 有 `AGENTS.md` ＋ `HANDOFF.md` | 適用，需要細節時往下找 |
| 沒有，而且使用者**明講**要導入這套制度（建交接機制／建骨架／bootstrap） | **模式 0 建制** |
| 沒有，使用者也沒提 | **本程序不適用**。直接做他要的事，**不要憑空建立交接檔案**；最多問一句「要不要導入這套交接制度？」，他說要才走模式 0 |

專案沒有 `tools/verify_state.py`／`tools/check_docs.py` 也能用：對應步驟改為「跳過並在回報寫明沒有該工具」，**不要自己發明驗證**。

## 需要細節時讀哪個檔

| 情況 | 模式 | 讀 |
|---|---|---|
| 這個資料夾還沒有這套制度，使用者要求建起來 | **0 建制** | `mode-0.md` |
| 接棒、續作、換機器；已交棒後又要改檔 | **A 接棒** | `mode-a.md`（正常路徑）；開場 `[facts]` 有不正常的值讀 `mode-a-stop.md` |
| **使用者要求**交棒／收工／換人接手 | **B 交棒** | `mode-b.md` |
| 工作告一段落；想拉最新或推一個安全點 | **C 同步** | `mode-b.md` 的 C 節 |
| 開場沒有 `[facts]`；在 Codex 或 Windows 上：指令跑得久、hook 接線有改、Git 寫不進 `.git` | 任何模式 | `env.md`（依工具、依平台各讀一節） |

- **使用者沒要求就不得自行交棒**：告一段落時自己判斷要不要 commit／push（C），不改 `↗`、不加次數。A5 開工標記與 C 中途安全點都不宣稱交棒。
- **模式檔與本檔同目錄**：專案有 `.claude/skills/handoff/` 就讀那裡，沒有就讀全域 `~/.claude/skills/handoff/`（Codex 是 `~/.codex/skills/handoff/`）。
- 要改、質疑或想繞過任何一條規則之前先讀 `reasons.md`。`mode-a.md` 與 `mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md` 衝突時以後四者為準；`env.md` 只寫環境差異，不改變共用狀態的判讀；它們全部與 `AGENTS.md` 衝突時以 `AGENTS.md` 為準。

## 全程禁令

🚫 全程禁止：`reset --hard`、`push --force`、自行 `stash`、覆寫他人 commit、刪 branch。

## 必須停下來問使用者（不得自行決定）

- Git 異常：dirty 來源不明、接棒時 ahead-only、fetch 失敗、diverged、不能 fast-forward、遠端意外前進、沒有 upstream
- origin 上的「工作中」是別人（同一條分支同時兩台＝違反 single writer）
- `push --force`、`reset --hard`、刪分支、改寫歷史
- 功能分支要併進 `main`（需使用者驗收；文件／基建分支驗證過可自己併）
- 憑證缺失，或需要跨機器搬憑證
- HANDOFF 沒授權的破壞性操作（刪檔、批次改資料、改 schema）
- **建制（模式 0）**：資料夾不是空的、已有 Git 歷史或 README；要覆蓋既有的 `.gitignore`／`README.md`；建 GitHub repo 與第一次 push

停下來等回答時，session 名稱改成 `※`（格式見下）。

## session 命名（每則訊息都適用）

格式、三種狀態、何時改與交棒計數的規則在 `AGENTS.md` 共用制度的「session 名稱」一節，這裡不重寫，以免兩份各自演化。時間戳用開場 `[facts]` 第一行印的 `MM.DD.HH`。細則、反例與「為什麼要改名」在 `reasons.md` 的「session 命名」；交棒計數何時加一在 `mode-b.md` 的 B9。
````

**`.claude/skills/handoff/mode-a.md`**——接棒的正常路徑。**新寫的摘要**；跟下一份衝突時以下一份為準。

````markdown
<!-- source: PROJECT-BOOTSTRAP.md v2026-11-17.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 模式 A：接棒（正常路徑）

> 碰到才讀的參考。必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。本檔只寫「一切正常」的走法；任何一步跟這裡寫的不一樣，讀同目錄的 `mode-a-stop.md`（完整判讀表、占用處理、漏交棒補救）。A1–A4 不修改任何檔案。

## A1＋A2.5 同步與占用：讀開場的 [facts]

開場 hook 會 fetch 一次，印出幾行 `[facts]`：時間（含 session 名用的 `MM.DD.HH`）、本機、分支；與 `origin/<當前分支>` 的落後與領先、origin 的短 SHA、未提交檔數；origin 那份 `HANDOFF.md` 的「工作中」原文。只報事實，判讀由你做。

一切正常的樣子：fetch 成功、落後 0、領先 0、未提交 0、「工作中」是 `無（已交棒）`。這時記下 origin 的 SHA（A5 要比對），往下走。

**它是快照，不是通行證。** 下列情況先重跑一次 `bash .claude/hooks/git-freshness.sh`，以新輸出為準：已交棒後續聊要改檔、之後切換過分支、工具沒有跑 hook 或開場找不到 `[facts]`。

任何一個值不是上面那樣（含腳本跑不起來、專案沒有這支 hook）：不要自己判斷「大概沒事」，讀 `mode-a-stop.md` 的 A1 與 A2.5 照表走。

## A2 站對分支

讀 `HANDOFF.md` 的「待續分支」。寫「無」就待在權威分支；指向別條分支就 `git switch <branch>`（切換失敗就停，禁止自動 stash），**切換後重做 A1**。要開新分支，從現在的主幹開，不是從 `main` 開。

## A3 最小讀取

只讀 `AGENTS.md` ＋ `HANDOFF.md`；其他文件等任務真的碰到再讀。

## A4 驗證（只記錄，不修）

```bash
python -X utf8 tools/verify_state.py
```

`python` 不存在就用 `python3`；`AGENTS.md` 指定別的驗證入口就照它；沒有工具就在回報寫明。與 HANDOFF 的「服務查證與期望快照」比對，以實況為準，差異留到開工標記推上去之後才修。FAIL／ERROR 是待修問題，SKIP／NOT_CONFIGURED 是未驗證，都不能寫成通過。要把連線失敗標成 SKIPPED 之前，先讀 `mode-a-stop.md` 的 A4。

## A5 回報後才動手

```text
Git：<分支>、<與 origin 關係>、<待續分支>
驗證：<verify_state 關鍵值／SKIPPED 與原因>
現況：<用自己的話講一句現在做到哪>
下一步：<我打算做的第一件事>
session：㊣　<MM.DD.HH｜主題>｜工作中｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次
```

回報完就改 session 名稱（規則在 `AGENTS.md` 的「session 名稱」）。**只讀、只問問題的 session 不寫開工標記。** 確定要改檔才做下面四步，做完才開始改：

1. 把 `HANDOFF.md` 的「工作中」改成本機與本 session（沒有這一欄就在「Git 狀態」補一列）：

   ```markdown
   - **工作中**：`desk-win` ／ `Claude Code` ／ `㊣　10.30.09｜匯入格式｜工作中｜交棒0次`，2026-10-30 09:12 (+08) 開工
   ```

   用全形斜線 `／` 分三欄：機器 ／ 工具 ／ session 名（第三欄可省）。**工具欄不能省**，寫慣用名（`Claude Code`／`Codex CLI`）。
2. **只** stage `HANDOFF.md`，核對 staged 清單後 commit，訊息用 `chore(handoff): <機器> 開工`。
3. 重新 `git fetch origin`。遠端 SHA 跟 A1 記下的不同就停；相同才 push 到當前分支。
4. push 成功後重讀 origin 的「工作中」，確認是本 session。

**push 失敗就不是「已標記」**：告訴使用者這次沒有標記保護，問要不要在這個狀態下繼續，不要靜默往下做。開工標記是協調訊號，不是互斥鎖；這次 push 是開工例外，不算交棒、不加次數。
````

**`.claude/skills/handoff/mode-a-stop.md`**——接棒的完整判讀表與異常處理（狀態轉移、A1–A6 原文）。開場 `[facts]` 有不正常的值時才讀。

````markdown
<!-- source: PROJECT-BOOTSTRAP.md v2026-11-17.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 模式 A：完整判讀與異常處理

> 2026-11-10 拆分 handoff skill 時逐字搬自單檔 `SKILL.md`。`mode-a.md` 是正常路徑的摘要，衝突時以本檔為準。文內的「session 命名」見入口 `SKILL.md` 與 `reasons.md` 的同名節；B 各步驟在 `mode-b.md`。
>
> 2026-11-13（需求決策書 v3）：本目錄降為碰到才讀的參考；必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。文內提到的 `[git-check]` 判讀行、「全綠」行已由只報事實的 `[facts]` 取代。

### A／B／C 狀態轉移（2026-11-02／F11）

| 狀態 | 前提 | 允許操作 | 成功證據 | 失敗處理 |
|---|---|---|---|---|
| 待接棒 | 尚未取得寫入資格 | A1 同步、A2 定位分支、A2.5 查占用 | fetch exit 0；乾淨；ahead=0、behind=0；origin 標記可依 A2.5 續行 | fetch 失敗／ahead-only／分岔／未知 dirty：停下回報，等待指示 |
| 已定位 | A1／A2／A2.5 通過 | A3 讀取、A4 驗證並記錄差異、A5 回報 | 驗證結束碼、FAIL／ERROR／SKIP／NOT_CONFIGURED 與差異已列出 | 未驗證不可寫成通過；只讀記錄，修檔延至 A5 開工成功後 |
| 開工中 | A5 回報完成且確定要改檔 | 只提交 HANDOFF 開工標記，fetch 確認遠端未意外前進後 push | push exit 0；origin 的工作中欄位是本 session | push 失敗停止修改，詢問是否接受沒有標記保護；遠端意外前進則停下 |
| 工作中 | A5 開工成功 | 執行已授權任務；C 推安全點走 B7 → B8 | 最終文件檢查 exit 0；push exit 0；本地與 upstream 對齊；origin 仍是本 session 工作中 | 驗證失敗修正或明記風險；fetch／push 失敗不宣稱同步成功 |
| 待交棒 | B1–B6 已完成 | B7 驗最終快照並安全提交，再走 B8 | 最終文件檢查 exit 0；push exit 0；工作樹乾淨且與 upstream 對齊；origin 標記為無（已交棒） | 最終文件檢查失敗不可發布；fetch／push 失敗不交棒、不加次數 |
| 已交棒 | B8 成功且遠端標記已清 | B9 改名並增加一次；新訊息依續聊規則恢復活動 | origin 工作中欄位與 session 回報可核對 | 改名失敗如實回報，重試不重複計數；再改檔前重走 A |

**證據的範圍**：驗證工具不存在或專案另有驗證入口時，依 AGENTS.md 執行並明記替代指令／不適用原因；不可把缺工具當成 exit 0。狀態表不把服務 FAIL／SKIP 自動變成通過，也不把工作中標記當成互斥鎖。
**為什麼要列狀態**：舊程序漏掉 ahead-only／fetch 失敗，切分支後沿用舊檢查，A4 又在 A5 之前叫人修檔；B6 改了快照卻只引用 B4 的舊結果，且所有 push 都被描述成交棒。這些順序互相打架，不能靠接手者自行猜例外。

---

## A. 接棒

### A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF）

```bash
git status -sb && git fetch origin && git status -sb && git log --oneline -3
```

判讀表——**只有前兩列可以自己往下走**：

| 看到 | 動作 |
|---|---|
| 乾淨、落後 origin | `git pull --ff-only` 後繼續 |
| 乾淨、與 origin 一致 | 直接繼續 |
| 乾淨但 ahead-only（ahead > 0、behind = 0） | **停**：列出未推送 commit 與來源，等待使用者指示；不得自動 push、reset 或把它當成已同步 |
| fetch 失敗（非零退出） | **停**：保留錯誤輸出，遠端新鮮度未知；不得用舊 tracking ref 宣稱同步完成 |
| 有未提交變更，來源不明 | **停**：貼 `git status --porcelain` 與 `git diff --stat`，問使用者這是誰留下的 |
| 已分岔（同時 ahead＋behind） | **停**：回報落後／領先數與雙方 commit 標題，等指示 |
| pull 不能 fast-forward | **停**：不要 rebase／merge 到一半才問 |
| 沒有 upstream | **停**：回報，不要自行 `push -u` 建立 |

🚫 全程禁止：`reset --hard`、`push --force`、自行 `stash`、覆寫他人 commit、刪 branch。

fetch 成功後才判讀；用 `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` 確認 upstream，再用 `git rev-list --left-right --count HEAD...@{upstream}` 取得 ahead／behind（左／右）。PowerShell 請把 `@{upstream}` 引號包住。pull 成功後重查 `git status --porcelain` 與計數，乾淨且兩者為 0 才進 A2。detached HEAD、無法讀取計數或 upstream 不對應 `origin/<當前分支>` 時停下回報，不猜比較對象。

### A2 站對分支

讀 `HANDOFF.md` 的「待續分支」：

- 寫「無」→ 待在權威分支（通常 `main`）。
- 指向 `feature/...` → **那條才是主幹，`main` 可能明顯落後**。要續作就 `git switch <branch>`；不要因為 `main` 是預設分支就以為它最新。
- 要開新分支 → 從**現在的主幹**開，不是從 `main` 開。

**切換到待續分支後重跑 A1**（含 fetch、upstream、dirty 與 ahead／behind 判讀），再讀該分支的 HANDOFF 並走 A2.5；不可沿用切換前的通過結果。切換失敗就停下，禁止自動 stash。

### A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆）

**本制度支援接力式 single-writer。「工作中」是協調訊號，不是互斥鎖。** 同一工作樹不得同時有兩個 writer；機器／工具／可變 session 標題不是穩定 owner token。A2.5 到 A5 仍有時間窗，Git 的 non-fast-forward 拒絕不能保護共用 index 與未提交檔案。
**時間戳不代表租約到期，不得自動奪取 writer**；未知是否仍在工作時，保留標記並請使用者確認。原子 claim 尚未實作，也未做並行實驗，不宣稱有並行互斥保證（2026-11-02／F12）。

**站對分支之後、讀文件之前**，看該分支 `HANDOFF.md` 的「工作中」欄位：

```bash
git show "origin/$(git rev-parse --abbrev-ref HEAD):HANDOFF.md" | grep -F "**工作中**"
```

讀 `origin/` 那一份、**不讀本機的**——此刻可能還沒 pull，本機那份是舊快照。
同時記錄觀測到的 `origin/<當前分支>` SHA，A5 再 fetch 時必須與此值比對；不能只看 ahead／behind 或標記文字。

| 看到 | 動作 |
|---|---|
| `無（已交棒）` | 正常，往下走 |
| 沒有這個欄位 | 這個專案的骨架還沒升級到有這個機制，照舊往下走——但**別把「沒有欄位」當成「沒人在做」**，這一輪沒有防呆，心裡要有數。欄位由 **A5** 寫標記時一併補上，那也就是這個專案的升級點 |
| 指向**別台**機器 | **停**，見下方三個選項 |
| 指向**這台**機器，工具欄是**你自己這個工具** | 多半是你自己還開著的另一個 session。核對標記裡的 session 名與開工時間對不對得上你開過的那一個；對不上就照「別台機器」處理 |
| 指向**這台**機器，工具欄是**別的工具** | **停**，照下方三個選項處理（選項 1 的「回那台機器」換成「回那個工具的 session」）。**這比跨機器更急**：跨機器至少是兩份磁碟，同機器通常就是同一個資料夾，兩個 agent 會即時互相覆寫 |
| 指向**這台**機器，**沒有工具欄**（舊格式） | 當成「別的工具」處理。分不出來的時候**不要往放行的方向猜** |

**指向別台機器時不要自己決定**，把這三個選項給使用者：

1. **回那台機器走完交棒**（預設建議）——那台的未提交變更只在那台的磁碟上，這裡拿不到
2. 使用者確認那台已經沒在跑 → 授權在這裡接手，由本 session 清掉舊標記並照 **A6** 回推補交接
3. 這次只讀不寫 → 不接棒、不寫標記、不動任何檔案

同時把 session 名稱改成 `※　MM.DD.HH｜<主題>｜待你決定｜交棒<N>次`（見「session 命名」）。

> **工具名的權威是寫標記的那一棒自己填的，不是環境變數。** 模型知道自己是哪個工具，三個平台都一致；
> 而環境變數在「從一個工具的殼層啟動另一個工具」時會被繼承——Codex 的 session 會自稱 Claude Code
> （2026-10-31 實測，細節見部署包「工具身分」一節）。所以 hook 的變數偵測只用來**加嚴**：
> 它看到的工具跟標記不一致就直接 🔴；一致、或認不出來，都只給 🟡 並把「你自己是不是 X」這一句丟回來給你答。
> **永遠不因為偵測失敗而放行。**
>
> **舊版只比機器名**，於是同機器換個工具會落進「大概是你自己另一個視窗」的 🟡，
> 而那時候叫人去驗的證據是「側欄有沒有 `㊣`」——只有 Claude Code 有側欄。
> 判準綁在一個工具的介面上，另外三個平面就等於沒有判準。

> **為什麼標記寫在開工而不是收工**：寫在開工的標記不依賴任何人記得收尾——A 沒交棒，標記就留在 origin 上，下一棒一定看得到。
> 2026-10-30 重查後，這條規則的理由要講得更準：Claude Code 與 Codex **有** `SessionEnd` 事件（Codex 的還會在閒置 30 分鐘時觸發）。但那個事件救不了這件事——它**不能擋下結束**，Claude Code 那邊預設只有 1.5 秒預算，做不完一次 `git push`。所以它最多提醒**離場的那一個人**，擔保仍然只能押在「開工就推上 origin」這一邊。
> **它救不回什麼**：A 那些未提交的變更仍然只在 A 的磁碟上。標記只讓你知道「有東西在那台機器」，東西還是得回去拿。

### A3 最小讀取

只讀 `AGENTS.md` ＋ `HANDOFF.md`。其他文件等任務真的碰到再讀（`ARCHITECT.md` 列了每份檔案的用途）。
**不要**為了「先了解全貌」把 `docs/` 全讀一遍——那是 token 黑洞，也不會讓你更準。

### A4 一鍵驗證

```bash
python -X utf8 tools/verify_state.py
```

（`python` 不存在就用 `python3`；腳本不存在就跳過並在回報寫明。）
**一律跑**，不是「有憑證才跑」：不需要憑證的本機與公開檢查照樣會動，缺憑證只讓需要它的那幾層記 SKIPPED。舊版寫「有憑證就跑」，整支腳本會被一個不相干的前提擋掉（2026-11-02／F15）。
與 HANDOFF 的「服務查證與期望快照」比對。不一致時**以實況為準**，此步只記錄差異與結束碼、不修改專案檔案；到 A5 回報且開工標記 push 成功後，才修文件並註記絕對日期。FAIL／ERROR 是待修問題，SKIP／NOT_CONFIGURED 是未驗證，不能寫成通過。

🔴 **標 SKIPPED 前先排除「設定沒帶到」**：連線失敗 ≠ 本機沒有憑證。先確認該機器的憑證路徑／環境變數是不是沒設，是不是暫時性網路錯誤（重試 2–3 次）。確認憑證真的不存在才寫 `SKIPPED（本機未配置）`。**不得**從系統資料庫、其他主機、Git history 或別台機器自行挖取／搬運憑證。

### A5 回報後才動手（3–5 行）

```text
Git：<分支>、<與 origin 關係>、<待續分支>
驗證：<verify_state 關鍵值／SKIPPED 與原因>
現況：<用自己的話講一句現在做到哪>
下一步：<我打算做的第一件事>
session：㊣　<MM.DD.HH｜主題>｜工作中｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次
```

不要重述整份 HANDOFF。有疑問就多一行問題。

**首次接棒回報完就改 session 名稱**成 `㊣　MM.DD.HH｜<主題>｜工作中｜交棒<N>次`（規則見「session 命名」）；**已交棒後續聊在收到新訊息時就先恢復工作中，不等 A5**。然後把實際結果寫進模板最後那行 `session：`——改了就寫改成什麼，工具沒有這個能力就寫 `不適用：<原因>` 並附交棒次數，不必為此停下來問使用者。**那一行不能省**：寫不出來就是沒做，而這是唯一看得出來的地方。這一步跟下面的開工標記是兩件事，**不要等它**。

**確定要動手改東西，才寫開工標記。** 只讀、只問問題的 session 不寫——那會在權威分支的歷史裡堆一堆沒有內容的 commit，而被灌爆的歷史沒人會認真看。
**開工標記是協調訊號，不是互斥鎖**；先確認同一工作樹只有一個 writer。遠端 SHA 與 A2.5 觀測值不同就停止；失敗的開工不能當一般 merge 衝突合併。push 後重讀 owner 只確認遠端標記內容，不等於取得原子 claim。

1. 把該分支 `HANDOFF.md` 的「工作中」欄位改成本機與本 session。舊專案沒有這一欄，就在「Git 狀態」那節補一列（這就是該專案的升級點，不用另外安排一次升級）：

   ```markdown
   - **工作中**：`desk-win` ／ `Claude Code` ／ `㊣　10.30.09｜匯入格式｜工作中｜交棒0次`，2026-10-30 09:12 (+08) 開工
   ```

   三欄，用全形斜線 `／` 分隔：**機器** ／ **工具** ／ **session 名**（最後一欄可選，環境沒有 session 名就省略）。

   - **工具欄不能省**（2026-10-31 加）。少了它，同一台機器換個工具就會落進「大概是你自己另一個視窗」的 🟡，
     而同機器通常就是同一個工作樹——兩個 agent 即時互相覆寫，比跨機器那個洞更貴。`check_docs.py` 第 6 項會擋。
   - **工具名用慣用寫法**（`Claude Code`／`Codex CLI`／`Gemini CLI`）：hook 比的是這個字串，
     寫同義詞只會讓它多報一次 🔴——那是加嚴的方向，不會放行，但也是噪音。
   - 記 session 名稱比只記機器名有用——有側欄的工具可以直接拿它把那個 session 點開。

2. **只** stage `HANDOFF.md`，核對 staged 清單後 commit；重新 fetch，確認遠端沒有比 A2.5 觀測值意外前進才 push 到**當前分支**。訊息用 `chore(handoff): <機器> 開工` 這類前綴，之後掃歷史時一眼可略過。這是開工 push 例外，不先走 B6 清標記、不宣稱交棒；push 成功後重讀 origin 的工作中欄位，確認是本 session，才開始任務修改。
**push 失敗就不是「已標記」**：明確告訴使用者「這次沒有標記保護，別台機器不會知道我在做」，問他要不要在這個狀態下繼續。**不要靜默往下做**——你會以為有保護，實際上沒有。（名稱照樣是 `㊣`——它說的是「這個 session 在做事」，不是「標記已經在 origin 上」。）

規則一句話：**側欄講的是這個 session，HANDOFF 講的是這條分支。** 只有 `↗ 已交棒` 是在宣稱一件 git 的事，所以只有它要等 push 成功。

### A6 回推補交接（只有在 A1 判定「前一輪漏交棒」時才走）

前一輪做完沒交棒，工作樹留著未提交變更，`HANDOFF.md` 停在更早的狀態。
**這種情況下最貴的損失不是那個 commit，是知識**——理由與取捨會永久消失，
只有留在磁碟上的東西救得回來。理由與事故的完整記述在同目錄 `reasons.md` 的
「漏交棒的補救」一節（2026-11-17 起；之前在專案的交接協定裡，v3 Q41）。

1. 先**唯讀**盤點產物：新產出的結果目錄、檔案 mtime、`git reflog`、結果檔裡的
   費用／參數。算出實際花了多少錢——`HANDOFF.md` 的費用欄多半已經錯了。
2. 問使用者三件事：**要不要收斂進這條分支**、**有沒有已知該留／該刪的東西**、
   **要不要補跑未完成的部分**（會花錢的一律等他點頭）。
3. **先落地知識（B2）再 commit（B7）**，讓知識與產生它的程式碼進同一批 commit。
4. 回推寫成的段落**一定要標明「這是事後回推、當時無記錄」**，
   **不要替它補理由**——編出來的理由會變成下一棒眼中的既成事實。
5. 修掉 `HANDOFF.md` 裡與實況矛盾的陳述，然後照 B 模式正常收工。

> 三層防呆（SessionStart／`hooks.json`／pre-push）擋不住這件事：它們全都掛在
> 「下一個動作」上。Claude Code 與 Codex 另外有 `SessionEnd`（2026-10-30 查），但它不能擋下
> 結束、預算只有 1.5 秒，推不了東西上去。所以這仍然是**程序
> 責任，不是工具責任**。
````

**`.claude/skills/handoff/mode-b.md`**——交棒 B1–B9、中途同步 C、交棒計數（原文）。

````markdown
<!-- source: PROJECT-BOOTSTRAP.md v2026-11-17.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 模式 B：交棒；模式 C：中途同步

> 2026-11-10 拆分 handoff skill 時逐字搬自單檔 `SKILL.md`。A／B／C 狀態轉移表與 A 各步驟在 `mode-a-stop.md`；文內的「session 命名」見入口 `SKILL.md` 與 `reasons.md` 的同名節。
>
> 2026-11-13（需求決策書 v3）：本目錄降為碰到才讀的參考；必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。文內提到的 `[git-check]` 判讀行、「全綠」行已由只報事實的 `[facts]` 取代。

### 同一 session 的交棒計數

- **交棒次數的家是該 session 標題尾端的 `｜交棒<N>次`，新 session 從 0 起算。** A5、續聊、`※` 與模式 C 都保留 N。沒有改名能力的工具，以同一 session 最近一次 `session：` 回報保存 N；上下文壓縮後也要從標題或這一行恢復。HANDOFF 仍是當下快照，不新增逐 session 清單；工作中欄位引用當時的完整 session 名稱即可。
- **只有 B1–B8 完成且 B8 push 成功，才在 B9 把 N 加 1。** 開工標記、中途安全點、失敗的 push 與重複回報同一次成功交棒都不增加；第幾次 commit 也不是第幾次交棒。同一輪跨多個 repo 收尾，以本 session 的一次 B9 回報計一次，必要的 push 全部成功後才加 1。先保存成功結果與新的 N，再改名並回報，改名失敗後重試仍使用同一個 N。
- **舊標題沒有次數時，先查本 session 的成功交棒回報，不拿別的 session 或整個 repo 的交棒數代替。** 能確認總數就補上；只知道至少交棒一次而無法還原總數，就寫 `交棒≥1次`，之後成功一次變成 `交棒≥2次`，保留「至少」的語意，不把未知編成精確數字。確定本 session 尚未交棒才填 0。
- **為什麼（2026-11-02）**：使用者指出 agent 會在任務階段結束時自主交棒；使用者仍在同一 session 對話，側欄卻一直是「已交棒」。只在 A5／B9 改名漏掉了「同一 session 再收到訊息」這個狀態轉換。用 session 自己的計數保留它曾交棒的事實，才能同時表達現在在做事、以前已交棒幾次，又不把 HANDOFF 變成歷史表。

---

## B. 交棒

**只有使用者要求交棒／收工／換人接手才走 B**；agent 自己覺得告一段落時走 C，不得自行交棒（理由見 `reasons.md` 的「交棒由使用者決定」）。

九步，**順序就是執行順序**，做完一步再下一步。

### B1 收斂到安全點

**動任何檔案、提交或推送前先核對占用。** 先 `git fetch origin`，從 origin 上持有開工標記的分支讀取 `HANDOFF.md`，記下該分支的 SHA。用本 session 開工時已確認推送的完整標記比對，含機器、工具、當時的 session 名（有填時）及開工時間。同一台機器、同一工具或使用者請你交棒，都不足以證明標記屬於本 session。

**標記屬於別人、缺失、已釋回或無法確認歸屬就停下**，回報遠端狀態，不改檔、不提交、不推送。fetch 失敗也停下。2026-11-15 的 Codex 占用者探針中，六個新 session 在同機器同工具下都釋回了舊 session 的標記，因此在第一步核對。

**使用者明確確認舊標記與工作屬於自己時，照 `mode-a-stop.md` A2.5 選項 2 接手。** 例如使用者說「上一個 session 斷線了，工作中標記和未提交修改都是我們自己的，請交棒」。本 session 先把「工作中」改成自己、推上並重讀遠端確認，再走 A6 與本程序其餘步驟。只說「請交棒」或只是同機器同工具，不算確認（2026-11-16 使用者決定，需求決策書 v3 Q36）。

未完成的東西二選一：完成並驗證；或 commit／push 到分支並在 HANDOFF 標明風險與已知安全 commit。
**不留來源不明的工作樹**，也不要把半成品併進 `main`。

**分支模型**（要開分支或併 `main` 時讀；2026-11-17 從專案的交接協定搬來，v3 Q41）：判準是「需不需要使用者驗收」。

| 類型 | 例 | 能不能自己併 `main` |
|---|---|---|
| 功能分支（需驗收） | `feature/<ID>-<slug>` | 不能，要使用者驗收通過才併 |
| 文件／基建分支（不需驗收） | `docs/cleanup`、`chore/…` | 能，驗證通過（`check_docs.py`＋`verify_state.py`）即可併 |

- 文件／基建變更不得被功能驗收阻塞：文件被關在某個功能的驗收閘門後面，接手者「先同步 `main`」就拿到過期文檔集。小型文件修正可直接在 `main`，成批整理才開分支。
- 功能分支若已成為事實上的主幹（`main` 明顯落後），新分支從該分支開，不要從 `main` 開，否則是在過期基礎上工作，日後必定衝突；開之前先在回報裡說明。
- 本輪做不完就 push 分支，並在 HANDOFF 記錄分支名、已知安全 commit、未完成內容與風險。

### B2 持久知識落地（今天學到的寫進 repo，不要留在對話裡）

| 你剛剛得到什麼 | 寫進 |
|---|---|
| 一條「以後都要這樣做」的規則、一次踩坑 | `AGENTS.md` 鐵律（重大）或 `docs/ai-notes/<主題>.md`（細節） |
| 做過兩次以上、而且踩過坑的操作步驟 | `.claude/skills/<slug>/SKILL.md` |
| 還有哪些事沒做、什麼被否決／暫緩及理由 | `docs/ai-notes/roadmap.md` |
| **專案結構變了**：新增／搬移目錄、換掉一個元件、改變資料流或權威版位置 | `ARCHITECT.md`（只有結構變動才動它，而且跟該變動同一個 commit） |
| 現在做到哪、下一步 | `HANDOFF.md`（B6 才寫） |

規則：**附絕對日期**（寫 `2026-08-05`，不要寫「今天」「上週」）；**每個事實只有一個家**，其他地方只放指標；新開 `docs/ai-notes/` 檔案要回頭在 `ARCHITECT.md` 補上一列，否則沒人找得到它（2026-11-17 起，`AGENTS.md` 只留開工必讀，沒有知識庫地圖）。

### B3 服務驗證

```bash
python -X utf8 tools/verify_state.py
```

### B4 文檔驗證（動過任何 `.md` 就必跑）

```bash
python -X utf8 tools/check_docs.py
```

**exit 2 表示要修**（死連結／過期字串／缺日期標頭）。這些 `verify_state.py` 一項都查不到。

### B5 條件式例行檢查

本專案若有固定流程（部署、版本號 bump、測試、備份），對照 `AGENTS.md` 鐵律：這輪有動到就執行並記錄；沒動到就在 HANDOFF 明記「不適用」。
**不要靜默略過**——接手者無法分辨「沒做」與「不用做」。

**hook 接線有改或同步過，就驗收實際執行**；Codex 的信任審核與驗收方法見 `env.md` 的「Codex」。

### B6 更新 `HANDOFF.md`（覆寫，≤80 行，不累積歷史）

```markdown
# HANDOFF — 工作交接狀態

- **交接時間**：YYYY-MM-DD HH:MM（<時區>）
- **交棒者**：<模型／機器>（主題一句話）

## 任務目標
<目前目標>

## Git 狀態
- Repo：`<owner>/<repo>`
- **待續分支**：<無，或 feature/... @ 已知安全 commit>；若 main 落後主幹要註明
- **工作中**：無（已交棒）　← 交棒時必須是這個值；開工時由 A5 改成 `機器` ／ `工具` ／ `session 名`
- 本機能力：<機器；哪些憑證可用／未配置，不寫祕密值>

## 已完成
- <事項與驗證>

## 未完成／下一步
1. <可執行步驟>

## 地雷與注意事項
- <最容易搞砸的事>

## 服務查證與期望快照
`python -X utf8 tools/verify_state.py`
<目前實際關鍵輸出；未能查的層級寫 SKIPPED 與原因>

## 懸置事項（AI 勿自行處理）
- <等使用者決定的事>
```

⚠️ **不要在 HANDOFF 裡寫它自己的最終 commit hash**——提交 HANDOFF 的當下就過時了。最終 hash 放交棒回覆（B9）。
⚠️ **「工作中」欄位要改回 `無（已交棒）`。** 這一欄是覆寫時最容易被原封不動抄過去的——交棒了卻還寫著「工作中」，下一棒會被擋在 A2.5，然後回頭去找一台其實已經收工的機器。
⚠️ 舊內容直接覆寫，不要往下疊成日誌；歷史由 Git 查。

### B7 安全提交

**先驗最終快照**：B6 覆寫完成後，先明確 stage 本次檔案，再執行下列檢查。2026-11-03／R07：檢查器用 Git 檔案集合，先驗再 stage 會漏掉新增文件；部分 stage 又可能讓工作樹的好內容遮住 index 的壞內容。

```bash
git diff --check && git status --porcelain
```

明確 stage 需要的檔案（**不要無腦 `git add -A`**），然後看過清單再 commit：

```bash
git diff --cached --name-only && git diff --cached --stat
```

清單確認後執行 `python -X utf8 tools/check_docs.py --staged`（無 `python` 用 `python3`；專案有替代入口依 AGENTS.md），exit 0 才提交發布。`--staged` 拒絕本次待提交文件或檢查器同時有未暫存變更，不允許部分 stage 驗證依據。其餘驗證用到的程式／設定也須確認 index 與工作樹一致；不能用工作樹結果證明不同的提交內容。之後若改文件內容或 stage 集合，必須重新驗證；缺工具明記不適用原因，不可引用 B4 的舊通過結果。服務程式、設定或驗證依據若在 B3 後改過，連 B3 也重跑；純粹填寫已取得的結果不必重新呼叫外部服務。2026-11-02／F11：先驗 B4 再寫 B6，舊結果不能證明最後那份快照合格。

祕密掃描（有輸出就停下來逐條確認）：

```bash
git diff --cached -U0 | grep -nEi "(api[_-]?key|secret|token|passwd|password|BEGIN [A-Z ]*PRIVATE KEY)" | head -20
```

確認沒有憑證、運行資料、備份、實際業務資料後才 commit。

### B8 發布

推送會釋回標記前，fetch 後比對 B1 的占用分支 SHA 與完整標記。若本 session 在流程中已推送該分支，SHA 以自己推送且已從遠端確認標記仍相同的 commit 為準。兩者任一對不上就停下，不推送。

```bash
git fetch origin && git status -sb
```

fetch 失敗 → **停下**，遠端新鮮度未知。遠端意外前進 → **停下**，禁止 force push，回報並等待使用者指示。正常才 push；push 後 `git status -sb` 必須 clean 且與 upstream 對齊。
**push 失敗就不是完成交棒**，不要在回覆裡寫「已交棒」。

### B9 收尾與回報（≤5 行）

三件事，**依序做，回報是最後一件**。這一輪 B1–B8 全做對、卻漏掉改名的 session（2026-11-01 量到兩個）漏掉的正是唯一沒有編號的那一步，所以它現在有編號了。

1. **push 成功之後**依「同一 session 的交棒計數」將 N 加 1，把 session 名稱的符號與狀態換成 `↗` 與 `已交棒`，尾端寫 `｜交棒<N>次`，前面的 `MM.DD.HH｜<主題>` 原封不動（見「session 命名」）。push 失敗就不要改、不要加次數——那不算交棒。同一次成功交棒重試改名或重複回報，不再加一次。A5 漏了改名、現在才要補的話，前綴照「session 命名」那條去抄，**不要用現在的時間重算**。
2. 確認推上去的那一份「工作中」真的已經清掉（本機改對了但沒推上去，下一棒看到的還是舊的）：

   ```bash
   git show "origin/$(git rev-parse --abbrev-ref HEAD):HANDOFF.md" | grep -F "**工作中**"
   ```

3. 回報，照這個模板：

   ```text
   結果：<做完什麼>
   驗證：<B3／B4 的結果；跳過的項目寫原因>
   分支／最終 commit：<branch> @ <hash>，已 push／未 push
   session：↗　<MM.DD.HH｜主題>｜已交棒｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次
   接手最容易搞砸：<一件事>
   ```

   **`session：` 那一行不能省**——它是改名這條規則唯一的守門人（理由見「session 命名」）。寫不出來就是沒做。

---

## C. 中途同步（還沒要交棒）

- 拉最新：照 A1 判讀表走，異常一樣停。
- 推安全點：這是中途 push 例外，**時機由 agent 自行判斷**，走 B7 → B8；保留本 session 的「工作中」標記，不走 B6 的釋出標記與 B9 的交棒計數。origin 的「工作中」仍是本 session 時，**不必為這次 push 更新 HANDOFF**；只有做了破壞性或高風險的改動、中途斷線會讓下一棒誤判時，才補一行風險，並照 B7 驗最終文件。成功後重讀 origin 標記仍是本 session。不得把中途同步說成已交棒。
- **建議交棒（只建議，不動手）**：一段工作做完、回報之前，工具讀得到上下文用量（例如 Claude Code 桌面 App 的 `get_usage`）就讀一次，照實寫出數字；達 70% 在回覆加一行「上下文 <N>%，建議交棒；要交棒請說『交棒』」，然後照常續作或等指示，不自行走 B。同一門檻只提一次，使用者沒要交棒，到 85% 再提一次。讀不到用量就不拿用量當理由，**不要估算**。
- **換機器前一定要 push，下一台機器一定要先 fetch。**
- **single writer**：同一時間只有一個 agent／一台機器可以改 `main` 與 `HANDOFF.md`。要換手就先交棒。
````

**`.claude/skills/handoff/mode-0.md`**——建制 0-1–0-8（原文）。

````markdown
<!-- source: PROJECT-BOOTSTRAP.md v2026-11-17.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 模式 0：建制

> 2026-11-10 拆分 handoff skill 時逐字搬自單檔 `SKILL.md`。B6、B9 在 `mode-b.md`；「session 命名」見入口 `SKILL.md`。
>
> 2026-11-13（需求決策書 v3）：本目錄降為碰到才讀的參考；必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。文內提到的 `[git-check]` 判讀行、「全綠」行已由只報事實的 `[facts]` 取代。

## 0. 建制（這個資料夾還沒有這套制度）

**這一模式是「把骨架生出來」，不是交接。** 產物的權威是 `PROJECT-BOOTSTRAP.md` 部署包，本節只是它的執行順序與停止判準。

### 0-1 先確認你在對的資料夾、對的情境

```bash
pwd && ls -a && git status -sb
```

| 看到 | 動作 |
|---|---|
| 空資料夾，或只有部署包 | 標準情境，往下走 |
| 已有 `AGENTS.md`／`HANDOFF.md` | **這不是建制**——改走模式 A 接棒 |
| 已有程式碼、README 或 Git 歷史 | **停**：這是「既有專案補裝」。既存檔案只補段落**不覆蓋**，動手前先把打算新增／修改的清單列給使用者看過 |
| 這是家目錄、桌面或某個大目錄 | **停**：先確認資料夾。灑錯地方的檔案沒人會逐一刪乾淨 |

🚫 使用者點頭之前不要建立任何檔案。

### 0-2 取得部署包（沒有它就停）

`PROJECT-BOOTSTRAP.md` 在這個資料夾嗎？在 → 用它，逐檔照抄。不在 → **停下來跟使用者要**（來源：`project-bootstrap` repo 的 `PROJECT-BOOTSTRAP.md`，或它產出的骨架 zip）。

🔴 **絕對不要憑記憶重刻骨架。** 憑印象生出來的版本，缺的永遠是最貴的那部分——每條規則後面的「為什麼」、hook 的邊界條件、`check_docs.py` 那幾項檢查。看起來像那套制度，實際上擋不住任何事，而且沒有任何跡象；下一棒會以為自己有防護網。

### 0-3 訪談：一次問完（部署包第 1 節）

照第 1 節那張表把佔位符**一次問完**，不要分五輪擠牙膏。最後追問一句：**「這個專案有沒有已知的『絕對不能做』的操作？」**

拿不到的答案就留 `<部署後填>`，**不要自己編一個看起來合理的值**——編出來的網址、憑證檔名會被下一棒當成事實，然後照著它去連一個不存在的東西。

### 0-4 逐檔建立（部署包第 3 節）

內容照抄、只換佔位符；**不要自行增刪制度**，也不要「順手優化」措辭——那些句子後面各有一次事故。
全檔 LF。macOS／Linux 建完要 `chmod +x .claude/hooks/*.sh`。

### 0-5 本機驗收後才首次發布（部署包第 4 節）

⚠️ **`.gitignore` 必須先就位再 `git add`**。順序反了祕密就進第一個 commit，之後刪不掉——那是要重建 repo 的等級。
建 GitHub repo 與第一次 push 前**先問使用者確認**（owner／repo 名、public 或 private）：這是外部動作，不是本機檔案操作。
先完成第 4 節的本機驗收（含 ignore、文件與可執行位元），全部通過才建立第一個 commit 並發布；不能等到上 GitHub 後才驗憑證是否已進 Git。

### 0-6 自檢（部署包第 5 節）

逐項跑、逐項回報通過／不適用／有問題。至少要有：

```bash
python -X utf8 tools/check_docs.py
```

（`python` 不存在就用 `python3`。）**exit 0 才算過**；`SKILL.md` 前三行必須是 frontmatter，壞掉 skill 就不會被載入，整套自動化靜默失效。

### 0-7 寫第一份 `HANDOFF.md` 與 `ARCHITECT.md`

建制本身就是第一段工作，所以照 **B6** 寫第一份 HANDOFF（任務目標＝骨架已就緒；下一步＝填 `README.md` 的連線資料與 `verify_state.py` 的檢查項）。
`ARCHITECT.md` 的「專案本體」這時候通常還是空的，**照實寫「尚未有程式碼」**——不要先畫一個想像中的架構，那會被下一棒當成既成事實去對齊。

### 0-8 刪掉部署包，回報

自檢全過之後才刪 `PROJECT-BOOTSTRAP.md`（以及壓縮檔附的 `讀我-先看這個.md`）。留著就是第二份會腐化的副本；而那份說明檔寫著「佔位符還沒填」，下一棒讀到會以為部署沒做完，再跑一次訪談。

回報 ≤5 行：建了什麼、自檢結果、repo 與分支、**還沒填的洞**、下一棒第一件事。
````

**`.claude/skills/handoff/reasons.md`**——理由、事故與 session 命名細則（原文）。要改、質疑或想繞過規則之前才讀。

````markdown
<!-- source: PROJECT-BOOTSTRAP.md v2026-11-17.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 理由、事故與細則原文

> 2026-11-10 拆分 handoff skill 時逐字搬自單檔 `SKILL.md`：每條規則的理由、日期與事故，加上 session 命名的完整細則。**不是每輪必讀；要改、質疑或想繞過某條規則之前先讀。** 文內的「本檔」指整個 handoff skill 目錄；A／B／C／0 各步驟分別在 `mode-a-stop.md`、`mode-b.md`、`mode-0.md`。
>
> 2026-11-13（需求決策書 v3）：本目錄降為碰到才讀的參考；必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。文內提到的 `[git-check]` 判讀行、「全綠」行已由只報事實的 `[facts]` 取代。

## 前言原文

> **本檔＝程序**：做什麼、下哪些指令、什麼時候必須停下來問人。
> override 只可加嚴或填補核心留給專案的設定，不能默默放寬同步、占用、驗證與發布門檻；使用者明確指示仍優先。不得在單一專案就地修改共用 skill，應回部署包修正再同步（2026-11-02／F10：避免舊協定推翻新程序）。
> **例外是模式 0（建制）**：那一段的權威是 `PROJECT-BOOTSTRAP.md` 部署包（協定檔本身也是它生出來的），衝突時以部署包為準。
> 純 Markdown，任何模型（Claude／Gemini／Codex）都應直接讀取，不限某一家工具。

## 適用判斷：為什麼沒人提就不建

最後一列是硬規定：這支 skill 會在使用者只是想改一行程式時被載入，未經同意就在別人的 repo 裡長出十幾個檔案是災難，而且他多半不會逐一刪乾淨——會留下半套制度，比沒有更糟。

## 模式 0 為什麼留在每一份副本裡

> 模式 0 在**已經部署好的專案裡永遠用不到**——這裡有雞生蛋問題：skill 是部署之後才存在於專案的。
> 它真正會被載入的地方是**全域副本**（`~/.claude/skills/handoff/`、`~/.codex/skills/handoff/`）。
> 專案內這份仍保留模式 0，是為了讓副本可以整份無腦覆蓋，不必維護兩種版本——分版本就是下一個「同一個事實有多個家」。

## 停下來問人時為什麼要改名

**停下來的同時把 session 名稱改成 `※　MM.DD.HH｜<主題>｜待你決定｜交棒<N>次`**（見「session 命名」）。**不只這張表**——「接下來做哪一件」這種普通的徵詢也是在等人回答，一樣要改。否則使用者在側欄只看到一個「工作中」的 session，不會知道它其實卡在等他回答——這種等待很容易一整天沒人發現。

---

## session 命名（每輪必做；工具做不到就在回報裡寫「不適用」）

側欄上十幾個 session 全叫「接棒」，要一個個點進去才知道哪個是哪個。**所以每換一次狀態就改一次 session 名稱**——有這個能力才做（例如 Claude Code 桌面版的 `set_session_title`），**沒有就跳過，不要為此停下來問使用者**：Codex CLI 與 Gemini CLI 目前沒有對應能力，為一個做不到的步驟回報失敗只是噪音。

🔴 **但「跳過」要說出來，不能安靜跳過**（2026-11-01 加硬）。**A5 與 B9 的回報模板各有一行 `session：`，必填**：改了就寫改成什麼，工具沒有這個能力就寫 `不適用：<原因>`。那一行是這條規則唯一能有的守門人——改名發生在 session 的外殼上，repo 裡不留任何痕跡，`check_docs.py`、`git-freshness.sh`、pre-push 防呆**三層全都看不到它**，所以漏掉是完全無聲的，而無聲的漏跟「沒有這條規則」在畫面上一模一樣。2026-11-01 量到：六個收尾 session（全 Sonnet）裡**只有四個**改了名，六個的 git 結果全部正確——漏的只有命名。**為什麼漏沒有量過**，所以這次不針對某個原因下藥，改的是「有沒有做」看不看得出來。

```text
<符號>　MM.DD.HH｜<主題>｜<狀態>｜交棒<N>次
```

| 符號 | 狀態 | 什麼時候改 |
|---|---|---|
| `㊣` | 工作中 | 首次接棒在 **A5** 回報完之後；已交棒後續聊在**收到新訊息時先改**，**不等開工標記**——只讀、只掃，或專案根本沒有 `HANDOFF.md` 的時候都寫不了標記，改名照樣要做 |
| `↗` | 已交棒 | **B9**，而且是 **push 成功之後**（push 失敗不改、不加次數，照 B8 那不算交棒）；**B9 的回報要寫出改成什麼與累計次數** |
| `※` | 待你決定 | **任何時候你把問題丟回去等回答就改**，不限「必須停下來問使用者」那張表 |

範例（同一個 session 兩次交棒，中間收到一則新訊息）：

```text
㊣　11.02.09｜修續聊狀態｜工作中｜交棒0次
↗　11.02.09｜修續聊狀態｜已交棒｜交棒1次
㊣　11.02.09｜修續聊狀態｜工作中｜交棒1次
↗　11.02.09｜修續聊狀態｜已交棒｜交棒2次
```

### 已交棒後續聊（每則新訊息的入口）

**每則使用者新訊息都先檢查 session 狀態，包含只問問題、補充、更正與致謝，不必等使用者再說「接棒」。** 上次是 `↗ 已交棒`（或 `※ 待你決定`）時，先用改名工具恢復 `㊣ 工作中`，再回答或執行任務；必要的標題讀取可先做。**保留原本的 `MM.DD.HH`、主題與交棒次數，不重算時間、不歸零、不另建 session。** 本輪後來真的需要使用者決定，仍依原規則轉成 `※`，並保留次數。

- **只讀續聊不改 HANDOFF、不 commit、不 push，也不為了結束回答再交棒。** 改名已足以表達 session 正在活動，不能為了一句問答新增空的開工／交棒紀錄。
- **續聊要改檔前重新走 A1–A5，重查 origin 的工作中標記。** 前次交棒已釋出分支，另一個 session 可能已接手；恢復側欄狀態不代表重新取得寫入權。通過 A1–A4 並完成 A5 回報後才寫開工標記，push 失敗照 A5 停下。
- **續聊回覆必須有 `session：` 一行，列出實際標題與交棒次數。** 沒有改名能力就寫 `不適用：<原因>；交棒<N>次`；有工具但呼叫失敗要如實寫失敗，不能宣稱已改。這是逐訊息的程序義務，SessionStart hook 不會因為同一 session 多一則訊息再跑一次，也不能宣稱只同步 skill 就讓所有舊 session 自動生效。

### 其他命名規則

- **`MM.DD.HH` 取接棒當下的時間，之後永遠不更新。** 交棒時一起改掉的話，同一個 session 在側欄的名字會跳掉，使用者記得的時間點就對不上了。
- **交棒才要補名字的時候，前綴去抄、不要用現在的時間重算。** A5 那一步漏掉的話，`MM.DD.HH` 從 `HANDOFF.md`「工作中」欄位抄（它記的就是開工時間，新格式連當時的 session 名都在裡面；B6 把它改回「無（已交棒）」之前先讀，已經改掉就 `git show <開工那個 commit>:HANDOFF.md`）。重算會寫出**交棒**的小時，而這個時間戳唯一的用途是讓人在側欄找回開工那一刻——錯了沒有任何徵兆。舊版 B9 只寫「前面的 `MM.DD.HH｜<主題>` 原封不動」，那句話**預設 A5 已經改過名**；沒改過的時候它無從執行，而唯一拿得到的時間正好是錯的那個。
- **主題 ≤10 字，取自 `HANDOFF.md` 的任務目標，壓成動詞＋受詞。** 不要寫「更新文件」「修 bug」這種放哪個 session 都成立的詞——那會退化回「全部長一樣」，等於沒改。還不知道要做什麼就先寫 `待指派`，第一件事確定後就地改一次。
- **符號後面接一個全形空格（U+3000）再開始日期。** 半形空格撐不開，`↗` 這種細筆畫的符號會黏在數字上。
- **符號放最前面**，是因為側欄窄的時候是從尾巴開始截字；狀態是最該被看見的東西，不能放在第一個被截掉的位置。尾綴那幾個字是版面夠寬時的補充，截掉不損失資訊。
- 同一天同一個主題開第二個 session 才在主題後面加數字（`匯入格式2`），不是每個都編號。
- **改名的依據是 session 的狀態，不是 git 的結果。** 側欄要回答的是「這個 session 現在在幹嘛」，`HANDOFF.md` 的「工作中」欄位要回答的是「哪台機器握著這條分支」——兩件事、兩個讀者，不要綁在一起。綁住的代價 2026-10-30 在骨架自己的 repo 上現形：舊版 A5 寫「push 成功才改名」，而 project-bootstrap 刻意沒有 `HANDOFF.md`、寫不了開工標記，於是改名那一步永遠到不了，這個 repo 的 session 全部停在「接棒」兩個字，直到交棒才一次拿到名字——那時候它已經不需要被認出來了。唯一的例外是 `↗ 已交棒`：它本身就在宣稱一件 git 的事，所以只有它要等 push。
- **側欄的 `㊣` 不證明 origin 上有開工標記。** 跨機器防呆看的是 `HANDOFF.md` 的欄位（A2.5），側欄只是給人看的；別拿它當防呆的證據。
- **模式 C 中途同步不改名**——狀態沒變。
- 模式 0 建制照 B9 收尾，主題寫 `骨架建制`。
- **改完這份規則、同步完副本之後，當下開著的 session 不保證自動採用新版。** `SKILL.md` 是 session 載入它的那一刻讀進 context 的快照，之後改磁碟上的檔案不會回溯生效——舊 session 要明確重新讀取新版 skill，或重開 session 才會拿到新版；重新讀取時仍保留原 session 時間與次數。已經寫下的 session 名稱也不會自己更新，要補只能呼叫改名工具。2026-10-24 加上全形空格那條時就是這樣：副本 15:20 全部同步完，一個 15:29 才交棒的 session 名字裡照樣沒有空格——那不是漏同步，查錯方向會白花一輪。

---

## 交棒由使用者決定（2026-11-12／Q31）

- **起因**：舊入口把「工作告一段落」與「準備 `git push`」都導向 B，push 提醒 hook 又在 `main` 沒更新 HANDOFF 時擋下並叫 agent 走 B。結果 agent 每做完一段就跑 B1–B9、覆寫整份 HANDOFF 並改成 `↗`；使用者還在同一個 session 對話，token 卻花在重複的收尾上。2026-11-12 使用者指示：commit／push 時機由 agent 自行判斷，可以主動看上下文用量建議交棒，但沒要求就不能交棒。
- **中途 push 為什麼可以不更新 HANDOFF**：origin 上的「工作中」仍是本 session，下一棒會在 A2.5 被這個標記擋下，不會拿暫時過期的快照當現況；session 中斷沒交棒時，A2.5／A6 的漏交棒補救本來就以 Git 實況為準。破壞性或高風險改動仍要補一行風險，因為那正是斷線後下一棒最容易誤判的地方。
- **為什麼門檻是 70%／85%、而且一定要讀數字**：Claude Code 桌面 App 的上下文視窗是 1M tokens，97% 才自動壓縮；70% 留得下一次完整的 B。2026-11-10 有 session 憑感覺說「接近 70%」就收工，實際只有 38%。讀不到就不拿用量當理由；同一門檻只提一次，避免提醒本身又變成消耗。
- **只建議不動手**：交棒會釋出分支、改 session 狀態，是使用者對「這段工作結束了」的判斷，agent 不代為決定。

## 跑得久的指令為什麼一次等完（2026-11-14）

- **起因**：2026-11-14 一次 Codex 桌面 App 接棒，從開始到推完開工標記約 2 分 40 秒、28 次模型呼叫，累計輸入約 112 萬 tokens。其中驗證腳本跑了兩次，每次約 54 秒；Codex 的指令工具約 1 秒就先交回，模型再每隔約 5 秒呼叫一次去讀輸出，兩次驗證共空等了 15 次呼叫，超過一半。每次呼叫都把整段上下文（當時約 35k–45k tokens）再送一次，累計輸入約有一半來自這些空等。同一份程序在 Claude Code 跑，殼層工具會等到指令結束，沒有這種呼叫。
- **為什麼寫成「一次等夠久」而不是「別跑驗證」**：驗證的輸出本身仍然要看，省的是等待時重複送出的上下文，不是驗證。等太久的代價只是那一次呼叫晚一點回來；問太勤的代價是每次都重送整段上下文。
- **沒有量過的部分**：改寫後 Codex 是否真的照做、呼叫次數降到多少，要在 Codex 實際接棒一次才知道；這段寫下時尚未驗收。

2026-11-14 後續實測：v2026-11-14.3 的 Codex 桌面 App 接棒用了 11 次模型呼叫、349,246 input tokens（其中 304,000 cached）、約 147 秒。已比前次少，但仍有兩次外層 `functions.exec` 在 30 秒返回，內層 `write_stdin` 的 60000 ms 並沒有控制外層；驗證完整成功輸出與已注入的 AGENTS 重讀又增加上下文。故改為外層與內層一起設定，單批等待最多一分鐘再回報進度，成功只回摘要，既有規則不重讀。這是同一工具的兩次觀測，非控制變因的模型 A/B；新版是否進一步省模型用量須另次實際交接驗收，不為量測自動呼叫模型。v3 共用入口不增加規則，正常驗證與 B7 staged 檢查保留。

## 反例（真的發生過，別重演）

- ❌ 開工沒 fetch，對著落後數十個 commit 的本機 HANDOFF 工作數小時 → 分岔，收拾一整天。
- ❌ 連線失敗直接寫「本機未配置」→ 其實只是金鑰環境變數沒設，結論全錯。
- ❌ 純文件修正卡在功能分支等驗收 → 接手者同步 `main` 拿到過期文檔集。
- ❌ 知識寫在對話裡或私有記憶 → 換模型、換機器後全部消失。
- ❌ HANDOFF 愈疊愈長變成日誌 → 接手者要讀 20 分鐘才知道現在做到哪。
- ❌ push 完才想起沒更新 HANDOFF → 下一棒拿到過期狀態（AI push 提醒只有有限覆蓋，可能漏判；不能當發布保證）。
- ❌ A 機器沒交棒就關掉，B 機器開 session 看到 `✅ 與 origin 同步` 就接棒 → 那個綠勾只證明「B 沒落後」，**不證明「沒有別台在做」**；A 的未提交變更整批被繞過。這就是「工作中」標記要擋的那件事。
- ❌ 會花錢的那一輪跑完直接關掉視窗 → 數字還在磁碟上，**當時的判斷與取捨永久消失**；三層防呆全都掛在「下一個動作」上，擋不住這件事（Claude Code 與 Codex 的 `SessionEnd` 也擋不住：它不能阻止結束，也來不及 push）。
- ❌ 建制時沒拿到部署包，憑印象生一套「差不多的」骨架 → 規則沒了理由、hook 沒了邊界條件，看起來有制度、實際擋不住任何事。
- ❌ 使用者只說「幫我看一下這個 repo」，agent 自作主張把整套骨架灑進去 → 別人的 repo 多出十幾個沒人要的檔案，而且不會被逐一刪乾淨。
- ❌ 建完沒刪部署包 → 第二份會腐化的副本，下一棒還會以為部署沒做完而重跑一次訪談。
- ❌ session 名稱全部一樣 → 側欄認不出哪個是哪個；主題寫成「更新文件」也一樣，改了名還是分不出來。
- ❌ 停下來問使用者卻沒改名 → 側欄顯示「工作中」，使用者以為它還在跑，實際上在等他。只把「必須停下來問使用者」那張表當成改名時機也一樣——普通的「要選哪個」同樣是在等人。
- ❌ 同一台機器上從一個工具換到另一個工具接棒，而標記只寫了機器名 → hook 印 🟡「大概是你自己另一個視窗」，兩個 agent 對著同一個工作樹即時互相覆寫。工具欄就是為這件事加的（2026-10-31）。
- ❌ 拿環境變數當工具身分的權威 → 在別的工具殼層裡啟動時變數被繼承，Codex 的 session 自稱 Claude Code，於是「同工具」成立、直接放行。變數只能加嚴。
- ❌ 把改名綁在「開工標記 push 成功」之後 → 這輪只讀、或專案刻意沒有 `HANDOFF.md`，標記寫不了，側欄就永遠停在「接棒」。2026-10-30 在骨架自己的 repo 上發現：三個 session 全是 `↗ 已交棒`，一個 `㊣ 工作中` 都沒有過。
- ❌ git 全做對、就是沒改 session 名稱 → 2026-11-01 量到六個收尾 session 裡有兩個這樣（全 Sonnet，git 結果全部正確，用的還是派工時給的標題）。**原因沒有量過**，所以別替它補一個；要知道的是**沒有任何檢查看得到這件事**（改名在 repo 外面），所以它只能靠 A5／B9 回報那一行 `session：` 露出來。
- ❌ 已交棒後收到新訊息，因為使用者沒再說「接棒」就保留 `↗` → 使用者仍在續聊，側欄卻表示已結束；收到訊息就恢復 `㊣`、保留交棒次數，改檔前再跑 A 模式。單純答問不新增一次交棒（2026-11-02）。

## 漏交棒的補救（2026-11-17 從專案的交接協定搬來，v3 Q41）

一輪工作做完就關掉、沒走交棒：工作樹留著未提交變更與整個結果目錄，`HANDOFF.md` 還停在前一輪，寫著與實況矛盾的話（典型的是費用欄寫「本輪未產生費用」）。這件事真的會發生，而且往往隔了好幾週、換了機器或模型才被下一棒發現。

- **代價不是那個沒有的 commit，是知識。** 產物還在磁碟上，數字都查得回來；當時的判斷與取捨永久消失：為什麼選這組參數、哪條路試過但放棄、哪些結果是在非基準組態下取得的。
- **hook 一個都擋不住**：它們都掛在「下一個動作」上，而直接關掉視窗沒有下一個動作。2026-10-30 重查：Claude Code 與 Codex 有 `SessionEnd`，但它不能擋下結束、預設只有 1.5 秒，做不完一次 `git push`，最多提醒離場的人，救不了下一棒。所以這是程序責任。
- **開工標記只縮小了洞**（2026-10-30 加）：寫在開工而不是收工，所以「直接關掉視窗」繞不過它。但它救不回 A 機器的未提交變更；A 在開工標記推上去之前就關掉時，origin 上什麼都沒有；A 那一端的 hook 沒真的生效時，只剩程序擔保。
- **回推寫的是數字，不是理由**：推測一旦寫成當時的理由，就會變成下一棒眼中的既成事實，所以回推的段落一定要標明「事後回推、當時無記錄」。
- 給交棒者的一句話：會花錢、或會產生無法重現之產物的那一輪，不交棒就等於沒做。補救成本遠高於當場寫 10 行 HANDOFF。

## 規則 → 理由在哪（對照表）

> 2026-11-10（決策書 Q17 (b)）：入口與 `mode-a.md` 不逐條加理由連結，免得吃掉常態必讀的額度；改在這裡列出每個段落的理由在哪。「本段內文」＝理由就寫在那一段裡；「沒有寫下理由」＝拆分前的單檔就沒寫，照實標出來，不補編；「分節標題」＝規則在它底下各步驟。`verify_bootstrap.py` 守：入口與四個模式檔的每個段落標題都列在左欄，右欄指到的段落真的存在。**它不判斷理由寫得對不對。**

| 規則（檔案 § 段落） | 理由在哪 |
|---|---|
| SKILL.md § 適用判斷（先做這一步） | reasons.md § 適用判斷：為什麼沒人提就不建<br>reasons.md § 反例（真的發生過，別重演） |
| SKILL.md § 需要細節時讀哪個檔 | reasons.md § 前言原文<br>reasons.md § 交棒由使用者決定（2026-11-12／Q31）<br>reasons.md § 模式 0 為什麼留在每一份副本裡<br>mode-a-stop.md § A／B／C 狀態轉移（2026-11-02／F11） |
| SKILL.md § 全程禁令 | 沒有寫下理由 |
| env.md § 開場沒有 [facts] 時依序查 | 本段內文 |
| env.md § Codex | 分節標題 |
| env.md § 跑得久的指令 | reasons.md § 跑得久的指令為什麼一次等完（2026-11-14） |
| env.md § hook 接線有改或同步過 | 本段內文 |
| env.md § 全域 skill 位置 | 沒有寫下理由 |
| env.md § Claude Code | 本段內文 |
| env.md § Windows | 本段內文 |
| env.md § macOS | 分節標題 |
| SKILL.md § 必須停下來問使用者（不得自行決定） | reasons.md § 停下來問人時為什麼要改名<br>mode-a-stop.md § A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF）<br>mode-a-stop.md § A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆）<br>mode-0.md § 0-1 先確認你在對的資料夾、對的情境 |
| SKILL.md § session 命名（每則訊息都適用） | reasons.md § session 命名（每輪必做；工具做不到就在回報裡寫「不適用」）<br>reasons.md § 已交棒後續聊（每則新訊息的入口）<br>reasons.md § 其他命名規則<br>reasons.md § 反例（真的發生過，別重演） |
| mode-a.md § A1＋A2.5 同步與占用：讀開場的 [facts] | mode-a-stop.md § A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF）<br>mode-a-stop.md § A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆）<br>reasons.md § 反例（真的發生過，別重演） |
| mode-a.md § A2 站對分支 | mode-a-stop.md § A2 站對分支 |
| mode-a.md § A3 最小讀取 | mode-a-stop.md § A3 最小讀取 |
| mode-a.md § A4 驗證（只記錄，不修） | mode-a-stop.md § A4 一鍵驗證<br>reasons.md § 反例（真的發生過，別重演） |
| mode-a.md § A5 回報後才動手 | mode-a-stop.md § A5 回報後才動手（3–5 行）<br>reasons.md § 反例（真的發生過，別重演） |
| mode-a-stop.md § A／B／C 狀態轉移（2026-11-02／F11） | 本段內文 |
| mode-a-stop.md § A. 接棒 | 分節標題 |
| mode-a-stop.md § A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
| mode-a-stop.md § A2 站對分支 | 本段內文 |
| mode-a-stop.md § A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
| mode-a-stop.md § A3 最小讀取 | 本段內文 |
| mode-a-stop.md § A4 一鍵驗證 | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
| mode-a-stop.md § A5 回報後才動手（3–5 行） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
| mode-a-stop.md § A6 回推補交接（只有在 A1 判定「前一輪漏交棒」時才走） | 本段內文<br>reasons.md § 漏交棒的補救（2026-11-17 從專案的交接協定搬來，v3 Q41） |
| mode-b.md § 同一 session 的交棒計數 | 本段內文 |
| mode-b.md § B. 交棒 | reasons.md § 交棒由使用者決定（2026-11-12／Q31） |
| mode-b.md § B1 收斂到安全點 | 本段內文 |
| mode-b.md § B2 持久知識落地（今天學到的寫進 repo，不要留在對話裡） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
| mode-b.md § B3 服務驗證 | reasons.md § 反例（真的發生過，別重演） |
| mode-b.md § B4 文檔驗證（動過任何 `.md` 就必跑） | 本段內文 |
| mode-b.md § B5 條件式例行檢查 | 本段內文 |
| mode-b.md § B6 更新 `HANDOFF.md`（覆寫，≤80 行，不累積歷史） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
| mode-b.md § B7 安全提交 | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
| mode-b.md § B8 發布 | 本段內文 |
| mode-b.md § B9 收尾與回報（≤5 行） | 本段內文<br>reasons.md § session 命名（每輪必做；工具做不到就在回報裡寫「不適用」） |
| mode-b.md § C. 中途同步（還沒要交棒） | reasons.md § 交棒由使用者決定（2026-11-12／Q31）<br>reasons.md § 反例（真的發生過，別重演） |
| mode-0.md § 0. 建制（這個資料夾還沒有這套制度） | reasons.md § 模式 0 為什麼留在每一份副本裡 |
| mode-0.md § 0-1 先確認你在對的資料夾、對的情境 | 本段內文<br>reasons.md § 適用判斷：為什麼沒人提就不建<br>reasons.md § 反例（真的發生過，別重演） |
| mode-0.md § 0-2 取得部署包（沒有它就停） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
| mode-0.md § 0-3 訪談：一次問完（部署包第 1 節） | 本段內文 |
| mode-0.md § 0-4 逐檔建立（部署包第 3 節） | 本段內文 |
| mode-0.md § 0-5 本機驗收後才首次發布（部署包第 4 節） | 本段內文 |
| mode-0.md § 0-6 自檢（部署包第 5 節） | 本段內文 |
| mode-0.md § 0-7 寫第一份 `HANDOFF.md` 與 `ARCHITECT.md` | 本段內文 |
| mode-0.md § 0-8 刪掉部署包，回報 | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |
````

**`.claude/skills/handoff/env.md`**——工具與平台差異（2026-11-16.4 起，決策書 v3 Q35）。在 Codex 或 Windows 上碰到對應狀況才讀；只寫環境怪癖與操作提醒，不改變共用狀態的判讀，要加會讓交接結果不同的規則就不放這裡。

````markdown
<!-- source: PROJECT-BOOTSTRAP.md v2026-11-17.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->

# 工具與平台差異（碰到才讀）

本檔只寫環境怪癖與操作提醒，**不改變共用狀態的判讀**。「工作中」標記、`HANDOFF.md`、交棒完成的定義、push 前 hook 的行為，在 Codex／Claude Code × macOS／Windows 四種組合都一樣，照 `AGENTS.md` 的共用制度與模式檔；本檔和它們衝突時以它們為準。

先讀你所在工具的一節，再讀平台的一節。沒寫的就是目前沒有已知差異。

**新增條目的條件**：觀察到重複發生的失敗，寫明工具版本、平台與日期（需求決策書 v3 D10）。只限某工具或平台、會讓交接結果不同的規則（例如只在 Windows 擋下某種推送）不放這裡；它屬於共用制度，要四種組合一起加，並先經 D14 對照與使用者決定（v3 Q35）。

## 開場沒有 [facts] 時依序查

出現症狀才查，不必每次接棒都查版本。查到原因後照實回報，不把缺了開場事實的狀態當成正常。

1. 手動重跑開場 hook（`AGENTS.md` 寫了路徑）。有輸出，表示 hook 本身正常，問題在工具沒有載入接線，往下查；沒有輸出或報錯，看 stderr。
2. Codex：專案要先被信任。未信任的專案不載入專案的 `.codex/hooks.json`，開場就沒有 `[facts]`（`0.169.0-alpha.11.1` 會在 stderr 印 `Untrusted project-local configuration is disabled`；macOS，2026-11-16 連續兩格重現）。專案信任與 hook 審核是兩件事，兩者都要過，驗收方法見下方「hook 接線有改或同步過」。
3. Windows：開場 hook 依序用 `python3`、`python` 產生輸出，WindowsApps 的 `python3` 別名可能找得到卻執行失敗（Codex CLI `0.166.0`，2026-11-16）。兩者都失敗時 hook 會在 stderr 報錯，回報使用者需要可執行的 Python。
4. 回報時寫明工具與版本（例如 `codex --version`）。同一台機器可能有多個版本：2026-11-16 的 Mac 上，Codex App 外掛內附 `0.167.0-alpha.3.2`、ChatGPT App 內附 `0.169.0-alpha.11.1`，`PATH` 上一個都沒有。

## Codex

### 跑得久的指令

驗證仍照專案要求執行；省的是工具往返與輸出，不省檢查。以下是 Codex 桌面 App 2026-11-14 的實測用法，參數上限以當前工具 schema 為準：

- `exec_command` 可先等 30000 ms；有 `session_id` 才用 `write_stdin` 等結果，勿每一兩秒輪詢。若透過 `functions.exec`，外層也要設 `// @exec: {"yield_time_ms": 60000}`，否則內層等 60 秒，外層仍在 30 秒交回。可在同一段 JS 先 `await exec_command`，尚未結束再 `await write_stdin` 等 30000 ms；超過一分鐘仍未完才回報進度並繼續等，不丟棄執行中的 promise。
- 已在上下文讀過的規則不再整份讀；正常接棒不展開理由與歷史。必要的獨立讀取合併一批；驗證、stage、commit、fetch 比對、push 等有相依的動作維持順序，任一步失敗就停。
- 成功驗證只回傳摘要與 exit code，完整輸出留本機暫存日誌；FAIL／SKIP 要讀細節。工具提供摘要選項才使用，不猜選項或吞掉結束碼。交棒已取得的結果依 B7 的失效條件決定是否重跑。

### hook 接線有改或同步過

**Codex hook 接線有改或同步過，就重新檢查信任並驗收實際執行。** 在互動 CLI 的 `/hooks` 或桌面 App 的 Hooks 設定審核當前定義，再於新 session 送出一則最小測試訊息；確認 hook 成功、輸出確實進入 context。只看檔案或信任狀態不算驗收：2026-11-01 在 Windows 的真專案上量到 hook 已信任，卻因 PATH 的 `bash` 指向缺少 `/bin/bash` 的 WSL 而 exit 1。模型呼叫仍依專案原有的額度與授權規則，不因這一項自動取得授權。

### 全域 skill 位置

專案沒有 `.claude/skills/handoff/` 時，讀 `~/.codex/skills/handoff/`。

## Claude Code

- 家目錄 `~/.claude/skills/handoff/` 與專案 `.claude/skills/handoff/` 都有時，Skill 工具載入的是家目錄那份（2.1.321，2026-11-12 實測）。專案有這個目錄就改讀專案那份（入口「模式檔與本檔同目錄」那條）。

## Windows

- **開場沒有 `[facts]`**：照上方「開場沒有 [facts] 時依序查」，Windows 特有的是第 3 步的 `python3` 別名。
- **驗證與測試跑得比 macOS 久**：原生 Windows 上一次完整驗證可能要三到四分鐘，超過指令工具常見的預設等待（120 秒）。2026-11-16 在一台 Windows 11 上連跑三次，分別是 224、234、244 秒，約九成花在子程序密集的測試（真的建 Git repo、起子程序比對），同一套在 macOS 上快得多。做法：提高該次指令的 timeout，或丟到背景再取結果。逾時不是驗證失敗，別把它寫成沒過；也不要為了避開上限只跑一部分就宣稱通過。（數字是在 Claude Code 的指令工具下量的；Codex 的等待設定見上方「跑得久的指令」。）
- **工作區沙箱下的 Git 更新**：若已授權的 Git 操作被沙箱拒絕寫入 `.git`，用 Codex 的單次命令審核核准該操作，並保留目前的工作區沙箱。推送後核對遠端分支與本機追蹤參照。Windows 實測 HTTP 推送可以在遠端收到 commit 且命令回傳 0 時，仍因無法鎖定 `.git` 而留下舊追蹤參照（Codex CLI `0.166.0`，2026-11-16）。

## macOS

目前沒有已知差異。
````

**同步規則（重要）**：這個 skill 目錄（七個檔）會同時存在於 ①本部署包 ②每個專案的 `.claude/skills/handoff/` ③（選用）全域 `~/.claude/skills/handoff/`。
⚠️ **在 Claude Code 裡，③ 會蓋掉 ②**（2026-11-12 在 2.1.321 實測，決策書 Q28）：兩處都有同名 skill 時，skill 清單與 Skill 工具用的是家目錄那份，專案那份只靠入口一句「專案有就讀那裡」救回來。所以全域副本一定要跟部署包同版；不同時 3.10 的開場 hook 會印一行 🟡 列出哪些檔不一樣。
**權威版是本部署包**；要改就改這裡，再覆蓋下去，不要在單一專案裡就地改——那正是「同一個事實有多個家」的典型失控起點。

### 3.9 `.claude/settings.json`

````json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-cdup).claude/hooks/git-freshness.sh\"",
            "timeout": 30,
            "statusMessage": "檢查 git 是否與 origin 同步…"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-cdup).claude/hooks/pre-push-handoff.sh\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
````

> Codex 的接線見 3.17——它掛的是**同樣這兩個 `.sh`**，不要複製第二份腳本進 `.codex/`。兩份各自演化就會出現「Claude 端會擋、Codex 端不會擋」的不對稱。

> 🔴 **腳本路徑前面那個 `$(git rev-parse --show-cdup)` 不是裝飾，拿掉就只有「從 repo 根目錄開的 session」才有防護。** hook 的 `command` 以 **session 的 cwd** 執行（Claude Code 的 handler「runs in the current directory」；Codex 官方文件同樣明寫，並直接建議改從 Git root 解析 repo hook），而人會從子目錄開 session——`cd tools && claude`。那時候 `bash .claude/hooks/git-freshness.sh` 是 **exit 127、No such file**，而 **SessionStart 失敗跟「檢查過了沒事」在畫面上一模一樣**：落後的本機、別台機器的「工作中」標記、骨架落後提醒三件事同時無聲消失。`--show-cdup` 回傳的是**到 repo 根目錄的相對路徑**（根目錄是空字串、子目錄是 `../`），所以修掉這個洞之後接線裡**仍然沒有任何絕對路徑**，鐵律 5 原封不動；不在 git repo 裡時它是空字串，行為退回跟舊版一樣（多一行 git 的 fatal 到 stderr，刻意不消音——這套骨架的失效一向是太安靜而不是太吵）。2026-11-02 在 `tools/` 下重現 exit 127，修完在 root／`tools/`／`docs/ai-notes` 三處都正常；`verify_bootstrap.py` 的「接線 cwd 定位」把這三處、Windows 啟動鏈與兩個負向測試（舊形式、混合斜線）一起釘住（F05）。

### 3.10 `.claude/hooks/git-freshness.sh`

> **2026-11-13 起只報事實（v3 D12）**：fetch 一次，把最多五行 `[facts]` 放入 SessionStart 的 `hookSpecificOutput.additionalContext`，不下指示、不判讀。2026-11-14 實測 Codex 0.169.0 會把裸的 `[facts]` 開頭輸出誤認為壞 JSON，丟掉整段 context；改用兩個工具都支援的 JSON 外殼。檔名沿用 `git-freshness.sh`，3.9 與 3.17 的接線因此不必改。
>
> Windows 需要 Git for Windows 附的 bash（Claude Code 內建可用）。建立後在 macOS／Linux 上加執行權限：`chmod +x .claude/hooks/git-freshness.sh`。

````bash
#!/usr/bin/env bash
# source: PROJECT-BOOTSTRAP.md v2026-11-16.3 — 權威版在部署包，改這裡之前先改部署包再同步各專案。
# SessionStart hook：fetch 一次，只報事實，不下指示（需求決策書 v3 第 5 節，D12）。
# 用 SessionStart JSON 把最多 5 行 [facts] 放進 context；Codex 會把裸的 [facts] 誤認為壞 JSON。只讀：不 pull、不 push、不寫任何檔。
# 怎麼判讀交給模型與 AGENTS.md 的共用制度；舊版的判讀表、全綠行與工具身分猜測在 2026-11-13 移除，
# 理由與 E1 對照實測見 project-bootstrap 的 experiments/handoff-ab/RESULTS.md。

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0
me=${HOSTNAME:-$(hostname 2>/dev/null || uname -n 2>/dev/null)}

facts=''
emit() { facts="${facts}${facts:+
}$1"; }
finish() {
  local py json output
  [ -n "$facts" ] || return
  json='import json, sys
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": sys.stdin.read()}}, ensure_ascii=False))'
  # Windows 的 python3 可能只是一個 PATH 找得到、實際執行會失敗的別名。
  for py in python3 python; do
    if output=$(printf '%s' "$facts" | "$py" -X utf8 -c "$json" 2>/dev/null) && [ -n "$output" ]; then
      printf '%s\n' "$output"
      return
    fi
  done
  printf '%s\n' 'Git facts unavailable: neither python3 nor python could encode SessionStart JSON' >&2
  exit 1
}
trap finish EXIT

# 第 1 行：時間（含 session 名用的 MM.DD.HH，F50）、本機、分支
emit "[facts] 時間 $(date '+%Y-%m-%d %H:%M %z')（session 名用 $(date +%m.%d.%H)）；本機 ${me}；分支 ${branch}"

# 第 2 行：與 origin 的關係
if ! git fetch --quiet origin 2>/dev/null; then
  emit "[facts] fetch origin 失敗：不知道本機是不是最新"
  exit 0
fi
counts=$(git rev-list --left-right --count "origin/${branch}...HEAD" 2>/dev/null)
dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ -z "$counts" ]; then
  emit "[facts] origin 上沒有分支 ${branch}；未提交或未追蹤 ${dirty} 個檔"
  exit 0
fi
behind=$(echo "$counts" | awk '{print $1}')
ahead=$(echo "$counts" | awk '{print $2}')
emit "[facts] 已 fetch：本機落後 origin/${branch} ${behind} 個 commit、領先 ${ahead} 個（origin=$(git rev-parse --short "origin/${branch}" 2>/dev/null)）；未提交或未追蹤 ${dirty} 個檔"

# 第 3 行：origin 那份 HANDOFF 的「工作中」。讀 origin 的、不讀本機的：此刻還沒 pull，本機那份可能是舊的。
# 照原文印出，不解析、不判讀；有幾列就說幾列，讓重複的欄位看得見。
remote_handoff=$(git show "origin/${branch}:HANDOFF.md" 2>/dev/null)
if [ -n "$remote_handoff" ]; then
  busy=$(printf '%s\n' "$remote_handoff" | grep -F '**工作中**')
  busy_n=$(printf '%s\n' "$busy" | grep -c '[^[:space:]]' || true)
  if [ "$busy_n" -gt 1 ]; then
    emit "[facts] origin 上的 HANDOFF 有 ${busy_n} 列「工作中」，第一列：$(printf '%s\n' "$busy" | head -1)"
  else
    emit "[facts] origin 上的 HANDOFF：${busy:-讀不到「工作中」那一行}"
  fi
fi

# 第 4 行（有差異才印）：共用制度的版本與上游不同（F18 提示）。
# 版本取自 AGENTS.md 共用制度開始標記裡的 source: 標記。抓不到（離線、沒有 curl）就安靜跳過。
# 結果快取 12 小時。關掉：BOOTSTRAP_VERSION_CHECK=off
UPSTREAM_VERSION_URL=https://raw.githubusercontent.com/Baliyoho/project-bootstrap/main/VERSION  # fork 的人改這一行
if [ "${BOOTSTRAP_VERSION_CHECK:-}" != off ] && [ -f AGENTS.md ]; then
  mine=$(sed -n 's/.*共用制度開始 source: PROJECT-BOOTSTRAP\.md v\([0-9][0-9.-]*\).*/\1/p' AGENTS.md | head -1)
  cache=.claude/.bootstrap-version
  # 本 repo 的 origin/main 已在上面成功 fetch；只在它確為權威來源時讀取該 ref。
  # 其他專案沒有這個 ref，仍沿用 12 小時快取與上游 HTTP。
  origin_url=$(git remote get-url origin 2>/dev/null)
  authority=0
  case "$origin_url" in
    https://github.com/Baliyoho/project-bootstrap|https://github.com/Baliyoho/project-bootstrap.git|git@github.com:Baliyoho/project-bootstrap|git@github.com:Baliyoho/project-bootstrap.git)
      authority=1
      latest=$(git show origin/main:VERSION 2>/dev/null | tr -d '\r\n \t') ;;
  esac
  if [ "$authority" -eq 1 ]; then
    if [[ "$latest" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\.[0-9]+)?$ ]]; then
      printf '%s' "$latest" > "$cache" 2>/dev/null
    else
      latest=''
    fi
  else
    if [ -n "$(find "$cache" -mmin -720 2>/dev/null)" ]; then
      latest=$(cat "$cache" 2>/dev/null)
    else
      latest=$(curl -fsS --max-time 5 "$UPSTREAM_VERSION_URL" 2>/dev/null | tr -d '\r\n \t')
      if [[ "$latest" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\.[0-9]+)?$ ]]; then
        printf '%s' "$latest" > "$cache" 2>/dev/null
      fi
    fi
  fi
  [[ "$latest" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\.[0-9]+)?$ ]] || latest=''
  # 版本號是 YYYY-MM-DD 或 YYYY-MM-DD.N；序號補成三位數後日期與序號能一起比字典序。
  verkey() {
    _d=${1%%.*}
    _n=${1#"$_d"}
    _n=${_n#.}
    [ -n "$_n" ] || _n=0
    case $_n in *[!0-9]*) _n=0 ;; esac
    printf '%s.%03d' "$_d" "$_n"
  }
  if [ -n "$mine" ] && [ -n "$latest" ]; then
    km=$(verkey "$mine")
    kl=$(verkey "$latest")
    if [ "$km" != "$kl" ]; then
      if [ "$(printf '%s\n%s\n' "$km" "$kl" | sort | head -1)" = "$km" ]; then
        emit "[facts] 共用制度落後：本機 v${mine}，上游 v${latest}（更新方法見 project-bootstrap 的 README）"
      else
        emit "[facts] 共用制度比上游新：本機 v${mine}，上游 v${latest}"
      fi
    fi
  fi
fi

# 第 5 行（有差異才印）：家目錄的 handoff skill 與專案那份不同。實測 Claude Code 2.1.321 會用家目錄那份
# 蓋掉專案的同名 skill（決策書 Q28）。逐檔比內容，只有一邊有的檔也算不同。
home_skill=${HOME:-}/.claude/skills/handoff
if [ -f .claude/skills/handoff/SKILL.md ] && [ -n "${HOME:-}" ] && [ -d "$home_skill" ]; then
  skill_diff=''
  for f in .claude/skills/handoff/*.md "$home_skill"/*.md; do
    [ -f "$f" ] || continue
    name=${f##*/}
    case " $skill_diff " in *" $name "*) continue ;; esac
    cmp -s ".claude/skills/handoff/$name" "$home_skill/$name" || skill_diff="$skill_diff $name"
  done
  [ -n "$skill_diff" ] && emit "[facts] 家目錄 ~/.claude/skills/handoff/ 與本專案的 handoff skill 不同（${skill_diff# }）；Claude Code 載入的是家目錄那份"
fi
exit 0
````

### 3.11 `.claude/hooks/pre-push-handoff.sh`（AI push 提醒）

> **AI push 提醒，不是 Git 原生 pre-push 或發布保證。** 只對殼層指令（payload 的 `command` 欄位）含字面 `git push` 的呼叫，依目前分支與本機 `origin` 追蹤 ref 判斷；不解析 shell、選項、實際 remote 或 refspec。`git -c … push`、GUI、間接執行的 script 可能漏判，指令裡只是提到 `git push`（例如 `echo`）也可能誤擋；編輯檔案等非殼層工具的內容提到它不算（2026-11-12，決策書 Q27）；feature 分支與判斷不了時放行。需要硬閘門時另評估 Git 原生 pre-push 與伺服器保護。
> 2026-11-16：2026-11-16.2 曾在這裡加 session ID 占用核對（釋回或替換標記時比對工具送來的 session ID），同日由 2026-11-16.3 撤回：缺資訊就擋，違反本段「判斷不了時放行」與 D1「標記是訊號不是鎖」，也沒有使用者定案。要重新加入，先依 D14 對照、由使用者決定，而且四種工具／平台組合用同一條規則。
> 2026-11-02／F06：移除「工作樹正在改，等一下會提交」的放行假設。staged／unstaged 修改都不會隨 push 上傳，只有已提交的 HANDOFF 差異才算；開工標記與交棒快照都能通過，**不代表內容已驗證或已交棒**。
> 退出碼 2 會擋下該次 Bash 呼叫並把訊息交給模型——這是唯一能讓 agent「當場改走交棒程序」的機制，警告訊息模型不一定看得到。

````bash
#!/usr/bin/env bash
# PreToolUse hook：AI push 提醒（不是 Git 原生 pre-push／發布保證）
# 起因：push 完才想起沒寫 HANDOFF，下一棒拿到過期狀態。
# 只看殼層指令（tool_input.command）裡的字面 git push、目前分支與 origin 追蹤 ref，不解析選項／remote／refspec。
# GUI／script 可能漏判，指令裡僅提到 git push 也可能誤擋；檢查已提交的 HANDOFF 差異。
# 其他情況（非 push 指令、非殼層工具、feature 分支中途推進度、判斷不了）一律放行——寧可漏擋，不要誤擋。
# 退出碼：0＝放行；2＝擋下並把 stderr 交給模型（模型會看到訊息並改走交棒程序）。
# 臨時停用：HANDOFF_HOOK=off
# source: PROJECT-BOOTSTRAP.md v2026-11-16.3 — 權威版在部署包，改這裡之前先改部署包再同步各專案。

[ "$HANDOFF_HOOK" = "off" ] && exit 0

payload=$(cat 2>/dev/null)
case "$payload" in
  *'git push'*) ;;
  *) exit 0 ;;
esac
# 2026-11-12（決策書 Q27）：只看 "command" 這個欄位，不看整段 payload。Codex 的 PreToolUse
# 沒有 matcher（3.17），每個工具呼叫都會跑到這裡；舊版拿整段 stdin 比對，編輯工具的內容只要
# 提到 git push 就被擋，Claude Code（matcher 只放殼層工具）卻不會，兩個工具結果不同。
# 欄位值可能是 JSON 字串或字串陣列，兩種都收；JSON 字串裡的 \" 跳脫不會讓比對提早結束。
# 只用 grep、不另外依賴直譯器：這支會被抄進各專案，Git Bash 只保證有 grep。
printf '%s' "$payload" \
  | grep -oE '"command"[[:space:]]*:[[:space:]]*("([^"\\]|\\.)*"|\[([^]"]|"([^"\\]|\\.)*")*\])' \
  | grep -qF 'git push' || exit 0

root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0
[ -f HANDOFF.md ] || exit 0                    # 沒有這套交接制度就不管

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0
main=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
main=${main#origin/}
[ -n "$main" ] || main=main
[ "$branch" = "$main" ] || exit 0               # feature 分支中途推進度不擋

git rev-parse --quiet --verify "refs/remotes/origin/$branch" >/dev/null 2>&1 || exit 0
[ -n "$(git rev-list "origin/$branch..HEAD" 2>/dev/null)" ] || exit 0   # 沒有要推的 commit
git diff --name-only "origin/$branch..HEAD" 2>/dev/null | grep -qx 'HANDOFF.md' && exit 0
# 2026-11-12（決策書 Q31）：origin 上的「工作中」不是「無（已交棒）」＝有人開工、還沒交棒，
# 這次 push 是中途安全點，不必更新 HANDOFF。看不出是哪個 session，別台機器的標記也會放行——
# 那種情況本該在 A2.5 停下，這支只是提醒，寧可漏擋。沒有這一欄或讀不到 origin 的檔都照舊擋。
git show "origin/$branch:HANDOFF.md" 2>/dev/null | grep -F '**工作中**' | grep -vqF '無（已交棒）' && exit 0
# F06：未提交的 staged／unstaged 修改不會隨 push 上傳，不可據此放行。

>&2 echo "[handoff-check] AI push 提醒：目前 $branch 相對 origin 的已提交差異沒有更新 HANDOFF.md（未提交修改不算）。"
>&2 echo "[handoff-check] origin 的「工作中」是「無（已交棒）」：中途 push 先照 A5 寫開工標記再推；使用者要求交棒才走 handoff skill 的 B 模式並在 B7 驗最終快照。"
>&2 echo "[handoff-check] 若真的只是中途推進度：改推 feature 分支，或本次設 HANDOFF_HOOK=off。"
exit 2
````

### 3.12 `.gitignore`

````gitignore
# Credentials (each machine keeps its own local copy)
.env
.env.*
!.env.example

# Runtime state, downloaded backups, and operational data
data/
backups/
persist/
archive/

# Local scratch artefacts
tmp/
scratch/
.claude/settings.local.json
.claude/.bootstrap-version
__pycache__/
*.py[cod]
*.log

# Editor and operating-system metadata
.DS_Store
Thumbs.db
.obsidian/

# Interview-specific rules: one Git ignore pattern per line, no Markdown backticks
{{SECRETS}}
{{RUNTIME_DIRS}}
````

> 上面兩個佔位符必須依訪談替換成 Git ignore patterns，**每行一個、不含 Markdown 反引號或頓號，不可用 `!` 反向納入祕密**；文件其他位置仍可用反引號列出檔名。不要只填文件卻漏掉這份範本（2026-11-02／F16：原先追加規則的指令在圍欄外，測試抽不到）。再加語言／框架專屬項目（`node_modules/`、`.venv/`、`dist/`、`.build/` …）。**寧可多擋不要少擋。**

### 3.13 `.gitattributes`

````gitattributes
# Keep source and documentation consistent across Windows and macOS.
* text=auto eol=lf
*.bat text eol=crlf
````

### 3.14 `tools/check_docs.py`

````python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件與交接快照的機械檢查（交接用）。verify_state.py 查「服務現況」，本腳本查「文件本身」。

**名字講的就是範圍**（2026-11-02 改／查核報告 F08）：它查**機械可判定**的腐化模式，
不查「文件寫得對不對」。它不是完整的 Markdown 驗證器（連結檢查是 regex，而且刻意
跳過圍欄與行內程式碼），也**不判斷待辦是否真的完成**——那是交接程序 B6 的事，沒有
工具代替得了。舊版叫「文檔一致性檢查」，而「一致性」聽起來像它驗過全部，於是
「通過」被讀成「文件沒問題」。

用法（專案根目錄執行）：
  python -X utf8 tools/check_docs.py              # 全部檢查
  python -X utf8 tools/check_docs.py --quiet      # 只印問題與結論
  python -X utf8 tools/check_docs.py --docs-only   # 只查文件，不查交接快照（第 7 項）

檢查七項（都是實際發生過的腐化模式）：
  1. 死連結     ——markdown 相對連結指向不存在的檔案（整併文件時最常見）
  2. 過期字串   ——換了網址／改了名稱後殘留的舊值（見下方 STALE_PATTERNS，依專案調整）
  3. 缺日期標頭 ——DATED_DIRS 底下每份都要有「最後更新」，否則無法判斷可信度
  4. 硬編數量   ——「共 N 份」這類會自己過期的寫法
  5. 殘留佔位符 ——部署訪談沒換掉的洞（2026-08-05 加入：原本是部署自檢清單上一個要人工 grep
                  的核取方塊，而人工核取方塊遲早會有人跳過；改由工具擋才會自動發生。這一項掃
                  PLACEHOLDER_GLOBS 的所有檔案，不只 .md——佔位符也會留在 tools/verify_state.py
                  這種非文件檔裡；比對的是 PLACEHOLDER_NAMES 這份封閉清單，不是雙大括號語法）
  6. 工作中欄位 ——HANDOFF.md 的「工作中」標記不見了，或標記在工作中卻沒填工具欄（2026-10-30
                  加入，2026-10-31 補工具欄：這個欄位是跨機器誤接棒防呆的唯一依據，掉了不會有
                  任何徵兆——下一棒只會看到一切正常然後接棒，正是這套骨架最怕的靜默失效。而
                  「欄位缺席」與「沒人在做」分不開，所以不接受「沒寫就是沒人」：必須明確寫
                  「無（已交棒）」。工具欄同理——少了它，同機器換工具的誤接棒會靜默退化成
                  「大概是你自己另一個視窗」，而退化後的畫面跟「沒這個機制」一模一樣。
                  沒有 HANDOFF.md 的 repo 整項跳過——那個洞由第 7 項補）
  7. 交接快照   ——`HANDOFF.md` 必須存在、必要欄位與章節齊備、不超過 80 行
                  （2026-11-02 加入／查核報告 F08：第 6 項只在「HANDOFF.md 有出現在
                  輸入清單裡」時才驗，所以**整份被刪掉或改名時它回報乾淨**，而那正好
                  把跨機器誤接棒防呆連根拔掉。80 行與必要章節是 skill B6 的規則，
                  在此之前較強的版本只存在於骨架自己的 repo，沒有部署給使用者。
                  真的只想查文件時用 `--docs-only`）

問題以結束碼 2 回報，乾淨為 0。本工具唯讀，絕不修改任何檔案。

source: PROJECT-BOOTSTRAP.md v2026-11-03 — 權威版在部署包，改這裡之前先改部署包再同步各專案。
「專案設定」區塊以外的內容應與權威版一致；副本落後時用這一行辨識。
"""
import argparse
import pathlib
import re
import subprocess
import sys

# ── 專案設定（部署後依實際情況調整）────────────────────────────
# 過期字串：搬遷／改名後不該再出現的東西。留空 list 就跳過這項檢查。
STALE_PATTERNS = [
    # ('localhost:8080', '已遷到正式網域，文件不該再出現本機位址'),
]
# 這些關鍵字出現在同一行時視為「刻意保留的歷史敘述」，不報錯。
STALE_OK = ('已停用', '已退役', '歷史', '勿再啟動', '~~')
# 這些路徑整份豁免（例如保存歷史決策的文件、已退役的部署設定）。
STALE_OK_PATHS = ()
# 這些路徑下的 .md 必須在前 8 行有「最後更新」。比對的是路徑前綴，所以單一檔案也放得進來。
# ARCHITECT.md 在列，是因為它會被拿來「找檔案」：沒有日期就無法判斷這份結構圖是哪一天的事實，
# 而過期的結構圖比沒有更糟——照著它找不到檔案的人，通常不會回頭修文件。
DATED_DIRS = ('docs/ai-notes/', 'ARCHITECT.md')
# 連結檢查的豁免路徑。部署包內嵌各檔範本，範本裡的相對路徑是照「該範本部署後的位置」寫的
# （例如 docs/ai-notes/ 或 .agents/skills/<slug>/），用部署包自己的位置去解析必然解不到——
# 那是假警報，不是死連結。沒有這條，自檢清單第 1 項在刪掉部署包之前永遠不可能通過，
# 而部署者只會學到「這支腳本的 FAIL 可以無視」，之後真的死連結也跟著被無視。
LINK_OK_PATHS = ('PROJECT-BOOTSTRAP.md',)
# 佔位符檢查掃哪些檔（不只 .md：訪談要填的值也會落在 .gitignore 與 verify_state.py 裡）。
PLACEHOLDER_GLOBS = ('*.md', '*.py', '*.sh', '*.json', '.gitignore', '.gitattributes')
# 豁免路徑。部署包本身整份都是佔位符，還沒刪掉時不該報錯（自檢清單最後一項會叫你刪它）。
# 專案若真的有檔案會用到上面那些名字當樣板變數，把該檔或該目錄加進來。
PLACEHOLDER_OK_PATHS = ('PROJECT-BOOTSTRAP.md',)
# ── 專案設定結束 ──────────────────────────────────────────────
# 以上依專案調整，以下與權威版一致。`tools/sync_project.py` 升級本檔時，會把上面這一段
# 原樣留下、只換掉其餘部分——沒有這個標記它就得用啟發式猜邊界，而猜錯就是把專案自己的
# 過期字串規則與豁免路徑默默洗掉，然後沒有人會發現。

# 第 7 項要求的欄位與章節。**這是制度的一部分，不是專案設定**——所以放在上面那個
# 標記之外，`sync_project.py` 升級本檔時會跟著覆蓋。要改就改部署包。
HANDOFF_FILE = 'HANDOFF.md'
HANDOFF_FIELDS = ('交接時間', '交棒者', '待續分支', '工作中')
HANDOFF_SECTIONS = ('任務目標', 'Git 狀態', '已完成', '未完成／下一步',
                    '地雷與注意事項', '服務查證與期望快照', '懸置事項（AI 勿自行處理）')
HANDOFF_MAX_LINES = 80

COUNT_RE = re.compile(r'(共|計|全)\s*\d+\s*(份|個|支|條)|\d+\s*份(?!量)')
COUNT_CONTEXT = ('份', '個檔', '支腳本', '知識庫')
# 部署訪談會填的佔位符（第 1 節那張表）。這裡刻意用「名字的封閉清單」而不是「任何雙大括號」
# 或「雙大括號＋全大寫」：專案自己的樣板語法長得一模一樣——verify_state.py 範本裡有 docker 的
# --format '{{ .Names }}'，也遇過專案拿同樣的大寫雙大括號寫法產 HTML——用語法比對兩者都會中。
# 骨架只會留下下面這幾個洞，列舉它們就抓得完，而且不可能誤傷別人的樣板。
# 部署包新增佔位符時要同步這份清單（verify_bootstrap.py 會比對，漏了會 FAIL）。
PLACEHOLDER_NAMES = (
    'PROJECT_NAME', 'ONELINER', 'GH_OWNER', 'GH_REPO', 'GH_VISIBILITY', 'LANG',
    'TZ', 'TODAY', 'SECRETS', 'RUNTIME_DIRS', 'STACK_DIRS', 'VERIFY_TARGETS',
)
PLACEHOLDER_RE = re.compile(r'\{\{(?:' + '|'.join(PLACEHOLDER_NAMES) + r')\}\}')


def tracked(*globs):
    # -z 不能拿掉：git ls-files 預設 core.quotepath=true，會把非 ASCII 檔名輸出成加了
    # 雙引號的八進位跳脫（"\350\256\200..."）。那串原封不動包成 Path，開檔必炸——Windows
    # 是 OSError errno 22、macOS／Linux 是 FileNotFoundError，兩邊都是 traceback 而不是
    # FAIL，接手的人很容易判成「環境或 Python 版本問題」而跳過驗證，正好繞開這套骨架
    # 唯一的文檔關卡。2026-08-05 實際部署時踩到（中文檔名的專案會一直踩）。
    # -z 另外連「檔名含換行」也一起擋掉，比 -c core.quotepath=false 更完整。
    out = subprocess.run(['git', 'ls-files', '-z', *globs],
                         capture_output=True, text=True, encoding='utf-8').stdout
    return [pathlib.Path(p) for p in out.split('\0') if p]


def tracked_md():
    return tracked('*.md')


FENCE_RE = re.compile(r'^\s*(```+|~~~+)')
TITLE_RE = re.compile(r'\s+["\'][^"\']*["\']\s*$')


def strip_code(text):
    """把圍欄區塊與行內 code span 換成空白（行號不變）。

    為什麼（2026-11-02／查核報告 F08）：文件裡的程式碼與範例常含 `[x](path)` 這種形狀，
    那不是連結、那個路徑也不該存在。照掃就會**把正確的文件報成死連結**，而「這支腳本的
    FAIL 可以無視」一旦被學會，真的死連結也跟著被無視——那比沒有這項檢查更糟。
    """
    out, fence = [], None
    for line in text.split('\n'):
        m = FENCE_RE.match(line)
        if fence is not None:
            out.append('')
            if m and line.strip().startswith(fence):
                fence = None
            continue
        if m:
            fence = m.group(1)
            out.append('')
            continue
        out.append(re.sub(r'`[^`]*`', lambda s: ' ' * len(s.group(0)), line))
    return '\n'.join(out)


def link_target(raw):
    """從 `](...)` 裡取出真正的路徑：去掉 <>、去掉 "title"、去掉 anchor。

    `[x](path "title")` 舊版會拿 `path "title"` 去開檔，必然不存在——又一種假警報。
    """
    link = raw.strip()
    # R09：先去 title，再去 destination 的角括號；兩種合法寫法可以同時出現。
    link = TITLE_RE.sub('', link).strip()
    if link.startswith('<') and link.endswith('>'):
        link = link[1:-1].strip()
    return link.split('#')[0].strip()


def check_links(files):
    bad, total = [], 0
    for md in files:
        posix = md.as_posix()
        if any(posix == p or posix.startswith(p) for p in LINK_OK_PATHS):
            continue
        body = strip_code(md.read_text(encoding='utf-8'))
        for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', body):
            link = link_target(m.group(2))
            if not link or link.startswith(('http://', 'https://', 'mailto:')):
                continue
            total += 1
            if not (md.parent / link).resolve().exists():
                bad.append(f'{md.as_posix()} -> {link}')
    return total, bad


def check_stale(files):
    bad = []
    if not STALE_PATTERNS:
        return bad
    for md in files:
        posix = md.as_posix()
        if any(posix.startswith(p) or posix == p for p in STALE_OK_PATHS):
            continue
        for n, line in enumerate(md.read_text(encoding='utf-8').split('\n'), 1):
            for pat, why in STALE_PATTERNS:
                if pat in line and not any(ok in line for ok in STALE_OK):
                    bad.append(f'{posix}:{n}  「{pat}」（{why}）  {line.strip()[:70]}')
    return bad


def check_dates(files):
    bad = []
    for md in files:
        if not any(md.as_posix().startswith(d) for d in DATED_DIRS):
            continue
        head = '\n'.join(md.read_text(encoding='utf-8').split('\n')[:8])
        if '最後更新' not in head:
            bad.append(f'{md.as_posix()}  前 8 行沒有「最後更新：YYYY-MM-DD」')
    return bad


def check_placeholders(files):
    bad = []
    for md in files:
        posix = md.as_posix()
        if any(posix == p or posix.startswith(p) for p in PLACEHOLDER_OK_PATHS):
            continue
        for n, line in enumerate(md.read_text(encoding='utf-8').split('\n'), 1):
            for m in PLACEHOLDER_RE.finditer(line):
                bad.append(f'{posix}:{n}  「{m.group(0)}」  {line.strip()[:70]}')
    return bad


# 交棒後「工作中」欄位唯一合法的值。hook 與這支檢查器都只接受它，
# 不接受任何含「無」的字串（2026-11-02，查核報告 F01）。
FREE_MARK = '無（已交棒）'


def check_busy_field(files):
    # 第 6 項：HANDOFF.md 的「工作中」欄位必須在。這一欄是 handoff skill A2.5 判斷
    # 「同一條分支有沒有別人在做」的唯一依據，而它掉了不會有任何徵兆——下一棒
    # 只會看到一切正常然後接棒。不接受「沒寫就是沒人在做」：那和「忘了寫」分不開。
    found, bad = False, []
    for md in files:
        if md.as_posix() != 'HANDOFF.md':
            continue
        found = True
        text = md.read_text(encoding='utf-8')
        if '**工作中**' not in text:
            bad.append('HANDOFF.md  「Git 狀態」缺「- **工作中**：無（已交棒）」欄位'
                       '——跨機器誤接棒防呆靠它（見 handoff skill 的 A2.5／A5／B6）')
            continue
        # 2026-10-31 加：標記在「工作中」的時候必須帶工具欄
        # （`機器` ／ `工具` ／ `session 名`，最後一欄可選）。少了工具名，同一台機器換個
        # 工具就會落進 hook 的「大概是你自己另一個視窗」🟡，而同機器通常就是同一個工作樹，
        # 兩個 agent 即時互相覆寫——比跨機器那個洞更貴。新格式少一欄不會壞掉，只會靜默
        # 退化回舊行為，而退化後的畫面跟「沒這個機制」一模一樣，所以要擋在這裡。
        # 判別子是 session 名裡的全形豎線：`機器` ／ `工具` 的第二欄不會有它，
        # `機器` ／ `session 名`（舊格式）的第二欄一定有。
        # 2026-11-02 改成精確比對（查核報告 F01）。舊版用 `'無' in value` 判「已交棒」，
        # 於是標記寫著別台機器正在做、而 session 主題叫「修無效連結」，整個格式驗證就被
        # 跳過——兩支 hook 用同一個判準，所以同一個**正常的任務名稱**會讓它們印出錯誤的
        # 綠燈。現在只有正規化後完整等於「無（已交棒）」才算空閒，其餘一律驗欄位。
        # 同時擋「欄位重複」：hook 只讀第一列，重複的話判讀結果等於看運氣。
        rows = [(n, l) for n, l in enumerate(text.splitlines(), 1) if '**工作中**' in l]
        if len(rows) > 1:
            bad.append('HANDOFF.md:%s  有 %d 列「工作中」欄位——這一欄只能有一列，'
                       'hook 只會讀到第一列，其餘的靜默失效（B6 是覆寫，不要往下疊）'
                       % ('、'.join(str(n) for n, _ in rows), len(rows)))
        for num, line in rows:
            # 砍掉「，2026-… (+08) 開工」那段尾註，再去頭尾的半形／全形空白與反引號
            value = line.split('：', 1)[-1].split('，')[0].strip(' \t\u3000`').strip()
            if value == FREE_MARK:
                continue
            fields = [f.strip(' \t\u3000`').strip() for f in value.split('／')]
            if not fields[0]:
                bad.append(f'HANDOFF.md:{num}  「工作中」欄位有值、但解析不出機器欄'
                           f'（讀到：{value[:40]}）——交棒後要正好寫「{FREE_MARK}」，'
                           '開工時寫 `機器` ／ `工具` ／ `session 名`（第三欄可選）')
            elif len(fields) < 2 or not fields[1] or '｜' in fields[1]:
                bad.append(f'HANDOFF.md:{num}  「工作中」標記缺工具欄——格式是 '
                           '`機器` ／ `工具` ／ `session 名`（可選）。少了工具名，'
                           '同機器換工具的誤接棒就擋不住（見 handoff skill 的 A5）')
    return found, bad


def check_snapshot(files):
    """第 7 項：交接快照的結構（存在、必要欄位、必要章節、行數上限）。

    為什麼第 6 項不夠（查核報告 F08）：它是「HANDOFF.md 有出現在輸入清單裡才驗」，
    所以**整份被刪掉或改名時，它回報乾淨**——而那一刀正好把跨機器誤接棒防呆連根拔掉，
    一聲不響。欄位唯一性、必要章節與 80 行這幾條是 skill B6 的規則，在 2026-11-02 之前
    只有骨架自己的 repo 在驗，使用者的專案拿不到。

    天花板：它驗結構，**不驗內容**。待辦是不是真的做完、快照寫得對不對，仍然只能靠 B6
    逐項核對；這一項全過不代表狀態正確。
    """
    bad = []
    target = [md for md in files if md.as_posix() == HANDOFF_FILE]
    if not target:
        return ['%s 不存在或沒被 git 追蹤——它是這套制度的核心檔，'
                '少了它 A2.5 的跨機器防呆與 B6 的交接快照都沒有依據'
                '（真的只想查文件請用 --docs-only）' % HANDOFF_FILE]
    text = target[0].read_text(encoding='utf-8')
    lines = text.splitlines()
    if len(lines) > HANDOFF_MAX_LINES:
        bad.append('%s 有 %d 行，超過 %d 行——它是當下快照，不是日誌（歷史查 Git；見 B6）'
                   % (HANDOFF_FILE, len(lines), HANDOFF_MAX_LINES))
    for label in HANDOFF_FIELDS:
        hits = re.findall(r'^- \*\*' + re.escape(label) + r'\*\*：(.+)$', text, re.M)
        if len(hits) != 1 or not hits[0].strip():
            bad.append('%s 的「%s」欄位要有且只有一列、而且非空（讀到 %d 列）'
                       % (HANDOFF_FILE, label, len(hits)))
    for heading in HANDOFF_SECTIONS:
        # 比對**開頭**而不是整行：標題後面加註記（`## 已完成（2026-11-01）`）無害，
        # 真正的病是同一節出現兩次——那就是 B6 禁止的「往下疊成日誌」。2026-11-02 在
        # 六個專案上實跑時量到：整行相等會把加了日期後綴的那一份判成「缺章節」，
        # 訊息指著錯的方向，而同一份檔案真的有兩個「已完成」。
        hits = re.findall(r'^## ' + re.escape(heading), text, re.M)
        if len(hits) == 0:
            bad.append('%s 缺少章節「## %s」（B6 的覆寫模板有這一節）'
                       % (HANDOFF_FILE, heading))
        elif len(hits) > 1:
            bad.append('%s 有 %d 個「## %s」——它是當下快照，不要往下疊成日誌'
                       '（歷史查 Git；見 B6）' % (HANDOFF_FILE, len(hits), heading))
    return bad


def check_counts(files):
    bad = []
    for md in files:
        for n, line in enumerate(md.read_text(encoding='utf-8').split('\n'), 1):
            if line.lstrip().startswith('>') and '最後更新' in line:
                continue
            m = COUNT_RE.search(line)
            if m and any(w in line for w in COUNT_CONTEXT):
                bad.append(f'{md.as_posix()}:{n}  「{m.group(0)}」 {line.strip()[:70]}')
    return bad


def check_staged_consistency():
    """R07：本次文件／檢查器不得部分 stage，才能用工作樹檢查證明提交內容。"""
    def names(*args):
        p = subprocess.run(['git', 'diff', '--name-only', '-z', *args],
                           capture_output=True, text=True, encoding='utf-8')
        if p.returncode:
            raise RuntimeError('無法讀取 Git 提交集合')
        return set(filter(None, p.stdout.split('\0')))
    staged = names('--cached')
    dirty = names()
    return sorted(p for p in staged & dirty if p.endswith('.md') or p == 'tools/check_docs.py')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--staged', action='store_true', help='提交前檢查，拒絕本次文件／檢查器部分 stage')
    ap.add_argument('--docs-only', action='store_true',
                    help='只查文件，不查交接快照（第 7 項）')
    args = ap.parse_args()

    if args.staged:
        partial = check_staged_consistency()
        if partial:
            print('[index] 🔴 本次文件／檢查器有未暫存變更，請先核對並重新 stage：' + '、'.join(partial))
            return 2
    files = tracked_md()
    if not files:
        print('找不到 tracked markdown——請在專案根目錄執行，且檔案已 git add')
        return 2

    problems = 0
    total, dead = check_links(files)
    if not args.quiet:
        print(f'[links]   檢查 {total} 個相對連結')
    if dead:
        problems += len(dead)
        print(f'[links]   🔴 {len(dead)} 個死連結：')
        for b in dead:
            print(f'            {b}')

    stale = check_stale(files)
    if stale:
        problems += len(stale)
        print(f'[stale]   🔴 {len(stale)} 處過期字串：')
        for b in stale:
            print(f'            {b}')

    undated = check_dates(files)
    if undated:
        problems += len(undated)
        print(f'[dates]   🔴 {len(undated)} 份缺「最後更新」標頭：')
        for b in undated:
            print(f'            {b}')
    elif not args.quiet:
        print('[dates]   受管目錄全部有「最後更新」標頭')

    left = check_placeholders(tracked(*PLACEHOLDER_GLOBS))
    if left:
        problems += len(left)
        print(f'[holes]   🔴 {len(left)} 處殘留佔位符（部署訪談沒填完，照文件做會失敗）：')
        for b in left:
            print(f'            {b}')
    elif not args.quiet:
        print('[holes]   沒有殘留的佔位符')

    found_handoff, busy = check_busy_field(files)
    if busy:
        problems += len(busy)
        print(f'[busy]    🔴 {len(busy)} 處「工作中」欄位問題：')
        for b in busy:
            print(f'            {b}')
    elif not args.quiet:
        print('[busy]    HANDOFF.md 的「工作中」欄位在位' if found_handoff
              else '[busy]    沒有 HANDOFF.md，跳過這一項')

    if args.docs_only:
        if not args.quiet:
            print('[snap]    --docs-only：跳過交接快照檢查')
    else:
        snap = check_snapshot(files)
        if snap:
            problems += len(snap)
            print(f'[snap]    🔴 {len(snap)} 處交接快照問題：')
            for b in snap:
                print(f'            {b}')
        elif not args.quiet:
            print('[snap]    交接快照的欄位、章節與行數都合格（內容仍由 B6 核對）')

    counts = check_counts(files)
    if counts:
        print(f'[counts]  🟡 {len(counts)} 處硬編數量（會自己過期，建議改成不寫數字）：')
        for b in counts:
            print(f'            {b}')

    print()
    if problems:
        print(f'FAIL：{problems} 個問題需修正（硬編數量僅提醒，不計入）')
        return 2
    print('OK：機械檢查通過（語意與「待辦是否真的完成」仍由交接程序 B6 核對）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
````

### 3.15 `tools/verify_state.py`（骨架，部署後填 CHECKS）

````python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一鍵現況查證（交接用）。把接手查證從 5+ 個 AI 回合壓到 1 個回合（省 token）。

用法（專案根目錄執行）：
  python -X utf8 tools/verify_state.py
  python -X utf8 tools/verify_state.py --strict   # 連 SKIP 都算不通過（驗收／CI 用）

輸出＝緊湊 key=value 事實快照 ＋ 最後的彙總行；與 HANDOFF.md「服務查證與期望快照」比對
即完成查證。腳本不判斷**期望值**（那放 HANDOFF，會隨進度變，避免兩處維護）——但
**「這一項失敗了」本身就是事實**，所以它一定會反映在結束碼上。

結束碼（2026-11-02 加／查核報告 F04）：
  0 ＝ 沒有 FAIL／ERROR
  2 ＝ 有 FAIL 或 ERROR
  3 ＝ `--strict` 且有非 OPTIONAL 的 SKIP
舊版**每一種情況都回 0**：在生成的檢查裡放一個 exit 7 的命令，畫面印著 `=rc7`，結束碼
仍是 0。於是任何「跑 verify_state，exit 0 就算驗過」的下游流程都會誤過關，而畫面上那行
字沒人會回頭看。`NOT_CONFIGURED` 仍然回 0，那是刻意的（骨架還沒填不是故障），但它跟
「真的失敗」從此分得開。

每項檢查的狀態只有五種：PASS／FAIL／ERROR／SKIP／NOT_CONFIGURED。
  FAIL  ＝ 服務回答了，但答得不對（HTTP 非 2xx、命令非零退出、expect 沒出現）
  ERROR ＝ 根本沒問到（連線失敗、timeout、未預期例外）——不要自己推論成「未配置」
  SKIP  ＝ 這台機器缺配置（憑證、BASE、執行檔）。**缺配置不等於通過**，所以它獨立列出；
          必需項的 SKIP 在 `--strict` 下不通過，真正可選的項目寫進 OPTIONAL。

source: PROJECT-BOOTSTRAP.md v2026-11-03 — 權威版在部署包，改這裡之前先改部署包再同步各專案。
本檔的 CHECKS 區塊本來就該逐專案填寫；其餘內容應與權威版一致。
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

# ── 專案設定（部署後填這裡）──────────────────────────────────
BASE = os.environ.get('PROJECT_BASE_URL', '')   # 例：https://example.com
SECRET_FILE = '.env'                            # 憑證來源檔
SECRET_KEY = 'API_KEY'                          # 檔內的變數名

# (顯示名稱, 相對路徑或完整 URL, 是否需要憑證[, 預期])
# 第 4 個元素可省；省略＝只要 HTTP 2xx 就算 PASS。填 int＝必須正好是這個狀態碼
# （例如 401，用來驗「保護真的生效」）；填 str＝這段字必須出現在回應裡。
# **只把「有回應」當成正常是不夠的**：200 配一個空的錯誤頁照樣會 PASS，所以會
# 影響交接判斷的那幾項請填 expect（查核報告 F04）。
HTTP_CHECKS = [
    # ('health', '/api/health', False, 'ok'),
]
# (顯示名稱, 命令 list)
CMD_CHECKS = [
    # ('containers', ['docker', 'ps', '--format', '{{ .Names }}']),
]
# 這些檢查缺配置時算可接受，連 `--strict` 都不會因為它們而非零。
# 沒列在這裡的項目，缺配置是「這台機器驗不了」，不是「驗過了」。
OPTIONAL = ()
# ── 專案設定結束 ──────────────────────────────────────────────

OK_STATUS = range(200, 300)
_SECRET = None


def read_secret():
    """從 SECRET_FILE 讀憑證；讀不到回 None（呼叫端標 SKIPPED，不得自行找憑證）。"""
    try:
        for line in open(SECRET_FILE, encoding='utf-8'):
            if line.startswith(SECRET_KEY + '='):
                return line.split('=', 1)[1].strip()
    except OSError:
        pass
    return None


def mask(text):
    """把憑證值從要印出來的字串裡遮掉。

    這一層是必要的，因為印出來的東西有兩個來源不在我們控制下：命令的 stdout／stderr，
    以及例外訊息（urllib 的錯誤字串會帶上整個 URL，而有些服務把 token 放在 query）。
    交接快照會被貼進 HANDOFF、貼進對話、貼進 issue——祕密只要漏一次就等於洩漏。
    """
    if not _SECRET or len(_SECRET) < 4:
        return text
    return text.replace(_SECRET, '***')


def say(line):
    print(mask(line))


def http(name, path, key, expect=None):
    url = path if path.startswith('http') else BASE.rstrip('/') + path
    req = urllib.request.Request(url)
    if key:
        req.add_header('Authorization', f'Bearer {key}')
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(4000).decode('utf-8', 'replace')
            try:
                data = json.loads(body)
                brief = str(len(data)) + ' items' if isinstance(data, list) else 'json ok'
            except json.JSONDecodeError:
                brief = f'{len(body)} bytes'
            if isinstance(expect, int) and r.status != expect:
                say(f'{name}=FAIL http={r.status} 預期 {expect}')
                return 'FAIL'
            if isinstance(expect, str) and expect not in body:
                say(f'{name}=FAIL http={r.status} 回應裡沒有「{expect}」 {brief}')
                return 'FAIL'
            if expect is None and r.status not in OK_STATUS:
                say(f'{name}=FAIL http={r.status} {brief}')
                return 'FAIL'
            say(f'{name}=PASS http={r.status} {brief}')
            return 'PASS'
    except urllib.error.HTTPError as e:
        # 4xx／5xx 也是回答。expect 指定了這個碼就算通過（驗「401 保護生效」用）。
        if isinstance(expect, int) and e.code == expect:
            say(f'{name}=PASS http={e.code}（預期）')
            return 'PASS'
        say(f'{name}=FAIL http={e.code}')
        return 'FAIL'
    except Exception as e:                      # 連線層錯誤：印事實，不下「未配置」結論
        say(f'{name}=ERROR {type(e).__name__}: {e}')
        return 'ERROR'


def cmd(name, argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        # R04：先遮罩完整字串，再做換行整理與截斷，否則憑證跨摘要邊界會洩出前綴。
        out = ' | '.join(l.strip() for l in mask(p.stdout).strip().split('\n') if l.strip())
        tail = out[:300] or mask(p.stderr).strip()[:200]
        # 非零退出碼**不得被吞掉**：舊版只印 `=rc7` 然後回 0（查核報告 F04）。
        status = 'PASS' if p.returncode == 0 else 'FAIL'
        say(f'{name}={status} rc{p.returncode} {tail}')
        return status
    except FileNotFoundError:
        say(f'{name}=SKIP（本機沒有 {argv[0]}）')
        return 'SKIP'
    except Exception as e:
        say(f'{name}=ERROR {type(e).__name__}: {e}')
        return 'ERROR'


def main(argv=None):
    global _SECRET
    ap = argparse.ArgumentParser()
    ap.add_argument('--strict', action='store_true',
                    help='非 OPTIONAL 的 SKIP 也算不通過（回 3）')
    args = ap.parse_args(argv)

    if not HTTP_CHECKS and not CMD_CHECKS:
        print('verify_state=NOT_CONFIGURED（尚未填 HTTP_CHECKS／CMD_CHECKS，見本檔頂端）')
        return 0

    _SECRET = read_secret()
    results = []
    for entry in HTTP_CHECKS:
        name, path, need_key = entry[0], entry[1], entry[2]
        expect = entry[3] if len(entry) > 3 else None
        if need_key and not _SECRET:
            say(f'{name}=SKIP（{SECRET_FILE} 沒有 {SECRET_KEY}'
                '——先確認是不是設定沒帶到，再下結論）')
            results.append((name, 'SKIP'))
            continue
        if not BASE and not path.startswith('http'):
            say(f'{name}=SKIP（未設 PROJECT_BASE_URL）')
            results.append((name, 'SKIP'))
            continue
        results.append((name, http(name, path, _SECRET if need_key else None, expect)))

    for entry in CMD_CHECKS:
        results.append((entry[0], cmd(entry[0], entry[1])))

    tally = {}
    for _, status in results:
        tally[status] = tally.get(status, 0) + 1
    print('verify_state=' + ' '.join(
        '%s:%d' % (s, tally[s]) for s in ('PASS', 'FAIL', 'ERROR', 'SKIP') if tally.get(s)))

    bad = [n for n, s in results if s in ('FAIL', 'ERROR')]
    skipped = [n for n, s in results if s == 'SKIP' and n not in OPTIONAL]
    if bad:
        print('FAIL：%d 項沒通過（%s）——exit 0 的下游流程不能把這當驗收'
              % (len(bad), '、'.join(bad)))
        return 2
    if skipped:
        print('SKIP：%d 項這台機器驗不了（%s）。缺配置不等於通過；--strict 會因此非零'
              % (len(skipped), '、'.join(skipped)))
        if args.strict:
            return 3
    print('OK：所有可驗的項目都通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
````

### 3.16 `.agents/skills/handoff/SKILL.md`（給 Codex 的指標）

> **2026-10-30 起這個檔不再只給 Antigravity。** `codex debug prompt-input` 印的「Skill roots」表證實 Codex CLI `0.164.0` 也把 repo 的 `.agents/skills/` 當成 skill 來源（官方另外列 `$CWD/../.agents/skills`、`$HOME/.agents/skills`、`/etc/codex/skills`）。Antigravity 一樣原生辨識專案根目錄的 `.agents/skills/`。所以這一個檔現在同時是兩個工具的專案層入口。
> 仍然**只放指標、不放內容**——複製一份程序在這裡，兩份就會各自演化，最後一份說要先 fetch、另一份沒說。
> ⚠️ **但既然它會被自動發現，`description` 就必須保持完整的觸發詞**：agent 是看 `description` 決定要不要去開那個檔的，把它寫短就等於把這個入口關掉，而關掉的時候毫無跡象。2026-10-30 把舊版那句只有十幾個字的描述換成跟權威版同一套觸發詞，就是為此。
> 只用得到 Claude Code 的專案可以不建這個檔；建了也不影響其他工具。

````markdown
---
name: handoff
description: 指標檔，權威版在 .claude/skills/handoff/SKILL.md——交接制度的參考檔（碰到才讀，不是必讀）：接棒時 git 狀態不正常（落後、領先、分岔、fetch 失敗、來源不明的未提交變更、別人的「工作中」標記）怎麼判讀與處理；交棒時 HANDOFF.md 怎麼覆寫、怎麼安全提交與 push；中途同步；在還沒有這套制度的資料夾裡把骨架建起來（模式 0 建制）；每條規則的理由與事故。規則本身在專案 AGENTS.md 的共用制度一節，衝突時以那裡為準。Triggers on 接手、接棒、交棒、收工、換機器、同步進度、建制、導入這套制度、建立交接機制、幫我建 HANDOFF、新專案骨架、handoff、hand off、resume work、bootstrap project、set up handoff。
---

<!-- source: PROJECT-BOOTSTRAP.md v2026-11-13 — 本檔只是指標，改內容請改權威版 -->

# 本檔只是指標，請讀權威版

**權威版：[`.claude/skills/handoff/SKILL.md`](../../../.claude/skills/handoff/SKILL.md)**（參考檔入口；碰到才讀。必守的條件在 `AGENTS.md` 的共用制度一節）

那份是純 Markdown，路徑掛在 `.claude/` 下只是因為 Claude Code 會自動載入該位置，內容不限任何工具。

**請勿在此複製內容。** 兩份副本會各自演進並產生矛盾（曾發生：一份已更新成新流程、另一份停在舊版，而入口文件指向舊的那份，照做就失敗）。新知識一律寫進權威版。
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
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-cdup).claude/hooks/git-freshness.sh\"",
            "commandWindows": "cmd /d /c \"$((git rev-parse --show-cdup) -replace '/','\\').claude\\hooks\\codex-hook.cmd\" git-freshness.sh",
            "timeout": 30,
            "statusMessage": "檢查 git 是否與 origin 同步…"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-cdup).claude/hooks/pre-push-handoff.sh\"",
            "commandWindows": "cmd /d /c \"$((git rev-parse --show-cdup) -replace '/','\\').claude\\hooks\\codex-hook.cmd\" pre-push-handoff.sh; exit $LASTEXITCODE",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
````

**Windows 用 `commandWindows` 經下面的啟動器找 Git Bash**，macOS／Linux 仍用原本的 `command`。它只處理管線，不複製任何 git 或交接判斷；stdin、stderr 與腳本結束碼原樣傳遞，否則 `PreToolUse` 的 exit 2 防呆會被吃掉；stdout 在原內容前加一行純文字標頭以免 JSON 誤判。接線自己先用 `$(git rev-parse --show-cdup)` 算出 repo 根目錄（2026-11-02／F05：舊版這裡寫「相對接線仍從 repo 根目錄啟動」，那是**假設**而不是事實，子目錄開的 session 直接 exit 127），啟動器再用 `%~dp0` 找腳本，兩層都不靠當下 cwd。⚠️ **Windows 這一欄要多做一次斜線正規化**：`--show-cdup` 回的是 `../`（正斜線），而 `cmd /d /c "../.claude\hooks\codex-hook.cmd"` 會死在 `'..' is not recognized`（2026-11-02 從子目錄實測），所以用 PowerShell 的 `-replace '/','\'` 先換成反斜線——`commandWindows` 本來就由 Codex 外層的 PowerShell 執行，用得上它。2026-11-01 在 Windows／CLI `0.166.0` 的真 repo 重現舊接線已信任卻 exit 1：PATH 的 `bash` 是 WSL，缺少 `/bin/bash`；直接改用 Git Bash 同一支 `.sh` 就成功。這是新的真部署案例，**不能倒推成稍早那組 exec／TUI 探針差異的原因**。

**`PreToolUse` 的 Windows 命令末尾必須保留 `; exit $LASTEXITCODE`。** 2026-11-01 補做真阻擋驗收時發現：只在原生 cmd 測到 exit 2 還不夠；Codex 外層的 PowerShell `-Command` 會把最後一個 native 命令的失敗折成 exit 1，於是畫面只報 Hook failed、工具仍被放行。加上明確 exit 才把 2 交回 Codex。驗證器同時測完整 PowerShell → cmd → Git Bash 啟動鏈與拿掉明確 exit 的負向情境，避免再用少一層的測試報成功。

**Windows 工作區沙箱下的 Git 更新**：執行時要知道的作法在 3.8 的 `env.md`「Windows」一節（2026-11-16.4 起；以前只寫在這裡，不會部署到專案）。

保持 **ASCII、全 LF、單行 if、沒有 label 與多行括號區塊**。尋找順序是 PATH 上 `git.exe` 的安裝位置、兩種 Program Files、使用者安裝位置；刻意不執行 PATH 上未驗明來源的 `bash`，以免又選到 WSL。找不到 Git Bash 就在 stderr 明確報錯並 exit 1，不假裝驗收成功。另量到 `0.166.0` 對以 `[` 開頭的純文字 stdout 會報 `invalid session start JSON output`；同一支腳本只加上 `Git status check:` 標頭後，互動驗收由 `HOOK_ABSENT` 變成 `HOOK_PRESENT`。所以標頭留在啟動器，不改兩支共用 `.sh` 的既有標記。

````bat
@echo off
rem source: PROJECT-BOOTSTRAP.md v2026-11-01.4 - authority is the kit; edit it first, then sync.
rem Codex Windows launcher. Plumbing only; rules stay in the existing .sh files.
rem ASCII-only, LF-only, no labels or multiline parenthesised blocks. See section 3.17.
setlocal
if "%~1"=="" >&2 echo [codex-hook] ERROR: missing script argument.
if "%~1"=="" exit /b 1
set "BASH="
for /f "delims=" %%G in ('where git 2^>nul') do if not defined BASH if exist "%%~dpG..\bin\bash.exe" set "BASH=%%~dpG..\bin\bash.exe"
if not defined BASH if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined BASH if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" set "BASH=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
if not defined BASH >&2 echo [codex-hook] ERROR: Git Bash not found; hook did not run. Install Git for Windows and retry.
if not defined BASH exit /b 1
rem Codex 0.166.0 treats stdout starting with [ as JSON. Keep a plain-text first line.
echo Git status check:
"%BASH%" "%~dp0%~1"
exit /b %ERRORLEVEL%
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
- [ ] 刪掉 `PROJECT-BOOTSTRAP.md`，以及用壓縮檔部署時附的 `讀我-先看這個.md`。前者的內容已分散進 AGENTS.md、ARCHITECT.md 與 handoff skill，留著就是第二份會腐化的副本；後者的內容在部署完成的當下就是假的（它寫著「檔案都在，但裡面還有佔位符沒填」），下一棒讀到會以為部署沒做完而重跑一次訪談

---

## 6. 之後怎麼維持（一頁操作卡）

**每次開工／收工**：跟 AI 說「接棒」或「交棒」（Claude Code 也可以打 `/handoff`）；工具沒自動找到 skill 時，指它讀 `.claude/skills/handoff/SKILL.md` 的 A 或 B 模式。**順序永遠是先交棒、後接棒**（舊 session 先把狀態寫進 `HANDOFF.md` 並 push，新 session 才讀得到）。

**改到 skill 或 hook 時**：權威版在本部署包 → 改這裡 → 覆蓋各專案 `.claude/skills/handoff/` 整個目錄（七個檔一起，與選用的全域副本）→ 檔頭 `source:` 標記跳版。

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
