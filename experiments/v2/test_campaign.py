"""F24: 20 mixed projects, at most 3 human prompts, nothing dropped or hidden."""

import tempfile
import unittest
from pathlib import Path

from experiments.v2.batch import assess_many
from experiments.v2.campaign import plan, summary

FAILURES = ['foreign-claim', 'dirty-worktree', 'ahead-only', 'fetch-failed', 'missing-target']


def report(eligible=14, archived=1, failed=FAILURES, extra=()):
    rows = [{'target': f'p{i:02d}', 'outcome': 'eligible', 'code': 'ok'} for i in range(eligible)]
    rows += [{'target': f'a{i}', 'outcome': 'excluded', 'code': 'archived'} for i in range(archived)]
    rows += [{'target': f'f-{code}', 'outcome': 'failed', 'code': code} for code in failed]
    rows += list(extra)
    return {'results': rows}


class CampaignTests(unittest.TestCase):
    def test_twenty_mixed_targets_fit_three_prompts_and_none_is_dropped(self):
        affected = [f'p{i:02d}' for i in range(10)]
        result = plan(report(), affected)
        self.assertEqual(len(result['rows']), 20)
        self.assertEqual(result['counts'], {'update': 10, 'skip-unaffected': 4, 'excluded': 1,
                                            'failed': 5})
        self.assertEqual([p['kind'] for p in result['prompts']],
                         ['approve-release', 'approve-targets', 'review-failures'])
        self.assertEqual(result['prompts'][1]['targets'], affected)
        self.assertEqual(sorted(result['prompts'][2]['targets']),
                         sorted(f'f-{c}' for c in FAILURES))
        self.assertTrue(result['within_budget'])
        self.assertFalse(result['ok'])
        self.assertTrue(summary(result).startswith('NOT OK: 1 excluded, 5 failed'))

    def test_clean_run_needs_two_prompts_and_is_ok(self):
        result = plan(report(eligible=19, failed=()), 'all')
        self.assertEqual((result['ok'], len(result['prompts']), result['counts']),
                         (True, 2, {'update': 19, 'excluded': 1}))
        self.assertEqual(summary(result), 'OK: 1 excluded, 19 update; 2 human prompts (budget 3)')

    def test_nothing_to_update_needs_no_prompt(self):
        result = plan(report(eligible=3, archived=0, failed=()), [])
        self.assertEqual((result['ok'], result['prompts'], result['counts']),
                         (True, [], {'skip-unaffected': 3}))

    def test_per_project_comparisons_are_counted_and_can_exceed_the_budget(self):
        drift = [{'target': f'd{i}', 'outcome': 'failed', 'code': 'release:component-drift'}
                 for i in range(2)]
        result = plan(report(failed=(), extra=drift), 'all')
        self.assertEqual([p['kind'] for p in result['prompts']],
                         ['approve-release', 'approve-targets', 'compare-by-hand', 'compare-by-hand'])
        self.assertEqual((result['within_budget'], result['ok']), (False, False))
        self.assertIn('4 human prompts (budget 3, OVER)', summary(result))
        one = plan(report(failed=(), extra=drift[:1]), 'all')
        self.assertEqual((one['within_budget'], one['ok']), (True, False))

    def test_unknown_outcome_and_duplicates_are_failures(self):
        extra = [{'target': 'odd', 'outcome': 'maybe', 'code': 'x'},
                 {'target': 'p00', 'outcome': 'eligible', 'code': 'ok'}]
        result = plan(report(eligible=2, archived=0, failed=(), extra=extra), 'all')
        self.assertIn({'target': 'odd', 'action': 'failed', 'code': 'unknown-outcome'},
                      result['rows'])
        self.assertEqual(result['problems'], [('p00', 'listed-twice')])
        self.assertEqual(len(result['rows']), 3)
        self.assertFalse(result['ok'])

    def test_a_duplicate_alone_or_a_tighter_budget_alone_is_not_ok(self):
        dup = [{'target': 'p00', 'outcome': 'eligible', 'code': 'ok'}]
        result = plan(report(eligible=2, archived=0, failed=(), extra=dup), 'all')
        self.assertEqual((result['problems'], result['ok']), ([('p00', 'listed-twice')], False))
        tight = plan(report(eligible=2, archived=0, failed=()), 'all', budget=1)
        self.assertEqual((tight['within_budget'], tight['ok']), (False, False))

    def test_affected_project_missing_from_the_batch_is_not_skipped_silently(self):
        result = plan(report(eligible=2, archived=0, failed=()), ['p00', 'ghost'])
        self.assertEqual(result['problems'], [('ghost', 'affected-but-not-assessed')])
        self.assertIn({'target': 'ghost', 'action': 'failed', 'code': 'not-assessed'},
                      result['rows'])
        self.assertEqual(result['prompts'][-1], {'kind': 'review-failures', 'targets': ['ghost']})
        self.assertFalse(result['ok'])

    def test_real_batch_rows_feed_the_plan(self):
        with tempfile.TemporaryDirectory(prefix='bootstrap-v2-campaign-') as directory:
            gone, old = str(Path(directory) / 'gone'), str(Path(directory) / 'old')
            batch = assess_many([(gone, 'active'), (old, 'archived')], owner='o')
        result = plan(batch, 'all')
        self.assertEqual([(r['action'], r['code']) for r in result['rows']],
                         [('failed', 'missing-target'), ('excluded', 'archived')])
        self.assertEqual([p['kind'] for p in result['prompts']], ['review-failures'])


if __name__ == '__main__':
    unittest.main()
