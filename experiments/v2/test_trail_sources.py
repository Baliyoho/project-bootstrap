"""F6／F7／F8 adapters on synthetic documents shaped like the real ones."""

import unittest

from experiments.v2.trail import check_decisions, check_roadmap, rejected_routes
from experiments.v2.trail_sources import decisions_from_book, roadmap_from_plan, routes_from_plan

BOOK = '''# 決策書

> 決策版本：2。

## 6. 待決事項

1. 這不是決策。理由：不同節。

## 7. 本次整理的決策與理由（2026-11-06）

1. 改名 history。理由：舊說法不應要求每次還原。
2. 補 F50。理由：原清單漏列。

## 8. 之後

1. 不屬於第七節。理由：在別節。
'''
PLAN = '''# 規劃

### 3.4 三條整體路線

| 路線 | 優點 | 代價 | 結論 |
|---|---|---|---|
| 延續部署包 | 遷移少 | 維護成本留在原處 | 適合作過渡，不作終局 |
| 小型核心 | 保留已驗行為 | 自行維護 | 推薦；以反例作門檻 |
| 全換工具 | 工作流完整 | 缺授權契約 | 沒有足夠理由 |
| 壞列 | 只有 | 三格 |

## 4. 其他

## 7. 分期交付

| 階段 | 工作 | 退出 | 粗估 |
|---|---|---|---|
| P0 可行性 | 證據索引 | 失敗就修架構 | 3 日 |
| P1 模組化 | src／tests | 等價重建 | 5 日 |
| 合計 | 全部 | 無 | 8 日 |

### 過渡期間

| 不是 | 階段 | 表 | 喔 |
|---|---|---|---|
| P9 假的 | x | y | z |
'''


class SourceTests(unittest.TestCase):
    def test_book_items_become_decisions_with_rationale_date_and_baseline(self):
        decisions = decisions_from_book(BOOK)
        self.assertEqual([(d['id'], d['title'], d['rationale'], d['date'], d['baseline'])
                          for d in decisions],
                         [('book-7.1', '改名 history。', '舊說法不應要求每次還原。', '2026-11-06',
                           '決策書決策版本 2'),
                          ('book-7.2', '補 F50。', '原清單漏列。', '2026-11-06', '決策書決策版本 2')])
        self.assertEqual(check_decisions(decisions)[0], [])

    def test_item_without_rationale_label_is_reported_by_the_checks(self):
        book = BOOK.replace('補 F50。理由：原清單漏列。', '補 F50，原清單漏列。')
        findings, _ = check_decisions(decisions_from_book(book))
        self.assertEqual(findings, [('book-7.2', 'decision-missing-rationale')])

    def test_missing_section_date_or_version_is_not_silently_complete(self):
        self.assertEqual(decisions_from_book('# 空\n'), [])
        undated = BOOK.replace('（2026-11-06）', '').replace('> 決策版本：2。\n', '')
        findings, _ = check_decisions(decisions_from_book(undated))
        self.assertEqual(sorted(set(code for _, code in findings)),
                         ['decision-date-invalid', 'decision-missing-baseline'])

    def test_route_table_gives_choice_and_rejected_routes_with_cost(self):
        routes = routes_from_plan(PLAN, '2026-11-06')
        self.assertEqual(check_decisions(routes)[0], [])
        self.assertEqual(routes[0]['title'], '小型核心')
        _, by_id = check_decisions(routes)
        self.assertEqual({(r['option'], r['reason']) for r in rejected_routes(by_id)},
                         {('延續部署包', '維護成本留在原處；適合作過渡，不作終局'),
                          ('全換工具', '缺授權契約；沒有足夠理由')})

    def test_route_table_without_exactly_one_recommendation_yields_nothing(self):
        self.assertEqual(routes_from_plan(PLAN.replace('推薦；', '可行；'), 'd'), [])
        self.assertEqual(routes_from_plan(PLAN.replace('沒有足夠理由', '推薦也行'), 'd'), [])

    def test_phase_table_gives_milestones_and_ignores_other_tables(self):
        milestones = roadmap_from_plan(PLAN, {'P0': 'active'})
        self.assertEqual([(m['id'], m['goal'], m['status']) for m in milestones],
                         [('P0', '證據索引', 'active'), ('P1', 'src／tests', 'planned')])
        self.assertEqual(check_roadmap(milestones, []), [])
        self.assertEqual(check_roadmap(roadmap_from_plan('# 空\n', {}), []),
                         [('roadmap', 'no-open-milestone')])


if __name__ == '__main__':
    unittest.main()
