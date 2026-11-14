"""The fetched upstream VERSION wins over a stale local cache in this repo."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


HOOK = Path(__file__).resolve().parents[2] / 'src/kit/files/.claude/hooks/git-freshness.sh.tmpl'


class VersionCacheTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.origin, self.writer, self.reader = root / 'origin.git', root / 'writer', root / 'reader'
        self.git(root, 'init', '-q', '--bare', str(self.origin))
        self.git(root, 'clone', '-q', str(self.origin), str(self.writer))
        self.git(self.writer, 'config', 'user.name', 'Test')
        self.git(self.writer, 'config', 'user.email', 'test@example.invalid')
        (self.writer / 'AGENTS.md').write_text('<!-- 共用制度開始 source: PROJECT-BOOTSTRAP.md v2026-11-14 -->\n')
        (self.writer / 'HANDOFF.md').write_text('- **工作中**：無（已交棒）\n')
        self.publish('2026-11-14')
        self.git(self.origin, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        self.git(root, 'clone', '-q', str(self.origin), str(self.reader))
        (self.reader / '.claude').mkdir()
        self.cache = self.reader / '.claude/.bootstrap-version'
        bin_dir = root / 'bin'
        bin_dir.mkdir()
        git_bin = shutil.which('git')
        (bin_dir / 'git').write_text('#!/bin/sh\nif [ "$1" = remote ] && [ "$2" = get-url ]; then\n'
                                     '  echo "${TEST_ORIGIN_URL:-https://github.com/Baliyoho/project-bootstrap.git}"\n'
                                     'else\n  exec "' + git_bin + '" "$@"\nfi\n')
        (bin_dir / 'git').chmod(0o755)
        (bin_dir / 'curl').write_text('#!/bin/sh\n[ -n "$TEST_CURL_VALUE" ] || exit 7\n'
                                      'printf "%s" "$TEST_CURL_VALUE"\n')
        (bin_dir / 'curl').chmod(0o755)
        self.env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])

    def git(self, cwd, *args):
        return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True)

    def publish(self, version):
        (self.writer / 'VERSION').write_text(version + '\n')
        self.git(self.writer, 'add', 'VERSION', 'AGENTS.md', 'HANDOFF.md')
        self.git(self.writer, 'commit', '-qm', 'version')
        self.git(self.writer, 'push', '-q', 'origin', 'HEAD:main')

    def hook(self):
        result = subprocess.run(['bash', str(HOOK)], cwd=self.reader, env=self.env,
                                check=True, capture_output=True, text=True)
        return json.loads(result.stdout)['hookSpecificOutput']['additionalContext']

    def test_new_fetched_version_replaces_old_cache_and_rejects_invalid(self):
        self.cache.write_text('2026-11-14')
        self.publish('2026-11-14.4')
        self.assertIn('上游 v2026-11-14.4', self.hook())
        self.assertEqual(self.cache.read_text(), '2026-11-14.4')
        self.env['TEST_ORIGIN_URL'] = 'git@github.com:Baliyoho/project-bootstrap.git'
        self.assertIn('上游 v2026-11-14.4', self.hook())
        self.publish('invalid')
        self.assertNotIn('共用制度落後', self.hook())

    def test_fetch_failure_does_not_read_old_tracking_ref(self):
        self.cache.write_text('2026-11-14.4')
        self.git(self.reader, 'remote', 'set-url', 'origin', str(self.reader / 'missing.git'))
        self.assertIn('fetch origin 失敗', self.hook())
        self.assertNotIn('共用制度落後', self.hook())

    def test_generic_project_cache_expiry_and_invalid_http(self):
        self.env['TEST_ORIGIN_URL'] = 'https://example.invalid/project.git'
        self.cache.write_text('2026-11-14.2')
        self.assertIn('上游 v2026-11-14.2', self.hook())
        self.cache.touch()
        os.utime(self.cache, (0, 0))
        self.env['TEST_CURL_VALUE'] = '2026-11-14.3'
        self.assertIn('上游 v2026-11-14.3', self.hook())
        self.assertEqual(self.cache.read_text(), '2026-11-14.3')
        os.utime(self.cache, (0, 0))
        self.env['TEST_CURL_VALUE'] = 'not-a-version'
        self.assertNotIn('共用制度落後', self.hook())
        self.assertEqual(self.cache.read_text(), '2026-11-14.3')
        del self.env['TEST_CURL_VALUE']
        self.assertNotIn('共用制度落後', self.hook())


if __name__ == '__main__':
    unittest.main()
