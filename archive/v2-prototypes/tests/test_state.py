"""F1／F2／F5: goal, progress and risk claims are checked against the decision and evidence."""

import copy
from pathlib import Path
import tempfile
import unittest

from project_bootstrap.state import check, decision_version, render

DECISION = '''# 決策書

> 決策版本：3。唯一權威。

## 3. 需求清單

| ID | 需求 | 等級 | 強度 |
|---|---|---|---|
| F1 | 目標 | 必要 | 偵測 |
| F2 | 進度 | 必要 | 偵測 |

## 4. 驗收規則
'''

GOOD = {
    'goal': {'text': '做 M2 原型', 'requirement_ids': ['F1', 'F2'], 'decision_version': 3,
             'source': 'decision.md'},
    'tasks': [
        {'id': 'T1', 'title': '寫檢查器', 'status': 'done', 'evidence': ['proof.txt']},
        {'id': 'T2', 'title': '寫視圖', 'status': 'open'},
        {'id': 'T3', 'title': '接工具', 'status': 'blocked', 'blocked_on': '使用者選工具'},
    ],
    'next': ['T2', 'T3'],
    'risks': [
        {'id': 'K1', 'kind': 'healthy', 'text': '本機 Git 正常', 'evidence': ['proof.txt']},
        {'id': 'K2', 'kind': 'unknown', 'text': 'Windows 未測'},
        {'id': 'K3', 'kind': 'broken', 'text': 'hook 在 bash 3.2 壞', 'evidence': ['proof.txt']},
    ],
}


class StateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-state-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / 'decision.md').write_text(DECISION, encoding='utf-8')
        (self.root / 'proof.txt').write_text('x')

    def findings(self, change):
        state = copy.deepcopy(GOOD)
        change(state)
        return check(state, DECISION, self.root), state

    def test_consistent_state_has_no_findings_and_renders_cleanly(self):
        self.assertEqual(decision_version(DECISION), 3)
        self.assertIsNone(decision_version('# no version\n'))
        findings = check(GOOD, DECISION, self.root)
        self.assertEqual(findings, [])
        view = render(GOOD, findings)
        self.assertIn('做 M2 原型（已核對：F1、F2；決策版本 3；來源 decision.md）', view)
        self.assertIn('1. 寫視圖\n2. 接工具（卡在：使用者選工具）', view)
        self.assertIn('- [已知正常] 本機 Git 正常', view)
        self.assertNotIn('⚠', view)

    def test_f1_missing_or_stale_goal_is_unverified_even_when_non_empty(self):
        cases = (
            (lambda s: s.pop('goal'), ('goal', 'goal-missing')),
            (lambda s: s['goal'].update(text='   '), ('goal', 'goal-missing')),
            (lambda s: s['goal'].update(requirement_ids=[]), ('goal', 'goal-without-ids')),
            (lambda s: s['goal'].update(requirement_ids=['F1', 'F99']),
             ('goal', 'goal-unknown-id')),
            (lambda s: s['goal'].update(decision_version=2), ('goal', 'goal-stale-version')),
            (lambda s: s['goal'].update(decision_version='3'), ('goal', 'goal-stale-version')),
            (lambda s: s['goal'].update(source='gone.md'), ('goal', 'goal-source-missing')),
        )
        for change, expected in cases:
            with self.subTest(expected=expected):
                findings, state = self.findings(change)
                self.assertEqual(findings, [expected])
                self.assertIn('未驗證', render(state, findings).split('\n## 已完成')[0])
        self.assertIn(('goal', 'decision-version-unreadable'),
                      check(GOOD, DECISION.replace('> 決策版本：3。', ''), self.root))

    def test_f2_done_task_listed_as_next_and_status_evidence_mismatch(self):
        findings, state = self.findings(lambda s: s['next'].insert(0, 'T1'))
        self.assertEqual(findings, [('T1', 'done-listed-as-next')])
        view = render(state, findings)
        # The view never shows a done task among next steps.
        self.assertNotIn('寫檢查器', view.split('## 未完成／下一步')[1])
        self.assertIn('寫檢查器（⚠ done-listed-as-next）', view)
        cases = (
            (lambda s: s['tasks'][0].update(evidence=[]), ('T1', 'done-without-evidence')),
            (lambda s: s['tasks'][0].update(evidence=['gone.txt']), ('T1', 'evidence-missing')),
            (lambda s: s['tasks'][0].update(evidence=['../proof.txt']),
             ('T1', 'evidence-invalid')),
            (lambda s: s['tasks'][0].update(evidence='proof.txt'), ('T1', 'evidence-invalid')),
            (lambda s: s['tasks'][2].pop('blocked_on'), ('T3', 'blocked-without-reason')),
            (lambda s: s['tasks'][1].update(status='finished'), ('T2', 'task-status-invalid')),
            (lambda s: s['next'].remove('T2'), ('T2', 'open-not-scheduled')),
            (lambda s: s['next'].append('T9'), ('T9', 'next-unknown-task')),
            (lambda s: s['next'].append('T2'), ('next', 'next-duplicate')),
            (lambda s: s['tasks'].append({'id': 'T1', 'status': 'open'}),
             ('T1', 'duplicate-or-missing-id')),
        )
        for change, expected in cases:
            with self.subTest(expected=expected):
                findings, state = self.findings(change)
                self.assertEqual(findings, [expected])
                self.assertIn(expected[1], render(state, findings))

    def test_f5_untested_is_unknown_never_known_healthy(self):
        for kind, label in (('healthy', '已知正常'), ('broken', '已知壞掉')):
            index = 0 if kind == 'healthy' else 2
            with self.subTest(kind=kind):
                findings, state = self.findings(
                    lambda s: s['risks'][index].update(evidence=[]))
                self.assertEqual(findings, [(f'K{index + 1}', f'{kind}-without-evidence')])
                view = render(state, findings)
                self.assertNotIn(f'[{label}]', view)
                self.assertIn('[未知]', view)
                findings, state = self.findings(
                    lambda s: s['risks'][index].update(evidence=['gone.txt']))
                self.assertNotIn(f'[{label}]', render(state, findings))
        findings, _ = self.findings(lambda s: s['risks'][1].update(kind='fine'))
        self.assertEqual(findings, [('K2', 'risk-kind-invalid')])
        findings, _ = self.findings(lambda s: s['risks'].append({'id': 'T1', 'kind': 'risk'}))
        self.assertEqual(findings, [('T1', 'duplicate-or-missing-id')])
        findings, state = self.findings(lambda s: s['tasks'].append({'id': 'T1', 'status': 'open'}))
        self.assertIn('- 寫檢查器（⚠ duplicate-or-missing-id）', render(state, findings))
        findings, state = self.findings(lambda s: s['next'].append('T9'))
        self.assertIn('其他狀態問題：T9:next-unknown-task', render(state, findings))
        # Unknown needs no evidence: saying "not tested" is always allowed.
        self.assertEqual(self.findings(lambda s: s['risks'][1].pop('text'))[0], [])


if __name__ == '__main__':
    unittest.main()
