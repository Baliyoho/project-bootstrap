"""F6／F7／F8: a rule leads to its reason, rejected routes stay findable, the roadmap survives cleanup."""

import copy
import unittest

from experiments.v2.trail import (check_decisions, check_roadmap, check_rules, compare,
                                  rejected_routes, why)

DECISIONS = [
    {'id': 'D1', 'title': '開工標記寫在開工', 'status': 'superseded', 'superseded_by': 'D2',
     'date': '2026-10-30', 'baseline': 'VERSION 2026-10-30', 'rationale': '收工不保證有下一個動作',
     'alternatives': [{'option': '靠 SessionEnd 寫標記', 'outcome': 'rejected',
                       'reason': '不能擋下結束，1.5 秒推不了'}]},
    {'id': 'D2', 'title': '開工標記加工具欄', 'status': 'accepted', 'supersedes': 'D1',
     'date': '2026-10-31', 'baseline': 'VERSION 2026-10-31', 'rationale': '同機換工具會互相覆寫',
     'alternatives': [{'option': '用環境變數判工具', 'outcome': 'rejected',
                       'reason': '殼層繼承會冒名'}]},
    {'id': 'D3', 'title': '原子 claim', 'status': 'rejected', 'date': '2026-11-02',
     'baseline': 'VERSION 2026-11-02', 'rationale': '未做並行實驗，不宣稱互斥'},
]
RULES = [{'id': 'R-marker', 'decision': 'D2'}]
MILESTONES = [{'id': 'M1', 'goal': '偵測原型', 'status': 'active'},
              {'id': 'M0', 'goal': '舊 P0', 'status': 'done'},
              {'id': 'M9', 'goal': '跨雲', 'status': 'dropped', 'reason': '想要項，暫不做'}]
TASKS = [{'id': 'T1', 'milestone': 'M1', 'status': 'open'},
         {'id': 'T0', 'milestone': 'M0', 'status': 'done'}]


def decisions(**edits):
    data = copy.deepcopy(DECISIONS)
    for did, change in edits.items():
        record = next(d for d in data if d['id'] == did)
        for key, value in change.items():
            if value is None:
                record.pop(key, None)
            else:
                record[key] = value
    return data


def codes(findings):
    return sorted(findings)


