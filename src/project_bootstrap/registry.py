"""Validate complete stable-ID coverage; the decision document stays authority."""
import re


SUBITEMS = {'F11': ('a', 'b'), 'F13': ('normal', 'interrupted', 'device-lost'),
            'F43': ('a', 'b')}
STATES = {'通過', '不通過', '未驗證', '不適用'}


def requirement_ids(text):
    """IDs of the requirement table, found by its heading name, not its number.

    2026-11-17 (v3 Q39): v2 put the list in section 3 and v3 in section 4; the
    section ends at the next level-2 heading. No such section yields no IDs,
    which ``validate`` then reports as a mismatch instead of passing.
    """
    match = re.search(r'^## \d+\. 需求清單.*$', text, re.MULTILINE)
    if not match:
        return []
    rest = text[match.end():]
    end = re.search(r'^## ', rest, re.MULTILINE)
    section = rest[:end.start()] if end else rest
    return re.findall(r'^\| (F\d+[ab]?) \|', section, re.MULTILINE)


def validate(data, decision, root):
    errors = []
    ids = requirement_ids(decision)
    rows = data.get('requirements', [])
    observed = [row.get('id') for row in rows]
    if len(ids) != len(set(ids)) or set(observed) != set(ids) or len(observed) != len(ids):
        errors.append('需求 ID 缺漏、重複或多出；以決策書「需求清單」節為準')
    for row in rows:
        for key in ('scope', 'origin', 'unknown', 'next'):
            if not row.get(key):
                errors.append(f'{row.get("id")} 缺 {key}')
        if row.get('result') not in STATES:
            errors.append(f'{row.get("id")} 結果無效')
        expected = set(SUBITEMS.get(row.get('id'), ()))
        if set(row.get('parts', {})) != expected:
            errors.append(f'{row.get("id")} 子項缺漏或多出')
        checks = [row] + list(row.get('parts', {}).values())
        for item in checks:
            if item.get('result') not in STATES or not item.get('scope'):
                errors.append(f'{row.get("id")} 子項結果／範圍無效')
            # P0 has no full requirement acceptance. A future promotion must add
            # independently checked evidence, not just flip the result string.
            if item.get('result') == '通過':
                errors.append(f'{row.get("id")} P0 索引不接受完整通過宣稱')
            for evidence in item.get('evidence', []):
                path = evidence.get('path', '')
                if not path or path.startswith('/') or '..' in path.split('/'):
                    errors.append(f'{row.get("id")} 證據路徑無效')
                elif not (root / path).is_file():
                    errors.append(f'{row.get("id")} 證據不可取得：{path}')
                if not evidence.get('scope'):
                    errors.append(f'{row.get("id")} 證據缺範圍')
    return errors
