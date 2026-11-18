# ARCHITECT 的結構變更紀錄（2026-08-05 到 2026-11-17）

> 最後更新：2026-11-17（建立：從 [ARCHITECT.md](../../ARCHITECT.md) 開頭搬來。ARCHITECT 只寫現況，逐次變更的經過留在這裡備查；連到根目錄的連結改成 `../../`，內文不改）
> 平常不讀，要回溯歷史先經使用者同意（需求決策書 v3 Q39）。新的結構變更不再記在這裡，看 Git 歷史；部署包的逐版紀錄在 [CHANGELOG.md](../../CHANGELOG.md)。

---

> 最後更新：2026-11-17：根目錄的需求與計畫類文件只留兩份權威——[需求決策書 v3](../../project-bootstrap-requirements-decision-v3.md)與新的[實施計畫 v3](../../project-bootstrap-implementation-plan-v3.md)；其餘 19 份（查核、複審、查核進度、效率計畫、舊實現規劃、需求歷史原件、skill 拆分設計、12 份需求來回討論）用 `git mv` 封存到 `docs/history/`，加[封存索引](README.md)。「封存原件」檢查從只擋 v2 檔名擴大到整個封存區。四份文件的分工寫在 CONTRIBUTING「需求與計畫文件的分工」

> 最後更新：2026-11-17：新增 [CHANGELOG.md](../../CHANGELOG.md)，部署包開頭的逐版變更紀錄（約 80 行）逐字搬過去，部署包只留目前的版本行與一行指標；部署出去的專案用不到那段歷史。

> 最後更新：2026-11-17（需求決策書 v3 Q41）：交接協定 `docs/ai-notes/handover-protocol.md` 移出部署包，3.6 保留編號、改成移除說明，部署包少一個檔；它獨有的分支模型、漏交棒理由與「verify_state 一律跑」搬進 3.8 的 skill。「核心與實例優先序」「接力協調邊界」「已修正的主張沒復活」「跨工具過期敘述」四項改成只讀 skill。

> 最後更新：2026-11-17（需求決策書 v3 Q40）：新增 [CONTRIBUTING.md](../../CONTRIBUTING.md)，收 AGENTS.md 裡碰到才需要的規則（副本規則、本 repo 交接快照、指標檔、行末、hook 訊息寫法）、README.md 裡的開發流程與副本同步用法，以及本檔原本的「開發注意事項」（那不是結構）；AGENTS.md 只留開工必守的規則，README.md 改成標準 README。部署包範本 3.1、3.4、3.5 同步改成職能分工：連線資料從 AGENTS 搬進 README，README 不再放交接 prompt。「規則理由連結」改成同時查 AGENTS.md 與 CONTRIBUTING.md，「結構摘要一致性」與「已修正的主張沒復活」改守新的 README 寫法。

> 最後更新：2026-11-17（需求決策書 v3 Q39）：v2 決策書退休，用 `git mv` 封存到 `docs/history/requirements-decision-v2.md`（逐位元組不改），v3 成為唯一需求書；`verify_v2.py`、`test_registry_repo.py`（新，從 `test_registry.py` 拆出）、`test_trail_repo.py` 與一致性檢查改讀 v3；`verify_bootstrap.py` 新增「封存原件」，文件檢查與行末檢查不讀 `docs/history/`。

> 最後更新：2026-11-14（Codex 交接成本優化）：`verify_bootstrap.py` 先啟動獨立的 `verify_v2.py` 子程序，與其餘暫存 fixture 檢查重疊，收尾仍必須驗其結束碼及報告；新增 `--quiet` 只縮成功輸出。`tests/test_verifier_execution.py` 驗大量輸出、失敗／SKIP 保留與異常清理。不部署新工具、不新增模型呼叫；skill 補 Codex 外層等待用法，版本 `2026-11-14.4`。

> 最後更新：2026-11-14（使用者決定：本 repo 補裝 push 前 hook——`.claude/hooks/repo-pre-push.sh` 是 3.11 的逐字副本，兩份接線都接 PreToolUse，pre-push 從已宣告例外移除；動作提醒 `repo-action-rules.sh` 與它的 PostToolUse 接線拿掉；驗證項「動作當下送規則」換成「本 repo push 前 hook」。前面同日：本 repo 交接制度對齊 v3：`.claude/hooks/repo-git-check.sh` 換成 3.10 `git-freshness.sh` 的逐字副本，只印 `[facts]`；驗證項「本 repo 工作中判讀」與「全綠行」退場，換成「本 repo 開場 hook」逐位元組比對；`.gitignore` 加 `.claude/.bootstrap-version`；`AGENTS.md` 開工段改名「跟部署出去的專案不同的地方」、只寫事實。前面同日：v3 Q33：執行屏障模組與測試封存到 [archive/v2-barrier/](../../archive/v2-barrier/README.md)，`verify_v2.py` 不再跑探針；前面同日：session 名稱時間戳改 `MM.DD.HH`，`VERSION` `2026-11-14`；`sync_project.py` 會同步 `AGENTS.md` 的共用制度，驗證項加「同步共用制度」）。前次 2026-11-13（v3 第 1 期：部署包改成 v3 形狀）：骨架 27 → 24 檔，`VERSION` `2026-11-13`。3.1 `AGENTS.md` 範本有開始／結束標記夾住的共用制度（≤40 行）；3.10 開場 hook 只報事實（最多五行 `[facts]`）；3.8 handoff skill 降為碰到才讀的參考；舊 3.18–3.20（Antigravity 轉接層、shim、`.agents/hooks.json`）移除，`sync_project.py` 不再處理 `.agents/hooks.json`，`owners.json` 少三列。驗證項的取捨記在「`tools/verify_bootstrap.py` 守的東西」表下方。
>
> 前次 2026-11-13（需求決策書 v3 與 handoff-ab 實測）：新增 `project-bootstrap-requirements-decision-v3.md` 當現行需求權威，v2 決策書並存供工具讀取（v3 Q32 (b)）；新增 `experiments/handoff-ab/`（對照實測，v3 的依據）。部署包、`VERSION`、驗證項都沒動。

> 最後更新：2026-11-12（v2 併進 main 與 `beta` epoch 3）：`main` 快轉到 `cf58954`（決策書 Q30），在那裡發 `channel/beta/3-ad6948d1…`；核對與乾淨環境安裝紀錄在 v2 說明。

> 2026-11-12 稍早（Claude Code skill 載入與 Q28／Q29）：第三次 `claude -p` 量到家目錄 handoff skill 蓋掉專案那份；決策書 Q28 (a) 讓部署包 3.10 開場 hook 在兩份不同時印 🟡（`source:` `v2026-11-12.3`，`VERSION` 不動，各專案未同步），`selftest.SKILLS` 的 Claude Code 改家目錄優先。Q29 (a)：Antigravity 凍結，不測、不追、不移除。

