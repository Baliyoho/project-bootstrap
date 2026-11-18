"""P2 slice 2: project pointer and per-write check, with a disposable ssh-keygen signer."""
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from project_bootstrap import package, pointer, release
from project_bootstrap.contracts import Denied
from project_bootstrap.release import statement

PROSE = '# kit\n\n> 版本：**2026-11-11.4**（測試）\n'
FILES = {
    '.claude/skills/handoff/SKILL.md': 'skill v1\n',
    '.claude/hooks/check.sh': '#!/bin/sh\necho v1\n',
    '.claude/settings.json': '{}\n',
    'AGENTS.md': '# agents\n',
    'HANDOFF.md': '# handoff\n',
}
OWNERS = {
    '.claude/skills/handoff/SKILL.md': {'owner': 'core', 'update': 'whole'},
    '.claude/hooks/check.sh': {'owner': 'adapter', 'update': 'whole'},
    '.claude/settings.json': {'owner': 'adapter', 'update': 'wiring'},
    'AGENTS.md': {'owner': 'project', 'update': 'seed'},
    'HANDOFF.md': {'owner': 'project', 'update': 'lines'},
}
OP = 'a' * 32
NOW = 1_794_000_000
TODAY = time.strftime('%Y-%m-%d', time.gmtime(NOW))
YESTERDAY = time.strftime('%Y-%m-%d', time.gmtime(NOW - 86400))
SUPPORTED = platform.system() == 'Darwin' and release.VERIFIER.is_file()


def needs_signer(test):
    """Without ssh-keygen, check the gate fails closed instead of skipping (no skips in A4)."""
    def run(self):
        if SUPPORTED:
            return test(self)
        with patch.object(release, 'VERIFIER', self.root / 'unavailable'):
            gate = pointer.WriteCheck(self.project, self.cache, b'ssh-ed25519 ' + b'A' * 68,
                                      lambda nonce: (b'{}', b'sig'))
            with self.assertRaises(Denied) as caught:
                gate.confirm(OP, 'x.md')
        self.assertEqual(str(caught.exception), 'channel-verifier-unavailable')
    run.__name__, run.__doc__ = test.__name__, test.__doc__
    return run


class PointerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='pointer-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.cache = self.root / 'cache'
        self.project = self.root / 'project'
        self.key, self.public = self.keypair('ci') if SUPPORTED else (None, None)
        self.installed = self.publish(FILES)
        self.latest = self.installed
        for path, text in FILES.items():
            (self.project / path).parent.mkdir(parents=True, exist_ok=True)
            (self.project / path).write_text(text)
        self.write_pointer()
        self.now, self.epoch = NOW, 5
        self.offline, self.replay, self.fetched = False, None, []

    def keypair(self, name):
        key = self.root / name
        subprocess.run([str(release.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f', str(key)],
                       check=True, timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return key, b' '.join(key.with_suffix('.pub').read_bytes().split()[:2])

    def publish(self, files, kind='formal'):
        """Build a package, mark it formal (slice 3 stand-in) and put it in the cache."""
        folder, manifest = package.build(PROSE, files, OWNERS, 'kit')
        manifest['kind'] = kind
        (Path(folder) / package.MANIFEST).write_bytes(package._dump(manifest))
        digest = package.digest(manifest)
        target = self.cache / digest
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(folder, target)
        else:
            shutil.rmtree(folder)
        return digest

    def write_pointer(self, **changes):
        data = {'schema': 1, 'channel': 'stable', 'installed': self.installed, 'exception': None}
        data.update(changes)
        path = self.project / pointer.POINTER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding='utf-8')

    def exception(self, **changes):
        data = {'pin': self.installed, 'paths': ['docs'], 'reason': 'waiting for review',
                'declared_by': 'owner', 'review_by': TODAY}
        data.update(changes)
        return data

    def sign(self, document, key=None):
        return subprocess.run([str(release.VERIFIER), '-Y', 'sign', '-f', str(key or self.key),
                               '-n', release.NAMESPACE], input=document, capture_output=True,
                              check=True, timeout=3).stdout

    def endpoint(self, nonce, channel='stable', key=None, issued=None, expires=None):
        if self.offline:
            raise ConnectionError('synthetic outage')
        if self.replay is not None:
            return self.replay
        document = statement(channel, self.epoch, self.latest, nonce,
                             self.now - 5 if issued is None else issued,
                             self.now + 60 if expires is None else expires)
        answer = (document, self.sign(document, key))
        self.fetched.append(answer)
        return answer

    def check(self, fetch=None):
        return pointer.WriteCheck(self.project, self.cache, self.public,
                                  fetch or self.endpoint, clock=lambda: self.now)

    def denied(self, code, call, *args):
        with self.assertRaises(Denied) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)

    @needs_signer
    def test_fresh_write_confirms_every_time(self):
        gate = self.check()
        result = gate.confirm(OP, 'docs/a.md')
        self.assertEqual(result, {'operation': OP, 'target': 'docs/a.md', 'epoch': 5,
                                  'version': '2026-11-11.4', 'installed': self.installed,
                                  'latest': self.installed, 'pinned': False})
        gate.confirm('b' * 32, 'docs/a.md')
        self.assertEqual(len(self.fetched), 2)

    @needs_signer
    def test_project_files_and_wiring_may_differ(self):
        (self.project / 'AGENTS.md').write_text('# our own rules\n')
        (self.project / 'HANDOFF.md').write_text('# busy\n')
        (self.project / '.claude/settings.json').write_text('{"permissions": {}}\n')
        self.check().confirm(OP, 'AGENTS.md')

    @needs_signer
    def test_crlf_copy_of_a_shared_file_passes_but_other_bytes_do_not(self):
        hook = self.project / '.claude/hooks/check.sh'
        original = FILES['.claude/hooks/check.sh'].encode('utf-8')
        hook.write_bytes(original.replace(b'\n', b'\r\n'))  # Q26 (a): Git may check out CRLF
        self.check().confirm(OP, 'x.md')
        hook.write_bytes(original.replace(b'\n', b'\r'))  # a lone CR is still a change
        self.denied('component-drift:.claude/hooks/check.sh', self.check().confirm, OP, 'x.md')
        hook.write_bytes(original.replace(b'echo', b'ec\rho'))  # so is a stray CR inside a line
        self.denied('component-drift:.claude/hooks/check.sh', self.check().confirm, OP, 'x.md')
        hook.write_bytes(original + b'\r\n')  # an extra line, even an empty one, is a change
        self.denied('component-drift:.claude/hooks/check.sh', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_local_edit_of_shared_files_stops(self):
        (self.project / '.claude/hooks/check.sh').write_text('#!/bin/sh\necho edited\n')
        self.denied('component-drift:.claude/hooks/check.sh', self.check().confirm, OP, 'x.md')
        (self.project / '.claude/hooks/check.sh').write_text(FILES['.claude/hooks/check.sh'])
        (self.project / '.claude/skills/handoff/SKILL.md').unlink()
        self.denied('component-missing:.claude/skills/handoff/SKILL.md', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_new_release_changing_only_a_hook_stops_old_projects(self):
        self.latest = self.publish(dict(FILES, **{'.claude/hooks/check.sh': '#!/bin/sh\necho v2\n'}))
        self.assertNotEqual(self.latest, self.installed)
        self.denied('release-mismatch', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_offline_refuses_even_after_a_good_write(self):
        gate = self.check()
        gate.confirm(OP, 'x.md')
        self.offline = True
        self.denied('channel-unreachable', gate.confirm, OP, 'x.md')

    @needs_signer
    def test_bad_statements(self):
        gate = self.check()
        gate.confirm(OP, 'x.md')
        self.replay = self.fetched[-1]
        self.denied('stale-confirmation', gate.confirm, OP, 'x.md')
        self.replay = None
        other, _ = self.keypair('other')
        cases = {
            'wrong-channel': lambda n: self.endpoint(n, channel='beta'),
            'invalid-channel-signature': lambda n: self.endpoint(n, key=other),
            'stale-confirmation': lambda n: self.endpoint(n, issued=NOW - 100, expires=NOW - 1),
        }
        for code, fetch in cases.items():
            with self.subTest(code=code):
                self.denied(code, self.check(fetch).confirm, OP, 'x.md')
        future = lambda n: self.endpoint(n, issued=NOW + 10, expires=NOW + 100)  # noqa: E731
        self.denied('stale-confirmation', self.check(future).confirm, OP, 'x.md')

        def text_epoch(nonce):
            document = json.dumps({'channel': 'stable', 'epoch': '5', 'manifest': self.latest,
                                   'nonce': nonce, 'issued': NOW - 5, 'expires': NOW + 60},
                                  sort_keys=True, separators=(',', ':')).encode('ascii')
            return document, self.sign(document)
        self.denied('invalid-channel-statement', self.check(text_epoch).confirm, OP, 'x.md')
        self.denied('invalid-channel-statement', self.check(lambda n: (b'', b'sig')).confirm, OP, 'x.md')
        document = json.dumps({'channel': 'stable'}).encode('ascii')
        self.denied('invalid-channel-statement',
                    self.check(lambda n: (document, self.sign(document))).confirm, OP, 'x.md')
        self.epoch = 4
        self.denied('channel-rollback', gate.confirm, OP, 'x.md')

    @needs_signer
    def test_rejected_write_does_not_raise_the_epoch(self):
        gate = self.check()
        self.epoch = 9
        self.latest = 'f' * 64
        self.denied('release-mismatch', gate.confirm, OP, 'x.md')
        self.latest, self.epoch = self.installed, 6
        gate.confirm(OP, 'x.md')

    @needs_signer
    def test_pointer_problems(self):
        (self.project / pointer.POINTER).unlink()
        self.denied('no-pointer', self.check().confirm, OP, 'x.md')
        (self.project / pointer.POINTER).write_text('{', encoding='utf-8')
        self.denied('invalid-pointer', self.check().confirm, OP, 'x.md')
        self.write_pointer(installed='e' * 64)
        self.denied('package-not-cached', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_pointer_is_read_again_for_each_write(self):
        gate = self.check()
        gate.confirm(OP, 'x.md')
        self.write_pointer(channel='beta')
        self.denied('wrong-channel', gate.confirm, OP, 'x.md')

    @needs_signer
    def test_cached_package_problems(self):
        folder = self.cache / self.installed
        (folder / 'AGENTS.md').write_text('tampered\n')
        self.denied('package-damaged:digest:AGENTS.md', self.check().confirm, OP, 'x.md')
        (folder / 'AGENTS.md').write_text(FILES['AGENTS.md'])
        moved = self.cache / ('d' * 64)
        shutil.copytree(folder, moved)
        self.write_pointer(installed='d' * 64)
        self.denied('package-mismatch', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_debug_package_refused(self):
        self.installed = self.publish(FILES, kind='debug')
        self.latest = self.installed
        self.write_pointer()
        self.denied('debug-release', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_declared_exception_pins_within_scope_and_date(self):
        self.latest = self.publish(dict(FILES, **{'.claude/hooks/check.sh': '#!/bin/sh\necho v2\n'}))
        self.write_pointer(exception=self.exception(paths=['docs', 'notes/today.md']))
        result = self.check().confirm(OP, 'docs/a.md')
        self.assertTrue(result['pinned'])
        self.assertEqual(result['latest'], self.latest)
        self.check().confirm(OP, 'notes/today.md')
        self.denied('exception-out-of-scope', self.check().confirm, OP, 'docsx/a.md')
        self.denied('exception-out-of-scope', self.check().confirm, OP, 'notes/other.md')
        self.write_pointer(exception=self.exception(review_by=YESTERDAY))
        self.denied('exception-expired', self.check().confirm, OP, 'docs/a.md')

    @needs_signer
    def test_exception_does_not_skip_freshness_or_drift(self):
        self.write_pointer(exception=self.exception())
        self.offline = True
        self.denied('channel-unreachable', self.check().confirm, OP, 'docs/a.md')
        self.offline = False
        self.latest = 'f' * 64
        (self.project / '.claude/hooks/check.sh').write_text('#!/bin/sh\necho edited\n')
        self.denied('component-drift:.claude/hooks/check.sh', self.check().confirm, OP, 'docs/a.md')

    @needs_signer
    def test_invalid_operation_and_target(self):
        gate = self.check()
        self.denied('invalid-operation', gate.confirm, 'nope', 'x.md')
        for target in ('', '/abs', 'a/../b', 'a//b', 'a\\b', None):
            with self.subTest(target=target):
                self.denied('invalid-target', gate.confirm, OP, target)
        self.assertEqual(self.fetched, [])

    @needs_signer
    def test_status_is_read_only(self):
        self.offline = True
        report = pointer.status(self.project, self.cache)
        self.assertEqual(report, {'state': 'ok', 'channel': 'stable', 'installed': self.installed,
                                  'exception': None, 'fresh': 'unconfirmed',
                                  'version': '2026-11-11.4', 'kind': 'formal'})
        (self.cache / self.installed / 'AGENTS.md').write_text('tampered\n')
        self.assertEqual(pointer.status(self.project, self.cache)['state'], 'package-damaged')
        self.write_pointer(installed='e' * 64)
        self.assertEqual(pointer.status(self.project, self.cache)['state'], 'package-not-cached')
        (self.project / pointer.POINTER).write_text('[]', encoding='utf-8')
        self.assertEqual(pointer.status(self.project, self.cache)['state'], 'invalid-pointer')
        (self.project / pointer.POINTER).unlink()
        self.assertEqual(pointer.status(self.project, self.cache),
                         {'state': 'no-pointer', 'fresh': 'unconfirmed'})


class ParseTests(unittest.TestCase):
    BASE = {'schema': 1, 'channel': 'stable', 'installed': 'a' * 64, 'exception': None}
    EXC = {'pin': 'a' * 64, 'paths': ['docs'], 'reason': 'r', 'declared_by': 'me',
           'review_by': '2026-12-01'}

    def parsed(self, **changes):
        return pointer.parse(json.dumps(dict(self.BASE, **changes)))

    def denied(self, code, text):
        with self.assertRaises(Denied) as caught:
            pointer.parse(text)
        self.assertEqual(str(caught.exception), code)

    def test_valid(self):
        self.assertEqual(self.parsed(), self.BASE)
        self.assertEqual(self.parsed(exception=self.EXC)['exception'], self.EXC)

    def test_invalid_shape(self):
        for text in ('{', '[]', json.dumps(dict(self.BASE, schema=2)),
                     json.dumps(dict(self.BASE, extra=1)),
                     json.dumps({k: v for k, v in self.BASE.items() if k != 'exception'}),
                     '{"schema":1,"schema":1,"channel":"stable","installed":"%s","exception":null}' % ('a' * 64)):
            with self.subTest(text=text[:30]):
                self.denied('invalid-pointer', text)

    def test_invalid_fields(self):
        cases = {
            'invalid-pointer:channel': [{'channel': 'Stable'}, {'channel': ''}, {'channel': 5}, {'channel': 'a' * 33}],
            'invalid-pointer:installed': [{'installed': 'A' * 64}, {'installed': 'a' * 63}, {'installed': None}],
            'invalid-pointer:exception': [{'exception': 'pin'}, {'exception': dict(self.EXC, extra=1)},
                                          {'exception': {k: v for k, v in self.EXC.items() if k != 'reason'}}],
            'invalid-pointer:pin': [{'exception': dict(self.EXC, pin='b' * 64)}],
            'invalid-pointer:paths': [{'exception': dict(self.EXC, paths=[])},
                                      {'exception': dict(self.EXC, paths='docs')},
                                      {'exception': dict(self.EXC, paths=['../x'])},
                                      {'exception': dict(self.EXC, paths=['/abs'])}],
            'invalid-pointer:reason': [{'exception': dict(self.EXC, reason='  ')},
                                       {'exception': dict(self.EXC, reason=None)}],
            'invalid-pointer:declared_by': [{'exception': dict(self.EXC, declared_by='')}],
            'invalid-pointer:review_by': [{'exception': dict(self.EXC, review_by='soon')},
                                          {'exception': dict(self.EXC, review_by=20261201)}],
        }
        for code, changes in cases.items():
            for change in changes:
                with self.subTest(code=code, change=change):
                    self.denied(code, json.dumps(dict(self.BASE, **change)))


if __name__ == '__main__':
    unittest.main()
