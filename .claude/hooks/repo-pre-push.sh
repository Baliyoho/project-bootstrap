#!/usr/bin/env bash
# PreToolUse hook：AI push 提醒（不是 Git 原生 pre-push／發布保證）
# 起因：push 完才想起沒寫 HANDOFF，下一棒拿到過期狀態。
# 只看殼層指令（tool_input.command）裡的字面 git push、目前分支與 origin 追蹤 ref，不解析選項／remote／refspec。
# GUI／script 可能漏判，指令裡僅提到 git push 也可能誤擋；檢查已提交的 HANDOFF 差異。
# 比對目前分支與本機 origin 追蹤參照。釋回或替換占用時，既有標記的 session-id 必須相符。
# 非 push、非殼層工具、feature 分支中途推進度照常放行。
# 退出碼：0＝放行；2＝擋下並把 stderr 交給模型（模型會看到訊息並改走交棒程序）。
# HANDOFF_HOOK=off 只停用原本的權威分支開工提醒，仍核對既有占用。
# source: PROJECT-BOOTSTRAP.md v2026-11-16.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案。

payload=$(cat 2>/dev/null)
case "$payload" in
  *'git push'*) ;;
  *) exit 0 ;;
esac
# 2026-11-12（決策書 Q27）：只看 "command" 這個欄位，不看整段 payload。Codex 的 PreToolUse
# 沒有 matcher（3.17），每個工具呼叫都會跑到這裡；舊版拿整段 stdin 比對，編輯工具的內容只要
# 提到 git push 就被擋，Claude Code（matcher 只放殼層工具）卻不會，兩個工具結果不同。
# 欄位值可能是 JSON 字串或字串陣列，兩種都收；JSON 字串裡的 \" 跳脫不會讓比對提早結束。
# 只用 grep、不另外依賴直譯器：這支會被抄進各專案，Git Bash 只保證有 grep。
printf '%s' "$payload" \
  | grep -oE '"command"[[:space:]]*:[[:space:]]*("([^"\\]|\\.)*"|\[([^]"]|"([^"\\]|\\.)*")*\])' \
  | grep -qF 'git push' || exit 0

root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0
git rev-parse --quiet --verify "refs/remotes/origin/$branch" >/dev/null 2>&1 || exit 0
[ -n "$(git rev-list "origin/$branch..HEAD" 2>/dev/null)" ] || exit 0

owner_field='^[[:space:]]*-[[:space:]]+\*\*工作中\*\*(：|:)'
old_owner=$(git show "origin/$branch:HANDOFF.md" 2>/dev/null | grep -E "$owner_field")
new_owner=$(git show HEAD:HANDOFF.md 2>/dev/null | grep -E "$owner_field")
idle="$owner_field"'[[:space:]]*無（已交棒）[[:space:]]*$'
owner_suffix=' \[session-id=([A-Za-z0-9_-]{1,128})\]$'
if [ -n "$old_owner" ] && [ "$old_owner" != "$new_owner" ] &&
    { [[ "$old_owner" == *$'\n'* ]] || ! [[ "$old_owner" =~ $idle ]]; }; then
  owner_id=''
  if [[ "$old_owner" != *$'\n'* && "$old_owner" =~ $owner_suffix ]]; then
    owner_id=${BASH_REMATCH[1]}
  fi
  session_id=''
  if [ -n "$owner_id" ]; then
    json='import json, re, sys
value = json.load(sys.stdin).get("session_id")
if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
    print(value)'
    for py in python3 python; do
      if session_id=$(printf '%s' "$payload" | "$py" -X utf8 -c "$json" 2>/dev/null) && [ -n "$session_id" ]; then
        break
      fi
    done
  fi
  if [ -z "$owner_id" ] || [ "$owner_id" != "$session_id" ]; then
    >&2 echo "[handoff-check] 無法以本次 hook 的 session-id 核對 origin 的開工者。已擋下更改「工作中」欄位的推送。保留原標記並照 B1 回報；舊標記依 A2.5／A6 處理。"
    exit 2
  fi
fi

[ "$HANDOFF_HOOK" = "off" ] && exit 0
[ -f HANDOFF.md ] || exit 0                    # 沒有這套交接制度就不管
main=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
main=${main#origin/}
[ -n "$main" ] || main=main
[ "$branch" = "$main" ] || exit 0               # feature 分支中途推進度不擋

git diff --name-only "origin/$branch..HEAD" 2>/dev/null | grep -qx 'HANDOFF.md' && exit 0
# 2026-11-12（決策書 Q31）：origin 上的「工作中」不是「無（已交棒）」＝有人開工、還沒交棒，
# 這次 push 是中途安全點，不必更新 HANDOFF。看不出是哪個 session，別台機器的標記也會放行——
# 那種情況本該在 A2.5 停下，這支只是提醒，寧可漏擋。沒有這一欄或讀不到 origin 的檔都照舊擋。
git show "origin/$branch:HANDOFF.md" 2>/dev/null | grep -F '**工作中**' | grep -vqF '無（已交棒）' && exit 0
# F06：未提交的 staged／unstaged 修改不會隨 push 上傳，不可據此放行。

>&2 echo "[handoff-check] AI push 提醒：目前 $branch 相對 origin 的已提交差異沒有更新 HANDOFF.md（未提交修改不算）。"
>&2 echo "[handoff-check] origin 的「工作中」是「無（已交棒）」：中途 push 先照 A5 寫開工標記再推；使用者要求交棒才走 handoff skill 的 B 模式並在 B7 驗最終快照。"
>&2 echo "[handoff-check] 若真的只是中途推進度：改推 feature 分支，或本次設 HANDOFF_HOOK=off。"
exit 2
