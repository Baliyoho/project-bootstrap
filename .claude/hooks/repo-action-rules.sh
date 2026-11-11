#!/usr/bin/env bash
# 本 repo 專屬：在動作當下把對應規則送進 context（決策書 Q6 (a)，F22 第二階段第 (2) 點試行）。
# 🔴 不是部署包的副本，**不要用 sync_project.py 同步它**；只接 Claude Code 的
# .claude/settings.json，Codex 那份接線刻意不接（Q6 (a)：Codex 要重新審核，這次不動）。
#
# 為什麼：常態必讀量超標（F22），而 push、改部署包、改 hook 這三件事的規則只在做那件事時
# 才用得到。開場全部讀一遍又容易在真正動手時忘掉；改成動手那一刻才送那幾條。
#
# 邊界：只送提醒，**永遠 exit 0、不輸出 permissionDecision**，不擋任何操作。沒有 git 呼叫、不寫檔。
# 規則原文在 AGENTS.md 與 handoff skill；這裡是摘要，衝突時以原文為準。
#
# 判斷方式（2026-11-10 第二版）：有 python3／python 就解析 JSON，**只看 tool_input**，
# 並把指令照 shell 規則切詞——引號裡與 heredoc 內文的 git push 不算，git 的子指令要真的是 push。
# 為什麼改：第一版拿整段原始 JSON 去比對，PostToolUse 的輸入含指令的「輸出」，輸出裡換行後
# 出現 git push（例如 git 自己的 hint）就誤報，試行第一天約五次；指令內引號裡的
# 「&& git push」與字面 \n 後的 git push 也誤報。已知漏報：bash -c "git push" 這類包在引號裡
# 再執行的寫法、指令註解後面同一行的內容不特別處理。
# 沒有 python 或解析失敗時退回第一版的原始字串比對（會有上述誤報，但誤報只多一段提醒）。
#
# 用法：bash repo-action-rules.sh pre|post   （stdin 是 Claude Code 的 hook JSON）

phase=$1
input=$(cat)
parser=auto

