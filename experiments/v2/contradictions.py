"""M4 detection for F45: the same fact stated differently across documents.

Covers what the acceptance names and no more: a rule written in reverse
(including README, AGENTS and the operation card), two sections of one file
or two files disagreeing, a pending question missing from the registry, and a
settled question still described as pending. Each rule is a declared table of
regular expressions per variant; free prose outside those tables is not judged,
so "未發現" never means the documents agree. A listed document that cannot be
read, or a required rule that matches nowhere in it, is 未知, not a pass.

Lines inside code fences and sections the caller marks as history are skipped,
and every skip is reported so an exclusion cannot hide a finding silently.
"""
from pathlib import Path
import re
import sys

PENDING_WORDS = re.compile(r'待決|待使用者決定|待你決定|等使用者決定')
_HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
_FENCE = re.compile(r'^\s*(```|~~~)')


def sections(text, transparent=False):
    """(heading path, line number, line) per line; fenced lines are counted and
    dropped unless ``transparent`` (a document whose templates live in fences)."""
    path, rows, fenced, skipped = [], [], False, 0
    for number, line in enumerate(text.splitlines(), 1):
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced and not transparent:
            skipped += 1
            continue
        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            path = path[:level - 1] + [''] * max(0, level - 1 - len(path)) + [heading.group(2)]
            continue
        rows.append((' > '.join(p for p in path if p), number, line))
    return rows, skipped


def _history(doc, heading, history):
    return any(item['doc'] == doc and re.search(item['heading'], heading) for item in history)


def _scan(docs, history, transparent=()):
    """Readable lines per document, plus skip and unreadable reports."""
    lines, skipped, unknown = {}, [], []
    for doc, text in docs.items():
        if text is None:
            unknown.append((doc, 'doc-unreadable'))
            continue
        rows, fenced = sections(text, doc in transparent)
        kept, excluded = [], 0
        for row in rows:
            if _history(doc, row[0], history):
                excluded += 1
            else:
                kept.append(row)
        if fenced:
            skipped.append((doc, 'code-fence', fenced))
        if excluded:
            skipped.append((doc, 'history-section', excluded))
        lines[doc] = kept
    return lines, skipped, unknown


def check_rules(lines, rules):
    findings, unknown = [], []
    for rule in rules:
        hits = []
        for doc, rows in lines.items():
            if rule.get('docs') and doc not in rule['docs']:
                continue
            for heading, number, line in rows:
                for variant, patterns in rule['variants'].items():
                    if any(re.search(p, line) for p in patterns):
                        hits.append({'doc': doc, 'section': heading, 'line': number,
                                     'variant': variant})
        for hit in hits:
            if hit['variant'] != rule['canonical']:
                findings.append(dict(hit, rule=rule['id'], code='reverse-rule'))
        variants = {}
        for hit in hits:
            variants.setdefault(hit['variant'], []).append(hit)
        if len(variants) > 1:
            docs = {hit['doc'] for hit in hits}
            for doc in sorted(docs):
                in_doc = {hit['variant'] for hit in hits if hit['doc'] == doc}
                if len(in_doc) > 1:
                    findings.append({'rule': rule['id'], 'doc': doc, 'code': 'section-conflict',
                                     'variants': sorted(in_doc)})
            if len(docs) > 1:
                findings.append({'rule': rule['id'], 'code': 'cross-doc-conflict',
                                 'variants': sorted(variants),
                                 'docs': sorted(docs)})
        for doc in rule.get('required_in', ()):
            if doc not in lines:
                unknown.append((doc, 'required-doc-unreadable:' + rule['id']))
            elif not any(hit['doc'] == doc for hit in hits):
                unknown.append((doc, 'rule-absent:' + rule['id']))
    return findings, unknown


_ENTRY = re.compile(r'^\s*[-*]\s+\*\*(?P<id>[A-Z][A-Za-z]*\d+)\*\*.*?狀態：(?P<status>待決|已決)')


def parse_registry(lines, doc, heading):
    """Entries of the registry section; a malformed entry is reported, not dropped."""
    entries, findings, found = {}, [], False
    for section, number, line in lines.get(doc, ()):
        if not re.search(heading, section):
            continue
        found = True
        if not re.match(r'^\s*[-*]\s+', line):
            continue
        entry = _ENTRY.match(line)
        if not entry:
            findings.append({'doc': doc, 'line': number, 'code': 'registry-entry-malformed'})
        elif entry.group('id') in entries:
            findings.append({'doc': doc, 'line': number, 'code': 'registry-duplicate-id',
                             'id': entry.group('id')})
        else:
            entries[entry.group('id')] = 'pending' if entry.group('status') == '待決' else 'decided'
    return entries, findings, found


