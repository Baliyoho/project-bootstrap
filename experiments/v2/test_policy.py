"""F36 ownership-aware update, F37 tighten-only merge, F38 slot schema and description."""

import unittest

from experiments.v2.contracts import Denied
from experiments.v2.policy import check_schema, describe, merge, plan_update

OLD = {'.claude/skills/handoff/SKILL.md': {'owner': 'core', 'sha256': 's1'},
       '.claude/hooks/git-freshness.sh': {'owner': 'adapter', 'sha256': 'h1'},
       '.claude/hooks/old.sh': {'owner': 'adapter', 'sha256': 'o1'}}
NEW = {'.claude/skills/handoff/SKILL.md': {'owner': 'core', 'sha256': 's2'},
       '.claude/hooks/git-freshness.sh': {'owner': 'adapter', 'sha256': 'h1'},
       '.claude/hooks/new.sh': {'owner': 'adapter', 'sha256': 'n2'}}
LOCAL = {'.claude/skills/handoff/SKILL.md': 's1', '.claude/hooks/git-freshness.sh': 'h1',
         '.claude/hooks/old.sh': 'o1', '.claude/hooks/project-audit.sh': 'p1',
         'src/app.py': 'a1'}
ROOTS = ('.claude',)
PROJECT = {'.claude/hooks/project-audit.sh'}

SCHEMA = {
    'mandatory': ['require_fetch_before_claim', 'forbid_force_push'],
    'slots': {
        'blocked_commands': {'direction': 'add-only', 'effect': 'restrict', 'default': [],
                             'doc': '再加禁止的指令'},
        'min_checks': {'direction': 'at-least', 'effect': 'restrict', 'default': 1,
                       'doc': '交棒前至少跑幾項檢查'},
        'max_reuse_hours': {'direction': 'at-most', 'effect': 'restrict', 'default': 24,
                            'doc': '沿用證據最長幾小時'},
        'require_signed_release': {'direction': 'true-only', 'effect': 'restrict',
                                   'default': False, 'doc': '只接受簽章發布'},
    },
}
CORE = {'require_fetch_before_claim': True, 'forbid_force_push': True,
        'blocked_commands': ['git push --force'], 'min_checks': 1, 'max_reuse_hours': 24,
        'require_signed_release': False}


class OwnershipTests(unittest.TestCase):
    def denied(self, code, call, *args):
        with self.assertRaises(Denied) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)

    def test_update_replaces_released_keeps_project_and_ignores_unmanaged(self):
        plan = plan_update(OLD, NEW, LOCAL, PROJECT, ROOTS)
        self.assertEqual(plan, {'.claude/skills/handoff/SKILL.md': 'replace',
                                '.claude/hooks/git-freshness.sh': 'unchanged',
                                '.claude/hooks/new.sh': 'replace',
                                '.claude/hooks/old.sh': 'remove-released',
                                '.claude/hooks/project-audit.sh': 'keep-project'})

    def test_unknown_owner_or_edited_release_stops_the_update(self):
        stray = dict(LOCAL, **{'.claude/hooks/mystery.sh': 'm1'})
        self.denied('ownership-unknown:.claude/hooks/mystery.sh', plan_update, OLD, NEW, stray,
                    PROJECT, ROOTS)
        for path, digest in (('.claude/skills/handoff/SKILL.md', 's1-edited'),
                             ('.claude/hooks/old.sh', 'o1-edited')):
            with self.subTest(path=path):
                self.denied('released-file-edited:' + path, plan_update, OLD, NEW,
                            dict(LOCAL, **{path: digest}), PROJECT, ROOTS)
        # A project file sitting where a new release wants to put its own.
        collide = dict(LOCAL, **{'.claude/hooks/new.sh': 'project-made'})
        self.denied('ownership-unknown:.claude/hooks/new.sh', plan_update, OLD, NEW, collide,
                    PROJECT, ROOTS)
        self.assertEqual(plan_update(OLD, NEW, dict(LOCAL, **{'.claude/hooks/new.sh': 'n2'}),
                                     PROJECT, ROOTS)['.claude/hooks/new.sh'], 'unchanged')
        self.denied('ownership-conflict:.claude/hooks/git-freshness.sh', plan_update, OLD, NEW,
                    LOCAL, PROJECT | {'.claude/hooks/git-freshness.sh'}, ROOTS)
        bad = dict(NEW, **{'x': {'owner': 'project', 'sha256': 'x'}})
        self.denied('manifest-owner-invalid', plan_update, OLD, bad, LOCAL, PROJECT, ROOTS)
        self.denied('manifest-owner-invalid', plan_update, bad, NEW, LOCAL, PROJECT, ROOTS)
        # A sibling directory that merely shares the prefix is not managed.
        self.assertNotIn('.claudette/x', plan_update(OLD, NEW, dict(LOCAL, **{'.claudette/x': 'q'}),
                                                     PROJECT, ROOTS))


