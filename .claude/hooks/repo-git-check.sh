#!/usr/bin/env bash
# 本 repo 專屬的 SessionStart 檢查。
# 🔴 這不是部署包 3.10 `git-freshness.sh` 的副本，**不要用 sync_project.py 同步它**。
#
# 為什麼不直接抄 3.10：抄過來會變成最容易腐化的那一份副本。sync_project.py 的 --all 靠
# `*/.claude/skills/handoff/SKILL.md` 發現專案（tools/sync_project.py 的 discover()），
# 而這個 repo 刻意沒有 skill，所以 --all 永遠掃不到它——改了 3.10，9 個專案一行同步完，
# 只有來源自己落後，而且沒有任何跡象。所以這裡只留「開場提醒 git 狀態」與「工作中標記」
# 這兩件事，邏輯簡單到不會腐化，也沒有同步義務。3.10 的另外兩段（骨架版本偵測、skill 提醒）
# 在這裡會因為條件不成立而安靜跳過，不抄也不損失什麼。
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

# 工作中標記（跨機器誤接棒防呆，2026-10-30 補）
# 起因：這個 repo 開始多機維護。在此之前 single writer 完全靠人顧，而上面那個 ✅ 只證明
# 「本機沒落後 origin」——別台機器**未提交**的變更，fetch 與 git log 都看不到。
# 跟部署包 3.10 用同一個載體（HANDOFF.md）、同一個欄位（**工作中**）、同一組結論符號：
# 刻意不發明第二種標記，否則就會分岔成「這裡會擋、別處不會擋」的不對稱（ARCHITECT.md 已禁）。
# 讀 origin 那一份、不讀本機的：此刻還沒 pull，本機那份可能是舊快照。
# 只讀、只提醒，絕不寫入——往權威分支自動 commit／push 是整套制度最不該自動化的地方。
# 寫入是 skill A5（開工）與 B6（交棒清掉）的事。
# 欄位在的時候一定印一句結論（✅／🟡／🔴），不要「沒事就不說話」：沉默跟「查過了沒事」
# 分不出來，而這個機制的全部價值就在於讓人知道「有沒有被查」。
remote_handoff=$(git show "origin/$branch:HANDOFF.md" 2>/dev/null)
if [ -n "$remote_handoff" ]; then
  busy=$(printf '%s\n' "$remote_handoff" | grep -F '**工作中**' | head -1)
  case "$busy" in
    '')
      echo "[repo-check] 🟡 origin 的 HANDOFF.md 沒有「工作中」欄位，無法確認有沒有別台機器在動 $branch（下次交棒時照 B6 補回來）。"
      ;;
    *無*)
      echo "[repo-check] ✅ 「工作中」是「無（已交棒）」，沒有別台機器佔著 $branch。"
      ;;
    *)
      who=${busy#*：}
      me=${HOSTNAME:-$(hostname 2>/dev/null || uname -n 2>/dev/null)}
      same=no
      [ -n "$me" ] && case "$busy" in *"$me"*) same=yes ;; esac
      # 工具欄＝標記的第二欄（欄位用全形斜線 ／ 分隔）。2026-10-31 加：只比機器名的時候，
      # 同一台機器換個工具就落進「大概是你自己另一個視窗」的 🟡——而同機器通常就是同一個
      # 工作樹，兩個 agent 會即時互相覆寫，比跨機器那個洞更貴（跨機器至少是兩份磁碟）。
      # 舊格式沒有工具欄，第二欄會是 session 名，而 session 名一定含全形豎線
      # （`符號　YYMMDDHH｜主題｜狀態`）——拿豎線當判別子，同一段邏輯讀新舊兩種格式都對，
      # 不必先知道這個專案升級了沒。全程只用參數展開，不用 sed：這段會被抄進各專案，
      # 而一條充滿轉義的 sed 腳本是最容易在抄寫時悄悄壞掉的東西。
      tool=''
      case "$who" in
        *／*)
          rest=${who#*／}
          tool=${rest%%／*}
          tool=${tool# }
          tool=${tool% }
          tool=${tool#'`'}
          tool=${tool%'`'}
          ;;
      esac
      case "$tool" in *｜*) tool='' ;; esac
      # 自己是哪個工具：環境變數只拿來**加嚴**，不拿來放寬（2026-10-31 實測，理由見部署包
      # 「工具身分」一節）。兩家以上的簽章同時在場＝在別的工具殼層裡被啟動、變數被繼承，
      # 這時不猜——猜錯的方向會是「放行」，正好是最貴的那一種錯。
      mytool=''
      sigs=0
      [ -n "${CODEX_VERSION:-}${CODEX_SESSION_ID:-}" ] && { mytool='Codex CLI'; sigs=$((sigs + 1)); }
      [ -n "${GEMINI_CLI:-}" ] && { mytool='Gemini CLI'; sigs=$((sigs + 1)); }
      [ -n "${CLAUDECODE:-}" ] && { mytool='Claude Code'; sigs=$((sigs + 1)); }
      [ "$sigs" -gt 1 ] && mytool=''
      # 比字串時不分大小寫，也接受標記寫得比偵測值長（例如 `Claude Code (desktop)`）：
      # 寫法差一點就報 🔴 是在加嚴的方向，但也只是噪音，而噪音多了就會有人學會無視它。
      mismatch=no
      if [ -n "$mytool" ] && [ -n "$tool" ]; then
        lc=$(printf '%s' "$tool" | tr 'A-Z' 'a-z')
        mylc=$(printf '%s' "$mytool" | tr 'A-Z' 'a-z')
        case "$lc" in *"$mylc"*) ;; *) mismatch=yes ;; esac
      fi
      if [ "$same" = no ]; then
        echo "[repo-check] 🔴 另一台機器正在 $branch 上工作，尚未交棒：$who"
        echo "[repo-check]    依 single writer 規則，同一時間只能有一台機器動同一條分支。"
        echo "[repo-check]    停下來問使用者（handoff skill 的 A2.5），不要直接接棒。"
        echo "[repo-check]    注意：那台未提交的變更只在那台的磁碟上，這裡拿不到——標記只告訴你東西在哪。"
      elif [ -z "$tool" ]; then
        echo "[repo-check] 🟡 這台機器（$me）還有一個 session 在 $branch 上沒交棒：$who"
        echo "[repo-check]    這個標記是舊格式、沒有工具欄，分不出是哪個工具寫的。確認是你自己這個工具開的另一個視窗才繼續，不是就照 A2.5 停下來。"
      elif [ "$mismatch" = yes ]; then
        echo "[repo-check] 🔴 同一台機器（$me）上另一個工具正在 $branch 上工作，尚未交棒：$who"
        echo "[repo-check]    標記寫的是「$tool」，這個 session 的環境看起來是「$mytool」。同機器通常就是同一個工作樹，兩個 agent 會即時互相覆寫——比跨機器那個洞更貴。"
        echo "[repo-check]    停下來問使用者（handoff skill 的 A2.5），不要直接接棒。"
      else
        echo "[repo-check] 🟡 這台機器（$me）上有一個「$tool」的 session 在 $branch 上沒交棒：$who"
        echo "[repo-check]    你自己是不是「$tool」？不是就照 🔴 處理（A2.5）。這一句由你答、不由環境變數答——跨工具啟動時變數會被繼承而說謊。"
      fi
      ;;
  esac
fi

echo "[repo-check] 本 repo 刻意沒有 handoff skill、沒有 pre-push 防呆、沒有 check_docs.py（理由見 ARCHITECT.md「這個 repo 刻意沒有的東西」）：接棒程序讀全域 ~/.claude/skills/handoff/。HANDOFF.md 只當「工作中」標記的載體，不是狀態日誌（界線寫在它開頭那節）。改制度就改 PROJECT-BOOTSTRAP.md，改完跑 python -X utf8 tools/verify_bootstrap.py。"
exit 0