> 2026-11-12 稍早（Claude Code 啟動自測第二次）：一次 `claude -p`，push 提醒的 exit 2 確實擋下 Bash 的 `git push`、`AGENTS.md` 經 `CLAUDE.md` 的 import 進到 context；`src/kit/capabilities.json` 的 `claude-code/push-reminder` 改成 `tested: [2.1.321]`，`reads-agents-md` 加註，部署包不變，包的 digest 會變。

> 2026-11-12 稍早（F14 程序入口等價）：`surfaces.compare_procedure` 比對每個 surface 讀到的指示檔（經 `CLAUDE.md` import／`GEMINI.md` 指標都要到 `AGENTS.md`）與 skill 載入器找到的 handoff skill（指標照連結追到權威版，比 `description` 與整個目錄的檔）；開場檢查另要求 Claude Code／Codex 那幾條的 stderr 是空的（`ag-wrap.sh` 會把 stderr 併進訊息）。因此找到部署包 3.16 指標的 `description` 少了模式 0 那句與三個觸發詞，已補齊，`source:` `v2026-11-12.2`，`VERSION` 不動，各專案副本未同步。

> 2026-11-12 稍早（Claude Code 啟動自測）：使用者登入 CLI 後跑一次 `claude -p`，開場 hook 的輸出確實進到模型 context；`src/kit/capabilities.json` 的 `claude-code/hooks` 從 `docs` 改成 `tested: [2.1.321]`，表上文字與部署包不變，包的 digest 會變（下次發布才帶出去）。

> 2026-11-12 稍早（決策書 Q27 (a)）：部署包 3.11 `pre-push-handoff.sh` 只看 payload 的 `command` 欄位（字串或字串陣列），不再拿整段 payload 比對；`source:` 標記 `v2026-11-12`，`VERSION` 不動，各專案副本未同步。`verify_bootstrap.py` 的 push 提醒情境加三條與一個負向儀器。

> 2026-11-12 稍早（本 repo 的動作提醒 hook 第三版）：`.claude/hooks/repo-action-rules.sh` 對 `bash`／`sh`／`zsh`／`dash -c` 與 `eval` 裡的指令再解析一層（最多三層），補上 `bash -c "git push"` 的漏報；`verify_bootstrap.py` 加 10 個案例與一個拿掉這條規則就要回到漏報的負向測試。仍只提醒、不擋；本 repo 專屬，不同步。

> 2026-11-12 稍早（F14 開場檢查的共用契約與薄 adapter）：新增 `src/project_bootstrap/surfaces.py` 與兩份測試，同一個專案狀態經每個 surface 的真實接線命令與工作目錄跑出的開場文字必須相同；不部署、不同步。

> 2026-11-12 稍早（P2 第 4 片補缺口：版本偵測、安裝自測、矩陣進包）：`tools/build_package.py` 把 `src/kit/capabilities.json` 放進包的 manifest（隨 digest 與簽章，不部署進專案），`package.check` 一併驗它；新增 `src/project_bootstrap/selftest.py` 與兩份測試，讀專案已安裝的包的矩陣、偵測 surface 版本、只看檔案做安裝自測。包的 digest 因此改變，部署包 `PROJECT-BOOTSTRAP.md` 與 `VERSION` 不變；`beta` epoch 1 是之前發的，沒有矩陣。

> 2026-11-12 稍早（決策書 Q26 (a)）：`package.py` 新增 `copy_digest`（CRLF 當 LF），寫入檢查、遷移器與 F39 盤點用它比專案副本，包本身仍逐位元組比；遷移器拿掉 `eol` 狀態。部署包與 `VERSION` 未動。

> 2026-11-11（P2 第 5 片遷移器，決策書 Q25）：`tools/sync_project.py` 的檔案清單改由 `src/kit/owners.json` 算出，同步行為不變，`owners.json` 出現同步器不會處理的混合檔就拒絕啟動；新增 `src/project_bootstrap/migrate.py`（遷移判斷與報告）、`tools/migrate_project.py`（預演只讀、寫入一次一個專案並寫指標）與兩份測試。不部署、不同步，部署包與 `VERSION` 未動。

> 2026-11-11 稍早（P2 第 4 片能力矩陣，決策書 Q24）：新增 `src/kit/capabilities.json`，部署包「跨工具與跨平台」的兩張表改由它生成（`kit.md` 換成 `<!-- kit-table: … -->` 指令行，`tools/build_kit.py` 展開）；部署包逐位元組不變，skill／hook／接線與 `VERSION` 未動。新增 `src/project_bootstrap/capabilities.py`（驗矩陣、生成表格、逐 surface／版本報缺口與 strict ready）與兩份測試。不部署、不同步。

> 2026-11-11 稍早（P2 第 3b 片收尾）：`tools/release_package.py` 把驗證器完整輸出印進 CI 日誌，並多輸出一個 `*.report.json`（SHA-256 等於簽章紀錄的 `report`），workflow 會一起上傳；`distribute.py` 多一個 `report_bytes`。已發的 `beta` epoch 1 沒有這個檔。

> 2026-11-11 稍早（P2 第 3b 片 E5，決策書 Q23）：乾淨環境驗收通過；同時實測發現 E3 的 tag ruleset（27014223）擋不住移動與刪除，channel 歷史沒有伺服器端保護，照實記錄、靠簽章。測試用的 `channel/e5-test/…` tag 建了、移了、刪了，GitHub 回到只有 `channel/beta/1-…`。使用者同意後已刪掉 ruleset 27014223，免得它在設定頁顯示 active 讓人以為有保護；repo 現在沒有任何 ruleset。repo 檔案只改文件與 `channel.py` 的說明。

> 2026-11-11 稍早（P2 第 3b 片 E4）：第一次正式發布。使用者核准 workflow run 42982470611（macOS runner）後，`verify_bootstrap.py` 全部本輪實查通過、簽章，建出 `channel/beta/1-ed31ffed…` tag（指向 `243074c`）與同名 prerelease（三個檔）。repo 檔案只改文件。

> 2026-11-11 稍早（P2 第 3b 片 E3，決策書 Q22）：GitHub 上加了一條 tag ruleset（id 27014223）：`refs/tags/channel/**` 不能移動、不能刪除，沒有任何人可以繞過，建立不限制。原計畫「只有 GitHub Actions 能建」做不到：個人帳號的 repo 不能把 Actions 列為例外。repo 檔案只改文件與 `channel.py` 的說明。

