# 證據

> 最後更新：2026-11-23
> v4 草稿，從需求決策書 v3 第 2 節與第 7 節最後一條拆出；「原則草稿引用的依據」與「查不到的」第二段出自協作系統原則草稿，標〔原則草稿 §4〕。回答「這些決定靠什麼資料撐著、可信到什麼程度」。本檔的寫法（來源、時間、適用範圍）就是 F40 要求的格式。

每一條標明性質。廠商觀點與二手資料只當方向，不當證據。

| # | 依據 | 性質 | 支持什麼 |
|---|---|---|---|
| E1 | [handoff-ab 兩輪實測](../experiments/handoff-ab/RESULTS.md)（2026-11-13）：十個情境、36 次，Opus 5.5 拿 22 行的極簡骨架，機器查得到的結果沒有比完整版多漏一項，成本約一半到四分之三；其中三個情境極簡版沒有任何對應規則 | 本 repo 實測 | 程序細節對這個模型不是必要的。**只測了一個模型、單輪對話**，Codex 與多輪沒測 |
| E2 | v2 現況索引：51 條需求 48 條未驗證、3 條不通過、0 條通過；v2 說明自己記載同 UID 可繞過、桌面 App 包不住 | 本 repo 實測 | 自製執行屏障兩週沒有一條達標，而且達不到的原因在工具邊界，不在工作量 |
| E3 | [Claude Code 記憶文件](https://code.claude.com/docs/en/memory)：指示檔是 context 不是強制設定；要擋動作用 PreToolUse hook；每份目標 200 行以內，「更長會降低遵循度」；v2.1.277 起沒有 `CLAUDE.md` 時直接讀 `AGENTS.md`；`/doctor prompt-audit` 會找出為舊模型寫的指示 | 官方文件 | 散文擋不住任何事；入口越短越被遵循；兩個工具可以共用一份入口 |
| E4 | [Codex 的 AGENTS.md 文件](https://learn.chatgpt.com/docs/agent-configuration/agents-md)：從 repo 根往下串接，合計上限預設 32 KiB，每個 session 只建一次 | 官方文件 | 入口有硬上限；session 中途改入口不會生效 |
| E5 | [Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988)（ETH Zurich，ICLR 2026）：指示檔整體傾向降低任務成功率、成本增加兩成以上；人寫的最多帶來約 4% 改善，模型生成的會變差；專案概觀沒有幫助；結論是只寫最少的必要要求 | 同儕審查研究（Python、單一基準） | 入口只寫非預設、非顯而易見的要求；不寫概觀；不讓模型代寫入口 |
| E6 | [OpenAI harness engineering](https://openai.com/index/harness-engineering/)：一份大 `AGENTS.md` 行不通，改成約 100 行的地圖指向深層文件；驗證靠機械檢查不靠模型 | 廠商觀點（全文未取得，經二手摘要） | 與 E3、E5 同向 |
| E7 | [Anthropic 長時程 harness 文章](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents)：每個 session 沒有前一個的記憶，要留下清楚的產物（進度檔、git 歷史）給下一個 | 廠商觀點（經二手摘要） | 交接靠留在 repo 的產物，不靠工具的私有記憶 |
| E8 | Latent Space 2026-09-29 訪談 Thariq Shihipar：為舊模型失敗寫的規則會綁住新模型；複雜且要安全的 harness 用官方的 | 廠商員工觀點（摘要檔有誇大處，已對過原始頁面） | 規則要能退場；執行屏障不自製 |
| E9 | [Claude Code plugin evals 文件](https://code.claude.com/docs/en/plugin-evals)與一則第三方實測：評估要比「有它」與「沒有它」；評分要查自己驗過的事實，否則滿分也可能是錯的 | 官方文件＋二手 | 與 E1 的教訓相同：第一輪評分器出過一次會翻轉結論的錯 |

## 查不到的

Claude Code 與 Codex 之間交接的公開實作研究。現有資料各講各的工具，跨工具這一段只有 E1 與本 repo 的事故紀錄。

原則草稿引用的來源談的都是寫程式；交接與協調規則沒有外部證據，靠本 repo 的 handoff-ab 實驗。〔原則草稿 §4〕

## 原則草稿引用的依據

原則草稿第 4 節「依據」引用的來源，還沒編 E 號；要不要併進上表、怎麼編號，重整時決定。〔原則草稿 §4〕

| 來源 | 原則草稿取用的重點 | 跟上表的關係 |
|---|---|---|
| Anthropic 的 [CLAUDE.md 寫法](https://code.claude.com/docs/en/memory) | 要短、只寫讀程式碼看不出來的事、硬規則交給 hook | 就是 E3 |
| Anthropic 的[最佳實務](https://code.claude.com/docs/en/best-practices) | 同上 | 新來源 |
| [AGENTS.md 標準](https://agents.md/) | 指向既有文件不抄、寫清楚怎麼算做完、過期指示比沒有糟 | 新來源 |
| Agentic AI Foundation 的[寫作建議](https://aaif.io/blog/writing-an-effective-agents-md) | 同上 | 新來源 |
| ETH 的[實驗研究](https://arxiv.org/abs/2602.11988) | 專案介紹沒幫助、多寫會多花成本，人寫的檔適合寫跟一般做法不同的地方 | 就是 E5 |

## 依據會過期

依據是取得當時的觀測。工具版本、訂閱條款、模型換代都會讓它過期；過期不自動改需求，但 D10 要求換模型後重跑反例。
