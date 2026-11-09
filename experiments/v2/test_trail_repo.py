"""F6／F7／F8 on this repo's real decision book and implementation plan.

Kept apart from test_trail_sources so mutation runs, which copy only
experiments/, never depend on the repo's documents.
"""

from pathlib import Path
import unittest

from experiments.v2.trail import check_decisions, check_roadmap, rejected_routes
from experiments.v2.trail_sources import decisions_from_book, roadmap_from_plan, routes_from_plan

ROOT = Path(__file__).resolve().parents[2]


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


if __name__ == '__main__':
    unittest.main()