# 三種提醒都不可能命中的輸入直接結束，不必啟動 python。
case $input in
  *push*|*.claude/hooks/*|*PROJECT-BOOTSTRAP.md*|*src/kit/*) ;;
  *) exit 0 ;;
esac

py_prog='
import json, re, shlex, sys
try:
    d = json.loads(sys.stdin.read())
    ti = d.get("tool_input") or {}
    tool = str(d.get("tool_name") or "")
    if tool in ("Edit", "Write", "MultiEdit"):
        fp = str(ti.get("file_path") or "").replace("\\", "/")
        print("hook" if ".claude/hooks/" in fp else "pack" if fp.endswith("PROJECT-BOOTSTRAP.md") or "/src/kit/" in fp else "none")
        sys.exit(0)
    cmd = str(ti.get("command") or "")
except Exception:
    sys.exit(3)
cmd = re.sub(r"<<-?[ \t]*([\"\x27]?)(\w+)\1([^\n]*)\n(?:.*?\n)?[ \t]*\2[ \t]*(?=\n|$)", r" \3", cmd, flags=re.S)
try:
    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    toks = list(lex)
except ValueError:
    hit = re.search(r"(^|&&|;|\|\||\n)\s*git(\s+[^\s;&|]+)*\s+push([^A-Za-z0-9_-]|$)", cmd)
    print("push" if hit else "none")
    sys.exit(0)
sep = set(";&|()")
skip = {"then", "do", "else", "elif", "if", "while", "until", "!", "{", "time", "command", "exec", "sudo", "env", "nohup"}
valopt = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
start, hit, i = True, False, 0
while i < len(toks):
    t = toks[i]
    i += 1
    if t and set(t) <= sep:
        start = True
        continue
    if not start:
        continue
    if t in skip or re.match(r"[A-Za-z_]\w*=", t):
        continue
    start = False
    if t == "git" or t.endswith("/git"):
        j = i
        while j < len(toks) and not (toks[j] and set(toks[j]) <= sep):
            u = toks[j]
            if u in valopt:
                j += 2
            elif u.startswith("-"):
                j += 1
            else:
                hit = hit or u == "push"
                break
print("push" if hit else "none")
'

kind=''
if [ "$parser" = auto ]; then
  for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
      kind=$(printf '%s' "$input" | "$py" -c "$py_prog" 2>/dev/null) || kind=''
      [ -n "$kind" ] && break
    fi
  done
fi

if [ -z "$kind" ]; then
  # 退路：第一版的原始字串比對。git push 必須在指令開頭，或接在 &&、;、||、換行（JSON 裡是 \n）後面。
  push_re='("command" *: *"|&& *|; *|\\n *|[|][|] *)git( +[^ ";&|]+)* +push([^A-Za-z0-9_-]|$)'
  kind=none
  if printf '%s' "$input" | grep -Eq '"tool_name" *: *"(Edit|Write|MultiEdit)"'; then
    if printf '%s' "$input" | grep -Eq '"file_path" *: *"[^"]*\.claude/hooks/'; then
      kind=hook
    elif printf '%s' "$input" | grep -Eq '"file_path" *: *"[^"]*(PROJECT-BOOTSTRAP\.md"|/src/kit/)'; then
      kind=pack
    fi
  elif printf '%s' "$input" | grep -Eq "$push_re"; then
    kind=push
  fi
fi

msg=''
event=''
if [ "$phase" = post ]; then
  event='PostToolUse'
  if [ "$kind" = push ]; then
    msg='[repo-rules] push 指令剛執行完：先看 git status -sb 是否與 upstream 對齊，再讀 origin 那份 HANDOFF 的「工作中」欄位——中途安全點應仍是本 session，交棒應是「無（已交棒）」。只有交棒的 push 成功才把 session 改成 ↗ 並把交棒次數加 1；push 失敗不算交棒，也不寫已交棒。'
  fi
else
  event='PreToolUse'
  case $kind in
    hook)
      msg='[repo-rules] 正在改 hook：雙引號裡不要寫反引號（會被當成命令替換）；$變數後面緊接中文或全形標點一律寫成 ${變數}（macOS bash 3.2 會吃掉位元組）；用腳本改檔不要把 patch 從 heredoc 餵進 python -，命中數不是 1 就中止；行末保持 LF。本 repo 自己的 hook 不在副本拓撲裡，不要同步。' ;;
    pack)
      msg='[repo-rules] 正在改部署包：PROJECT-BOOTSTRAP.md 由 src/kit 生成，不要手改；改 src/kit/kit.md 或 src/kit/files/ 底下的 .tmpl，再跑 python3 -X utf8 tools/build_kit.py 重生，兩者同一個 commit；不在單一專案就地改；改到 skill／hook 內容要同步更新 source: 標記（同一天第二次起加 .2、.3）；只有 handoff skill 目錄六個檔改了內容才跳 VERSION，六個標記同版本；保留每條規則的理由；不放專案專屬內容、客戶名稱或本機絕對路徑；改完跑 python3 -X utf8 tools/verify_bootstrap.py，exit 0 才算改完，之後再用 sync_project.py 逐專案同步。' ;;
    push)
      msg='[repo-rules] 準備 push：先明確 stage（不要 git add -A），再跑 python3 -X utf8 tools/verify_bootstrap.py --staged，exit 0 才提交，指令用 && 綁住結束碼；push 前先 fetch，遠端意外前進就停下回報，禁止 force push。開工標記與中途安全點都不算交棒、不加次數；要交棒就先走 B6，把「工作中」改回「無（已交棒）」並覆寫整份 HANDOFF。' ;;
  esac
fi

if [ -n "$msg" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}\n' "$event" "$msg"
fi
exit 0
