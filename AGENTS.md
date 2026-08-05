# AGENTS.md — 改這個 repo 之前先讀

> 最後更新：2026-08-05

## 這個 repo 是什麼

**AI 協作專案管理骨架的權威版。** 唯一產出物是 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)——一份自帶所有檔案範本的部署包，複製到新專案資料夾就能生出整套制度。用法見 [README.md](README.md)。

**這裡不是知識庫。** 不要在本 repo 累積專案知識、踩坑紀錄或狀態；那些屬於各自的專案 repo。

## 鐵律

1. **`PROJECT-BOOTSTRAP.md` 是權威版。** 制度要改就改它，再覆蓋到各專案的副本；**不要**在單一專案裡就地改 skill 或 hook——那正是「同一個事實有多個家」的失控起點。
2. **改動 skill／hook 內容時，同步更新檔頭的 `<!-- source: PROJECT-BOOTSTRAP.md v日期 -->` 標記**，否則沒人分得出哪份副本落後。
3. **保留每條規則的「為什麼」**。這份骨架的價值不在條文，在條文背後的事故；砍掉理由，下一棒就會繞過規則。
4. **改完要驗證**：從部署包重新生成一次骨架，確認檔案齊全、`check_docs.py` 通過、pre-push hook 四情境（非 push／權威分支未更新 HANDOFF／已更新／feature 分支）行為正確。
5. **不要塞專案專屬內容**（網址、docId、憑證檔名、業務規則）。部署包只放通用制度與佔位符。

## 已知的副本位置

部署包內（權威）→ 各專案 `.claude/skills/handoff/SKILL.md`、`.claude/hooks/*.sh` → 選用的全域 `~/.claude/skills/handoff/SKILL.md`。
改完部署包後，記得把這幾處一起覆蓋。

## 行末

`.gitattributes` 強制 `eol=lf`。部署包全檔是 LF；用 Python 改寫時記得 `newline=''` 或事後正規化，否則 Windows 會把整份寫成 CRLF。
