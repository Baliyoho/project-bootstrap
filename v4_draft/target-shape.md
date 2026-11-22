# 部署目標形狀

> 最後更新：2026-11-22
> v4 草稿，從需求決策書 v3 第 5 節，以及第 4 節「處置與理由」欄裡講做法的部分拆出；出自實施計畫 v3 的內容標〔計畫 §N〕。回答「交付到各專案的東西要長什麼樣、每條需求由哪個部件承擔」。這是需求的推論，不是實作完成的宣告；現行有哪些檔看 [ARCHITECTURE](../ARCHITECTURE.md)。

## 安裝程式

對外的安裝途徑是單一檔 `bootstrap.py`，不讓 AI 讀部署包照抄。

- 只用 Python 標準函式庫、範本全部內嵌；只支援 macOS 與 Windows；最低 Python 3.12（`pyproject.toml` 的 `requires-python`）。
- 訪談由程式問，也可以用答案檔或參數非互動執行；有判斷空間的題目（驗證項、絕對不能做的操作）與留空的題目，列進安裝後 agent 的第一批工作。答案存成專案的 `.bootstrap/answers.json` 供更新使用，不得含祕密。
- 已存在的同名檔一律不覆寫，新內容寫成 `<路徑>.bootstrap-new`；寫完逐檔比對雜湊，換行依 `.gitattributes`。
- 不碰網路、不推送、不建 GitHub repo；不在任何 Git 工作樹裡時 `git init -b main`，不 add、不 commit。
- 寫完的 `HANDOFF.md`「工作中」是 `無（已交棒）`，「未完成／下一步」列第一批工作，agent 照平常接棒接手。
- 安裝與更新是同一支程式；更新依 `owners.json` 只換 core 與 adapter 擁有的部分，合併邏輯與 `sync_project.py` 是同一套。
- `bootstrap.py` 由 `tools/build_kit.py` 從 `src/kit/` 生成，不手改。它是唯一的產出物：部署包的說明就是 `src/kit/kit.md`。
- 不是用 `bootstrap.py` 裝的已部署專案（沒有答案檔），由 `sync_project.py` 升級。

## 部署出去的檔案

| 檔案 | 內容 | 預算 |
|---|---|---|
| `AGENTS.md` | 分兩大段，邊界是共用制度的兩個標記：「共用制度」（協作目標、環境事實、共用規則）由部署包管；「專案專用」（專用規則、碰到才讀）歸專案。共用規則與專用規則各自從 1 編號，別處引用寫「共用規則 N」或「專用規則 N」。連線資料不放這裡 | 見 D11 |
| `README.md` | 標準 README：是什麼、為什麼做、快速開始（含連線資料）、開發與驗證、結構指標、協作方式、授權。不放交接程序 | — |
| `CLAUDE.md` | 一行 `@AGENTS.md`。Claude Code 新版可直接讀 `AGENTS.md`，但官方文件說部分 session 讀不到，保留這一行 | 1 行 |
| `HANDOFF.md` | 當下狀態，欄位照現行範本 | 見 D11 |
| 開場 hook | fetch 一次，印出時間、落後與領先、未提交檔數、origin 的「工作中」。只報事實，不下指示 | 輸出 ≤ 5 行 |
| hook 接線 | Claude Code 與 Codex 各一份，掛同一支腳本。第 1 期只要求 Claude Code 那份驗過；不含 Antigravity 的接線與轉接檔；現有 Windows 的 hook 接線留著不擴充 | — |
| 參考檔（選用） | 逐步程序、異常判讀表、理由。碰到才讀，不在常態入口 | 不限，但不得被入口要求必讀 |
| 檢查腳本（選用） | 死連結、行數預算、「工作中」欄位格式 | — |

表裡沒列的 `ARCHITECTURE.md`、`docs/ai-notes/roadmap.md` 與兩支檢查腳本，歸在「參考檔」「檢查腳本」兩列。〔計畫 §1〕

## 共用制度必須涵蓋

- 接手前看 `HANDOFF.md` 的「待續分支」，主幹可能不在 `main`。
- 不提交祕密或金鑰樣式的內容；提交前看 staged 清單，不整批加入。
- session 命名（F50）：兩種狀態的格式、何時改、交棒計數何時加一。

handoff skill 是選用的參考檔，不是制度成立的前提。

## 各需求由誰承擔

只列 v3 有寫做法的需求。

| ID | 由誰承擔 |
|---|---|
| F1 | `HANDOFF.md` 的「任務目標」欄 |
| F2 | `HANDOFF.md` 的「目前進度／下一步」欄 |
| F3 | 入口一條「沒驗證過的事不寫成已驗證」 |
| F4 | 開場 hook 讀 origin 的「工作中」並印出 |
| F5 | `HANDOFF.md` 的「地雷」欄 |
| F44 | `HANDOFF.md` 的「懸置事項」欄 |
| F6 | 理由檔（碰到才讀） |
| F9 | 開場 hook fetch 並印出落後幾個 commit |
| F10 | 交棒完成的定義寫進入口。push 前 hook 擋一種情形：推權威分支、這次推送沒改 `HANDOFF.md`、origin 的「工作中」又是 `無（已交棒）`（等於沒寫開工標記就推）；其他推送只靠入口的定義。不核對 session ID |
| F11 | origin 上的「工作中」協調訊號 |
| F13 | 開工標記留在 origin 上，下一棒看得到 |
| F42 | 工具的權限模式與沙箱；入口保留一條禁止清單 |
| F50 | 開場 hook 算好時間戳（提示）；每次接棒與交棒的回覆有一行 `session：` 寫實際標題與次數（留痕） |
| F25 | 每條分支自己的 `HANDOFF.md` 標記 |
| F28 | 寫進 `HANDOFF.md` 或 `AGENTS.md`，下一棒開場讀得到 |
| F14 | 兩個工具讀同一份 `AGENTS.md`（E3、E4） |
| F47 | 一張兩欄的能力表 |
| F16a | git 與 F9 |
| F17 | `bootstrap.py`，見上面「安裝程式」 |
| F18 | 開場 hook 提示版本落後；升級用 `bootstrap.py update` |
| F45 | 現有的死連結檢查 |
| F20 | 專案自己的驗證指令寫在 `HANDOFF.md`；接手時跑一次 |
| F21 | 發布前驗證（F35） |
| F22 | 檢查腳本量 D11 的行數 |
| F23 | 只讀的 session 不寫標記 |
| F32 | 檔頭一行版本標記 |
| F40 | [證據](evidence.md)的寫法 |
| F30 | 十個以內的專案，一張清單 |
| F35 | 發布前跑驗證並記錄結果 |
| F43 | `.gitignore`，加上入口一條「不提交祕密、不無腦全加」 |
