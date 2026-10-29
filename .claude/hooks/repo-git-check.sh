#!/usr/bin/env bash
# 本 repo 專屬的 SessionStart 檢查。
# 🔴 這不是部署包 3.10 `git-freshness.sh` 的副本，**不要用 sync_project.py 同步它**。
#
# 為什麼不直接抄 3.10：抄過來會變成最容易腐化的那一份副本。sync_project.py 的 --all 靠
# `*/.claude/skills/handoff/SKILL.md` 發現專案（tools/sync_project.py 的 discover()），
# 而這個 repo 刻意沒有 skill，所以 --all 永遠掃不到它——改了 3.10，9 個專案一行同步完，
# 只有來源自己落後，而且沒有任何跡象。所以這裡只留「開場提醒 git 狀態」這一件事，
# 邏輯簡單到不會腐化，也沒有同步義務。3.10 的另外三段（工作中標記、版本偵測、skill 提醒）
# 在這裡本來就會因為條件不成立而安靜跳過，不抄也不損失什麼。
#
# 2026-10-30 加：在此之前這個 repo 開場完全沒有提醒，接棒程序 A1 的 fetch 全靠使用者記得
# 打「接棒」把全域 skill 載進來；哪天直接說「幫我改部署包第 3.8 節」，skill 不會載入，
# 就可能對著落後的本機動手——那是反例清單第一條。
#
# 只讀不寫，絕不自動 pull/push。

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0

if ! git fetch --quiet origin 2>/dev/null; then
  echo "[repo-check] ⚠️ 無法 fetch origin（離線或金鑰問題）——無法確認本機是否最新。branch=$branch"
  exit 0
fi

counts=$(git rev-list --left-right --count "@{upstream}...HEAD" 2>/dev/null)
if [ -z "$counts" ]; then
  echo "[repo-check] ⚠️ branch=$branch 沒有 upstream，跳過比對。"
  exit 0
fi
behind=$(echo "$counts" | awk '{print $1}')
ahead=$(echo "$counts" | awk '{print $2}')
dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

if [ "$behind" -gt 0 ] && [ "$ahead" -gt 0 ]; then
  echo "[repo-check] 🔴 已分岔：落後 origin $behind、領先 $ahead（branch=$branch）。開工前必須先整合，禁止 push --force 或 reset --hard。"
elif [ "$behind" -gt 0 ]; then
  echo "[repo-check] 🔴 本機過時：落後 origin $behind 個 commit（branch=$branch）。先 git pull --ff-only 再動任何東西——部署包是權威版，對著舊快照改會分岔。"
elif [ "$ahead" -gt 0 ]; then
  echo "[repo-check] 🟡 有 $ahead 個未推送 commit（branch=$branch）。上一棒可能沒推完，收工前記得 push。"
else
  echo "[repo-check] ✅ 本機沒落後 origin（branch=$branch）——只比對本機與 origin，不代表沒有別台機器在做。"
fi
if [ "$dirty" -gt 0 ]; then
  echo "[repo-check] 🟡 工作區有 $dirty 個未提交變更（先辨認來源再動）。"
fi

echo "[repo-check] 本 repo 刻意沒有 HANDOFF.md、沒有 skill、沒有跨機器「工作中」標記（理由見 ARCHITECT.md「這個 repo 刻意沒有的東西」）：接棒程序讀全域 ~/.claude/skills/handoff/，single writer 靠人顧。改制度就改 PROJECT-BOOTSTRAP.md，改完跑 python -X utf8 tools/verify_bootstrap.py。"
exit 0
