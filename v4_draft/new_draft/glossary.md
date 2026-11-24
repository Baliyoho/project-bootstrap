# 名詞表

> 最後更新：2026-11-24
> v4 初稿，不是現行約束文件。回答「這套協作系統的名詞各指什麼、英文叫什麼」。其他文件用到這些名詞時照這裡的意思，不另下定義。括號裡是對應的英文名稱（[設計原則](principles_v4.md)原則 11）；同一個概念全套文件用同一個名詞（原則 9）。

- **session**（session）：AI 從開工到停下的一段工作，不論用哪個工具。
- **交接文件**（handoff note）：`HANDOFF.md`。
- **交棒**（handoff）、**接棒**（pickup）：交棒是 session 把成果和現況完整留在 origin 後釋出；接棒是新的 session 從上一棒停下的地方接著做。跟 Anthropic 談長時間 agent 時的 handoff 同義；OpenAI Agents SDK 的 handoff 指同一次執行裡把控制權轉給另一個 agent，意思不同。
- **工作中標記**（advisory lock）：origin 上 `HANDOFF.md` 的「工作中」一行；`無（已交棒）` 表示沒人在做。大家約好遵守，不強制。
- **預設分支**（default branch）：測試要一直是過的那條分支，通常是 `main`。
- **工作分支**（feature branch）：`HANDOFF.md` 指定下一棒要接著做的分支。
- **常態入口**（always-loaded context）：每個 session 開場一定會讀的檔：共用制度、專案的 `AGENTS.md`、`HANDOFF.md`。
- **按需讀取的參考檔**（progressive disclosure）：只有遇到特定情況才讀的檔，例如 handoff skill、維護手冊。
- **範本**（template）：本 repo 發到各專案的制度檔，由 `bootstrap.py` 寫入與更新。
