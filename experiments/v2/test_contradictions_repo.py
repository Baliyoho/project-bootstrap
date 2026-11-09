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


if __name__ == '__main__':
    unittest.main()
