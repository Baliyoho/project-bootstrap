"""registry on synthetic documents only (mutation group tests.test_registry).

2026-11-17 (v3 Q39): the real decision book and status index moved to
test_registry_repo.py. Mutation runs copy only src/ and tests/, so a test that
read the repo's documents errored in every run and counted each mutant as
killed whether or not it was caught.
"""
import copy
from pathlib import Path
import tempfile
import unittest

from project_bootstrap.registry import requirement_ids, validate

BOOK = '''# 決策書

## 3. 方案約束

| ID | 決定 |
|---|---|
| F98 | 不是需求列：別節的表 |

## 4. 需求清單

| ID | 功能 | 強度 |
|---|---|---|
| F1 | 目標 | 留痕 |
| F11 | 標記 | 偵測 |

## 5. 之後

| F99 | 不屬於需求清單 |
'''


def row(rid, **extra):
    item = {'id': rid, 'result': '未驗證', 'scope': '合成', 'origin': '合成', 'unknown': '合成',
            'next': '合成', 'evidence': [{'path': 'evidence.txt', 'scope': '合成'}]}
    if rid == 'F11':
        item['parts'] = {k: {'result': '未驗證', 'scope': '合成'} for k in ('a', 'b')}
    item.update(extra)
    return item


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'root'
        self.root.mkdir()
        (self.root / 'evidence.txt').write_text('x', encoding='utf-8')
        (Path(self.tmp.name) / 'outside.txt').write_text('x', encoding='utf-8')
        self.data = {'requirements': [row('F1'), row('F11')]}

    def test_ids_come_from_the_named_section_only(self):
        self.assertEqual(requirement_ids(BOOK), ['F1', 'F11'])
        self.assertEqual(requirement_ids(BOOK.replace('## 4. 需求清單', '## 9. 需求清單')),
                         ['F1', 'F11'])
        self.assertEqual(validate(self.data, BOOK, self.root), [])

    def test_missing_section_is_a_mismatch_not_a_pass(self):
        book = BOOK.replace('需求清單', '別的東西')
        self.assertEqual(requirement_ids(book), [])
        self.assertTrue(validate(self.data, book, self.root))

    def test_section_stops_at_the_next_heading(self):
        book = BOOK.replace('## 5. 之後\n\n| F99 |', '## 5. 之後\n\n| F1 |')
        self.assertEqual(requirement_ids(book), ['F1', 'F11'])

    def test_each_broken_record_is_rejected(self):
        def mutate(change):
            data = copy.deepcopy(self.data)
            rows = data['requirements']
            first, f11 = rows[0], rows[1]
            if change == 'missing':
                rows.pop()
            elif change == 'duplicate':
                rows.append(copy.deepcopy(first))
            elif change == 'extra':
                first['id'] = 'F999'
            elif change == 'empty-field':
                first['next'] = ''
            elif change == 'bad-result':
                first['result'] = '也許'
            elif change == 'success':
                first['result'] = '通過'
            elif change == 'part-missing':
                f11['parts'].pop('b')
            elif change == 'part-bad-result':
                f11['parts']['a']['result'] = '也許'
            elif change == 'part-extra':
                f11['parts']['c'] = {'result': '未驗證', 'scope': '合成'}
            elif change == 'evidence-absent':
                first['evidence'] = [{'path': 'does-not-exist.txt', 'scope': '合成'}]
            elif change == 'evidence-escape':
                first['evidence'] = [{'path': '../outside.txt', 'scope': '合成'}]
            elif change == 'evidence-unscoped':
                first['evidence'] = [{'path': 'evidence.txt'}]
            return data
        for change in ('missing', 'duplicate', 'extra', 'empty-field', 'bad-result', 'success',
                       'part-missing', 'part-bad-result', 'part-extra', 'evidence-absent', 'evidence-escape',
                       'evidence-unscoped'):
            with self.subTest(change=change):
                self.assertTrue(validate(mutate(change), BOOK, self.root))


if __name__ == '__main__':
    unittest.main()
