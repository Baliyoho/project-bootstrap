# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-02 15:10（+08）
- **交棒者**：Claude Code ／ `DESKTOP-M8MRS05`（修 F01／F09／F02／F03 並發下副本）

## 任務目標

維護 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md) 的協作制度。依
[project-bootstrap-audit.md](project-bootstrap-audit.md) 分批修正；已修 **F01、F09、F02、F03**
（四條 P1），其餘 12 條未實作。本輪並把 F01／F09 發到六個專案。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；權威分支：`main`。
- **待續分支**：無。
- **工作中**：無（已交棒）
- **骨架版本**：`2026-11-02`
- 本機能力：Windows、Python 3.13.15、Git Bash；本輪 fetch、開工標記與收尾 push 均成功。

## 已完成

- **F01**（占用判讀改精確解析）、**F09**（版本偵測改判方向）、**F02**（同步的所有權降到
  handler 層，同組自訂 hook 不再被刪）、**F03**（先驗再寫、失敗非零退出）。
  驗證器從 37 項加到 **38 項**；四條都逐項對舊實作跑過，負向證據全部是反的。
- **副本已發下**：六個專案的 `git-freshness.sh` 與 `check_docs.py` 都到 `v2026-11-02.2`；
  `解決網路速度問題` 另補兩份落後的 `SKILL.md`（它原本停在 `2026-10-31`）。共 16 項、
  全部 exit 0、零 FAIL、F02 的新拒絕一次都沒觸發。`序號卡` 已完結，**刻意排除**。
- 驗收不只看檔案在不在（B5）：六個專案的 `check_docs.py` 實跑 exit 0 且專案設定區塊都還在；
  三個專案實跑 `git-freshness.sh` 讀到真的「無（已交棒）」且不再誤報骨架落後；
  在 `Grist_test` 用本機可還原的壞標記證實**部署出去的那一份**三種壞格式都 exit 2。
- `解決網路速度問題` 的 `.claude/.bootstrap-version` 已刪（它是唯一會印落後的專案）。

## 未完成／下一步

1. **六個專案現在都有未提交的變更，每個都要在自己的 session 照 B 模式收尾。**
   `sync_project.py` 刻意不 commit（專案工作樹可能有別人的東西）。⚠️ 四個在權威分支
   （`Grist_test`、`NAS_MAINT`、`第三批56箱後檢查`、`解決網路速度問題`）**不更新 HANDOFF.md
   就會被 pre-push 防呆擋下（exit 2）**；`NAA_TR`（`feature/W15-research-shell`）與
   `摘要skill設計`（`feature/claude-native`）在功能分支上不會被擋。
   ⚠️ `解決網路速度問題` 另有兩個與本次無關的未提交檔（`docs/ai-notes/` 下兩份），
   使用者說過不用管——所以那個專案要**明確 stage**，不可 `git add -A`。
2. **全域副本（`~/.claude/skills/handoff/`、`~/.codex/skills/handoff/`）尚未重新覆蓋。**
   它們只放 `SKILL.md`，而本輪沒動 `SKILL.md`，所以嚴格說沒有落後；但下次動到 skill 時要記得。
3. 其餘 12 條未實作。複核過的優先序：**F05 的 PreToolUse fail-open → F15／F14 → F08**。
   F04 與 F07 嚴重度低於報告所列；F12 只採納文件修正，不做 claim 機制。

## 地雷與注意事項

- **不要因為報告的建議去跳 `VERSION`**：它是「`SKILL.md` 的版本」，跳了各專案會永遠印
  「骨架落後」而且同步修不掉（鐵律 1）。本輪四條修正都沒有動 `SKILL.md`。
- 本輪**沒有**重跑報告的原始反例（`audit_probe.py` 等不在 repo 裡）；F01／F02／F03／F06／F09
  是本 session 自己重現的，F04 等只做程式與文件核實。
- F01 的「錯誤綠燈」在六個專案上**沒有**對著真 origin 重測過（那要往別人的 remote 推測試標記，
  刻意不做）；in situ 驗到的是新碼會跑、讀得對，壞格式那部分由 fixture 與本機測試涵蓋。

## 服務查證與期望快照

`python -X utf8 tools/verify_bootstrap.py`：exit 0、**38 項全過**、重生骨架 22 檔，無 skip。
B4：本 repo 沒有 `check_docs.py`，由上述完整驗證涵蓋。
B5：副本已同步並逐項驗收（見「已完成」）；未改任何接線，故無接線重審需求。

## 懸置事項（AI 勿自行處理）

- 六個專案的 commit／push 要不要在這裡代做，等使用者決定（牽涉六個 repo 各自的 HANDOFF）。
- 新增模型探針仍須先取得授權且只用訂閱額度；本輪未呼叫任何模型探針。
- Antigravity IDE hook 未觸發原因維持未知、不再追查；早期 exec／TUI 差異仍歷史無法歸因。
