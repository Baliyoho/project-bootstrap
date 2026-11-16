# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-17 06:30（+08）
- **交棒者**：Claude Code／Windows `DESKTOP-M8MRS05`（Windows 平台感知、Q37／Q38 登記、骨架 2026-11-16.7 全面同步）

## 任務目標

bootstrap v3 的跨平台驗收已完成四種組合（Codex／Claude Code × macOS／Windows）全部實測。本棒把 Windows 從「固定 exit 2 的平台基線」改成真正 exit 0：平台不適用的檢查改成平台感知地斷言不適用（不收 `skip`），順手修掉四個真的可攜性 bug。制度方向仍依需求決策書 v3 Q35：一套共用規則，工具與平台差異只寫在碰到才讀的 `.claude/skills/handoff/env.md`。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`，權威分支 `main`。
- **待續分支**：無（`fix/windows-platform-aware` 已以 `--no-ff` 併入 `main`，分支保留不刪）。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-16.7`
- 本棒改了 `.claude/skills/handoff/env.md` 的內容，因此跳版到 `2026-11-16.7`；七個 skill 檔的 `source:` 標記同版本，部署包已重生，所有副本已覆蓋。

## 已完成

- **Windows 首次 exit 0**（`3a66a1b`，併入 `main`）：68 項全過，`verify_v2` 434 項 run、skipped=0。原本 exit 2 的構成經逐項判讀為：32 個平台不適用、3 個真的可攜性 bug、5 個簽章 skip（`/usr/bin/ssh-keygen` 寫死）、6 個與平台無關的內容失敗（macOS 也會紅，等於前一棒交棒後的 `main` 兩邊都是紅的）。
- **平台感知而非 skip**：`package.RECORDS_EXECUTE_BIT`、`selftest._runnable` 的 Windows 分支、測試裡的 `can_symlink(root)`；照本 repo「A4 不收 skip」的慣例，能力不存在就斷言不適用結果。
- **四個真 bug**（兩平台都受益）：`contracts.path_escapes` 取代兩份 POSIX-only 的路徑逃脫判斷（`\server\share`、磁碟機相對路徑原本過得去）；`distribute.pack` 改讀 manifest 決定 tar mode，不再靠本機檔案權限；`approvals.system_ssh_keygen()` 平台釘死絕對路徑、`verifier_env()` 補上 Windows `ssh-keygen -Y verify` 唯一需要的 `ProgramData`；`pointer.SOURCE_RE` 認得 `C:\` 開頭的來源。
- **Q37／Q38 登記在需求決策書 v3 §8**（`404670d`、`3f5002c`）：Q37 平台感知（已決）、Q38 Windows 驗證耗時寫進 `env.md`（已決）。一致性檢查器的 registry 從 v2 改指 v3 §8，`REPO_DOCS` 補上 v3；這是「HANDOFF 懸置只放指向編號的指標」這條規則第一次真的做得到。
- **骨架 2026-11-16.7 全面同步**（`5a65da9`、`0f73944`）：`env.md` 新增 Windows 驗證耗時那條 → 重生部署包 → 本 repo `AGENTS.md` 共用制度區塊重貼 → 兩份全域 `skills/handoff/`（`~/.claude`、`~/.codex`，14 檔 byte-identical）→ 桌面六個專案各自走完整流程（Grist_test `7ce1935`、NAA_TR `95d5f66`、NAS_MAINT `8ab3a35`、摘要skill設計 `668e04a`、第三批56箱後檢查 `42a1db9`、鍵鼠同佈署 `d03cd0a`），每個都刪掉 `.claude/.bootstrap-version`。

## 未完成／下一步

1. `learn coding with ai agent` 仍未同步：不在這台機器的桌面上，掃不到，應是 Mac 那邊的事。
2. 序號卡（`.codex/hooks.json` 有無法確認所有權的命令，且專案已完結）與解決網路速度問題（兩個已知的未提交變更，同步器判 dirty 整個跳過）依使用者 2026-11-17 指示刻意停在舊版，不是漏掉。
3. 使用者若開 Windows「開發人員模式」，`can_symlink` 的分支會走到真的建 symlink 那條，覆蓋率提高；現在不開也 exit 0。
4. 桌面 App 的 F50 五步互動沿用既有暫緩決定。

## 地雷與注意事項

- **全套驗證在原生 Windows 約 3–4 分鐘**（2026-11-17 三次 224／234／244 秒，`verify_v2` 單獨 213 秒占九成），超過指令工具預設 120 秒上限，要提高 timeout 或丟背景；timeout 不等於失敗。這條已寫進 `env.md`。
- **`--staged` 在 index 空的時候 0 秒回 exit 2**，印「沒有 staged 提交候選」。那既不是過也不是失敗，別讀成「變快了」。
- **Windows 上 `python3` 是 WindowsApps 別名**（rc=49），要用 `python`；hook 的回退正常運作。
- **`ssh-keygen -Y verify` 在最小環境下回 255 且無 stderr**：唯一必要的變數是 `ProgramData`，已由 `verifier_env()` 處理；再遇到類似靜默失敗，用貪婪法收斂環境變數。
- 用腳本改 Python 時，`r'[\/]'`、`b'pack v1\n'` 這類反斜線在 heredoc 裡會被吃掉；本棒用 `B = chr(92)` 組字串並 grep 回驗。含 `C:\Users` 或 `\.` 的 docstring 要寫成 raw。
- **跳版時別忘了根目錄的 `VERSION` 檔**：本棒漏過一次，`--staged` 直接五項失敗。
- 跨專案寫入一律先在該專案推開工標記、再用 `--owner` 聲明；`--write` 不吃批次。同步完要刪該專案的 `.claude/.bootstrap-version`，否則它最多 12 小時不知道有新版，且毫無徵兆。
- `sync_project.py` 的 MIGRATE **只比對標題字串、不看內容**，改完內容要連標題一起改。
- AI push hook 只擋「推權威分支、沒改 `HANDOFF.md`、origin 標記是無（已交棒）」一種情形。

## 服務查證與期望快照

- 2026-11-17 Windows `DESKTOP-M8MRS05`：`python -X utf8 tools/verify_bootstrap.py --staged` → **exit 0**，68 項全過，無 skip。`verify_v2` 434 項 run、failures=0、errors=0、skipped=0（另有 3 個需外部套件的測試檔 A4 不跑，要 `uv run pytest`）。
- Windows 的「39 個平台失敗基線」已作廢，接棒者在 Windows 看到任何失敗都是回歸。macOS 本棒沒有重跑，前一棒紀錄是 68 項全過。
- 桌面六個專案 `env.md` 皆為 `v2026-11-16.7`，與 origin 一致、未提交 0 個、標記皆「無（已交棒）」；`sync_project.py --all` 預演只剩上述兩個刻意不動的目標。

## 懸置事項（AI 勿自行處理）

- 無。
