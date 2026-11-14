# v2 執行屏障模組（封存）

> 最後更新：2026-11-14（建立：需求決策書 v3 Q33，使用者決定封存）

這裡是 v2 為了「自己造執行屏障」寫的原型程式與它們的測試。需求決策書 v3 的 D9 把執行屏障交給工具原生的權限與沙箱，這些模組從 2026-11-13 起凍結；2026-11-14 依 [Q33](../../project-bootstrap-requirements-decision-v3.md) 從 `src/` 與 `tests/` 搬來這裡，內容一個字沒改。

**不再執行**：`pytest` 只收 `tests/`，`tools/verify_v2.py` 不再跑這裡的探針與同 UID 反例，`verify_bootstrap.py` 的「v2 P0 原型回歸」也不算這裡的測試。git 歷史完整保留（用 `git mv` 搬的）。

## 搬了什麼

- `src/project_bootstrap/`：`launcher`、`supervisor`、`isolation`、`vm_probe`（含 `vm_runner.swift`、`vm_guest_init.sh`、`vm_managed_worker.sh`）、`broker_fixture`、`managed_fixture`、`materializer`、`lifecycle`、`guest_runs`、`crash_release`、`tree_probe`、`guardian`、`feasibility`。
- `tests/`：上面這些模組的測試，加上 `test_recovery`、`test_host_crash`、`test_approvals`。
- `mutants.json`：從 `src/project_bootstrap/mutants.json` 移來的十組變異，路徑寫的是封存前的位置；另加一組 `broker.py` 的兩個變異——`broker.py` 留在 `src/`，但這兩個只有封存的測試擋得住（2026-11-14 重跑 `tests.test_broker` 那組時存活）。

## 沒搬的，以及為什麼

- **`broker.py` 留在 `src/`**：凍結中的簽章發布鏈（`approvals` → `release` → `package`，接到現役的 `build_package.py`、`migrate_project.py`、`install_package.py`）還 import 它。`release`、`pointer`、`channel` 只用 `Broker.unique_keys`，`approvals` 則建在 Broker 上；使用者 2026-11-14 選了「broker 留著」。
- **`approvals.py` 留在 `src/`，但測試搬來這裡**：`release` 只用它的 `VERIFIER` 常數；它的測試全靠 `launcher` 當授權方，`launcher` 封存之後就跑不起來。所以 `approvals.py` 現在在 `src/` 裡沒有測試。

## 要重新跑的話

這些模組 import 的是 `project_bootstrap.*`，而套件的 `__init__.py` 在 `src/`，Python 不會把兩個目錄併成同一個套件。所以在暫存目錄裡拼回封存前的樣子再跑（從 repo 根目錄執行）：

```bash
T=$(mktemp -d) && mkdir -p $T/src $T/tests && cp -R src/project_bootstrap $T/src/ && cp archive/v2-barrier/src/project_bootstrap/* $T/src/project_bootstrap/ && cp archive/v2-barrier/tests/*.py $T/tests/ && touch $T/tests/__init__.py && cd $T && PYTHONPATH=src:. python3 -X utf8 -m unittest discover -s tests -t .
```

2026-11-14 封存當天用這個做法抽跑 `test_guardian`、`test_supervisor`、`test_launcher`、`test_guest_runs` 四支，55 個測試通過；其餘沒跑（VM 與 macOS 沙箱相關的要特定環境）。
