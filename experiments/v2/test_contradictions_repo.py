"""F45 on this repo's own documents: the declared table must find nothing.

Kept apart from test_contradictions so mutation runs, which copy only
experiments/, never depend on the repo's documents.
"""

from pathlib import Path
import unittest

from experiments.v2.contradictions import REPO_CONFIG, REPO_DOCS, check, read_docs

ROOT = Path(__file__).resolve().parents[2]


class RepoDocumentTests(unittest.TestCase):
    def test_repo_documents_have_no_declared_contradiction(self):
        result = check(read_docs(ROOT, REPO_DOCS), REPO_CONFIG)
        self.assertEqual((result['findings'], result['unknown']), ([], []))
        self.assertEqual(result['overall'], '未發現')

    def test_each_repo_rule_catches_its_reverse_sentence_in_the_real_documents(self):
        reverse = {'core-priority': ('README.md', '兩者衝突以協定為準。'),
                   'requirement-count': ('AGENTS.md', '決策書列出 50 個穩定需求 ID。'),
                   'busy-marker-not-lock': ('README.md', '「工作中」標記是一把互斥鎖。'),
                   'serial-vs-version-line': ('AGENTS.md', '序號跟版本行同一個號。')}
        self.assertEqual(set(reverse), {rule['id'] for rule in REPO_CONFIG['rules']})
        for rule, (doc, sentence) in reverse.items():
            docs = read_docs(ROOT, REPO_DOCS)
            docs[doc] += '\n\n## 注入\n\n' + sentence + '\n'
            with self.subTest(rule=rule):
                found = check(docs, REPO_CONFIG)['findings']
                self.assertIn((rule, doc, 'reverse-rule'),
                              {(f['rule'], f.get('doc'), f['code']) for f in found})


if __name__ == '__main__':
    unittest.main()