> 2026-11-11 稍早（P2 第 3b 片 E1）：在 GitHub 建了 `release` environment（必要審核人是 repo 擁有者），CI 私鑰存成它的 `RELEASE_SIGNING_KEY` secret，本機私鑰已刪；公鑰寫進 `src/kit/release-keys.txt`，指紋寫進 README。還沒 push、沒設保護規則，workflow 沒跑過。

> 2026-11-11 稍早（P2 第三片後半 3b 的本機準備，決策書 Q21）：新增 `.github/workflows/release.yml`（本 repo 第一支 workflow，只由 `release-request/*` tag 觸發、要使用者核准）、`tools/release_package.py`（CI 用：乾淨 checkout、建包、跑驗證、簽章、打包）、`tools/install_package.py`（使用者用：驗簽、裝進快取、寫指標，可鋪空專案）、`src/kit/release-keys.txt`（發布公鑰；目前是空的，等 E1）、`src/project_bootstrap/distribute.py` 與兩份測試。還沒有 push、沒有建 secret、environment 或保護規則，workflow 不會跑；部署包、skill／hook／接線與 `VERSION` 未動。

> 2026-11-11 稍早（P2 第三片前半 3a，決策書 Q20）：`src/project_bootstrap/` 新增 `channel.py`（CI 端發布、沿金鑰鏈安裝、從來源 repo 的 `channel/*` tag 做每次寫入的檢查），`tests/` 新增 `test_channel.py`；`pointer.py` 抽出三個共用步驟並允許指標多一個 `source` 欄位。全部在本機驗，沒有建 workflow、secret 或保護規則；部署包、skill／hook／接線與 `VERSION` 未動，不部署、不同步。

> 2026-11-11 稍早（P2 第二片：專案指標與每次寫入的檢查）：`src/project_bootstrap/` 新增 `pointer.py`、`tests/` 新增 `test_pointer.py`。專案指標 `.bootstrap/pointer.json` 只是原型裡的路徑，還沒進部署包；部署包、skill／hook／接線與 `VERSION` 未動，不部署、不同步。

> 2026-11-11 稍早（P2 第一片：正式包格式）：`src/kit/` 新增 `owners.json`（每個範本的歸屬：core／adapter／project 與更新方式）；新增 `tools/build_package.py`，由 `src/kit` 生成 `dist/package/`（每個部署檔一份加 `manifest.json`，Git 不追蹤）；`src/project_bootstrap/package.py` 與 `tests/test_package.py`、`tests/test_package_repo.py`。部署包內容、skill／hook／接線與 `VERSION` 未動，不部署、不同步。

> 2026-11-11 稍早（F22 第二輪）：新增「碰到才讀的文件」（從 AGENTS.md 搬來）與「開發注意事項」（從 HANDOFF.md 的地雷搬來），常態必讀因此變短。

> 2026-11-11 稍早：P1 第四片：`src/project_bootstrap/` 新增 `status_card.py`（只讀狀態卡）、`schema_check.py` 與 `status.schema.json`／`mutants.schema.json`（jsonschema）、`mdlinks.py`（markdown-it-py）；`tests/` 新增對應四份測試。後兩支用鎖檔套件，列在 `verify_bootstrap.py` 的 `P1_EXTRAS`：別的程式不能 import 它們；它們的測試開頭寫 `raise unittest.SkipTest('needs …')`；A4 的 `verify_v2` 不跑這些檔，報告與 v2 項會逐一列出（「跳過數必須是 0」的規則不變）。「P1 開發骨架」改守這三條規則。同日 P1 第三片（來源權威切換）：新增 `src/kit/`（`kit.md` 散文＋`files/` 底下 27 個 `.tmpl` 範本）與 `tools/build_kit.py`；`PROJECT-BOOTSTRAP.md` 改成由它生成、仍提交，第一次拆出時逐位元組重建。AGENTS 鐵律 1 同批改寫；`verify_bootstrap.py` 新增「部署包由來源生成」；本 repo 兩支 hook 的提醒改指 `src/kit`。部署出去的內容沒變，`VERSION` 不跳、不同步。同日 P1 第二片：`experiments/v2` 的程式（`.py`、兩支 guest 腳本、`vm_runner.swift`、`mutants.json`）用 `git mv` 搬到 `src/project_bootstrap/`，測試搬到 `tests/`（加 `tests/__init__.py`），模組名 `experiments.v2.x` → `project_bootstrap.x`、`experiments.v2.test_x` → `tests.test_x`；`experiments/v2/` 只留 [說明](../../experiments/v2/README.md) 與 [現況索引](../../experiments/v2/status.json)。程式內容只改 import、路徑與子程序的工作目錄，邏輯沒動。下方舊登記裡的 `experiments/v2/*.py` 是當時位置。同日稍早 P1 第一片（開發骨架）：根目錄新增 `pyproject.toml`、`uv.lock`、`src/project_bootstrap/`、`tests/`；`.gitignore` 加 `.venv/`；`verify_bootstrap.py` 新增「P1 開發骨架」。用 uv 鎖依賴（版本、sha256、授權），pytest 跑既有 v2 測試與新 `tests/`；最低 Python 3.12。`verify_bootstrap.py`／`verify_v2.py`／v2 原型仍只用標準函式庫，A4 不需要裝 uv。部署包、skill／hook／接線與 `VERSION` 未動，不部署、不同步。

> 2026-11-10 同日深夜：部署包 3.8 的 `reasons.md` 末尾加「規則 → 理由在哪」對照表（決策書 Q17 (b)），六個 skill 檔與 `VERSION` 跳到 `2026-11-10.2`，這台 Mac 的兩個全域副本一起覆蓋；`verify_bootstrap.py` 新增「skill 規則對照表」。結構沒有新增檔案。同日稍晚：本 repo 新增 `.claude/hooks/repo-action-rules.sh`（決策書 Q6 (a)），只接 Claude Code；`verify_bootstrap.py` 新增「動作當下送規則」，「本 repo 兩份接線」放寬為 Claude Code 可多接這支。這台 Mac 的兩個全域副本換成六檔版（Q11 (a)）。同日稍早：**部署包 3.8 從一個檔變成六個檔**（決策書 Q9／F22）：handoff skill 是一個目錄，入口 `SKILL.md` 加 `mode-a.md`、`mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md`；骨架 22 → 27 檔，`VERSION` `2026-11-10`。`tools/` 新增 `skill_split_baseline.json`；`verify_bootstrap.py` 新增「skill 拆分」「同步補齊模式檔」「全綠行」三項；兩支開場 hook 多印全綠行。同日 Q11 (a)：只有這台 Mac 的兩個全域副本換成六檔版；各專案尚未同步，`main` 也還沒有這一版。同日稍早：根目錄新增 [skill 拆分設計稿](project-bootstrap-skill-split-design.md)（決策書 Q8 (a)，等 Q9 審閱，未實施）。同日稍早：根目錄新增 [AGENTS-reasons.md](../../AGENTS-reasons.md)：AGENTS.md 的事故與理由逐字搬過去，入口只留規則加「為什麼」連結（決策書第 6 節 Q4 第一階段，F22）；`verify_bootstrap.py` 新增「規則理由連結」一項附 7 個負向測試；第二輪複審快照從每輪必讀改成條件式。只動本 repo 自己的檔，部署包、skill／hook／接線與 `VERSION` 未動，不部署、不同步。

