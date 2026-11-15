"""Offline checks for the same-session relay scorer; never calls a model or the CLI."""
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
import relay
from common import IDLE, MACHINE, out

SID = '11111111-2222-4333-8444-555555555555'
USAGE = {'input_tokens': 1, 'cache_creation_input_tokens': 2,
         'cache_read_input_tokens': 3, 'output_tokens': 4}


class RelayTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='pb-relay-')
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name).resolve()
        for patcher in (mock.patch.dict(os.environ, {'HANDOFF_AB_ROOT': str(self.root)}),
                        mock.patch.object(comparable, 'TOOL', 'claude')):
            patcher.start()
            self.addCleanup(patcher.stop)
        os.environ.pop('HANDOFF_AB_CONFIG', None)
        comparable.prepare(self.root)
        self.cell = self.root / 'runs' / 'takeover-B-1'
        self.work = self.cell / 'work'
        self.env = comparable.fixture_env(self.root, 'subject')
        self.projects = self.root / 'claude-config' / 'projects' / 'slug'
        self.projects.mkdir(parents=True)

    def push(self, edit, message):
        path = self.work / 'HANDOFF.md'
        path.write_text(edit(path.read_text(encoding='utf-8')), encoding='utf-8')
        comparable.git(self.work, 'add', '--', 'HANDOFF.md', env=self.env)
        comparable.git(self.work, 'commit', '-qm', message, env=self.env)
        comparable.git(self.work, 'push', '-q', 'origin', 'main', env=self.env)

    def rows(self, path, rows):
        path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')

    def records(self, second_prompt):
        def assistant(ident, when):
            return {'type': 'assistant', 'timestamp': when,
                    'message': {'id': ident, 'stop_reason': 'end_turn', 'usage': dict(USAGE)}}
        self.rows(self.cell / 'run-config.json', [{'session_id': SID}])
        self.rows(self.cell / relay.EVENTS2, [
            {'type': 'system', 'subtype': 'init', 'model': 'claude-opus-5-5', 'session_id': SID},
            {'type': 'assistant', 'message': {'content': [
                {'type': 'tool_use', 'id': 't1', 'name': 'Bash', 'input': {'command': 'git status'}}]}},
            {'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'done'}])
        self.rows(self.projects / (SID + '.jsonl'), [
            {'type': 'user', 'uuid': 'u1', 'timestamp': '2026-01-01T00:00:00Z',
             'message': {'content': 'first'}},
            assistant('m1', '2026-01-01T00:00:09Z'),
            {'type': 'user', 'uuid': 'u2', 'timestamp': '2026-01-01T00:01:00Z',
             'message': {'content': second_prompt}},
            assistant('m2', '2026-01-01T00:01:05Z')])
        (self.cell / 'wall2.json').write_text('{"seconds": 6.0, "exit": 0}\n', encoding='utf-8')

    def test_relay_turn_two_scoring(self):
        self.push(lambda t: t.replace(IDLE, '`%s` ／ `Claude Code`，開工' % MACHINE, 1), 'claim')
        (self.cell / 'score-turn1.json').write_text(json.dumps(
            {'main_after_turn1': out(self.cell / 'origin.git', 'rev-parse', 'main')}), encoding='utf-8')
        self.records(relay.prompt2('B'))
        self.assertTrue(relay.prompt2('B').endswith(comparable.FOCUS))
        # 還沒交棒：標記沒釋回、沒有第二次推送
        row = relay.assess2(self.cell)
        self.assertEqual(row['invalid'], [])
        self.assertTrue({'handoff-pushed', 'marker-released', 'snapshot-updated'} <= set(row['failed']))

        def handoff(text):
            lines = ['- **交接時間**：2099-01-01 00:00（+08）' if '交接時間' in line else line
                     for line in text.splitlines()]
            return '\n'.join(IDLE.join(line.split('：', 1)[:1] + ['']).replace(IDLE, '：' + IDLE, 1)
                             if '**工作中**' in line else line for line in lines) + '\n'
        self.push(handoff, 'handoff')
        row = relay.assess2(self.cell)
        self.assertEqual((row['failed'], row['verdict']), ([], 'PENDING_REVIEW'))
        # 第二回合的用量只算第二則人類訊息之後
        self.assertEqual((row['usage']['seconds'], row['usage']['model_responses'],
                          row['usage']['input_tokens'], row['tool_calls']), (5.0, 1, 6, 1))
        (self.cell / 'review2.json').write_text(
            '{"subject_verification": true, "task_scope": true}', encoding='utf-8')
        self.assertEqual(relay.assess2(self.cell)['verdict'], 'PASS')
        # 紀錄裡最後一則人類訊息不是第二句提示：不能算數，用量未知
        self.records('something else')
        row = relay.assess2(self.cell)
        self.assertEqual((row['verdict'], row['usage']), ('INVALID', None))
        # 第二回合沒正常結束
        self.records(relay.prompt2('B'))
        (self.cell / 'wall2.json').write_text('{"seconds": 6.0, "exit": "timeout"}\n', encoding='utf-8')
        self.assertEqual(relay.assess2(self.cell)['verdict'], 'INVALID')

    def test_only_prepared_takeover_cells(self):
        with self.assertRaisesRegex(RuntimeError, 'takeover'):
            relay.execute(self.root, 'handoff-A-1')


if __name__ == '__main__':
    unittest.main()
