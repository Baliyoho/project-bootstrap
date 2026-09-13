# ARCHITECT — 這個 repo 的結構

> **本檔＝結構的唯一權威**：`project-bootstrap` 由什麼組成、每樣東西的家在哪、改哪裡會影響到什麼。
> 最後更新：2026-09-07（建立）
>
> **什麼時候改**：只有**結構**變動才改——根目錄多／少一個檔案、部署包增刪一節範本、`verify_bootstrap.py` 增減檢查項、副本拓撲改變。
> 制度內容本身怎麼寫（鐵律的措辭、skill 的步驟）**不要動這一份**，那些的家在 [AGENTS.md](AGENTS.md) 與部署包裡。

## 一句話

唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)——一份自帶所有檔案範本的部署包，複製到新專案資料夾就能生出整套制度。
其餘每個檔案都是它的**說明、指標或測試**，沒有第二個產出物。

## 根目錄

| 路徑 | 是什麼 | 什麼時候動 |
|---|---|---|
| [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) | **權威版部署包**：訪談表＋各檔範本＋上 GitHub＋自檢清單＋維持操作卡 | 制度要改就改它（鐵律第 1 條） |
| [README.md](README.md) | 人的入口：怎麼用、部署後長什麼樣、跨工具相容性、改這份骨架的開場 prompt | 用法或相容性改變 |
| [AGENTS.md](AGENTS.md) | AI 的入口：這個 repo 是什麼、鐵律、副本位置、行末規則 | 多一條鐵律、副本位置改變 |
| [CLAUDE.md](CLAUDE.md)、[GEMINI.md](GEMINI.md) | 指標，內容只有一句「去讀 AGENTS.md」 | 幾乎不動 |
| 本檔 | 結構 | 只有結構變動 |
| [LICENSE](LICENSE) | MIT（2026-09-07 起公開） | 授權改變 |
| [tools/verify_bootstrap.py](tools/verify_bootstrap.py) | **部署包的測試**，不是骨架的一部分、也不會被部署出去 | 部署包多一種失效模式時 |
| `.gitignore`、`.gitattributes` | `dist/` 不進 Git；全檔強制 `eol=lf` | 幾乎不動 |
| `dist/` | 建置產物（`--zip` 產出的骨架壓縮檔），**不進 Git** | 要發佈就重跑一次，不要留在 repo 裡跟部署包唱反調 |

## 部署包的內部結構

| 節 | 內容 | 誰會讀它 |
|---|---|---|
| 表頭 | 部署 prompt、版本日期、來源 | 拿到這份檔案的人 |
| 交接自動化怎麼運作 | 觸發（hook）／程序（skill）／防呆（hook）三層 | 想理解設計的人 |
| 跨工具與跨平台 | Claude Code／Codex CLI／Codex 桌面 App／Antigravity 的能力矩陣 | 要在別的工具上部署的人 |
| 0 | 這套骨架在解決什麼問題（失效模式 → 對策） | 想知道「為什麼要有這條規則」的人 |
| 1 | 部署前訪談：佔位符表 | 執行部署的 agent |
| 2 | 要建立的檔案結構 | 同上 |
| 3 | **各檔範本**（3.1–3.18），照抄只換佔位符 | 同上，改到哪份讀哪節 |
| 4 | 上 GitHub | 同上 |
| 5 | 部署後自檢清單 | 同上 |
| 6 | 之後怎麼維持（一頁操作卡） | 部署完的專案 |

第 3 節的範本清單就是 `verify_bootstrap.py` 裡 `EXPECTED` 的對照表：