> 2026-11-10 新增 `experiments/v2/crash_release.py` 與 `test_crash_release.py`：無共享 guest 的父程序崩潰後，依決策書 Q1 (a) 讀開機前登記在 `guest_runs` 帳本的 runner `.host` 停機紀錄，再要 host 本機終端（`/dev/tty`）照打挑戰碼，兩者都過才退場；缺證據維持阻擋。合成原型，同 UID 偽造不排除。

> 2026-11-10 稍早：根目錄表的決策書需求數更正為 51（2026-11-06 補 F50 後漏改，`experiments/v2/contradictions.py` 首次對 ARCHITECT 跑時抓到）。

> 2026-11-09：`experiments/v2/vm_probe.py`、`vm_runner.swift`、`vm_guest_init.sh`、`vm_managed_worker.sh` 與 `test_vm_probe.py` 是 Mac VM 候選的合成探針及離線負向控制：固定映像 digest、無網路 guest。退場與跨 VM 鎖反例掛獨立暫存共享目錄及 `setsid` 後代；新固定工具路徑由 `/init` 在無共享 guest 中啟動 `vm_managed_worker.sh`，只經第二個雙向 virtio console 載入前提並發原始 broker 請求。host 核對請求後由 outbox／broker／materializer 寫入合成工作樹，正式 repo 不掛載進 VM。舊 `managed_fixture.py` 路徑仍用 host worker，按 actor＋epoch 保存各台 VM 退場證據，未確認時重啟保持阻擋；新無共享工具路徑另由 `guest_runs.py`（離線測試 `test_guest_runs.py`）在同一私有資料庫持久記錄每台 guest 的 parent 選定身分 digest 與 host 停機證據，未退場時新 guest、ACK、寫入與重啟都阻擋；每台 run 綁一個 broker channel，退場時輪換 capability。runner 的 host 標記另寫 `.host` 日誌，不與 guest console 混用。這些資料流仍未接真實工具或現行部署包，也不提供 host 故障後的自動復原保證。詳見 [P0 說明](../../experiments/v2/README.md)。

> 2026-11-09 新增 `experiments/v2/doctor.py` 與 `test_doctor.py`：F16b 本機能力診斷，缺工具／缺設定／連線失敗分開報，不讀出設定值。

> 2026-11-09 新增 `experiments/v2/mutants.py`、`mutants.json` 與 `test_mutants.py`：本輪守門的 mutation 規格與重跑入口（F29／F49），不在 `verify_v2.py` 預設流程。

> 2026-11-09 新增 `experiments/v2/impact.py` 與 `test_impact.py`：F31 改動影響圖，從 `status.json` 證據路徑推出元件→需求→重驗測試，未分類變更回全驗。

> 2026-11-09 新增 `experiments/v2/policy.py` 與 `test_policy.py`：F36 依所有權規劃更新、F37 只能加嚴的覆寫合併、F38 空位 schema 與說明。未接進 `sync_project.py` 或骨架。

> 2026-11-09 新增 `experiments/v2/decisions.py` 與 `test_decisions.py`：F44 待決事項與委任、F34 已宣告例外的紀錄檢查與生成視圖。未接進現行程序。

> 2026-11-09 新增 `experiments/v2/evidence.py`、`facts.py` 與對應測試：M2 證據帳（本輪／沿用／未驗證／不通過分開，沿用依賴 digest 失效與撤銷，F3／F40）與文件命題對 Git／檔案的事實 adapter（F20）。未接進現行程序。

> 2026-11-09 新增 `experiments/v2/state.py` 與 `test_state.py`：M2 狀態模型（目標／任務／下一步／風險＋證據）與生成的 HANDOFF 視圖，F1／F2／F5 原型。未取代現行手寫 HANDOFF。

> 2026-11-09 新增 `experiments/v2/readonly.py` 與 `test_readonly.py`：F23 只讀輪次前後快照比對（ref、index、變更檔、遠端），偵測標記、stage、commit、push。未接進現行程序。

> 2026-11-09 新增 `experiments/v2/lines.py` 與 `test_lines.py`：F12 並行線登記檢查，以 Git 回報的工作樹、index 與分支判定兩線是否共用。只偵測，未接進現行程序。

> 2026-11-09 新增 `experiments/v2/preflight.py` 與 `test_preflight.py`：把 `gitclaim` 的寫入時資格（遠端標記須正好是本 session、不得落後或分岔）與 `release.WriteGate` 組成單一受管寫入前檢查，`batch.py` 可選逐目標發布確認。未接進現行程序。

> 2026-11-09 新增 `experiments/v2/release.py` 與 `test_release.py`：M1 整包 manifest（元件 digest）與每次寫入前的 nonce 簽章新鮮度確認原型（F18／F32／F33），沒有快取路徑。未接進現行 `git-freshness.sh` 或同步工具。

> 2026-11-09 新增 `experiments/v2/gitclaim.py` 與 `test_gitclaim.py`：F9／F10 的 M3 開工資格與收尾閘門原型，對本機 bare origin 實測，收尾成功才產生 `session.py` 的交棒收據。`batch.py`／`test_batch.py` 在其上做多目標彙總（F30）。未接進現行程序。詳見 [P0 說明](../../experiments/v2/README.md)。

> 2026-11-08 新增 `experiments/v2/tree_probe.py` 與 `test_tree_probe.py`，只在合成 POSIX 程序群組比較一般後代與脫離 session 的後代，透過檔案鎖觀察退場。一鍵入口列出這個候選反例；它不接入 `lifecycle.py`，也不提供任意程序樹保證。詳見 [P0 說明](../../experiments/v2/README.md)。

> 最後更新：2026-11-08。新增 `experiments/v2/approvals.py`，以固定公開金鑰與驗證器驗收合成動作簽核。私有資料庫同一交易保存簽核文件、簽章與限期授權；broker 在當前前提下才可消耗。簽署測試用一次性金鑰；真人身分、金鑰治理及真實動作未接入。範圍見 [P0 說明](../../experiments/v2/README.md)。

