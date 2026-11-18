"""F21: staged in-place edits of shared rules are refused; other skips leave a findable record."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from project_bootstrap.bypass import audit, guard_commit, record
from project_bootstrap.contracts import Denied
from project_bootstrap.release import build_manifest

OWNERS = {'.claude/skills/handoff/SKILL.md': 'core', '.claude/hooks/git-freshness.sh': 'adapter',
          'docs/notes.md': 'project'}


class CommitGuardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-bypass-')
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name) / 'repo'
        (Path(directory.name) / 'home').mkdir()
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(Path(directory.name) / 'home'),
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}
        self.git('init', '--quiet', str(self.repo))
        for path, text in zip(OWNERS, ('skill v1\n', 'echo v1\n', 'mine\n')):
            (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / path).write_text(text)
        self.manifest = build_manifest(self.repo, list(OWNERS), '2026-11-10', 'formal')
        self.git('-C', str(self.repo), 'add', '-A')
        self.git('-C', str(self.repo), 'commit', '--quiet', '-m', 'deploy')

    def git(self, *args):
        subprocess.run(['git', *args], env=self.env, check=True, capture_output=True)

    def guard(self):
        return guard_commit(self.repo, self.manifest, OWNERS, env=self.env)

    def refused(self, code):
        with self.assertRaises(Denied) as caught:
            self.guard()
        self.assertEqual(str(caught.exception), code)

    def test_untouched_release_and_project_edits_pass(self):
        self.assertTrue(self.guard())
        (self.repo / 'docs/notes.md').write_text('changed\n')
        self.git('-C', str(self.repo), 'add', 'docs/notes.md')
        self.assertTrue(self.guard())

    def test_staged_edit_of_core_or_adapter_is_refused(self):
        for path in ('.claude/skills/handoff/SKILL.md', '.claude/hooks/git-freshness.sh'):
            with self.subTest(path=path):
                (self.repo / path).write_text('loosened\n')
                self.git('-C', str(self.repo), 'add', path)
                self.refused('in-place-core-edit:' + path)
                self.git('-C', str(self.repo), 'checkout', 'HEAD', '--', path)
        self.assertTrue(self.guard())

    def test_it_judges_the_index_not_the_working_tree(self):
        path = '.claude/skills/handoff/SKILL.md'
        (self.repo / path).write_text('loosened\n')
        self.assertTrue(self.guard())  # unstaged: not part of the commit
        self.git('-C', str(self.repo), 'add', path)
        (self.repo / path).write_text('skill v1\n')  # tree restored, index still edited
        self.refused('in-place-core-edit:' + path)

    def test_deleting_a_released_file_from_the_index_is_refused(self):
        self.git('-C', str(self.repo), 'rm', '--quiet', '--cached', '.claude/hooks/git-freshness.sh')
        self.refused('in-place-core-delete:.claude/hooks/git-freshness.sh')


class SkipLogTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-skiplog-')
        self.addCleanup(directory.cleanup)
        self.log = Path(directory.name) / 'events.jsonl'

    def write(self):
        record(self.log, {'step': 'A4', 'status': 'done', 'by': 's1', 'at': '2026-11-10T10:00'})
        record(self.log, {'step': 'B5', 'status': 'skipped', 'by': 's1', 'at': '2026-11-10T11:00',
                          'reason': '本輪沒動 Codex 接線'})

    def test_done_and_recorded_skips_account_for_required_steps(self):
        self.write()
        result = audit(self.log, ['A4', 'B5'])
        self.assertEqual(result, {'chain': 'ok', 'steps': {'A4': 'done', 'B5': 'skipped'},
                                  'findings': []})

    def test_a_step_neither_done_nor_recorded_is_a_silent_skip(self):
        self.write()
        result = audit(self.log, ['A4', 'B5', 'B4'])
        self.assertEqual((result['steps']['B4'], result['findings']),
                         ('silent-skip', [('B4', 'silent-skip')]))

    def test_skip_needs_a_reason_and_events_need_a_known_status(self):
        for event, code in (({'step': 'B4', 'status': 'skipped', 'reason': ' '}, 'skip-without-reason'),
                            ({'step': 'B4', 'status': 'later'}, 'event-invalid'),
                            ({'status': 'done'}, 'event-invalid')):
            with self.subTest(event=event):
                with self.assertRaises(Denied) as caught:
                    record(self.log, event)
                self.assertEqual(str(caught.exception), code)
        self.assertFalse(self.log.exists())

    def test_a_reasonless_skip_written_around_record_is_not_accepted(self):
        self.write()
        last = self.log.read_text(encoding='utf-8').splitlines()[-1]
        forged = json.dumps({'step': 'B4', 'status': 'skipped',
                             'prev': hashlib.sha256(last.encode()).hexdigest()})
        with self.log.open('a') as handle:
            handle.write(forged + '\n')
        result = audit(self.log, ['A4', 'B5', 'B4'])
        self.assertEqual(result['chain'], 'ok')
        self.assertEqual(result['findings'], [('B4', 'event-unaccounted'), ('B4', 'silent-skip')])

    def test_edited_or_truncated_logs_break_the_chain(self):
        self.write()
        lines = self.log.read_text(encoding='utf-8').splitlines()
        self.log.write_text(lines[0].replace('s1', 's2') + '\n' + lines[1] + '\n', encoding='utf-8')
        edited = audit(self.log, ['A4', 'B5'])
        self.assertEqual((edited['chain'], edited['findings'][0]), ('broken', ('line 2', 'chain-broken')))
        self.log.write_text(lines[1] + '\n', encoding='utf-8')
        cut = audit(self.log, ['A4', 'B5'])
        self.assertEqual(cut['chain'], 'broken')
        self.assertEqual(cut['steps'], {'A4': 'silent-skip', 'B5': 'silent-skip'})
        self.log.write_text(lines[0] + '\njunk\n' + lines[1] + '\n', encoding='utf-8')
        inserted = audit(self.log, ['A4', 'B5'])
        # Nothing after the break is trusted, even a line that still links to the last good one.
        self.assertEqual(inserted['steps'], {'A4': 'done', 'B5': 'silent-skip'})
        self.log.write_text('not json\n', encoding='utf-8')
        self.assertEqual(audit(self.log, [])['chain'], 'broken')

    def test_missing_log_is_reported(self):
        result = audit(self.log, ['A4'])
        self.assertEqual((result['chain'], result['findings']),
                         ('missing', [('log', 'log-missing'), ('A4', 'silent-skip')]))


if __name__ == '__main__':
    unittest.main()
