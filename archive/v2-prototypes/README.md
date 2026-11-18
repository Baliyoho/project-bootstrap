# v2 原型（封存）

> 最後更新：2026-11-18（建立：需求決策書 v3 Q46，使用者決定封存）

v2 時期為各需求 ID 寫的合成原型。它們沒有接進任何工具或程序，只有自己的測試在跑；2026-11-18 起不留在 main（Q46），用 `git mv` 搬到這裡，內容不改。

- `src/project_bootstrap/`：`batch`、`bypass`、`campaign`、`confluence`、`decisions`、`doctor`、`facts`、`gitclaim`、`impact`、`install`、`inventory`、`lines`、`policy`、`preflight`、`presence_probe`、`readonly`、`session`、`state`、`status_card`、`baseline` 二十個模組。其中 `impact`（F31）與 `inventory`（F39）對應的需求在 v3 已退役。
- `tests/`：上面這些模組的測試（19 支），含 `test_contracts.py`（測的是 `contracts` 與 `session`；`contracts` 封存在 `archive/v2-channel/`）。

有些模組 import 封存在 `archive/v2-channel/` 的 `contracts`、`release` 等模組，單獨拼回會缺檔；要跑就把兩處一起拼回暫存目錄。

這裡的程式不執行，main 上的程式、測試與現況索引都不引用它（`verify_bootstrap.py`「封存原件」擋）。平常不讀，要回溯先經使用者同意。
