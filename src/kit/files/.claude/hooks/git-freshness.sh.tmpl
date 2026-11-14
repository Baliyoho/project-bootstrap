#!/usr/bin/env bash
# source: PROJECT-BOOTSTRAP.md v2026-11-14 — 權威版在部署包，改這裡之前先改部署包再同步各專案。
# SessionStart hook：fetch 一次，只報事實，不下指示（需求決策書 v3 第 5 節，D12）。
# 輸出到 stdout 的內容會進到 session 開頭的 context，最多 5 行。只讀：不 pull、不 push、不寫任何檔。
# 怎麼判讀交給模型與 AGENTS.md 的共用制度；舊版的判讀表、全綠行與工具身分猜測在 2026-11-13 移除，
# 理由與 E1 對照實測見 project-bootstrap 的 experiments/handoff-ab/RESULTS.md。

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0
me=${HOSTNAME:-$(hostname 2>/dev/null || uname -n 2>/dev/null)}

# 第 1 行：時間（含 session 名用的 MM.DD.HH，F50）、本機、分支
echo "[facts] 時間 $(date '+%Y-%m-%d %H:%M %z')（session 名用 $(date +%m.%d.%H)）；本機 ${me}；分支 ${branch}"

# 第 2 行：與 origin 的關係
if ! git fetch --quiet origin 2>/dev/null; then
  echo "[facts] fetch origin 失敗：不知道本機是不是最新"
  exit 0
fi
counts=$(git rev-list --left-right --count "origin/${branch}...HEAD" 2>/dev/null)
dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ -z "$counts" ]; then
  echo "[facts] origin 上沒有分支 ${branch}；未提交或未追蹤 ${dirty} 個檔"
  exit 0
fi
behind=$(echo "$counts" | awk '{print $1}')
ahead=$(echo "$counts" | awk '{print $2}')
echo "[facts] 已 fetch：本機落後 origin/${branch} ${behind} 個 commit、領先 ${ahead} 個（origin=$(git rev-parse --short "origin/${branch}" 2>/dev/null)）；未提交或未追蹤 ${dirty} 個檔"

# 第 3 行：origin 那份 HANDOFF 的「工作中」。讀 origin 的、不讀本機的：此刻還沒 pull，本機那份可能是舊的。
# 照原文印出，不解析、不判讀；有幾列就說幾列，讓重複的欄位看得見。
remote_handoff=$(git show "origin/${branch}:HANDOFF.md" 2>/dev/null)
if [ -n "$remote_handoff" ]; then
  busy=$(printf '%s\n' "$remote_handoff" | grep -F '**工作中**')
  busy_n=$(printf '%s\n' "$busy" | grep -c '[^[:space:]]' || true)
  if [ "$busy_n" -gt 1 ]; then
    echo "[facts] origin 上的 HANDOFF 有 ${busy_n} 列「工作中」，第一列：$(printf '%s\n' "$busy" | head -1)"
  else
    echo "[facts] origin 上的 HANDOFF：${busy:-讀不到「工作中」那一行}"
  fi
fi

# 第 4 行（有差異才印）：共用制度的版本與上游不同（F18 提示）。
# 版本取自 AGENTS.md 共用制度開始標記裡的 source: 標記。抓不到（離線、沒有 curl）就安靜跳過。
# 結果快取 12 小時。關掉：BOOTSTRAP_VERSION_CHECK=off
UPSTREAM_VERSION_URL=https://raw.githubusercontent.com/Baliyoho/project-bootstrap/main/VERSION  # fork 的人改這一行
if [ "${BOOTSTRAP_VERSION_CHECK:-}" != off ] && [ -f AGENTS.md ]; then
  mine=$(sed -n 's/.*共用制度開始 source: PROJECT-BOOTSTRAP\.md v\([0-9][0-9.-]*\).*/\1/p' AGENTS.md | head -1)
  cache=.claude/.bootstrap-version
  if [ -n "$(find "$cache" -mmin -720 2>/dev/null)" ]; then
    latest=$(cat "$cache" 2>/dev/null)
  else
    latest=$(curl -fsS --max-time 5 "$UPSTREAM_VERSION_URL" 2>/dev/null | tr -d '\r\n \t')
    [ -n "$latest" ] && printf '%s' "$latest" > "$cache" 2>/dev/null
  fi
  # 版本號是 YYYY-MM-DD 或 YYYY-MM-DD.N；序號補成三位數後日期與序號能一起比字典序。
  verkey() {
    _d=${1%%.*}
    _n=${1#"$_d"}
    _n=${_n#.}
    [ -n "$_n" ] || _n=0
    case $_n in *[!0-9]*) _n=0 ;; esac
    printf '%s.%03d' "$_d" "$_n"
  }
  if [ -n "$mine" ] && [ -n "$latest" ]; then
    km=$(verkey "$mine")
    kl=$(verkey "$latest")
    if [ "$km" != "$kl" ]; then
      if [ "$(printf '%s\n%s\n' "$km" "$kl" | sort | head -1)" = "$km" ]; then
        echo "[facts] 共用制度落後：本機 v${mine}，上游 v${latest}（更新方法見 project-bootstrap 的 README）"
      else
        echo "[facts] 共用制度比上游新：本機 v${mine}，上游 v${latest}"
      fi
    fi
  fi
fi

# 第 5 行（有差異才印）：家目錄的 handoff skill 與專案那份不同。實測 Claude Code 2.1.321 會用家目錄那份
# 蓋掉專案的同名 skill（決策書 Q28）。逐檔比內容，只有一邊有的檔也算不同。
home_skill=${HOME:-}/.claude/skills/handoff
if [ -f .claude/skills/handoff/SKILL.md ] && [ -n "${HOME:-}" ] && [ -d "$home_skill" ]; then
  skill_diff=''
  for f in .claude/skills/handoff/*.md "$home_skill"/*.md; do
    [ -f "$f" ] || continue
    name=${f##*/}
    case " $skill_diff " in *" $name "*) continue ;; esac
    cmp -s ".claude/skills/handoff/$name" "$home_skill/$name" || skill_diff="$skill_diff $name"
  done
  [ -n "$skill_diff" ] && echo "[facts] 家目錄 ~/.claude/skills/handoff/ 與本專案的 handoff skill 不同（${skill_diff# }）；Claude Code 載入的是家目錄那份"
fi
exit 0
