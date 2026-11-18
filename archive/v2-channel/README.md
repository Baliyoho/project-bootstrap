# v2 簽章發布通道（封存）

> 最後更新：2026-11-18（建立：需求決策書 v3 Q46，使用者決定封存）

v2 時期試做的「由 CI 簽章發布正式包、專案只留指標」整條通道：模組、四支工具、測試、發布用的 GitHub workflow 與根公鑰清單。需求決策書 v3 第 5 節已把這條通道凍結；2026-11-18 起它不留在 main（Q46），用 `git mv` 搬到這裡，內容不改。

- `src/project_bootstrap/`：`package`、`pointer`、`channel`、`distribute`、`publish`、`release`、`approvals`、`broker`、`contracts`、`evidence`、`ingest`、`migrate`、`selftest` 十三個模組。
- `tools/`：`build_package.py`、`release_package.py`、`install_package.py`、`migrate_project.py`。
- `tests/`：上面這些模組與工具的測試（16 支）。
- `.github/workflows/release.yml`：原本由 `release-request/<channel>` tag 觸發的發布 workflow。放在這裡 GitHub 不會執行。
- `src/kit/release-keys.txt`：發布用的根公鑰清單。

origin 上已發出的 `channel/beta/1`–`3` 三個 tag 不撤回。封存時查過：發布者那台 Mac 上的專案沒有一個使用 `.bootstrap/pointer.json`，其他機器沒有查。

這裡的程式不執行，main 上的程式、測試與現況索引都不引用它（`verify_bootstrap.py`「封存原件」擋）。平常不讀，要回溯先經使用者同意。要重新研究，在暫存目錄把 `src/`、`tests/`、`tools/` 拼回一個 checkout 再跑；不要搬回 main 而不先改需求決策書。