def check_pending(lines, registry_doc, registry_heading, pending_sections):
    entries, findings, found = parse_registry(lines, registry_doc, registry_heading)
    unknown = [] if found else [(registry_doc, 'registry-section-missing')]
    ids = re.compile(r'\b(' + '|'.join(map(re.escape, entries)) + r')\b') if entries else None
    for place in pending_sections:
        doc = place['doc']
        if doc not in lines:
            unknown.append((doc, 'pending-doc-unreadable'))
            continue
        for section, number, line in lines[doc]:
            if not re.search(place['heading'], section) or not re.match(r'^\s*[-*]\s+', line):
                continue
            if re.match(r'^\s*[-*]\s+無[。.]?\s*$', line):
                continue
            cited = set(ids.findall(line)) if ids else set()
            if not cited:
                findings.append({'doc': doc, 'section': section, 'line': number,
                                 'code': 'pending-unregistered'})
            for cid in sorted(cited):
                if entries[cid] != 'pending':
                    findings.append({'doc': doc, 'section': section, 'line': number,
                                     'code': 'decided-still-pending', 'id': cid})
    if ids:
        listed = {(p['doc'], p['heading']) for p in pending_sections}
        for doc, rows in lines.items():
            for section, number, line in rows:
                if doc == registry_doc and re.search(registry_heading, section):
                    continue
                if any(doc == d and re.search(h, section) for d, h in listed):
                    continue
                if not PENDING_WORDS.search(line):
                    continue
                for cid in sorted(set(ids.findall(line))):
                    if entries[cid] == 'decided':
                        findings.append({'doc': doc, 'section': section, 'line': number,
                                         'code': 'decided-still-pending', 'id': cid})
    return findings, unknown


def check(docs, config):
    lines, skipped, unknown = _scan(docs, config.get('history', ()),
                                    config.get('scan_fences', ()))
    findings, more = check_rules(lines, config.get('rules', ()))
    unknown += more
    registry = config.get('registry')
    if registry:
        found, more = check_pending(lines, registry['doc'], registry['heading'],
                                    config.get('pending_sections', ()))
        findings += found
        unknown += more
    overall = '矛盾' if findings else '未知' if unknown else '未發現'
    return {'overall': overall, 'findings': findings, 'unknown': unknown, 'skipped': skipped,
            'note': '只比對宣告的規則表與待決登記；未發現不等於文件一致'}


# This repo's own declared table. Narrow on purpose: a pattern that also
# matches a sentence describing the old rule would turn history into a finding.
REPO_CONFIG = {
    'rules': [{
        'id': 'core-priority',
        'canonical': 'skill',
        'variants': {
            'skill': [r'核心優先序：SKILL', r'以同步的 ?(SKILL\.md|skill) ?為準'],
            'protocol': [r'(?<!宣稱)(衝突|兩者)[^。\n]{0,6}以(專案)?協定為準',
                         r'(?<!宣稱)協定優先於 ?(SKILL|skill)'],
        },
        'docs': ['README.md', 'AGENTS.md', 'PROJECT-BOOTSTRAP.md'],
        'required_in': ['README.md', 'PROJECT-BOOTSTRAP.md'],
    }],
    'registry': {'doc': 'project-bootstrap-requirements-decision.md', 'heading': r'(^| > )6\. 待決事項$'},
    'pending_sections': [{'doc': 'HANDOFF.md', 'heading': r'懸置事項'}],
    'history': [],
    'scan_fences': ['PROJECT-BOOTSTRAP.md'],
}
REPO_DOCS = ('README.md', 'AGENTS.md', 'PROJECT-BOOTSTRAP.md', 'HANDOFF.md',
             'project-bootstrap-requirements-decision.md')


def read_docs(root, names):
    docs = {}
    for name in names:
        try:
            docs[name] = (Path(root) / name).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            docs[name] = None
    return docs


def main(argv=None):
    root = Path(argv[0] if argv else Path(__file__).resolve().parents[2])
    result = check(read_docs(root, REPO_DOCS), REPO_CONFIG)
    for item in result['findings']:
        print('FINDING', item)
    for item in result['unknown']:
        print('UNKNOWN', item)
    for item in result['skipped']:
        print('SKIPPED', item)
    print(result['overall'], '—', result['note'])
    return {'未發現': 0, '未知': 1, '矛盾': 2}[result['overall']]


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
