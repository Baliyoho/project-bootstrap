"""F44 pending decisions and F34 declared exceptions stay registered and visible."""

import copy
import datetime
import unittest

from project_bootstrap.decisions import check_decisions, check_exceptions, render

TODAY = datetime.date(2026, 11, 9)
DELEGATION = {'id': 'G1', 'granted_by': 'user', 'source': '決策書第 7 節',
              'scope': ['F22', 'F24']}
DECISIONS = [
    {'id': 'D1', 'question': '人工退場以什麼作可信真人核准？', 'affects': ['F42', 'F13'],
     'options': ['硬體金鑰簽章', '另一台裝置確認'], 'status': 'pending'},
    {'id': 'D2', 'question': '接棒時間上限？', 'affects': ['F22'], 'status': 'decided',
     'decided_by': 'ai', 'rationale': '原稿無法判斷通過', 'source': '決策書第 4 節'},
    {'id': 'D3', 'question': 'Antigravity IDE 要不要追？', 'affects': ['F47'],
     'status': 'decided', 'decided_by': 'user', 'source': 'AGENTS.md 2026-10-31'},
]
TASKS = [{'id': 'T1', 'waits_for_decision': 'D1'}, {'id': 'T2'}]
EXCEPTION = {'id': 'X1', 'what': '本 repo 不裝 handoff skill', 'authorized_by': '使用者',
             'source': 'ARCHITECT「刻意沒有的東西」', 'scope': 'project-bootstrap 本身',
             'reason': '來源不是交接中的專案', 'recheck': {'when': 'F46 驗收時'}}


class DecisionTests(unittest.TestCase):
    def check(self, change=None):
        decisions, delegations, tasks = (copy.deepcopy(DECISIONS), [dict(DELEGATION)],
                                         copy.deepcopy(TASKS))
        if change:
            change(decisions, delegations, tasks)
        return check_decisions(decisions, delegations, tasks), decisions

    def test_registered_decisions_are_clean_and_pending_ones_are_listed(self):
        findings, decisions = self.check()
        self.assertEqual(findings, [])
        view = render(decisions, [EXCEPTION], findings)
        self.assertIn('- D1：人工退場以什麼作可信真人核准？（影響 F42、F13；'
                      '選項 硬體金鑰簽章 ／ 另一台裝置確認）', view)
        self.assertNotIn('D2', view)
        self.assertIn('無登記中的待決事項。', render([], [], []))

    def test_ai_may_not_settle_outside_a_user_delegation(self):
        cases = (
            (lambda d, g, t: d[1].update(affects=['F22', 'F42']), ('D2', 'ai-decided-without-delegation')),
            (lambda d, g, t: g.clear(), ('D2', 'ai-decided-without-delegation')),
            (lambda d, g, t: d[1].update(rationale=' '), ('D2', 'delegated-without-rationale')),
            (lambda d, g, t: d[1].update(decided_by='model'), ('D2', 'decider-unknown')),
            (lambda d, g, t: d[2].pop('source'), ('D3', 'decided-without-source')),
            (lambda d, g, t: d[2].update(status='done'), ('D3', 'decision-status-invalid')),
        )
        for change, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(self.check(change)[0], [expected])
        for broken in ({'granted_by': 'ai'}, {'source': ''}, {'scope': []}, {'scope': 'F22'}):
            with self.subTest(delegation=broken):
                findings, _ = self.check(lambda d, g, t: g[0].update(broken))
                self.assertEqual(findings, [('G1', 'delegation-invalid'),
                                            ('D2', 'ai-decided-without-delegation')])

    def test_delegated_question_is_not_parked_for_the_user(self):
        findings, _ = self.check(lambda d, g, t: d.append(
            {'id': 'D4', 'question': '批次上限？', 'affects': ['F24'],
             'options': ['20', '50'], 'status': 'pending'}))
        self.assertEqual(findings, [('D4', 'delegated-but-waiting-for-user')])

    def test_pending_question_cannot_hide_in_a_task_or_lack_options(self):
        cases = (
            (lambda d, g, t: t[1].update(waits_for_decision='D9'),
             ('T2', 'waits-for-unregistered-decision')),
            (lambda d, g, t: t[1].update(waits_for_decision='D3'),
             ('T2', 'waits-for-settled-decision')),
            (lambda d, g, t: d[0].pop('options'), ('D1', 'pending-without-options')),
            (lambda d, g, t: d[0].update(question=''), ('D1', 'decision-incomplete')),
            (lambda d, g, t: d[0].update(affects=[]), ('D1', 'decision-incomplete')),
            (lambda d, g, t: d.append({'id': 'D1'}), ('D1', 'duplicate-or-missing-id')),
        )
        for change, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(self.check(change)[0], [expected])
        findings, decisions = self.check(lambda d, g, t: d[0].pop('options'))
        self.assertIn('（⚠ pending-without-options）', render(decisions, [], findings))


class ExceptionTests(unittest.TestCase):
    def test_complete_exception_is_listed_as_not_a_pass(self):
        self.assertEqual(check_exceptions([EXCEPTION], TODAY), [])
        view = render([], [EXCEPTION], [])
        self.assertIn('## 已宣告例外（宣告不等於通過）', view)
        self.assertIn('X1：本 repo 不裝 handoff skill；授權 使用者（ARCHITECT「刻意沒有的東西」）；'
                      '範圍 project-bootstrap 本身；理由 來源不是交接中的專案；重檢 F46 驗收時', view)

    def test_missing_fields_and_due_recheck_are_flagged(self):
        for key in ('what', 'authorized_by', 'source', 'scope', 'reason'):
            with self.subTest(key=key):
                self.assertEqual(check_exceptions([dict(EXCEPTION, **{key: ''})], TODAY),
                                 [('X1', 'exception-missing-' + key)])
        for recheck, code in (({}, 'exception-missing-recheck'), (None, 'exception-missing-recheck'),
                              ({'until': '2026-13-01'}, 'exception-recheck-invalid'),
                              ({'until': '2026-11-09'}, 'exception-recheck-due')):
            with self.subTest(recheck=recheck):
                self.assertEqual(check_exceptions([dict(EXCEPTION, recheck=recheck)], TODAY),
                                 [('X1', code)])
        self.assertEqual(check_exceptions([dict(EXCEPTION, recheck={'until': '2026-11-10'})],
                                          TODAY), [])
        self.assertEqual(check_exceptions([EXCEPTION, EXCEPTION], TODAY),
                         [('X1', 'duplicate-or-missing-id')])
        findings = check_exceptions([dict(EXCEPTION, recheck={'until': '2026-11-01'})], TODAY)
        self.assertIn('（⚠ exception-recheck-due）', render([], [dict(EXCEPTION)], findings))


if __name__ == '__main__':
    unittest.main()
