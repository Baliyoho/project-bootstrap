#!/usr/bin/env python3
"""Read one explicitly selected local turn. Never copy source records into reports.

usage.py codex ROLLOUT.jsonl TURN_ID
usage.py claude SESSION.jsonl USER_UUID
"""
import datetime as dt
import json
import pathlib
import sys


def records(path):
    with pathlib.Path(path).open(encoding='utf-8') as source:
        for line in source:
            if line.strip():
                yield json.loads(line)


def seconds(start, end):
    if not start or not end:
        return None
    try:
        a = dt.datetime.fromisoformat(start.replace('Z', '+00:00'))
        b = dt.datetime.fromisoformat(end.replace('Z', '+00:00'))
        return round((b - a).total_seconds(), 3) if b >= a else None
    except (ValueError, TypeError):
        return None


def number(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def codex(path, turn_id):
    started = completed = None
    usage = None
    responses = set()
    missing_response_id = False
    for row in records(path):
        payload = row.get('payload') or {}
        if payload.get('turn_id') != turn_id:
            continue
        if row.get('type') == 'event_msg':
            if payload.get('type') == 'task_started':
                started = row.get('timestamp')
            elif payload.get('type') == 'task_complete':
                completed = row.get('timestamp')
        elif row.get('type') == 'token_usage_record':
            if payload.get('response_id'):
                responses.add(payload['response_id'])
            else:
                missing_response_id = True
            usage = payload.get('turn_token_usage')
    if not started:
        raise ValueError('turn_id has no task_started')
    raw = {key: number((usage or {}).get(key)) for key in
           ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
            'output_tokens', 'reasoning_output_tokens')}
    return summarize('codex', completed, started,
                     len(responses) if responses and not missing_response_id else None,
                     raw, raw.get('cached_input_tokens'))


def human_user(row):
    if row.get('type') != 'user' or row.get('isSidechain'):
        return False
    content = (row.get('message') or {}).get('content')
    return isinstance(content, str) or (isinstance(content, list) and any(
        isinstance(part, dict) and part.get('type') == 'text' for part in content))


def claude(path, user_uuid):
    active = False
    started = completed = None
    messages = {}
    last_stop = None
    for row in records(path):
        if human_user(row):
            if active:
                break
            if row.get('uuid') == user_uuid:
                active, started = True, row.get('timestamp')
            continue
        if not active or row.get('isSidechain') or row.get('type') != 'assistant':
            continue
        message = row.get('message') or {}
        last_stop = message.get('stop_reason')
        msgid = message.get('id')
        if msgid and isinstance(message.get('usage'), dict):
            # Streaming rows repeat the same message id. The last row has final usage.
            messages[msgid] = message['usage']
        completed = row.get('timestamp') if last_stop == 'end_turn' else None
    if not active:
        raise ValueError('user UUID was not found')
    keys = ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens',
            'output_tokens')
    raw = {key: sum(values[key] for values in messages.values())
           if messages and all(number(values.get(key)) is not None for values in messages.values())
           else None for key in keys}
    # Only cache reads were reused. Cache creation belongs to noncached input.
    cached = raw['cache_read_input_tokens']
    return summarize('claude', completed, started, len(messages) if messages else None,
                     raw, cached)


def summarize(tool, completed, started, responses, raw, cached):
    if completed is None:
        return {'tool': tool, 'complete': False, 'seconds': None,
                'model_responses': None, 'input_tokens': None, 'cached_input_tokens': None,
                'noncached_input_tokens': None, 'output_tokens': None,
                'raw_usage': {key: None for key in raw},
                'note': 'Incomplete turn; all totals are unknown.'}
    if tool == 'claude':
        # Common total includes every input category, not just Claude's input_tokens.
        parts = [raw['input_tokens'], raw['cache_creation_input_tokens'], raw['cache_read_input_tokens']]
        total = sum(parts) if all(x is not None for x in parts) else None
        noncached = (raw['input_tokens'] + raw['cache_creation_input_tokens']
                     if raw['input_tokens'] is not None and
                     raw['cache_creation_input_tokens'] is not None else None)
    else:
        total = raw['input_tokens']
        noncached = total - cached if total is not None and cached is not None and cached <= total else None
    return {'tool': tool, 'complete': True, 'seconds': seconds(started, completed),
            'model_responses': responses, 'input_tokens': total, 'cached_input_tokens': cached,
            'noncached_input_tokens': noncached, 'output_tokens': raw['output_tokens'],
            'raw_usage': raw, 'note': 'Unknown values are null; subscription quota is not in these logs.'}


def main(argv):
    if len(argv) != 3 or argv[0] not in ('codex', 'claude'):
        raise SystemExit(__doc__)
    result = (codex if argv[0] == 'codex' else claude)(argv[1], argv[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main(sys.argv[1:])
