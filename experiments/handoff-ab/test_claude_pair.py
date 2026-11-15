"""Offline checks for the Claude Code adapter; never calls a model or the CLI."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import claude_pair
import comparable
from common import MACHINE, busy_value, out

SID = '11111111-2222-4333-8444-555555555555'
USAGE = {'input_tokens': 2, 'cache_creation_input_tokens': 3,
         'cache_read_input_tokens': 5, 'output_tokens': 7}


def tool_use(ident, name, **args):
    return {'type': 'assistant', 'message': {'content': [
        {'type': 'tool_use', 'id': ident, 'name': name, 'input': args}]}}


def stream(model='claude-opus-5-5', facts=True, result=None, session_id=SID):
    hook = {'type': 'system', 'subtype': 'hook_response',
            'stdout': '[facts] 時間' if facts else 'nothing'}
    return [{'type': 'system', 'subtype': 'init', 'model': model, 'session_id': session_id,
             'skills': ['handoff']}, hook,
            tool_use('t1', 'Read', file_path='HANDOFF.md'),
            tool_use('t1', 'Read', file_path='HANDOFF.md'),       # 重複串流，同一個 id
            tool_use('t2', 'Skill', skill='handoff'),
            tool_use('t3', 'Bash', command='git fetch origin && git status'),
            tool_use('t4', 'Bash', command='python3 tools/verify_state.py'),
            tool_use('t5', 'Bash', command='cat AGENTS.md'),
            result or {'type': 'result', 'subtype': 'success', 'is_error': False,
                       'result': 'done', 'duration_ms': 9000, 'duration_api_ms': 7000,
                       'num_turns': 6}]


def session(extra_user=False, finished=True):
    def assistant(ident, stop, when):
        return {'type': 'assistant', 'timestamp': when,
                'message': {'id': ident, 'stop_reason': stop, 'usage': dict(USAGE)}}
    rows = [{'type': 'user', 'uuid': 'u1', 'timestamp': '2026-01-01T00:00:00Z',
             'message': {'content': 'start'}},
            assistant('m1', 'tool_use', '2026-01-01T00:00:01Z'),
            assistant('m1', 'tool_use', '2026-01-01T00:00:01Z'),
            # Skill 載入：harness 插進來的 isMeta 文字，不是新的一輪
            {'type': 'user', 'uuid': 'meta1', 'isMeta': True, 'sourceToolUseID': 't2',
             'message': {'content': [{'type': 'text', 'text': 'skill body'}]}},
            {'type': 'user', 'uuid': 'r1',
             'message': {'content': [{'type': 'tool_result', 'content': 'ok'}]}}]
    if finished:
        rows.append(assistant('m2', 'end_turn', '2026-01-01T00:00:04Z'))
    if extra_user:
        rows.append({'type': 'user', 'uuid': 'u2', 'message': {'content': 'again'}})
    return rows


class ClaudePairTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='pb-claude-pair-')
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name).resolve()
        env = mock.patch.dict(os.environ, {'HANDOFF_AB_ROOT': str(self.root)})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop('HANDOFF_AB_CONFIG', None)
        self.run_dir = self.root / 'runs' / 'takeover-A-1'
        self.run_dir.mkdir(parents=True)
        self.projects = self.root / 'claude-config' / 'projects' / 'slug'
        self.projects.mkdir(parents=True)
        self.write(self.run_dir / 'run-config.json', [{'session_id': SID}])
        self.write(self.run_dir / 'stream.jsonl', stream())
        self.write(self.projects / (SID + '.jsonl'), session())

    def write(self, path, rows):
        path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
                        encoding='utf-8')

    def problems(self):
        return claude_pair.validity(self.root, self.run_dir)

    def test_valid_cell_usage_and_observed_actions(self):
        self.assertEqual(self.problems(), [])
        got = claude_pair.usage_for(self.root, self.run_dir)
        # 兩個 message id（m1 重複串流只算一次），isMeta 那一則沒有把回合切斷
        self.assertEqual((got['complete'], got['model_responses'], got['input_tokens'],
                          got['cached_input_tokens'], got['noncached_input_tokens'],
                          got['output_tokens'], got['seconds']), (True, 2, 20, 10, 10, 14, 4.0))
        seen = claude_pair.observation(self.run_dir)
        self.assertEqual((seen['tool_calls'], seen['read_commands'], seen['verify_commands'],
                          seen['git_commands'], seen['skill_calls']), (5, 2, 1, 1, 1))
        self.assertIsNone(seen['waiting_seconds'])
        self.assertEqual(claude_pair.cli_reported(self.run_dir)['num_turns'], 6)

    def test_stream_problems_are_invalid(self):
        for rows, expect in (
                (stream(model='claude-sonnet-5-5'), '模型是'),
                (stream(facts=False), '開場 hook'),
                (stream(session_id='other'), 'session id'),
                (stream(result={'type': 'result', 'subtype': 'error_during_execution',
                                'is_error': True}), 'result 事件'),
                (stream()[:-1], 'result 事件'),
                (stream() + [tool_use('t9', 'Read', file_path=str(comparable.build.REPO / 'AGENTS.md'))],
                 '測試 repo 以外')):
            self.write(self.run_dir / 'stream.jsonl', rows)
            self.assertTrue(any(expect in p for p in self.problems()), (expect, self.problems()))
        (self.run_dir / 'stream.jsonl').unlink()
        self.assertEqual(self.problems(), ['沒有串流紀錄'])
        self.assertIsNone(claude_pair.observation(self.run_dir)['tool_calls'])

    def test_session_record_problems_leave_usage_unknown(self):
        self.write(self.projects / (SID + '.jsonl'), session(extra_user=True))
        self.assertTrue(any('不是剛好一則' in p for p in self.problems()))
        self.assertIsNone(claude_pair.usage_for(self.root, self.run_dir))
        self.write(self.projects / (SID + '.jsonl'), session(finished=False))
        got = claude_pair.usage_for(self.root, self.run_dir)
        self.assertEqual((got['complete'], got['input_tokens']), (False, None))
        (self.projects / (SID + '.jsonl')).unlink()
        self.assertTrue(any('找不到唯一' in p for p in self.problems()))
        self.assertIsNone(claude_pair.usage_for(self.root, self.run_dir))
        other = self.root / 'claude-config' / 'projects' / 'slug2'
        other.mkdir()
        for folder in (self.projects, other):
            self.write(folder / (SID + '.jsonl'), session())
        self.assertTrue(any('找不到唯一' in p for p in self.problems()))

    def test_command_keeps_session_record(self):
        with mock.patch.object(claude_pair.claude_cli, 'claude_bin', return_value='claude'):
            cmd = claude_pair.command('hi', SID)
        self.assertNotIn('--no-session-persistence', cmd)
        self.assertEqual(cmd[cmd.index('--session-id') + 1], SID)
        self.assertEqual(cmd[cmd.index('--effort') + 1], claude_pair.EFFORT)


class ClaudeFixtureTest(unittest.TestCase):
    def test_claude_fixture_marker_and_tool_guard(self):
        with tempfile.TemporaryDirectory(prefix='pb-claude-fixture-') as folder, \
                mock.patch.object(comparable, 'TOOL', 'claude'):
            root = pathlib.Path(folder).resolve()
            comparable.prepare(root)
            plan = json.loads((root / 'paired-plan.json').read_text(encoding='utf-8'))
            self.assertEqual((plan['tool'], plan['model'], plan['reasoning']),
                             ('claude', claude_pair.MODEL, claude_pair.EFFORT))
            cell = root / 'runs' / 'handoff-A-1'
            marker = busy_value(out(cell / 'origin.git', 'show', 'main:HANDOFF.md'))
            self.assertIn(MACHINE, marker)
            self.assertIn(claude_pair.MARKER_TOOL, marker)
            self.assertNotIn('Codex', marker)
            self.assertFalse((cell / 'stream.jsonl').exists())
            with mock.patch.object(comparable, 'TOOL', 'codex'), \
                    mock.patch.object(claude_pair, 'launch') as launch:
                with self.assertRaisesRegex(RuntimeError, '為 claude 準備'):
                    comparable.execute(root, 'handoff-A-1')
                launch.assert_not_called()
            # 沒跑過模型的格子：不能算數，用量未知
            row = comparable.assess(cell)
            self.assertEqual((row['verdict'], row['usage']), ('INVALID', None))


if __name__ == '__main__':
    unittest.main()
