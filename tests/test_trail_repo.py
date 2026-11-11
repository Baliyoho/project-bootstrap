"""F6／F7／F8 on this repo's real decision book and implementation plan.

Kept apart from test_trail_sources so mutation runs, which copy only
experiments/, never depend on the repo's documents.
"""

from pathlib import Path
import unittest

from project_bootstrap.trail import check_decisions, check_roadmap, check_rules, rejected_routes, why
from project_bootstrap.trail_sources import (absences_from_architect, decisions_from_book,
                                          nongoals_from_plan, questions_from_book,
                                          roadmap_from_plan, routes_from_plan,
                                          rules_from_agents)

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding='utf-8')


class RepoTrailTests(unittest.TestCase):
    def test_every_section_7_decision_has_reason_date_and_baseline(self):
        decisions = decisions_from_book(read('project-bootstrap-requirements-decision.md'))
        self.assertGreaterEqual(len(decisions), 7)
        self.assertEqual(check_decisions(decisions)[0], [])

    def test_rejected_routes_are_findable_with_their_cost(self):
        routes = routes_from_plan(read('project-bootstrap-implementation-plan.md'), '2026-11-06')
        findings, by_id = check_decisions(routes)
        self.assertEqual((len(routes), findings), (1, []))
        rejected = rejected_routes(by_id)
        self.assertEqual(len(rejected), 2)
        self.assertTrue(all(r['reason'] for r in rejected))

    def test_roadmap_has_the_six_phases_and_an_open_one(self):
        # P0 has not exited (HANDOFF); the plan itself holds no progress.
        milestones = roadmap_from_plan(read('project-bootstrap-implementation-plan.md'),
                                       {'P0': 'active'})
        self.assertEqual([m['id'] for m in milestones], ['P0', 'P1', 'P2', 'P3', 'P4', 'P5'])
        self.assertEqual(check_roadmap(milestones, []), [])

    def test_architect_declared_absences_each_have_reason_and_date(self):
        # 2026-11-10 first run: the CI bullet had no date; the git first-appearance date was added.
        decisions = absences_from_architect(read('ARCHITECT.md'))
        self.assertGreaterEqual(len(decisions), 3)
        self.assertEqual(check_decisions(decisions)[0], [])


    def test_every_agents_rule_walks_to_a_dated_reason(self):
        # 2026-11-10 first run: four sections had no date; git first-appearance dates were added.
        rules, decisions = rules_from_agents(read('AGENTS.md'), read('AGENTS-reasons.md'))
        self.assertGreaterEqual(len(rules), 20)
        findings, by_id = check_decisions(decisions)
        self.assertEqual(findings, [])
        self.assertEqual(check_rules(rules, by_id), [])
        cited = {r['decision'] for r in rules}
        self.assertEqual(sorted(set(by_id) - cited), [])
        self.assertTrue(all(why(r['id'], rules, by_id) for r in rules))


    def test_decided_questions_record_every_option_with_a_reason(self):
        # 2026-11-10 Q7 (b): reasons found in the documents, else "當時沒有記錄理由".
        decisions = questions_from_book(read('project-bootstrap-requirements-decision.md'))
        self.assertGreaterEqual(len(decisions), 10)
        self.assertEqual(check_decisions(decisions)[0], [])
        self.assertTrue(all(d['alternatives'] for d in decisions))

    def test_efficiency_nongoals_are_rejected_routes_with_reasons(self):
        decisions = nongoals_from_plan(read('project-bootstrap-efficiency-plan.md'), '2026-11-03')
        self.assertEqual(len(decisions), 5)
        findings, by_id = check_decisions(decisions)
        self.assertEqual(findings, [])
        self.assertEqual(len(rejected_routes(by_id)), 5)

if __name__ == '__main__':
    unittest.main()
