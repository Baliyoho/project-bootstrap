#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Negative probes for Codex-specific validity checks; never calls a model."""
import json
import pathlib
import tempfile

import codex_run


def put(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
                    encoding='utf-8')


def expect(label, result, message):
    if not result:
        raise AssertionError(label + ': ' + message)
    print('[  ok  ] ' + label)


with tempfile.TemporaryDirectory(prefix='codex-ab-check-') as folder:
    root = pathlib.Path(folder)
    run = root / 'runs' / 'clean-full-1'
    run.mkdir(parents=True)
    thread = 'test-thread'
    events = [{'type': 'thread.started', 'thread_id': thread},
              {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'done'}},
              {'type': 'turn.completed'}]
    records = [{'type': 'turn_context', 'payload': {'model': codex_run.MODEL}},
               {'type': 'response_item', 'payload': {'role': 'user',
                'content': [{'type': 'input_text', 'text': '[facts] origin clean'}]}}]
    event_file = run / 'codex-events.jsonl'
    rollout = root / 'codex-home' / 'sessions' / ('rollout-' + thread + '.jsonl')
    prompt = run / 'prompt-input.json'
    input_items = [{'content': '# AGENTS.md instructions for test'},
                   {'content': str(run / 'work' / '.agents' / 'skills')}]
    put(event_file, events)
    put(rollout, records)
    prompt.write_text(json.dumps(input_items), encoding='utf-8')
    expect('正常 Codex 事件可用', codex_run.codex_validity(run) == [],
           str(codex_run.codex_validity(run)))

    put(event_file, [events[0], events[1]])
    expect('缺完成事件被擋', 'Codex 沒有正常完成' in codex_run.codex_validity(run), '')
    put(event_file, events)

    put(rollout, [{'type': 'turn_context', 'payload': {'model': 'wrong-model'}}, records[1]])
    expect('錯模型被擋', any('模型不是' in p for p in codex_run.codex_validity(run)), '')
    put(rollout, records)

    put(rollout, [records[0]])
    expect('缺開場事實被擋', '模型輸入沒有 SessionStart [facts]' in codex_run.codex_validity(run), '')
    put(rollout, records)

    prompt.write_text(json.dumps([input_items[0]]), encoding='utf-8')
    expect('缺專案 skill 被擋', any('隔離檢查失敗' in p for p in codex_run.codex_validity(run)), '')
    prompt.write_text(json.dumps(input_items), encoding='utf-8')

    contaminated = input_items + [{'content': str(pathlib.Path.home() / '.codex' / 'skills' / 'handoff')}]
    expect('全域 skill 污染被擋', not codex_run.prompt_isolated(contaminated, run), '')

print('Codex 守門負向自檢通過')
