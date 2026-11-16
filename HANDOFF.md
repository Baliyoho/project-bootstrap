# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-16 15:00（+08）
- **交棒者**：Claude Code／Windows `DESKTOP-M8MRS05`（四種組合最後一格的實測、Windows 可攜性修正、六個專案的 v3 對齊）

## 任務目標

bootstrap v3 的跨平台驗收。**四種組合（Codex／Claude Code × macOS／Windows）到此全部實測過**，本棒補上最後一格「Claude Code × Windows」。制度方向仍依需求決策書 v3 Q35：一套共用規則，工具與平台的差異只寫在碰到才讀的 `.claude/skills/handoff/env.md`，不改變共用狀態的判讀。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無。
- **工作中**：`DESKTOP-M8MRS05` ／ `Claude Code` ／ `㊣　11.16.20｜待指派｜工作中｜交棒0次`，2026-11-16 20:17 (+08) 開工
- **骨架版本**：`2026-11-16.6`
- 本棒沒改 skill／hook 內容，刻意不跳版；部署包與所有副本未動。

## 已完成

- **Claude Code × Windows 首次實測 PASS**：開場 `[facts]` 有進 context；`bash` 是 Git for Windows 那支；push 前 hook 在規定情形回 exit 2、三種放行情形回 0（在 scratchpad 的隔離 clone 做，沒拿 `main` 當試驗場）。整個 session 另外在 8 個 repo 做了 18 次 push，沒有一次遇到 `env.md` 記的「HTTP 推送成功但追蹤參照停在舊 SHA」——是沒遇到，不是反證。
- **這台機器的全域 skill 同步到 `2026-11-16.6`**：`~/.claude/skills/handoff/` 與 `~/.codex/skills/handoff/` 從單檔 v2026-11-03 換成七檔，逐檔 byte-identical。
- **桌面上 8 個裝過骨架的專案**：4 個只是沒拉（ff 後本來就是 `2026-11-16.6`），2 個實際同步（摘要skill設計 `38865e8`、第三批56箱後檢查 `4d73450`）；序號卡與解決網路速度問題依使用者指示不動。
- **六個專案的舊交接段落對齊 v3**（HANDOFF 前一棒的第 4 項）：刪掉與共用制度重疊的 Git 同步與 single writer 兩條（舊版漏掉開工標記、把協調訊號寫成互斥鎖），開工段改成指向共用制度，段尾引文改指 skill 與理由檔分工；標題改成名實相符，`sync_project.py` 的 MIGRATE 從 6 筆降到 0。各專案的加嚴句、`.obsidian` 例外、`hooksPath` 設定都保留。
- **修掉兩個 POSIX 假設**（`eda4702`）：`surfaces.py` 寫死 `/bin/sh`、Git 唯讀檔刪不掉（新增 `package.force_rmtree`）。Windows 的測試失敗 66 → 39（errors 35 → 8），逐項比對沒有新的失敗。
- **README 對齊現況**（`f22315c`）：skill 五個檔改七個、三層表改四層並把「必守條件在 `AGENTS.md`」獨立一層、開場 hook 描述改成只印 `[facts]`、`python3`／`python` 順序照實寫、補 Windows 的 exit 2 現況。

## 未完成／下一步

1. **Windows 上 `verify_bootstrap.py` 固定 exit 2 怎麼處理**（見懸置）。在決定之前，Windows 的接棒者要比對的是「有沒有**新的**失敗」，不是「有沒有失敗」；基線是 39 個（3 個 symlink 權限、36 個 POSIX 執行位元及其下游）。
2. 使用者若願意開 Windows 的「開發人員模式」，那 3 個 symlink 失敗會自己消失，基線降到 36。
3. `learn coding with ai agent` 仍未同步：不在這台機器的桌面上，掃不到，應是 Mac 那邊的事。
4. 序號卡（`.codex/hooks.json` 有無法確認所有權的命令，且專案已完結）與解決網路速度問題（兩個已知的未提交變更）依使用者指示刻意停在舊版，不是漏掉。
5. 桌面 App 的 F50 五步互動沿用既有暫緩決定。

## 地雷與注意事項

- **Windows 上 `python3` 是 WindowsApps 別名**（rc=49），要用 `python`；hook 的 `python3 → python` 回退正常運作。
- **全套驗證在原生 Windows 跑約 160–240 秒**，超過指令工具預設的 120 秒上限，要提高 timeout 或丟背景。這點還沒寫進 `env.md`（見懸置）。
- **驗證器的 README 負向測試曾把整句標題寫死當錨點**：改標題就會讓測試自己壞掉而不是擋住錯誤。本棒改成不含層數的半句並放寬成「層自動發生」，守的東西沒變。日後改入口文件的標題仍要留意這類錨點。
- `sync_project.py` 的 MIGRATE **只比對標題字串、不看內容**，所以改完內容不會讓它閉嘴，要連標題一起改。
- AI push hook 只擋「推權威分支、沒改 `HANDOFF.md`、origin 標記是無（已交棒）」一種情形；斷線 session 的舊標記仍靠 B1／A2.5 文字，使用者明確確認歸屬才可接手。
- 跨專案寫入一律先在該專案推開工標記、再用 `--owner` 聲明；`--write` 不吃批次。

## 服務查證與期望快照

- 2026-11-16 Windows `DESKTOP-M8MRS05`：`python -X utf8 tools/verify_bootstrap.py --staged --quiet` → **exit 2**，唯一失敗項是「v2 P0 原型回歸（非需求達標）」，其餘全過。unittest 436 項：failures=31、errors=8、skipped=5。
- 同日 Mac 的基線是 66 項全過 exit 0（前一棒紀錄）；Windows 的 exit 2 是平台基線，不是回歸。
- 六個專案的 `check_docs.py --staged` 全部 exit 0。

## 懸置事項（AI 勿自行處理）

- **Windows 的 exit 2 要用哪種解法**：讓驗證器平台感知（把 POSIX 執行位元那組標成本平台不適用），或記一份 Windows 預期失敗清單只比對新增。這會動到驗證判準，屬需求決策書範圍。
- **要不要把「全套驗證超過指令預設上限」寫進 `env.md` 的 Windows 節**：會動 `src/kit/`、跳 `VERSION`、重生部署包並同步所有副本。
