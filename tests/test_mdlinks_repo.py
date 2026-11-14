"""F20／F46: a second, parser-based dead-link check over this repo's own documents.

Reads the real repo (so it is not in a mutation group). The A4 check in
verify_bootstrap.py uses a regex; this reads the same files with markdown-it-py
and must agree that no local link is dead. src/kit/ is skipped for the same
reason A4 skips it: its text is generated into PROJECT-BOOTSTRAP.md, where
links to files that exist only after deployment are template content.
Needs markdown-it-py: A4 (verify_v2) leaves this file out and lists it; `uv run pytest` runs it.
"""
from pathlib import Path
import subprocess
import sys
import unittest

try:
    from project_bootstrap.mdlinks import dead_links
except ImportError as exc:  # markdown-it-py missing
    raise unittest.SkipTest('needs markdown-it-py (uv run pytest): %s' % exc)

ROOT = Path(__file__).resolve().parents[1]


class RepoLinkTests(unittest.TestCase):
    def test_no_dead_local_link_in_repo_documents(self):
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import verify_bootstrap
        finally:
            sys.path.remove(str(ROOT / 'tools'))
        listed = subprocess.run(['git', 'ls-files', '-z', '--', '*.md'], cwd=ROOT,
                                capture_output=True, check=True).stdout.decode('utf-8').split('\0')
        documents = [p for p in listed if p and not p.startswith('src/kit/')]
        self.assertIn('PROJECT-BOOTSTRAP.md', documents)

        # AGENTS.md carries a verbatim copy of the kit's shared section (2026-11-14); it links
        # the deployed skill path, which this repo deliberately lacks (it reads the global copy).
        # verify_bootstrap checks the copy is byte-identical to the kit template.
        shared_copy = ('.claude/skills/handoff/SKILL.md',)

        def template(document, target):
            if document == 'AGENTS.md' and str(target).split('#')[0] in shared_copy:
                return True
            return document == 'PROJECT-BOOTSTRAP.md' and verify_bootstrap.template_link(target)
        self.assertEqual(dead_links(ROOT, documents, skip=template), [])


if __name__ == '__main__':
    unittest.main()
