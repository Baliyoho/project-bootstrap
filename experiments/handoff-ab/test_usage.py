"""Offline checks for selected-turn usage extraction."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().with_name('usage.py')
spec = importlib.util.spec_from_file_location('handoff_usage', MODULE)
usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usage)


class UsageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'events.jsonl'

    def rows(self, *rows):
        self.path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')

    def test_codex_turn_boundary_and_missing_completion(self):
        start = {'type': 'event_msg', 'timestamp': '2026-01-01T00:00:00Z',
                 'payload': {'type': 'task_started', 'turn_id': 'a'}}
        token = {'type': 'token_usage_record', 'payload': {'turn_id': 'a', 'response_id': 'r1',
                 'turn_token_usage': {'input_tokens': 10, 'cached_input_tokens': 4,
                                      'output_tokens': 2}}}
        done = {'type': 'event_msg', 'timestamp': '2026-01-01T00:00:02Z',
                'payload': {'type': 'task_complete', 'turn_id': 'a'}}
        other = {'type': 'token_usage_record', 'payload': {'turn_id': 'b', 'response_id': 'r2',
                 'turn_token_usage': {'input_tokens': 900}}}
        self.rows(start, token, token, other, done)
        result = usage.codex(self.path, 'a')
        self.assertEqual((result['model_responses'], result['input_tokens'],
                          result['noncached_input_tokens'], result['seconds']), (1, 10, 6, 2.0))
        self.rows(start, token)
        self.assertIsNone(usage.codex(self.path, 'a')['seconds'])
        self.assertFalse(usage.codex(self.path, 'a')['complete'])
        missing_id = {'type': 'token_usage_record', 'payload': {'turn_id': 'a',
                      'turn_token_usage': {'input_tokens': 12, 'cached_input_tokens': 4,
                                           'output_tokens': 3}}}
        self.rows(start, token, missing_id, done)
        self.assertIsNone(usage.codex(self.path, 'a')['model_responses'])

    def test_claude_stream_dedup_and_cache_columns(self):
        user = {'type': 'user', 'uuid': 'u1', 'timestamp': '2026-01-01T00:00:00Z',
                'message': {'content': 'start'}}
        assistant = {'type': 'assistant', 'timestamp': '2026-01-01T00:00:03Z',
                     'message': {'id': 'm1', 'stop_reason': 'end_turn', 'usage': {
                         'input_tokens': 2, 'cache_creation_input_tokens': 3,
                         'cache_read_input_tokens': 5, 'output_tokens': 7}}}
        next_user = {'type': 'user', 'uuid': 'u2', 'message': {'content': 'next'}}
        later = {'type': 'assistant', 'message': {'id': 'm2', 'usage': {
            'input_tokens': 100, 'cache_creation_input_tokens': 0,
            'cache_read_input_tokens': 0, 'output_tokens': 1}}}
        self.rows(user, assistant, assistant, next_user, later)
        result = usage.claude(self.path, 'u1')
        self.assertEqual((result['model_responses'], result['input_tokens'],
                          result['cached_input_tokens'], result['noncached_input_tokens'],
                          result['seconds']), (1, 10, 5, 5, 3.0))
        assistant['message']['usage'].pop('cache_read_input_tokens')
        assistant['message']['stop_reason'] = 'tool_use'
        self.rows(user, assistant)
        result = usage.claude(self.path, 'u1')
        self.assertIsNone(result['cached_input_tokens'])
        self.assertIsNone(result['seconds'])
        self.assertEqual(result['noncached_input_tokens'], None)
        later_assistant = {'type': 'assistant', 'timestamp': '2026-01-01T00:00:04Z',
                           'message': {'id': 'm2', 'stop_reason': 'tool_use', 'usage': {
                               'input_tokens': 1, 'cache_creation_input_tokens': 0,
                               'cache_read_input_tokens': 0, 'output_tokens': 1}}}
        self.rows(user, {'type': 'assistant', 'timestamp': '2026-01-01T00:00:03Z',
                         'message': {'id': 'm1', 'stop_reason': 'end_turn', 'usage': {
                             'input_tokens': 2, 'cache_creation_input_tokens': 3,
                             'cache_read_input_tokens': 5, 'output_tokens': 7}}}, later_assistant)
        self.assertFalse(usage.claude(self.path, 'u1')['complete'])


if __name__ == '__main__':
    unittest.main()
