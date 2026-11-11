"""The local formatter in test_ingest must print exactly what verify_bootstrap prints.

Kept apart because it imports tools/, which mutation runs do not copy.
"""

import contextlib
import importlib.util
import io
from pathlib import Path
import unittest

from tests.test_ingest import real_lines

ROOT = Path(__file__).resolve().parents[1]
ROWS = [('OK', '骨架檔案清單', '22 檔'), ('FAIL', '跨平台防呆', '絕對路徑'), ('SKIP', 'bash 情境'),
        ('OK', '空說明', '')]


class FormatTests(unittest.TestCase):
    def test_local_formatter_matches_the_real_record_function(self):
        spec = importlib.util.spec_from_file_location('vb_under_test',
                                                      ROOT / 'tools/verify_bootstrap.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for row in ROWS:
                module.record(*row)
        self.assertEqual(out.getvalue(), real_lines(*ROWS))


if __name__ == '__main__':
    unittest.main()
