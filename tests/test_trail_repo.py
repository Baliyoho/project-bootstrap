"""F6／F7／F8 on this repo's real decision book and implementation plan v3.

The decision book is v3. Since 2026-11-17 (v3 Q39) v2 is a frozen archive that
no program reads; its section 7 and Q1–Q31 are no longer checked here.

Kept apart from test_trail_sources so mutation runs, which copy only
experiments/, never depend on the repo's documents.
"""

from pathlib import Path
import unittest

from project_bootstrap.trail import check_decisions, check_roadmap, check_rules, rejected_routes, why
from project_bootstrap.trail_sources import (absences_from_architect, constraints_from_book,
                                          nongoals_from_plan, questions_from_book,
                                          roadmap_from_plan, routes_from_plan,
                                          rules_from_agents)

ROOT = Path(__file__).resolve().parents[1]
BOOK = 'project-bootstrap-requirements-decision-v3.md'
# 2026-11-17: v2's implementation plan and the efficiency plan are archived; the
# routes, phases and non-goals now come from implementation plan v3.
PLAN = 'project-bootstrap-implementation-plan-v3.md'
# 2026-11-17 (v3 Q42): decided questions moved from the book's section 8 to here.
BOOK_HISTORY = 'docs/history/project-bootstrap-requirements-v3-history.md'


def read(name):
    return (ROOT / name).read_text(encoding='utf-8')


class RepoTrailTests(unittest.TestCase):
    def test_every_constraint_has_reason_date_and_baseline(self):
        decisions = constraints_from_book(read(BOOK))
        self.assertEqual([d['id'] for d in decisions], ['book-D%d' % n for n in range(1, 16)])
        self.assertEqual(check_decisions(decisions)[0], [])

    def test_rejected_routes_are_findable_with_their_cost(self):
        routes = routes_from_plan(read(PLAN), '2026-11-17')
        findings, by_id = check_decisions(routes)
        self.assertEqual((len(routes), findings), (1, []))
        rejected = rejected_routes(by_id)
        self.assertEqual(len(rejected), 1)
        self.assertTrue(all(r['reason'] for r in rejected))

    def test_roadmap_has_the_three_phases_and_an_open_one(self):
        # Phase 1 closed (user, 2026-11-17), phase 2 is open; the plan itself holds no progress.
        milestones = roadmap_from_plan(read(PLAN), {'phase-1': 'done', 'phase-2': 'active'})
        self.assertEqual([m['id'] for m in milestones], ['phase-1', 'phase-2', 'phase-3'])
        self.assertEqual(check_roadmap(milestones, []), [])

    def test_architect_declared_absences_each_have_reason_and_date(self):
        # 2026-11-10 first run: the CI bullet had no date; the git first-appearance date was added.
        decisions = absences_from_architect(read('ARCHITECT.md'))
        self.assertGreaterEqual(len(decisions), 3)
        self.assertEqual(check_decisions(decisions)[0], [])


    def test_every_agents_rule_walks_to_a_dated_reason(self):
        # 2026-11-10 first run: four sections had no date; git first-appearance dates were added.
        # 2026-11-17 (v3 Q40): the on-demand rules moved to CONTRIBUTING.md; both files are the rule set.
        rules, decisions = rules_from_agents(read('AGENTS.md') + '\n' + read('CONTRIBUTING.md'),
                                             read('AGENTS-reasons.md'))
        self.assertGreaterEqual(len(rules), 20)
        findings, by_id = check_decisions(decisions)
        self.assertEqual(findings, [])
        self.assertEqual(check_rules(rules, by_id), [])
        cited = {r['decision'] for r in rules}
        self.assertEqual(sorted(set(by_id) - cited), [])
        self.assertTrue(all(why(r['id'], rules, by_id) for r in rules))


    def test_decided_questions_record_every_option_with_a_reason(self):
        # 2026-11-10 Q7 (b): reasons found in the documents, else "當時沒有記錄理由".
        # 2026-11-17 Q39: v3 section 8 (Q32 on). An option the question lists but the
        # record leaves out still comes back with an empty reason and is reported by
        # check_decisions. Q34–Q36 listed no options, so "every decision has an
        # alternative" (the v2-era assertion) no longer holds and is not asserted.
        decisions = questions_from_book(read(BOOK_HISTORY))
        self.assertGreaterEqual(len(decisions), 11)
        self.assertEqual({d['baseline'] for d in decisions}, {'決策紀錄第 2 節'})
        # The book's own section 8 now holds only undecided items.
        self.assertEqual(questions_from_book(read(BOOK)), [])
        self.assertEqual(check_decisions(decisions)[0], [])

    def test_plan_nongoals_are_rejected_routes_with_reasons(self):
        decisions = nongoals_from_plan(read(PLAN), '2026-11-17')
        self.assertEqual(len(decisions), 5)
        findings, by_id = check_decisions(decisions)
        self.assertEqual(findings, [])
        self.assertEqual(len(rejected_routes(by_id)), 5)

if __name__ == '__main__':
    unittest.main()
