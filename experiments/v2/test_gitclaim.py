"""Real Git fixtures for the M3 start/finish gates (local bare remote only)."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from experiments.v2.gitclaim import (IDLE, GitGateDenied, assess_start, finish, owner_field,
                                     run_check)
from experiments.v2.session import Session

ME = '`mac` ／ `Claude Code` ／ `㊣　26110922｜測試｜工作中｜交棒0次`'
OTHER = '`win` ／ `Codex CLI` ／ `㊣　26110901｜別人｜工作中｜交棒0次`'


def handoff(owner):
    return f'# HANDOFF\n\n## Git 狀態\n- **工作中**：{owner}\n'


class GitGateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        home = self.root / 'home'
        home.mkdir()
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(home),
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid',
                    'LC_ALL': 'C'}
        self.origin = self.root / 'origin.git'
        self.git(self.root, 'init', '--quiet', '--bare', '--initial-branch=main', str(self.origin))
        self.a = self.clone('a')
        self.commit(self.a, 'HANDOFF.md', handoff(IDLE))
        self.git(self.a, 'push', '--quiet', '-u', 'origin', 'main')
        self.b = self.clone('b')

    def tearDown(self):
        self.directory.cleanup()

    def git(self, cwd, *args, check=True):
        result = subprocess.run(['git', *args], cwd=cwd, env=self.env, capture_output=True)
        if check and result.returncode:
            raise AssertionError(result.stderr.decode())
        return result.stdout.decode().strip()

    def clone(self, name):
        target = self.root / name
        self.git(self.root, 'clone', '--quiet', str(self.origin), str(target))
        return target

    def commit(self, repo, name, text):
        (repo / name).write_text(text, encoding='utf-8')
        self.git(repo, 'add', name)
        self.git(repo, 'commit', '--quiet', '-m', f'edit {name}')

    def remote_head(self):
        return self.git(self.root, '--git-dir', str(self.origin), 'rev-parse', 'refs/heads/main')

    def denied(self, code, call, *args, **kwargs):
        with self.assertRaises(GitGateDenied) as caught:
            call(*args, **kwargs)
        self.assertEqual(str(caught.exception), code)

    # --- F9: start eligibility -------------------------------------------------

    def test_clean_aligned_idle_checkout_is_eligible(self):
        facts = assess_start(self.b, ME, env=self.env)
        self.assertEqual((facts['branch'], facts['upstream'], facts['remote_owner']),
                         ('main', 'origin/main', IDLE))
        self.assertEqual(facts['remote_sha'], self.remote_head())

    def test_ahead_only_diverged_and_behind_are_not_eligible(self):
        self.commit(self.a, 'a.txt', 'a')
        self.denied('ahead-only', assess_start, self.a, ME, env=self.env)
        self.commit(self.b, 'b.txt', 'b')
        self.git(self.b, 'push', '--quiet')
        self.denied('diverged', assess_start, self.a, ME, env=self.env)
        c = self.clone('c')
        self.commit(self.b, 'b2.txt', 'b')
        self.git(self.b, 'push', '--quiet')
        self.denied('behind-pull-required', assess_start, c, ME, env=self.env)
        self.git(c, 'pull', '--quiet', '--ff-only')
        assess_start(c, ME, env=self.env)

    def test_offline_never_falls_back_to_cached_tracking_ref(self):
        self.origin.rename(self.root / 'moved.git')
        # The cached origin/main still says aligned and idle; it must not count.
        self.assertEqual(self.git(self.b, 'rev-list', '--count', 'HEAD...origin/main'), '0')
        self.denied('fetch-failed', assess_start, self.b, ME, env=self.env)

    def test_unknown_dirty_state_is_not_eligible(self):
        (self.b / 'untracked.txt').write_text('x')
        self.denied('dirty-unknown', assess_start, self.b, ME, env=self.env)
        (self.b / 'untracked.txt').unlink()
        (self.b / 'HANDOFF.md').write_text(handoff(ME), encoding='utf-8')
        self.denied('dirty-unknown', assess_start, self.b, ME, env=self.env)

    def test_location_must_be_a_branch_tracking_its_own_remote_branch(self):
        self.git(self.b, 'switch', '--quiet', '-c', 'topic')
        self.denied('no-upstream', assess_start, self.b, ME, env=self.env)
        self.git(self.b, 'branch', '--quiet', '--set-upstream-to=origin/main')
        self.denied('upstream-mismatch', assess_start, self.b, ME, env=self.env)
        self.git(self.b, 'switch', '--quiet', '--detach', 'main')
        self.denied('detached-head', assess_start, self.b, ME, env=self.env)

    def test_remote_marker_decides_occupancy_not_the_local_copy(self):
        self.commit(self.a, 'HANDOFF.md', handoff(OTHER))
        self.git(self.a, 'push', '--quiet')
        self.git(self.b, 'fetch', '--quiet')
        self.git(self.b, 'pull', '--quiet', '--ff-only')
        self.denied('busy-other-machine', assess_start, self.b, ME, env=self.env)
        self.commit(self.a, 'HANDOFF.md', handoff(ME))
        self.git(self.a, 'push', '--quiet')
        self.git(self.b, 'pull', '--quiet', '--ff-only')
        self.assertEqual(assess_start(self.b, ME, env=self.env)['remote_owner'], ME)
        self.denied('invalid-owner', assess_start, self.b, IDLE, env=self.env)
        self.denied('invalid-owner', assess_start, self.b, '  ', env=self.env)

    def test_two_lines_are_separate_and_a_second_writer_on_one_line_stops(self):
        # F25: each branch carries its own marker, so two lines do not block each other.
        self.git(self.a, 'switch', '--quiet', '-c', 'line2')
        self.git(self.a, 'push', '--quiet', '-u', 'origin', 'line2')
        assess_start(self.a, ME, env=self.env)
        self.commit(self.a, 'HANDOFF.md', handoff(ME))
        self.git(self.a, 'push', '--quiet')
        assess_start(self.b, OTHER, env=self.env)  # main is still idle
        # A second writer on line2 stops, however old the first claim looks.
        stale = '`mac` ／ `Claude Code` ／ `㊣　20010101｜舊｜工作中｜交棒0次`，2001-01-01 00:00 (+08) 開工'
        self.commit(self.a, 'HANDOFF.md', handoff(stale))
        self.git(self.a, 'push', '--quiet')
        self.git(self.b, 'fetch', '--quiet')
        self.git(self.b, 'switch', '--quiet', '--track', 'origin/line2')
        self.denied('busy-other-machine', assess_start, self.b, OTHER, env=self.env)
        self.git(self.b, 'switch', '--quiet', 'main')
        assess_start(self.b, OTHER, env=self.env)

    def test_occupancy_codes_separate_machine_tool_and_session(self):
        # F4: same machine with another tool, another session, an old marker
        # without a tool field and an unreadable remote are all told apart.
        cases = (
            ('`win` ／ `Claude Code` ／ `s1`', 'busy-other-machine'),
            ('`mac` ／ `Codex CLI` ／ `s1`', 'busy-same-machine-other-tool'),
            ('`mac` ／ `Claude Code` ／ `㊣　26110800｜舊的｜工作中｜交棒0次`，2026-11-08 開工',
             'busy-same-tool-other-session'),
            ('`mac` ／ `Claude Code`', 'busy-same-tool-other-session'),
            ('`mac` ／ `Claude Code`，2026-11-08 開工', 'busy-same-tool-other-session'),
            ('`mac` ／ `㊣　26110800｜舊格式｜工作中`', 'busy-unidentified-tool'),
            ('`mac`', 'owner-unknown'),
            ('`mac` ／ `` ／ `s1`', 'owner-unknown'),
            ('`mac` ／ `  ` ／ `s1`', 'owner-unknown'),
            ('mac ／ Claude Code ／ s1', 'owner-unknown'),
            ('`mac`x ／ `Claude Code` ／ `s1`', 'owner-unknown'),
        )
        for marker, code in cases:
            with self.subTest(marker=marker):
                self.commit(self.a, 'HANDOFF.md', handoff(marker))
                self.git(self.a, 'push', '--quiet')
                self.denied(code, assess_start, self.a, ME, env=self.env)
        for bad in ('not a marker', '`mac` ／ `Claude Code`', '`mac` ／ `` ／ `s`'):
            with self.subTest(owner=bad):
                self.denied('invalid-owner', assess_start, self.a, bad, env=self.env)
        self.origin.rename(self.root / 'moved.git')
        self.denied('fetch-failed', assess_start, self.a, ME, env=self.env)

    def test_missing_or_ambiguous_owner_is_unknown_not_idle(self):
        for text in ('# HANDOFF\n', handoff(IDLE) + handoff(IDLE), handoff('')):
            with self.subTest(text=text):
                self.commit(self.a, 'HANDOFF.md', text)
                self.git(self.a, 'push', '--quiet')
                self.denied('owner-unknown', assess_start, self.a, ME, env=self.env)
        self.git(self.a, 'rm', '--quiet', 'HANDOFF.md')
        self.git(self.a, 'commit', '--quiet', '-m', 'drop')
        self.git(self.a, 'push', '--quiet')
        self.denied('owner-unknown', assess_start, self.a, ME, env=self.env)

    # --- F10: finish only on a confirmed release --------------------------------

    def claim_and_work(self, repo):
        assess_start(repo, ME, env=self.env)
        self.commit(repo, 'HANDOFF.md', handoff(ME))
        self.git(repo, 'push', '--quiet')
        self.commit(repo, 'work.txt', 'done')
        self.commit(repo, 'HANDOFF.md', handoff(IDLE))

    def checks(self, repo):
        return [run_check(repo, ['git', 'diff', '--quiet', 'HEAD'], env=self.env)]

    def test_successful_finish_returns_receipt_that_counts_once(self):
        self.claim_and_work(self.b)
        receipt = finish(self.b, self.checks(self.b), env=self.env)
        self.assertTrue(receipt.valid())
        self.assertEqual(receipt.event_id, self.remote_head())
        session = Session('26110922', '測試')
        handed = session.transition('handoff', receipt)
        self.assertEqual((handed.state, handed.count), ('handed_off', 1))
        self.assertEqual(handed.transition('handoff', receipt).count, 1)

    def test_remote_advance_blocks_finish_without_pushing(self):
        self.claim_and_work(self.b)
        self.commit(self.a, 'a.txt', 'foreign')
        self.git(self.a, 'pull', '--quiet', '--rebase=false', '--no-edit')
        self.git(self.a, 'push', '--quiet')
        before = self.remote_head()
        self.denied('remote-advanced', finish, self.b, self.checks(self.b), env=self.env)
        self.assertEqual(self.remote_head(), before)

    def test_rejected_push_gives_no_receipt(self):
        self.claim_and_work(self.b)
        hook = self.origin / 'hooks' / 'pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        before = self.remote_head()
        self.denied('push-failed', finish, self.b, self.checks(self.b), env=self.env)
        self.assertEqual(self.remote_head(), before)
        self.assertEqual(owner_field(self.git(self.root, '--git-dir', str(self.origin),
                                              'show', 'main:HANDOFF.md')), ME)

    def test_offline_finish_is_not_a_handoff(self):
        self.claim_and_work(self.b)
        self.origin.rename(self.root / 'moved.git')
        self.denied('fetch-failed', finish, self.b, self.checks(self.b), env=self.env)

    def test_finish_needs_checks_clean_tree_and_released_marker(self):
        self.claim_and_work(self.b)
        before = self.remote_head()
        good = self.checks(self.b)
        for value in (True, False, None, [], 'yes', [True], [{**good[0], 'extra': 1}],
                      [{**good[0], 'exit': False}]):
            with self.subTest(checks=value):
                self.denied('final-checks-missing', finish, self.b, value, env=self.env)
        for value in ([{**good[0], 'exit': 1}], [{**good[0], 'skipped': 1}],
                      good + [{**good[0], 'exit': 2}]):
            with self.subTest(checks=value):
                self.denied('final-checks-failed', finish, self.b, value, env=self.env)
        (self.b / 'stray.txt').write_text('x')
        self.denied('final-tree-dirty', finish, self.b, good, env=self.env)
        (self.b / 'stray.txt').unlink()
        # A receipt for the previous tree does not cover a later commit.
        self.commit(self.b, 'late.txt', 'changed after checks')
        self.denied('final-checks-stale', finish, self.b, good, env=self.env)
        self.commit(self.b, 'HANDOFF.md', handoff(ME))
        self.denied('marker-not-released', finish, self.b, self.checks(self.b), env=self.env)
        self.assertEqual(self.remote_head(), before)

    def test_check_receipts_record_failure_skip_and_tree_changes(self):
        self.claim_and_work(self.b)
        tree = self.git(self.b, 'rev-parse', 'HEAD^{tree}')
        failed = run_check(self.b, ['sh', '-c', 'exit 3'], env=self.env)
        self.assertEqual((failed['exit'], failed['tree']), (3, tree))
        skipped = run_check(self.b, ['sh', '-c', 'echo "[ skip ] bash missing"'], env=self.env)
        self.assertEqual((skipped['exit'], skipped['skipped']), (0, 1))
        self.denied('check-changed-tree', run_check, self.b,
                    ['sh', '-c', 'echo x > made.txt'], env=self.env)
        (self.b / 'made.txt').unlink()
        self.denied('invalid-check', run_check, self.b, [], env=self.env)
        (self.b / 'dirty.txt').write_text('x')
        self.denied('final-tree-dirty', run_check, self.b, ['true'], env=self.env)

    def test_post_push_recheck_catches_unreleased_remote(self):
        self.claim_and_work(self.b)
        # A server-side hook rewrites nothing but a racing writer re-occupies the
        # branch right after our push lands: emulate with a post-receive hook.
        hook = self.origin / 'hooks' / 'post-receive'
        hook.write_text(
            '#!/bin/sh\n'
            'unset GIT_DIR\n'
            f'git clone --quiet "{self.origin}" "{self.root}/racer" >/dev/null 2>&1 || exit 0\n'
            f'cd "{self.root}/racer" || exit 0\n'
            f"printf '%s\\n' '# HANDOFF' '' '## Git 狀態' '- **工作中**：{OTHER}' > HANDOFF.md\n"
            'git commit --quiet -am race >/dev/null 2>&1 && git push --quiet >/dev/null 2>&1\n'
            'exit 0\n', encoding='utf-8')
        hook.chmod(0o755)
        self.denied('remote-not-confirmed', finish, self.b, self.checks(self.b), env=self.env)


if __name__ == '__main__':
    unittest.main()