class TrailTests(unittest.TestCase):
    def test_complete_records_are_clean_and_rule_leads_to_its_reason(self):
        findings, by_id = check_decisions(DECISIONS)
        self.assertEqual(findings, [])
        self.assertEqual(check_rules(RULES, by_id), [])
        chain = why('R-marker', RULES, by_id)
        self.assertEqual([(c['id'], c['baseline'], c['rationale']) for c in chain],
                         [('D2', 'VERSION 2026-10-31', '同機換工具會互相覆寫')])

    def test_rule_on_a_replaced_decision_is_flagged_and_chain_reaches_current(self):
        _, by_id = check_decisions(DECISIONS)
        rules = [{'id': 'R-old', 'decision': 'D1'}]
        self.assertEqual(check_rules(rules, by_id), [('R-old', 'rule-cites-superseded')])
        self.assertEqual([c['id'] for c in why('R-old', rules, by_id)], ['D1', 'D2'])

    def test_rule_without_decision_or_on_rejected_route_is_flagged(self):
        _, by_id = check_decisions(DECISIONS)
        rules = [{'id': 'R-x'}, {'id': 'R-y', 'decision': 'D404'}, {'id': 'R-z', 'decision': 'D3'}]
        self.assertEqual(check_rules(rules, by_id), [('R-x', 'rule-without-decision'),
                                                     ('R-y', 'rule-without-decision'),
                                                     ('R-z', 'rule-cites-rejected')])
        self.assertIsNone(why('R-x', rules, by_id))
        self.assertIsNone(why('missing', rules, by_id))

    def test_decision_missing_reason_baseline_or_date_is_flagged(self):
        findings, _ = check_decisions(decisions(D2={'rationale': ' ', 'baseline': None,
                                                    'date': '昨天', 'title': None}))
        self.assertEqual(codes(findings), [('D2', 'decision-date-invalid'),
                                           ('D2', 'decision-missing-baseline'),
                                           ('D2', 'decision-missing-rationale'),
                                           ('D2', 'decision-missing-title')])
        bad, _ = check_decisions(decisions(D3={'status': 'maybe'}))
        self.assertEqual(bad, [('D3', 'decision-status-invalid')])
        dup, _ = check_decisions(DECISIONS + [{'id': 'D1'}, {}])
        self.assertEqual(codes(dup), [('D1', 'decision-duplicate-or-missing-id'),
                                      ('None', 'decision-duplicate-or-missing-id')])

    def test_rejected_routes_are_listed_with_reasons(self):
        _, by_id = check_decisions(DECISIONS)
        routes = {(r['decision'], r['option'], r['reason']) for r in rejected_routes(by_id)}
        self.assertEqual(routes, {('D1', '靠 SessionEnd 寫標記', '不能擋下結束，1.5 秒推不了'),
                                  ('D2', '用環境變數判工具', '殼層繼承會冒名'),
                                  ('D3', '原子 claim', '未做並行實驗，不宣稱互斥')})

    def test_alternative_without_reason_or_outcome_is_flagged(self):
        alts = [{'option': '只靠記得', 'outcome': 'rejected'},
                {'option': 'x', 'outcome': 'maybe', 'reason': 'y'},
                {'outcome': 'deferred', 'reason': 'later'}]
        findings, _ = check_decisions(decisions(D2={'alternatives': alts}))
        self.assertEqual(findings, [('D2', 'alternative-incomplete')] * 3)
        ok, _ = check_decisions(decisions(D2={'alternatives': [
            {'option': '之後再說', 'outcome': 'deferred', 'reason': '等量測'}]}))
        self.assertEqual(ok, [])

    def test_supersession_must_be_mutual_and_point_somewhere(self):
        lone, _ = check_decisions(decisions(D1={'superseded_by': 'D9'}))
        self.assertIn(('D1', 'superseded-without-successor'), lone)
        one_way, _ = check_decisions(decisions(D2={'supersedes': None}))
        self.assertEqual(one_way, [('D1', 'supersession-not-mutual')])
        backward, _ = check_decisions(decisions(D3={'supersedes': 'D2'}))
        self.assertEqual(backward, [('D3', 'supersedes-unknown-or-not-mutual')])
        stray, _ = check_decisions(decisions(D3={'superseded_by': 'D2'}))
        self.assertEqual(stray, [('D3', 'successor-on-unsuperseded')])

    def test_erasing_or_rewriting_history_is_found(self):
        self.assertEqual(compare(DECISIONS, DECISIONS + [{'id': 'D4'}]), [])
        erased = [d for d in decisions() if d['id'] != 'D3']
        self.assertEqual(compare(DECISIONS, erased), [('D3', 'decision-erased')])
        no_alt = decisions(D1={'alternatives': []})
        self.assertEqual(compare(DECISIONS, no_alt), [('D1', 'alternative-erased')])
        rewritten = decisions(D3={'rationale': '從來沒考慮過'})
        self.assertEqual(compare(DECISIONS, rewritten), [('D3', 'rationale-rewritten')])
        restatus = decisions(D2={'status': 'superseded', 'rationale': '改理由'})
        self.assertEqual(compare(DECISIONS, restatus), [('D2', 'rationale-rewritten')])

    def test_roadmap_locates_tasks_after_handoff_cleanup(self):
        self.assertEqual(check_roadmap(MILESTONES, TASKS), [])
        self.assertEqual(check_roadmap(MILESTONES, []), [])

    def test_roadmap_gaps_are_flagged(self):
        tasks = TASKS + [{'id': 'T2'}, {'id': 'T3', 'milestone': 'M0', 'status': 'open'},
                         {'id': 'T4', 'milestone': 'M9', 'status': 'open'}]
        self.assertEqual(check_roadmap(MILESTONES, tasks),
                         [('T2', 'task-without-milestone'), ('T3', 'open-task-on-closed-milestone'),
                          ('T4', 'open-task-on-closed-milestone')])
        closed = [dict(m, status='done') for m in MILESTONES[:2]]
        self.assertEqual(check_roadmap(closed, []), [('roadmap', 'no-open-milestone')])
        planned = [{'id': 'M2', 'goal': 'x', 'status': 'planned'}]
        self.assertEqual(check_roadmap(planned, []), [])
        broken = [{'id': 'M1', 'goal': '', 'status': 'active'},
                  {'id': 'M2', 'goal': 'g', 'status': 'later'},
                  {'id': 'M3', 'goal': 'g', 'status': 'dropped'}, {'id': 'M1'}]
        self.assertEqual(sorted(check_roadmap(broken, [])),
                         [('M1', 'milestone-duplicate-or-missing-id'), ('M1', 'milestone-missing-goal'),
                          ('M2', 'milestone-status-invalid'), ('M3', 'dropped-without-reason')])


if __name__ == '__main__':
    unittest.main()
