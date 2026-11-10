#!/usr/bin/env bash
# 本 repo 專屬：在動作當下把對應規則送進 context（決策書 Q6 (a)，F22 第二階段第 (2) 點試行）。
# 🔴 不是部署包的副本，**不要用 sync_project.py 同步它**；只接 Claude Code 的
# .claude/settings.json，Codex 那份接線刻意不接（Q6 (a)：Codex 要重新審核，這次不動）。
#
# 為什麼：常態必讀量超標（F22），而 push、改部署包、改 hook 這三件事的規則只在做那件事時
# 才用得到。開場全部讀一遍又容易在真正動手時忘掉；改成動手那一刻才送那幾條。
#
# 邊界：只送提醒，**永遠 exit 0、不輸出 permissionDecision**，不擋任何操作；判斷只看原始
# JSON 字串，會有誤報（例如 echo 裡提到 git push），但誤報只多一段提醒。沒有 git 呼叫、不寫檔。
# 規則原文在 AGENTS.md 與 handoff skill；這裡是摘要，衝突時以原文為準。
#
# 用法：bash repo-action-rules.sh pre|post   （stdin 是 Claude Code 的 hook JSON）

phase=$1
input=$(cat)

# git push 必須在指令開頭，或接在 &&、;、||、換行（JSON 裡是 \n）後面；只是在 heredoc 或
# echo 的文字裡提到不算。2026-11-10 試行第一天，寬鬆版被 heredoc 裡的說明文字觸發兩次才改。
push_re='("command" *: *"|&& *|; *|\\n *|[|][|] *)git( +[^ ";&|]+)* +push([^A-Za-z0-9_-]|$)'

msg=''
event=''
if [ "$phase" = post ]; then
  event='PostToolUse'
  if printf '%s' "$input" | grep -Eq "$push_re"; then
    msg='[repo-rules] push 指令剛執行完：先看 git status -sb 是否與 upstream 對齊，再讀 origin 那份 HANDOFF 的「工作中」欄位——中途安全點應仍是本 session，交棒應是「無（已交棒）」。只有交棒的 push 成功才把 session 改成 ↗ 並把交棒次數加 1；push 失敗不算交棒，也不寫已交棒。'
  fi
else
  event='PreToolUse'
  if printf '%s' "$input" | grep -Eq '"tool_name" *: *"(Edit|Write|MultiEdit)"'; then
    if printf '%s' "$input" | grep -Eq '"file_path" *: *"[^"]*\.claude/hooks/'; then
      msg='[repo-rules] 正在改 hook：雙引號裡不要寫反引號（會被當成命令替換）；$變數後面緊接中文或全形標點一律寫成 ${變數}（macOS bash 3.2 會吃掉位元組）；用腳本改檔不要把 patch 從 heredoc 餵進 python -，命中數不是 1 就中止；行末保持 LF。本 repo 自己的 hook 不在副本拓撲裡，不要同步。'
    elif printf '%s' "$input" | grep -Eq '"file_path" *: *"[^"]*PROJECT-BOOTSTRAP\.md"'; then
      msg='[repo-rules] 正在改部署包：制度只改 PROJECT-BOOTSTRAP.md，不在單一專案就地改；改到 skill／hook 內容要同步更新 source: 標記（同一天第二次起加 .2、.3）；只有 handoff skill 目錄六個檔改了內容才跳 VERSION，六個標記同版本；保留每條規則的理由；不放專案專屬內容、客戶名稱或本機絕對路徑；改完跑 python3 -X utf8 tools/verify_bootstrap.py，exit 0 才算改完，之後再用 sync_project.py 逐專案同步。'
    fi
  elif printf '%s' "$input" | grep -Eq "$push_re"; then
    msg='[repo-rules] 準備 push：先明確 stage（不要 git add -A），再跑 python3 -X utf8 tools/verify_bootstrap.py --staged，exit 0 才提交，指令用 && 綁住結束碼；push 前先 fetch，遠端意外前進就停下回報，禁止 force push。開工標記與中途安全點都不算交棒、不加次數；要交棒就先走 B6，把「工作中」改回「無（已交棒）」並覆寫整份 HANDOFF。'
  fi
fi

if [ -n "$msg" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}\n' "$event" "$msg"
fi
exit 0
