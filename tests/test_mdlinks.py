"""F20: what a Markdown parser sees that a link regex does not.

Needs markdown-it-py: A4 (verify_v2) leaves this file out and lists it; `uv run pytest` runs it.
"""
import tempfile
from pathlib import Path
import unittest

try:
    from project_bootstrap.mdlinks import dead_links, links, local_target
except ImportError as exc:  # markdown-it-py missing
    raise unittest.SkipTest('needs markdown-it-py (uv run pytest): %s' % exc)


class LinkTests(unittest.TestCase):
    def test_parser_reads_what_a_regex_misreads(self):
        text = ('[paren](a_(b).md) [ref][r] `[code](no.md)` \\[escaped](no2.md) <!-- [c](no3.md) -->\n\n'
                '```\n[fenced](no4.md)\n```\n\n| t |\n|---|\n| [cell](cell.md) |\n\n'
                '![img](pic.png)\n\n[r]: ref.md "title"\n')
        self.assertEqual(links(text), ['a_(b).md', 'ref.md', 'cell.md', 'pic.png'])

    def test_external_and_anchor_links_are_not_files(self):
        for target in ('https://x.invalid/a', 'mailto:a@x.invalid', '#top', 'ftp://x', ''):
            self.assertIsNone(local_target(target), target)
        self.assertEqual(local_target('docs/a%20b.md#part'), 'docs/a b.md')

    def test_dead_links_resolve_from_the_document_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'docs').mkdir()
            (root / 'docs' / 'here.md').write_text('x', encoding='utf-8')
            (root / 'docs' / 'a.md').write_text('[ok](here.md) [up](../top.md) [ref][x]\n\n[x]: gone.md\n',
                                                encoding='utf-8')
            self.assertEqual(dead_links(root, ['docs/a.md']), ['docs/a.md → ../top.md', 'docs/a.md → gone.md'])
            self.assertEqual(dead_links(root, ['docs/a.md'], skip=lambda d, t: True), [])


if __name__ == '__main__':
    unittest.main()
