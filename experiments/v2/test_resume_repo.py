"""F16a on this repository: with an empty home, AGENTS.md still leads to the procedure."""

from pathlib import Path
import tempfile
import unittest

from experiments.v2.resume import check

ROOT = Path(__file__).resolve().parents[2]


class ResumeRepoTests(unittest.TestCase):
    def test_empty_home_finds_the_procedure_in_the_package(self):
        with tempfile.TemporaryDirectory(prefix='bootstrap-v2-resume-home-') as home:
            result = check(ROOT, home)
        self.assertEqual((result['result'], result['reasons'], result['missing']),
                         ('通過', [], []))
        self.assertIn('PROJECT-BOOTSTRAP.md', [p['path'] for p in result['procedures']])
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertTrue(all(p['source'] for p in result['procedures']))
        # The procedure's marker follows its own edits, so it may be ahead of VERSION, not behind.
        self.assertGreaterEqual(result['procedures'][0]['source'].split(' v')[1], version)


if __name__ == '__main__':
    unittest.main()