class MergeTests(unittest.TestCase):
    def denied(self, code, override, schema=SCHEMA):
        with self.assertRaises(Denied) as caught:
            merge(CORE, override, schema)
        self.assertEqual(str(caught.exception), code)

    def test_tightening_overrides_merge_and_core_is_untouched(self):
        override = {'blocked_commands': ['git push --force', 'git reset --hard'],
                    'min_checks': 3, 'max_reuse_hours': 6, 'require_signed_release': True}
        effective = merge(CORE, override, SCHEMA)
        self.assertEqual(effective['min_checks'], 3)
        self.assertTrue(effective['forbid_force_push'])
        self.assertEqual(CORE['min_checks'], 1)
        self.assertEqual(merge(CORE, {}, SCHEMA), CORE)
        self.assertTrue(merge(dict(CORE, require_signed_release=True),
                              {'require_signed_release': True}, SCHEMA)['require_signed_release'])

    def test_loosening_unknown_mandatory_and_wrong_type_are_refused(self):
        self.denied('mandatory-not-overridable:forbid_force_push', {'forbid_force_push': False})
        self.denied('mandatory-not-overridable:forbid_force_push', {'forbid_force_push': True})
        self.denied('unknown-field:skip_fetch', {'skip_fetch': True})
        self.denied('loosens:blocked_commands', {'blocked_commands': []})
        self.denied('loosens:min_checks', {'min_checks': 0})
        self.denied('loosens:max_reuse_hours', {'max_reuse_hours': 48})
        with self.assertRaises(Denied) as caught:
            merge(dict(CORE, require_signed_release=True), {'require_signed_release': False}, SCHEMA)
        self.assertEqual(str(caught.exception), 'loosens:require_signed_release')
        for key, value in (('min_checks', '3'), ('min_checks', True), ('min_checks', 2.0),
                           ('blocked_commands', 'git clean'), ('require_signed_release', 1)):
            with self.subTest(key=key, value=value):
                self.denied('type-mismatch:' + key, {key: value})
        with self.assertRaises(Denied) as caught:
            merge(dict(CORE, min_checks='1'), {'min_checks': 3}, SCHEMA)
        self.assertEqual(str(caught.exception), 'type-mismatch:min_checks')

    def test_new_slot_in_a_release_is_usable_and_default_applies(self):
        schema = {**SCHEMA, 'slots': {**SCHEMA['slots'], 'protected_paths': {
            'direction': 'add-only', 'effect': 'restrict', 'default': [], 'doc': '不得寫入的路徑'}}}
        self.assertEqual(merge(CORE, {'protected_paths': ['secrets/']}, schema)['protected_paths'],
                         ['secrets/'])


class SchemaTests(unittest.TestCase):
    def test_slot_directions_must_tighten_and_mandatory_has_no_entry(self):
        self.assertEqual(check_schema(SCHEMA), [])
        cases = (
            ({'direction': 'add-only', 'effect': 'permit'}, 'direction-loosens'),
            ({'direction': 'add-only'}, 'effect-unconfirmed'),
            ({'direction': 'add-only', 'effect': 'probably-fine'}, 'effect-unconfirmed'),
            ({'direction': 'replace', 'effect': 'restrict'}, 'direction-unknown'),
        )
        for slot, code in cases:
            with self.subTest(code=code):
                schema = {'slots': {'allowed_hosts': slot}}
                self.assertEqual(check_schema(schema), [('allowed_hosts', code)])
                with self.assertRaises(Denied) as caught:
                    merge({}, {}, schema)
                self.assertEqual(str(caught.exception), 'schema-invalid')
        clash = {**SCHEMA, 'mandatory': SCHEMA['mandatory'] + ['min_checks']}
        self.assertEqual(check_schema(clash), [('min_checks', 'mandatory-has-override-slot')])

    def test_description_lists_slots_and_unchangeable_parts(self):
        text = describe(SCHEMA)
        self.assertIn("- min_checks：at-least，預設 1；交棒前至少跑幾項檢查", text)
        after = text.split('不可改的部分（沒有覆寫入口）：\n')[1]
        self.assertEqual(after, '- forbid_force_push\n- require_fetch_before_claim\n')


if __name__ == '__main__':
    unittest.main()