> 最後更新：2026-11-08。新增 `experiments/v2/managed_fixture.py`，由可信父程序經固定啟動計畫與 guardian 連接單一 macOS 合成 worker。前提切換先封住舊 epoch，再回收並替換 worker，核對新前提摘要才啟用。合成結果由父程序 outbox 送往 broker／materializer。一鍵入口獨立呈現此探針，範圍與失敗案例見 [P0 說明](../../experiments/v2/README.md)。

> `experiments/v2/lifecycle.py` 經 `guardian.py` 啟動受管 worker。父程序獨占生命管道寫端，監護在 EOF 後以持有的 Popen 終止並 wait；它把回收證據寫到本次啟動專用的私有檔案。新父程序經 `reconcile` 核對原票據、計畫與檔案身分後可續作，`managed_fixture.py` 從初始前提或持久通知重建上下文。缺證據仍停止。Mac fixture 禁止 fork／spawn／signal；任意後代、Windows、真實人類入口未驗收。

> 2026-11-07 重連資格：新增 `experiments/v2/launcher.py` 與 `test_launcher.py`。可信 parent 產生 principal、保存重連票據雜湊與限期資源資格；broker 每次請求及恢復寫盤前重查。原始請求在送出前寫入私有 outbox，重啟沿用相同 bytes；缺漏不猜測重建。Mac 合成管道探針改用此資格層，尚非正式人類授權服務或完整工具 launcher。現行部署結構與程序不變。

> 2026-11-07 恢復覆核：materializer 的私有實驗庫新增 root 身分／資源映射綁定，拒絕以新設定接管舊事件；broker 重送寫入時重查當前資源權限，恢復 replace 後補目錄 fsync 才記 applied。反例與恢復測試同存 `test_recovery.py`。僅合成原型，舊無綁定實驗庫與搬機遷移尚不支援；現行部署結構不變。

> 2026-11-07 最新 P0 批次：新增 `experiments/v2/materializer.py` 與 `test_recovery.py`，在合成 POSIX 工作樹做 prepared→replace→applied 恢復；Lab 交易支援 savepoint，request 收據與內容／合成效果同交易，parent 可輪替 capability 恢復已知 principal。broker 的受隔離 agent 探針已接套用層，實測程序終止及失敗反例；不代表真實專案、Windows、斷電、多 writer 或外部服務 exactly-once 已驗收。下方前批「沒有 materializer」描述當時範圍；現行限制見 [P0 說明](../../experiments/v2/README.md)。

> 2026-11-07 P0 管道分權：新增 `experiments/v2/broker.py`（parent-only 管理能力、管道身分、資源與請求序號）、`broker_fixture.py`（受隔離合成 agent）及兩份測試；write／effect 的 epoch 在資料交易內檢查。一鍵入口彙整 broker 探針，報告缺項亦有負向測試。內容仍只存實驗庫，沒有正式工作樹 materializer、模型或工具接線；現行部署包及副本不變。

> 最後更新：2026-11-07。v2 P0 補 `supervisor.py` 與其負向測試，驗固定子程序的中止、上下文重建與 epoch 啟用；尚未接入模型／桌面工具。下列歷史日期與數字只對各自基準。

> 2026-11-06 v2 P0 結構：新增 [experiments/v2](../../experiments/v2/README.md) 的隔離契約、反例、Mac OS 邊界探針、F50 狀態機、成本量測及 [51 ID 現況索引](../../experiments/v2/status.json)；[tools/verify_v2.py](../../tools/verify_v2.py) 統一執行，既有驗證器加一項 P0 回歸並有報告負向測試。需求決策版本 2 補 F50；狀態權威由 HANDOFF 逐項移交到索引。這些只測合成資料，不部署；部署包仍是現行 22 檔權威，VERSION／skill／hook／接線不變。下方長結構登記是歷史，不取代本段。

> 2026-11-06 最新結構登記：新增 [需求實現規劃](project-bootstrap-implementation-plan.md)，根目錄 Markdown 總數 26；內容為技術棧選型與 50 項需求映射，不是已部署架構。部署包、skill、hook、接線與 VERSION 未變。
> 2026-11-06 需求文件分家：原 requirements 改名 history，新增 decision 為現行唯一權威；本 repo 共 25 份 Markdown。下方舊結構登記只描述當時狀態。
> 2026-11-06 最新結構登記：功能完整性複查（v3.9）與八項缺口全部納入（v3.10），**根目錄新增 [project-bootstrap-requirements-completeness-audit-2026-11-06.md](project-bootstrap-requirements-completeness-audit-2026-11-06.md)**，本 repo **24 份 Markdown**（前次 23）。[需求權威版](project-bootstrap-requirements-history.md)第 4 節**新增第九類「不該流出去的東西」與八條 F42–F49**，條目數 42→50；第 6 節留「已更正」指標並記 C01–C08→F42–F49 的對應；第 9 節新增兩個小節。本檔「這個 repo 刻意沒有的東西」那節**新增一條正式例外宣告**（F46 的落地方式，使用者 2026-11-06 決定）。驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，**未改檢查器**，不部署、不同步。⚠️ **本檔漏了一輪**：新增那份報告的 commit（`3d7b991`）按「改本檔的時機」就該同時改本檔，當時沒改——`verify_bootstrap.py` 只查本檔的日期標頭，查不到「根目錄多一個檔案而本檔沒登記」，所以這一類漏掉目前沒有守門人（它正是新納入的 F45 要擋的形狀，而 F45 還沒實作）。
>
> 2026-11-06 前次結構登記：使用者逐項定案第 6 節的五項待決，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3.4**（50 處定點修改，含第 4 節 28 項強度＋第 9 節新增「v3.3 的定案」小節）：第 4 節原標「待定」的 28 項最低強度全部填上（F9／F10／F18／F35／F37 阻擋，F6／F7／F8 留痕，其餘偵測）、F11(b) 保留為必要並定「不允許部分歸因」、F28 定為使用前＋立即通知、證據時效政策三條搬進 F40 驗收、強度表前的說明與第 7 節第 1 步的前置條件連帶改寫、第 6 節只剩 D8 專案數與四項待蒐集資料，兩處歷史「仍未定案」行加上版本指標（v3.3 與 v3.4 同日採納，日期分不出來）。入口摘要同步更新 AGENTS 與本檔。**改了檢查器一處**：`verify_bootstrap.py` 的「結構摘要一致性」原本用全行子字串 `'3.4'` 找 README prompt 那一列，本檔表格寫進 `v3.4` 就把需求文件那一列誤判成它（本輪當場 FAIL），改成認範本編號欄 `| 3.4 |`，並加一個反向保險（缺了那一列仍要被判出來）。本 repo 23 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，不部署、不同步。
>
> 2026-11-06 前次結構登記：使用者指示直接依[2214 最後審閱指令](project-bootstrap-requirements-final-review-2026-11-05-2214.md)的五項替換指令修改，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3.3**（18 處定點修改＋第 9 節新增「v3.2 的修正」小節與一筆勘誤）：第 3 節 D3 段的範圍句只限定理由與事故敘述、D3 改稱方案約束而非實作狀態報告；F13 理由改成明示轉述既有紀錄與 2026-10-30 的查證範圍；第 5 節把達成狀態切換規則收成唯一一份（逐需求 ID／子項、移交條件、未驗證也可移交、部分子項與新位置不可讀的處理），環境那一條改成區分工作假設與已查證觀測，「不滾動更新」改成按用途與內容判定並取消 append-only 豁免；第 7 節第 1 步改成引用第 5 節並補三種紙上核對輸入；第 8／9 節改用新界線（範圍不保證歷史事實正確、不免除勘誤責任、可在原處加「已更正」指標）。入口摘要同步更新 AGENTS 與本檔。本 repo 23 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，**未改檢查器**，不部署、不同步。
>
> 2026-11-05 前次結構登記：使用者採納 [1632 定向審閱](project-bootstrap-requirements-response-review-2026-11-05-1632.md)，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3.2**（12 處定點修改＋第 9 節新增「v3.1 的同日修正」小節）：第 3 節 D1／D2／D3 的理由、F16b 的分類括號、F11 共同邊界與 F13 理由各自定錨到當時的觀測；第 5 節新增三條歷史例外限制、第三類狀態（環境假設）、實作狀態逐項單一權威與逐 ID 切換，並把「HANDOFF 耐久性最低」限定在可見性；F11 驗收 (b) 新增四種現在就可判定的情境並禁止編造還原比例；第 7 節第 1 步新增三個接縫的移交責任；第 8／9 節各加一行整段範圍以取代逐句免責。根目錄新增[對 1632 的逐項回覆](project-bootstrap-requirements-response-review-reply-2026-11-05-2150.md)，其中更正 1620 把共現反例指在第 295 行（真正的反例是第 277 行）。本 repo 22 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，**未改檢查器**，不部署、不同步。

