"""F45 on this repo's own documents: the declared table must find nothing.

Kept apart from test_contradictions so mutation runs, which copy only
experiments/, never depend on the repo's documents.
"""

from pathlib import Path
import unittest

from project_bootstrap.contradictions import REPO_CONFIG, REPO_DOCS, check, read_docs

ROOT = Path(__file__).resolve().parents[1]


class RepoDocumentTests(unittest.TestCase):
    def test_repo_documents_have_no_declared_contradiction(self):
        result = check(read_docs(ROOT, REPO_DOCS), REPO_CONFIG)
        self.assertEqual((result['findings'], result['unknown']), ([], []))
        self.assertEqual(result['overall'], '未發現')

    def test_each_repo_rule_catches_its_reverse_sentence_in_the_real_documents(self):
        reverse = {'core-priority': ('README.md', '兩者衝突以協定為準。'),
                   'requirement-count': ('AGENTS.md', '決策書列出 50 個穩定需求 ID。'),
                   'busy-marker-not-lock': ('README.md', '「工作中」標記是一把互斥鎖。'),
                   'serial-vs-version-line': ('AGENTS.md', '序號跟版本行同一個號。'),
                   'version-follows-skill': ('src/kit/', '改到範本就要跳 VERSION。')}
        self.assertEqual(set(reverse), {rule['id'] for rule in REPO_CONFIG['rules']})
        for rule, (doc, sentence) in reverse.items():
            docs = read_docs(ROOT, REPO_DOCS)
            docs[doc] += '\n\n## 注入\n\n' + sentence + '\n'
            with self.subTest(rule=rule):
                found = check(docs, REPO_CONFIG)['findings']
                self.assertIn((rule, doc, 'reverse-rule'),
                              {(f['rule'], f.get('doc'), f['code']) for f in found})

    def test_v3_is_where_the_requirement_count_must_be_stated(self):
        # 2026-11-17 v3 Q39: v2 is archived and unread, so v3 carries the count.
        book = 'project-bootstrap-requirements-decision-v3.md'
        docs = read_docs(ROOT, REPO_DOCS)
        self.assertIn('51 條需求', docs[book])
        docs[book] = docs[book].replace('51 條需求', '這些需求')
        unknown = check(docs, REPO_CONFIG)['unknown']
        self.assertIn((book, 'rule-absent:requirement-count'), unknown)
        docs = read_docs(ROOT, REPO_DOCS)
        docs[book] += '\n\n## 注入\n\n本檔共 50 條需求。\n'
        found = check(docs, REPO_CONFIG)['findings']
        self.assertIn(('requirement-count', book, 'reverse-rule'),
                      {(f['rule'], f.get('doc'), f['code']) for f in found})

if __name__ == '__main__':
    unittest.main()