| 節 | 產出 | 角色 |
|---|---|---|
| 3.1 | `AGENTS.md` | AI 入口、鐵律、知識庫地圖 |
| 3.2 | `CLAUDE.md`＋`GEMINI.md` | 指標（**一節產兩檔**，只有標題不同） |
| 3.3 | `HANDOFF.md` | 當下狀態（≤80 行、覆寫不累積） |
| 3.4 | `README.md` | 人的入口、交接 prompt A／B |
| 3.5 | `ARCHITECT.md` | 結構的唯一權威（2026-09-07 加入） |
| 3.6 | `docs/ai-notes/handover-protocol.md` | 交接的規則與理由 |
| 3.7 | `docs/ai-notes/roadmap.md` | 持久待辦與決策記錄 |
| 3.8 | `.claude/skills/handoff/SKILL.md` | **本骨架的核心**：0 建制／A 接棒／B 交棒／C 同步 |
| 3.9 | `.claude/settings.json` | 兩個 hook 的接線 |
| 3.10 | `.claude/hooks/git-freshness.sh` | SessionStart：git 新鮮度 |
| 3.11 | `.claude/hooks/pre-push-handoff.sh` | PreToolUse：push 前防呆 |
| 3.12 | `.gitignore` | 祕密與運行資料 |
| 3.13 | `.gitattributes` | 行末 LF |
| 3.14 | `tools/check_docs.py` | 文檔一致性檢查 |
| 3.15 | `tools/verify_state.py` | 一鍵現況查證（骨架） |
| 3.16 | `.agents/skills/handoff/SKILL.md` | Antigravity 的指標檔 |
| 3.17 | `.codex/hooks.json` | Codex CLI 的 hook 接線（掛 3.10／3.11 同樣那兩個 `.sh`） |
| 3.18 | —— | 其他 skills 的**慣例說明**，不產檔 |

## 部署包 → 骨架的抽取規則（改範本前先讀這段）

`verify_bootstrap.py` 的 `extract()` 就是「照著部署包生檔案」的機器版，規則只有四條：

1. **`### 3.x` 標題行裡的反引號路徑＝產出的檔名。** 改標題就是改檔名——3.2 的標題有兩個路徑，所以一節產兩檔。
2. **標題後的第一個 fence 內容＝檔案內容。** fence 前的散文是給人看的說明，不會進檔案。
3. **標題行沒有路徑就不產檔**（3.18 是慣例說明）。
4. `GEMINI.md` 的標題替換是腳本裡的特判，因為它與 `CLAUDE.md` 共用同一個範本。

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
| 真實部署形狀 | 部署包在場＋非 ASCII 檔名時仍 exit 0 | 照說明部署的人一定會踩到 |
| 跨平台防呆 | 無絕對路徑、有 `python3` 退路 | 換一台機器會靜默失效 |
| pre-push hook 五情境 | 該擋的擋、該放的放 | 防呆變成誤擋或形同虛設 |
| 行末與雜項 | 全 LF、JSON 合法、腳本可執行 | Windows 寫出 CRLF、設定檔打錯字 |

**exit 0 才算改完**（鐵律第 4 條）。印出 `skip` 的項目沒有被驗證，回報時要照實寫。

## 副本拓撲（同一份東西存在於多個地方的，只有這些）

```text
handoff SKILL.md
  部署包 3.8（權威）
    └─→ 各專案 .claude/skills/handoff/SKILL.md
          ├─→ （選用）~/.claude/skills/handoff/   ← 模式 0 建制真正會被載入的地方
          ├─→ （選用）~/.codex/skills/handoff/    ← Codex 桌面 App
          └─→ .agents/skills/handoff/SKILL.md     ← 只放指標，不複製內容

兩個 hook .sh
  部署包 3.10／3.11（權威）
    └─→ 各專案 .claude/hooks/*.sh   ← 只有這一份腳本
          ├─← .claude/settings.json 指向它
          └─← .codex/hooks.json 指向同樣那兩個（不複製第二份）

check_docs.py
  部署包 3.14（權威，「專案設定」區塊除外——那塊本來就該依專案調）
    └─→ 各專案 tools/check_docs.py
```

每份副本檔頭有 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->`，**改內容就要跳版**，否則沒人分得出哪份落後（鐵律第 2 條）。
沒改內容的檔案不要跟著跳版——謊報「副本落後」之後，這個標記就沒人再信。

## 這個 repo 刻意沒有的東西

- **沒有 `HANDOFF.md`、沒有 hooks、沒有 `check_docs.py`。** 它是制度的**來源**，不是一個交接中的工作專案；把骨架套到它自己身上，就會出現「權威版與它的副本互相同步」的迴圈。跨 session 狀態看 `git log` 與各檔的 `source:` 版本標記。
- **沒有 CI。** 驗證是一個指令（`python -X utf8 tools/verify_bootstrap.py`），跑它是鐵律第 4 條的義務。
- `tools/` 底下只有 `verify_bootstrap.py` 這一支——它是部署包的測試，不是骨架的一部分。

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