> 2026-11-05 前次結構登記：使用者採納 [1606 審閱](project-bootstrap-requirements-response-review-2026-11-05-1606.md)，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3.1**（9 處定點修改＋第 9 節新增「v3 的同日修正」小節）：第 5 節的現況禁令從「不含任何『現在有沒有』的判斷」改成「不承載持續更新的達成狀態」並允許帶日期的歷史事故、新增決策狀態與達成狀態的分工；第 3 節與 F28 驗收補日期；第 6／7 節移除 F11(b) 的實作判斷；F11 驗收 (b) 補「揭露未知不等於達成歸因」。根目錄新增[對 1606 的逐項回覆](project-bootstrap-requirements-response-review-reply-2026-11-05-1620.md)。本 repo 20 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，**未改檢查器**，不部署、不同步。

> 2026-11-05 前次結構登記：使用者採納第三輪審閱與逐項回覆的結論，[需求權威版](project-bootstrap-requirements-history.md)改成 **v3**（21 處定點修改＋新增第 9 節的改動理由；**未新增功能條目或編號**，但 F11(b) 新增了內容識別與還原程度揭露的要求，已明示為擴張）；根目錄新增[第三輪審閱的逐項回覆](project-bootstrap-requirements-response-review-reply-2026-11-05-1545.md)，是那次採納的理由記錄。本 repo 18 份 Markdown；驗證 52 項與骨架 22 檔不變，skill／hook／接線／`VERSION` 皆未動，不部署、不同步。

> 2026-11-05 前次結構登記：新增 [第三輪需求審閱](project-bootstrap-requirements-response-review-2026-11-05-0927.md)，逐項核對 Opus 2310 回覆；尚未採納、不部署、不同步。17 份 Markdown，驗證 52 項與骨架 22 檔不變。

> 2026-11-04 最新結構登記：新增 [再評估的逐項回覆](project-bootstrap-requirements-response-reply-2026-11-04-2310.md)——對 S1–S6 與六條整體校正的判定、理由與建議措辭，**尚未採納**；需求權威版、skill／hook／接線／`VERSION` 皆未動。本 repo 16 份 Markdown；驗證仍 52 項，骨架仍 22 檔。不部署、不同步。
>
> 2026-11-04 前次結構登記：報告檔名已依使用者要求補上原提交時分 2230，引用同步更新；新增 [需求修訂再評估](project-bootstrap-requirements-response-2026-11-04-2230.md)，核對 Opus 回覆與修訂，屬未採納審閱快照，不部署、不同步。本 repo 15 份 Markdown；驗證仍 52 項，骨架仍 22 檔。下列舊登記保留歷史理由。

> 2026-11-04 本次結構登記：使用者採納需求定義的 v2 修訂，[project-bootstrap-requirements-history.md](project-bootstrap-requirements-history.md) 改成 v2 全文、原 v1 內容刪除（在 git 歷史，基準 `81a8cff`）；中途那個帶版號的臨時檔已 `git mv` 到權威路徑並不再存在——**檔名不帶版號**，否則版號本身會腐化，而 `AGENTS.md` 與審閱意見檔的連結會斷。根目錄淨增一檔（審閱回覆），本 repo 14 份 Markdown；驗證項仍 52 項、骨架仍 22 檔，skill／hook／接線／VERSION 皆未動。前次登記：根目錄新增 `project-bootstrap-requirements-v2.md`（已不存在，已搬到權威路徑） 與 [project-bootstrap-requirements-review-reply-2026-11-04.md](project-bootstrap-requirements-review-reply-2026-11-04.md)——前者是依 Q1–Q7 逐項評估修訂的需求草案（新增 F40 證據時效、「強度」詞彙與 9 項驗收區塊，收緊 D1 與 F11、F13、F26、F28，刪掉「6 個專案時 F30／F31 可以不要」），**尚未採納，權威仍是 v1，採納後應取代並刪除 v1**；後者是對審閱意見的逐項回覆與同意／不同意的理由。兩者都不部署、不同步，驗證項仍 52 項、骨架仍 22 檔，skill／hook／接線／VERSION 皆未動。前次登記：新增需求審閱意見 project-bootstrap-requirements-review-2026-11-04.md，供下一棒討論，尚未採納、不部署、不同步。原登記：根目錄新增 [project-bootstrap-requirements-history.md](project-bootstrap-requirements-history.md)——與使用者逐項定案的功能需求（F1–F39）與前提決定（D1–D8），是「要什麼」的唯一家；現況對照與工具評估尚未做，刻意不寫進它裡面。不部署、不同步，驗證項仍 52 項、骨架仍 22 檔，skill／hook／接線／VERSION 皆未動；`AGENTS.md` 的開工段加一段指向它。前次 2026-11-03：驗證新增「同步升級 mode」與「結構摘要一致性」，共 52 項、骨架仍 22 檔。同步器原子替換前複製既有檔案權限；否則 POSIX 的可執行 wrapper 會隨 inode 替換失去 x bit。Windows 只驗呼叫與失敗契約，POSIX 分支另驗 0755／0640、直接執行與 Git mode diff。結構摘要區分 Claude import／Gemini 文字指標與收工／開工 prompt。只改工具及 ARCHITECT 範本，不改 skill／hook，VERSION 與 source 標記不跳；ARCHITECT 是專案實例，不自動覆蓋既有專案。

