"""P2 slice 3b prep: report, keys, epoch, archive, seed and pointer helpers."""
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest

from project_bootstrap import distribute, package, pointer
from project_bootstrap.contracts import Denied

PROSE = '# kit\n\n> 版本：**2026-11-11.6**（測試）\n'
FILES = {'.claude/hooks/check.sh': '#!/bin/sh\necho v1\n', 'AGENTS.md': '# agents\n',
         'docs/notes/a.md': 'a\n'}
OWNERS = {'.claude/hooks/check.sh': {'owner': 'core', 'update': 'whole'},
          'AGENTS.md': {'owner': 'project', 'update': 'seed'},
          'docs/notes/a.md': {'owner': 'project', 'update': 'seed'}}
KEY = 'ssh-ed25519 ' + 'A' * 68
KEY2 = 'ssh-ed25519 ' + 'B' * 68


class DistributeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='distribute-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        folder, self.manifest = package.build(PROSE, FILES, OWNERS, 'kit')
        self.folder = self.root / 'pkg'
        shutil.move(folder, self.folder)

    def denied(self, code, call, *args):
        with self.assertRaises(Denied) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)

    def tar(self, entries):
        """entries: [(TarInfo, bytes or None)] written as a tar.gz."""
        path = self.root / ('t%d.tar.gz' % len(list(self.root.glob('t*.tar.gz'))))
        with tarfile.open(path, 'w:gz') as tar:
            for info, data in entries:
                tar.addfile(info, io.BytesIO(data) if data is not None else None)
        return path

    def entry(self, name, data=b'x', kind=tarfile.REGTYPE, link=''):
        info = tarfile.TarInfo(name)
        info.type, info.linkname = kind, link
        info.size = len(data) if kind == tarfile.REGTYPE else 0
        return info, data if kind == tarfile.REGTYPE else None

    # verifier report
    def test_report_passes_only_on_a_clean_run(self):
        ok = '[  ok  ] alpha  — fine\n[  ok  ] beta\n'
        report = distribute.report_from_verifier(ok, 0, 'c' * 40, 'r1', 0)
        self.assertEqual(report['overall'], '通過')
        self.assertEqual([r['claim'] for r in report['rows']],
                         ['verify_bootstrap:alpha', 'verify_bootstrap:beta', 'verify_bootstrap'])
        self.assertTrue(all(r['state'] == '本輪實查' for r in report['rows']))
        cases = {
            '不通過': [(ok + '[ FAIL ] gamma\n', 2), (ok, 2), ('', 0), ('[ ?? ok ] x\n', 0)],
            '未驗證': [(ok + '[ skip ] gamma\n', 1)],
        }
        for overall, runs in cases.items():
            for text, code in runs:
                with self.subTest(text=text, code=code):
                    self.assertEqual(distribute.report_from_verifier(text, code, 'c', 'r', 0)['overall'], overall)

    # keys and epochs
    def test_load_keys(self):
        self.assertEqual(distribute.load_keys('# root\n\n%s\n  %s  \n%s\n' % (KEY2, KEY, KEY)), [KEY, KEY2])
        self.denied('no-release-keys', distribute.load_keys, '# nothing yet\n\n')
        self.denied('no-release-keys', distribute.load_keys, '')
        self.denied('invalid-release-key', distribute.load_keys, KEY + '\nssh-rsa AAAA\n')

    def test_next_epoch(self):
        self.assertEqual(distribute.next_epoch([]), 1)
        self.assertEqual(distribute.next_epoch([(1, 'a'), (4, 'b'), (2, 'c')]), 5)
        self.denied('channel-conflict', distribute.next_epoch, [(4, 'b'), (4, 'c')])

    def test_asset_names(self):
        self.assertEqual(distribute.asset_names('beta', 3, 'abcdef0123456789' * 4),
                         {'package': 'beta-3-abcdef012345.tar.gz',
                          'record': 'beta-3-abcdef012345.record.json',
                          'signature': 'beta-3-abcdef012345.sig'})

    # archives
    def test_pack_is_reproducible_and_round_trips(self):
        one = distribute.pack(self.folder, self.root / 'one.tar.gz').read_bytes()
        two = distribute.pack(self.folder, self.root / 'two.tar.gz').read_bytes()
        self.assertEqual(one, two)
        self.assertEqual(one[4:8], b'\0\0\0\0')  # gzip header mtime
        folder = distribute.unpack(self.root / 'one.tar.gz', self.root / 'out')
        self.assertEqual(package.check(folder), [])
        self.assertEqual(os.stat(folder / '.claude/hooks/check.sh').st_mode & 0o777, 0o755)
        self.assertEqual(os.stat(folder / 'AGENTS.md').st_mode & 0o777, 0o644)
        with tarfile.open(self.root / 'one.tar.gz') as tar:
            self.assertTrue(all(m.mtime == 0 for m in tar.getmembers()))

    def test_pack_refuses_a_broken_package(self):
        (self.folder / 'AGENTS.md').write_text('edited\n')
        self.denied('bad-package', distribute.pack, self.folder, self.root / 'x.tar.gz')

    def test_unpack_refuses_unsafe_archives(self):
        cases = {
            'unsafe-archive-path:/package/a': [self.entry('/package/a')],
            'unsafe-archive-path:package/../a': [self.entry('package/../a')],
            'unsafe-archive-path:other/a': [self.entry('other/a')],
            'unsafe-archive-path:package//a': [self.entry('package//a')],
            'unsafe-archive-path:package/a\\b': [self.entry('package/a\\b')],
            'unsafe-archive-member:package/link': [self.entry('package/link', kind=tarfile.SYMTYPE, link='/etc')],
            'unsafe-archive-member:package/hard': [self.entry('package/hard', kind=tarfile.LNKTYPE, link='package/a')],
            'unsafe-archive-member:package/fifo': [self.entry('package/fifo', kind=tarfile.FIFOTYPE)],
            'unsafe-archive-path:duplicate': [self.entry('package/a'), self.entry('package/a')],
        }
        for code, entries in cases.items():
            with self.subTest(code=code):
                out = self.root / ('out-' + str(abs(hash(code))))
                self.denied(code, distribute.unpack, self.tar(entries), out)
                self.assertFalse(out.exists())
        garbage = self.root / 'garbage.tar.gz'
        garbage.write_bytes(b'not a tarball')
        self.denied('invalid-archive', distribute.unpack, garbage, self.root / 'g')

    def test_unpack_checks_the_package(self):
        distribute.pack(self.folder, self.root / 'ok.tar.gz')
        with tarfile.open(self.root / 'ok.tar.gz') as tar:
            entries = []
            for member in tar.getmembers():
                data = tar.extractfile(member).read() if member.isfile() else None
                if member.name == 'package/AGENTS.md':
                    data = b'tampered\n'
                    member.size = len(data)
                entries.append((member, data))
        self.denied('bad-package:digest:AGENTS.md', distribute.unpack, self.tar(entries), self.root / 'o')

    # seed and pointer
    def test_seed(self):
        project = self.root / 'new'
        self.assertEqual(distribute.seed(project, self.folder), sorted(FILES))
        self.assertEqual((project / 'docs/notes/a.md').read_text(), 'a\n')
        self.assertFalse((project / package.MANIFEST).exists())
        self.assertEqual(os.stat(project / '.claude/hooks/check.sh').st_mode & 0o111, 0o111)
        self.denied('project-not-empty', distribute.seed, project, self.folder)
        empty = self.root / 'empty'
        empty.mkdir()
        distribute.seed(empty, self.folder)

    def test_write_pointer(self):
        project = self.root / 'p'
        data = distribute.write_pointer(project, 'beta', 'a' * 64, 'https://example.invalid/r.git')
        text = (project / pointer.POINTER).read_text(encoding='utf-8')
        self.assertEqual(pointer.parse(text), data)
        self.assertEqual(data['exception'], None)
        distribute.write_pointer(project, 'beta', 'b' * 64, 'https://example.invalid/r.git')
        self.assertEqual(pointer.parse((project / pointer.POINTER).read_text())['installed'], 'b' * 64)
        exception = {'pin': 'b' * 64, 'paths': ['docs'], 'reason': 'r', 'declared_by': 'me',
                     'review_by': '2026-12-01'}
        current = json.loads((project / pointer.POINTER).read_text())
        (project / pointer.POINTER).write_text(json.dumps(dict(current, exception=exception)))
        self.denied('exception-present', distribute.write_pointer, project, 'beta', 'c' * 64,
                    'https://example.invalid/r.git')
        self.denied('invalid-pointer:source', distribute.write_pointer, self.root / 'q', 'beta', 'a' * 64, '-x')
        self.assertFalse((self.root / 'q' / pointer.POINTER).exists())


if __name__ == '__main__':
    unittest.main()
