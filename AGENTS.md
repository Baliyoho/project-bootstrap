# AGENTS.md — 改這個 repo 之前先讀

> 最後更新：2026-09-07

## 這個 repo 是什麼

**AI 協作專案管理骨架的權威版。** 唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)——一份自帶所有檔案範本的部署包，複製到新專案資料夾就能生出整套制度。用法見 [README.md](README.md)。

**結構問題（有哪些檔、部署包各節產出什麼、副本存在於哪些地方）看 [ARCHITECT.md](ARCHITECT.md)**——動到結構就跟它同一個 commit 改；本檔只放規則。

**這裡不是知識庫。** 不要在本 repo 累積專案知識、踩坑紀錄或狀態；那些屬於各自的專案 repo。

唯一的例外是 `tools/verify_bootstrap.py`——它是**部署包的測試**，不是骨架的一部分，也不會被部署出去。本 repo 依然刻意沒有 `HANDOFF.md` 與 hooks——它是制度的**來源**，不是一個交接中的工作專案（理由見 [ARCHITECT.md](ARCHITECT.md)「這個 repo 刻意沒有的東西」）。

## 鐵律

1. **`PROJECT-BOOTSTRAP.md` 是權威版。** 制度要改就改它，再覆蓋到各專案的副本；**不要**在單一專案裡就地改 skill 或 hook——那正是「同一個事實有多個家」的失控起點。
2. **改動 skill／hook 內容時，同步更新檔頭的 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->` 標記**，否則沒人分得出哪份副本落後。
3. **保留每條規則的「為什麼」**。這份骨架的價值不在條文，在條文背後的事故；砍掉理由，下一棒就會繞過規則。
4. **改完要驗證**：跑 `python -X utf8 tools/verify_bootstrap.py`，**exit 0 才算改完**。它會重生骨架比對檔案清單、模擬部署填佔位符、跑 `check_docs.py`、負向測試佔位符檢查與 `ARCHITECT.md` 日期標頭檢查真的擋得住、掃絕對路徑與缺 `python3` 退路的跨平台地雷、測 pre-push hook 五情境、查全檔 LF 與兩份 JSON 設定。2026-08-05 之前這段是要人照著手刻的敘述，每一棒都得重刻一次，於是實務上常被跳過——所以固化成一個指令。跳過的項目（例如機器上沒有 bash）腳本會印 `skip` 並回傳 1，回報時要照實寫。
5. **不要塞專案專屬內容**（網址、docId、憑證檔名、業務規則）。部署包只放通用制度與佔位符。
6. **這是公開 repo**（2026-09-07 起公開，MIT 授權）。任何人都看得到**全部 Git 歷史**，所以文件裡不要寫客戶／單位名稱、內部專案代號、本機絕對路徑——`README.md` 的「來源」那節就是為此改成不點名的中性描述。要補來源或舉例時照樣寫成中性描述；已經進歷史的東西刪不掉，所以是提交前擋，不是事後補救。

## 副本規則

**完整的副本拓撲（哪一份是權威、覆蓋到哪些地方）在 [ARCHITECT.md](ARCHITECT.md)**，這裡只放規則：

- **改完部署包，把所有副本一起覆蓋**，包括選用的全域 `~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/`。漏掉一份，那台機器就繼續照舊制度做事。
- **Codex 的 hook 與 Claude Code 同格式同語意**，所以兩邊掛的是同樣那兩個 `.sh`——不要複製第二份腳本進 `.codex/`。兩份各自演化就會出現「Claude 端會擋、Codex 端不會擋」的不對稱。
- **接線路徑一律相對**：寫死絕對路徑換機器就靜默失效（真的發生過），`verify_bootstrap.py` 的「跨平台防呆」會擋。
- **Antigravity 的 `.agents/` 只放指標**，不複製程序內容。

## 行末

`.gitattributes` 強制 `eol=lf`。部署包全檔是 LF；用 Python 改寫時記得 `newline=''` 或事後正規化，否則 Windows 會把整份寫成 CRLF。
