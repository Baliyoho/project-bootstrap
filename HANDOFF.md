# HANDOFF — 工作交接狀態

- **交接時間**：2026-11-07 08:19（+08；模式 C 中途安全點，未釋出 writer）
- **交棒者**：Codex CLI ／ `baliyohodeMini`（v2 P0 第一批原型；本聊天仍工作中）

## 任務目標

依使用者已授權方向重做 project-bootstrap v2，先證明強保障架構及接棒成本，再逐批遷移。
需求以 [決策書](project-bootstrap-requirements-decision.md) 決策版本 2 為準，分期以 [實現規劃](project-bootstrap-implementation-plan.md) 為準。
**51 ID 與 F11／F13／F43 子項狀態已全部移交 [v2 現況索引](experiments/v2/status.json)**；原狀態來源 `fdc0bbd:HANDOFF.md`，每列有範圍、來源、證據入口與未知。索引不可讀時停止判定，不從舊快照恢復權威。

## Git 狀態

- Repo：public `Baliyoho/project-bootstrap`；穩定分支 `main`。
- **待續分支**：`codex/project-bootstrap_v2`；從 `main @ 40a2d02` 建立，繼續在此分支，不重新從 main 開始。
- **工作中**：`baliyohodeMini` ／ `Codex CLI` ／ `㊣　26110621｜重建骨架v2｜工作中｜交棒0次`，2026-11-06 21:17 (+08) 開工
- **骨架版本**：`2026-11-03`
- 本機能力：macOS、Python 3.15、bash 3.2；未驗 Windows／Linux。本輪未改 main、部署包、skill、hook、接線或 VERSION。

## 已完成

- 補登必要需求 F50、51 ID 映射與狀態移交；F50 狀態機和改名 adapter 契約已有正常／負向案例，未接真實事件自動化。
- [P0 原型](experiments/v2/README.md)：內容／事件交易、授權範圍、掃描後不可變候選、epoch／通知與 ACK、執行中子程序停止及上下文替換。
- 三個繞過反例可重現；Mac OS 子程序隔離機制可驗，但沒有把目前桌面 App／MCP 包入隔離。完整需求判定見索引。
- `tools/verify_v2.py` 產生可重跑 JSON，含來源 digest、取得時間、環境、字元與驗證器耗時；已接回原一鍵入口，沒有啟用驗證快取或跳過 A4。

## 未完成／下一步

1. P0 尚未退出：將可信 launcher／管理端與 agent 分權，確立正式內容只能經代理變更的執行介面；原型管理方法不能直接暴露給 agent。
2. 接續合成 supervisor，補可控執行介面的恢復與跨機通知；模型／桌面工具實際停止、上下文重建仍需另驗，不拿 ACK 冒充理解。
3. 鎖定真正採用的外部元件版本／LICENSE／digest；驗 Windows／Mac 門檻，之後才開始 P1 來源／測試模組化與短入口。
4. F22 仍超過 12,000 字元；完整接棒時間與 token 未量。短入口、按需理由、驗證分層須配合證據依賴／失效，不能直接省 A4。
5. 舊部署限制保留：Windows hook 同步、Mac Codex 真實注入、R01–R09 邊界獨立複審仍待做；F41 七缺口維持想要。逐項達成不在此複製。

## 地雷與注意事項

- 原型與回歸成功不等於必要強保障通過；`--require-ready` 預期 exit 2，不能改成綠燈湊完成。
- 所有原文、capability、假禁入值與 Git object 只在合成暫存 fixture；不得換成真實敏感資料。0600 不是同 UID 身分隔離。
- `sandbox-exec` 已 deprecated，只作 OS 機制實驗；沒有採作正式 launcher 或驗過逃逸。
- 實作授權不包含外部部署、付費／額外模型探針、改遠端保護或 merge main。額外模型先授權且只用訂閱額度。
- 現行 A／B／C 照跑，原子 claim 另案、Antigravity IDE 不重開、來源三項例外不撤銷。

## 服務查證與期望快照

- 本輪 `python3 -X utf8 tools/verify_bootstrap.py`：exit 0，52 項通過、無 skip；含 30 個 v2 測試。最終暫存內容經同入口驗證；本機 JSON 證據在 gitignored `dist/v2-p0-evidence.json`，跨機請重跑取得。
- `python3 -X utf8 tools/verify_v2.py --require-ready`：P0 回歸正常、強保障未就緒（exit 2）；本機 Mac 隔離與合成上下文替換可重跑。
- 無 verify_state.py／check_docs.py，依 AGENTS 用替代入口；接線未改，信任重審不適用。尚未呼叫額外模型、安裝候選或部署專案。

## 懸置事項（AI 勿自行處理）

- 不需重新詢問是否開始 v2；當下停點是 P0 架構與整合缺口，不是任務撤回。
- 本次為模式 C 安全點，owner 保留本聊天；要換聊天／機器仍須完成 B 模式釋出。