> **本檔＝結構的唯一權威**：`project-bootstrap` 由什麼組成、每樣東西的家在哪、改哪裡會影響到什麼。
> 最後更新：2026-11-08（F46 文件設定同組情境：驗證 58 項，骨架 22 檔，未改部署包與版本；前次：需求權威版採納 **v3.4**：使用者定案五項待決——第 4 節 28 項強度全部填上、F11(b) 保留且不允許部分歸因、F28 使用前＋立即通知、證據時效政策進 F40 驗收、第 6 節只剩 D8 與四項待蒐集資料；檢查器「結構摘要一致性」改成認範本編號欄並加反向保險（`v3.4` 這種版本號曾讓它誤判）；23 份 Markdown，骨架與驗證項不變。前次：需求權威版採納 v3.3 修正：18 處定點修改＋第 9 節新增「v3.2 的修正」小節與 append-only 豁免的勘誤，入口摘要同步更新 AGENTS 與本檔；23 份 Markdown，骨架與驗證項不變，未改檢查器。前次：新增 2214 最後審閱指令，23 份 Markdown；骨架與驗證項不變。前次：需求權威版採納 v3.2 修正並在第 9 節新增 v3.1 的同日修正小節，根目錄新增對 1632 的逐項回覆 project-bootstrap-requirements-response-review-reply-2026-11-05-2150.md，22 份 Markdown，驗證項與骨架不變。前次：新增 1632 定向審閱，21 份 Markdown，骨架與驗證項不變。前次：需求權威版採納 v3.1 修正並在第 9 節新增同日修正小節，根目錄新增對 1606 的逐項回覆 project-bootstrap-requirements-response-review-reply-2026-11-05-1620.md，20 份 Markdown，驗證項與骨架不變。前次：新增 1606 審閱回覆，19 份 Markdown，驗證項與骨架不變。前次：需求權威版採納 v3 修訂並新增第 9 節的改動理由，根目錄新增第三輪審閱的逐項回覆 project-bootstrap-requirements-response-review-reply-2026-11-05-1545.md，18 份 Markdown，驗證項與骨架不變。前次：根目錄新增再評估的逐項回覆 project-bootstrap-requirements-response-reply-2026-11-04-2310.md，16 份 Markdown，未採納、不部署、不同步，驗證項與骨架不變。前次：需求定義採納 v2 修訂：project-bootstrap-requirements-history.md 改成 v2 全文、原 v1 刪除，帶版號的臨時檔已搬到權威路徑；根目錄淨增審閱回覆一檔，14 份 Markdown，驗證項與骨架不變。前次：根目錄新增需求定義 v2 草案 project-bootstrap-requirements-v2.md 與審閱回覆 project-bootstrap-requirements-review-reply-2026-11-04.md，兩者未採納、不部署、不同步，驗證項與骨架不變。前次：根目錄新增功能需求定義 project-bootstrap-requirements-history.md：F1–F39 與 D1–D8，不部署、不同步，驗證項與骨架不變。前次：2026-11-03 新增第二輪複審快照 project-bootstrap-reaudit-2026-11-03.md；接棒入口要求先讀，不部署、不同步，驗證項與骨架不變。前次：2026-11-02 F13／F16 新增同步範圍與部署生命週期，第 49／50 項；骨架仍 22 檔。前次：F12 新增第 48 項接力協調邊界；原子 claim 未實作。前次：F10 新增第 47 項核心與實例優先序；同步列人工遷移需求。前次：F11 新增第 45／46 項協作狀態契約與 Git 異常提示，版本 .5。前次：F07 新增第 44 項「ZIP 發布門檻」：SKIP 預設不打包，顯式調試包附 UNVERIFIED.json；部署範本與版本未改。前次：根目錄新增 project-bootstrap-audit-progress.md：查核報告 16 條的處理進度（已修 9／未修 7），寫給下一輪接棒的另一個模型；查核報告是凍結快照，狀態不寫進它裡面，所以這是新的一個家。`AGENTS.md` 的開工段加一行要求先讀它。不部署、不同步，制度與測試未改。前次：修掉查核報告的 F04 與 F08：`verify_state.py` 改成每項檢查回傳 PASS／FAIL／ERROR／SKIP／NOT_CONFIGURED，FAIL／ERROR 讓結束碼非零、`--strict` 連 SKIP 都不放行，輸出過一層祕密遮罩；`check_docs.py` 新增第 7 項「交接快照」（存在、必要欄位與章節、80 行上限），連結檢查改成先塗白程式碼並解析 title／角括號，對外名稱改成「文件與交接快照的機械檢查」。新增第 42 項「verify_state 失敗訊號」與第 43 項「交接快照檢查」，Windows 驗證為 **43 項**、骨架仍為 **22 檔**。3.14／3.15 的 `source:` 標記跳到 `v2026-11-02.3`；`SKILL.md` 未動，`VERSION` 不跳。🔴 3.14 是同步對象而 `VERSION` 沒跳，落後偵測不會提示，需手動同步六個專案。前次：修掉查核報告的 F14 與 F15：兩支維護工具改用包著 `open(..., newline='')` 的 `read_lf`／`write_lf`，檔頭宣告並檢查 `MIN_PY = (3, 8)`；五處「已修正的主張又復活」一起修（README 範本說其他工具沒有 skill 機制、第 6 節的序號算法與鐵律 2 不同、`verify_state` 被寫成有憑證才跑、prompt 的 A／B 跟 skill 相反、可攜層與三層的過度保證）。新增第 40 項「Python 版本下限」與第 41 項「已修正的主張沒復活」，Windows 驗證為 **41 項**、骨架仍為 **22 檔**。`SKILL.md` 與帶 `source:` 標記的範本都沒動，所以 `VERSION` 與標記都不跳、`sync_project.py` 零改動，六個專案沒有新的同步債。前次：修掉查核報告的 F02 與 F03：`sync_project.py` 的所有權從「整組」降到「handler」，同組的專案自訂 hook 不再被靜默刪除，matcher 衝突與重複／異常分組改成拒絕並說明；同步改成 `Plan` → preflight → `apply_plan`，任一項算不出來就零寫入，失敗與不存在的目標非零退出。新增第 38 項「同步安全」，Windows 驗證為 **38 項**、骨架仍為 **22 檔**。`sync_project.py` 不部署，所以沒有 `source:` 標記要跳、沒有副本義務，`VERSION` 不動。前次：修掉查核報告的 F01 與 F09 兩個錯誤安全訊號：兩支 hook 與 `check_docs.py` 的「工作中」判讀從子字串改成精確解析，版本偵測改成判方向並在領先時勸退同步；`SKILL.md` 未動、`VERSION` 刻意不跳，3.10 與 3.14 的 `source:` 標記跳到 `v2026-11-02.2`。「工具欄（負向測試）」擴成「工作中欄位格式（負向測試）」，共用情境表加 5 項，版本偵測加 2 項；Windows 驗證仍為 **37 項**、骨架仍為 **22 檔**。🔴 六個專案的副本尚未同步，而落後的副本正是會印錯誤綠燈的那一版。前次：使用者要求交棒攜帶查核報告，根目錄新增 project-bootstrap-audit.md：查核快照、不部署、不同步；既有制度與測試未改。前次：新增「續聊狀態與計數」程序契約檢查與負向測試，Windows 驗證為 **37 項**；骨架仍為 **22 檔**，交棒計數的家是 session 標題，不新增 repo 歷史檔。前次 2026-11-01：本輪恢復 HANDOFF 為當下交接快照，新增「本 repo 交接狀態」與負向測試，Windows 驗證為 **36 項**；前一輪新增 Codex Windows 啟動器與四項驗證，骨架為 **22 檔**、Windows 驗證為 **35 項**；`sync_project.py --codex-only` 只更新 Codex 接線與依賴的啟動器。原有紀錄：新增「ZIP 說明指標」與「跨工具過期敘述」兩項檢查：ZIP 的工具差異只指向部署包，已知過期散文由回歸測試守住；原有 29 項加到 31 項。修正本檔拓撲中的「2.0 未測」，骨架仍是 21 檔，skill／hook 與 VERSION 均未改。前一次是同日：本 repo 自己多一份 Codex 接線 `.codex/hooks.json`——指向它自己那支 `repo-git-check.sh`，**不是 3.17 的副本**；`sync_project.py` 加一道「拒絕把本 repo 自己當目標」的防護（兩份接線跟 `WIRING` 同名，覆蓋下去會指到不存在的 `git-freshness.sh`）；`verify_bootstrap.py` 從 27 項變 **29 項**（「本 repo settings.json」擴成「本 repo 兩份接線」、新增「sync 拒絕本 repo」）。**骨架仍是 21 檔**，但這次動到範本 3.10（多印一行開工改名提示），所以它的 `source:` 標記跳到 `v2026-11-01`；`SKILL.md` 沒動，`VERSION` 刻意不跳。前一次是同日第二次：`verify_bootstrap.py` 多一項「README 跨工具表一致性」：README 那張跨工具表是部署包那一張的轉述，而保鮮期只守部署包那一份，於是它可以無聲分岔；加的當下就抓到一處。**只動腳本與敘述，骨架仍是 21 檔，範本與 `sync_project.py` 都沒動。**前一次是 2026-10-31 同日第五次：**補上 Antigravity CLI 的 hook 接線，端到端實測過**——新增 3.18 `.claude/hooks/ag-wrap.sh`（轉接層）、3.19 `.agents/ag-hook.cmd`（Windows shim，找 Git Bash）、3.20 `.agents/hooks.json`（只接 `SessionStart`），舊 3.18「其他 skills 慣例」順延成 3.21；`verify_bootstrap.py` 加「Antigravity 接線」情境，`sync_project.py` 的 `WHOLE` 多兩份並新增 `AG_WIRING`（只換 `handoff-git-check` 那一個頂層 key）。骨架從 18 檔變 21 檔。同日第四次：**在 Antigravity CLI `1.4.7` 上把 hook 實測完**——`agy -p` headless 量到專案層 `.agents/hooks.json` 會讀、六個事件全部觸發，cwd 是 `.agents/`；相對路徑可用、絕對路徑才脆弱（`command` 照空白切 token、不解析引號），所以**上一次那個「骨架的不變量可能害探針測不出東西」的推論被推翻**，鐵律 5 跟它沒有衝突；`PreToolUse` 不明確回 `allow_tool` 就等於拒絕。骨架仍不附接線，理由換成「Windows 缺一層 `.cmd` shim」。只改敘述，接線／`verify_bootstrap.py`／`sync_project.py` 都沒動。同日第三次：**重新界定 Antigravity 那輪探針的範圍**——Antigravity 是四個獨立 surface（2.0 桌面 App／CLI／IDE／SDK），探針只覆蓋 IDE `1.107.0`，所以「這個工具沒有 hook 這一層」改寫成「骨架還沒附接線，2.0 與 CLI 沒測」；全域路徑 `~/.gemini/<applicationName>/hooks.json` 是跟著 surface 走的，`antigravity-ide` 那一份不能一般化成整個產品。只改敘述，接線不動、`verify_bootstrap.py` 與 `sync_project.py` 不動。同日第二次：**部署包移除 Antigravity 的 hook 接線**——舊 3.18 `.claude/hooks/antigravity-wrap.sh` 與舊 3.19 `.agents/hooks.json` 刪除，舊 3.20「其他 skills 慣例」遞補回 3.18；`verify_bootstrap.py` 移除「Antigravity 轉接層」六情境，`sync_project.py` 的 `WHOLE`／`WIRING` 各少一份。原因是實測：Antigravity IDE `1.107.0` **不讀專案層的 `.agents/hooks.json`**，那兩個檔部署出去也不會被觸發。同日稍早才加上它們，當天就被自己的驗收條件判出局。前一次是 2026-10-30 同日第二次：三平台能力重查後，`extract()` 的抽取規則從「第一個區塊」改成「區塊依序對應檔名」、`sync_project.py` 把 `CLAUDE.md` 從 `INSTANCE` 搬到 `PARTIAL`、`verify_bootstrap.py` 加「跨工具表保鮮期」、副本拓撲裡 `.agents/skills/` 的角色改變）
>
> **什麼時候改**：只有**結構**變動才改——根目錄多／少一個檔案、部署包增刪一節範本、`verify_bootstrap.py` 增減檢查項、副本拓撲改變。
> 制度內容本身怎麼寫（鐵律的措辭、skill 的步驟）**不要動這一份**，那些的家在 [AGENTS.md](../../AGENTS.md) 與部署包裡。
