"""F45: reverse rules, section and cross-document conflicts, unregistered and stale pending."""

import unittest

from experiments.v2.contradictions import REPO_CONFIG, check, sections

RULE = {
    'id': 'core-priority',
    'canonical': 'skill',
    'variants': {
        'skill': [r'核心優先序：SKILL'],
        'protocol': [r'(?<!宣稱)(衝突|兩者)[^。\n]{0,6}以協定為準'],
    },
    'required_in': ['README.md'],
}
REGISTRY = '''# 決策書

## 6. 待決事項

說明文字不是登記列。

- **Q1**（2026-11-10）：崩潰後解除？影響 F11。需使用者決定。狀態：待決
- **Q2**（2026-11-01）：舊問題？影響 F3。狀態：已決（2026-11-02，使用者）

## 7. 其他

Q2 早已定案。
'''
HANDOFF = '''# HANDOFF

## 懸置事項（AI 勿自行處理）

- Q1：等使用者回覆。
'''
CONFIG = {
    'rules': [RULE],
    'registry': {'doc': 'decision.md', 'heading': r'(^| > )6\. 待決事項$'},
    'pending_sections': [{'doc': 'HANDOFF.md', 'heading': r'懸置事項'}],
}


def docs(**changes):
    base = {'README.md': '# R\n\n**核心優先序：SKILL.md**。\n',
            'AGENTS.md': '# A\n\n## 規則\n\n舊實例仍宣稱協定優先也不算。\n',
            'decision.md': REGISTRY, 'HANDOFF.md': HANDOFF}
    base.update(changes)
    return base


def codes(result):
    return sorted(item['code'] for item in result['findings'])


class ContradictionTests(unittest.TestCase):
    def test_consistent_documents_report_nothing_found_not_agreement(self):
        result = check(docs(), CONFIG)
        self.assertEqual((result['overall'], result['findings'], result['unknown']),
                         ('未發現', [], []))
        self.assertIn('不等於', result['note'])

    def test_reverse_rule_in_the_human_entry_is_found_with_its_place(self):
        readme = '# R\n\n**核心優先序：SKILL.md**。\n\n## 用法\n\n兩者衝突以協定為準。\n'
        result = check(docs(**{'README.md': readme}), CONFIG)
        self.assertEqual(result['overall'], '矛盾')
        self.assertEqual(codes(result), ['reverse-rule', 'section-conflict'])
        reverse = [f for f in result['findings'] if f['code'] == 'reverse-rule'][0]
        self.assertEqual((reverse['doc'], reverse['section'], reverse['line']),
                         ('README.md', 'R > 用法', 7))

    def test_two_documents_disagreeing_is_a_cross_document_conflict(self):
        result = check(docs(**{'AGENTS.md': '# A\n\n衝突時以協定為準。\n'}), CONFIG)
        self.assertEqual(codes(result), ['cross-doc-conflict', 'reverse-rule'])
        cross = [f for f in result['findings'] if f['code'] == 'cross-doc-conflict'][0]
        self.assertEqual(cross['docs'], ['AGENTS.md', 'README.md'])

    def test_conflict_is_reported_even_when_no_variant_is_reverse(self):
        rule = dict(RULE, canonical='none-yet')
        rule['variants'] = {'a': [r'甲為準'], 'b': [r'乙為準']}
        rule.pop('required_in')
        result = check({'X.md': '# X\n\n## 一\n\n甲為準\n\n## 二\n\n乙為準\n'},
                       {'rules': [rule]})
        self.assertIn('section-conflict', codes(result))

    def test_pending_question_missing_from_registry_is_found(self):
        handoff = HANDOFF + '- 要不要改用 B 方案，待使用者決定。\n'
        result = check(docs(**{'HANDOFF.md': handoff}), CONFIG)
        self.assertEqual(codes(result), ['pending-unregistered'])
        self.assertEqual(result['findings'][0]['line'], 6)

    def test_empty_pending_list_written_as_none_is_not_a_question(self):
        result = check(docs(**{'HANDOFF.md': '# H\n\n## 懸置事項\n\n- 無。\n'}), CONFIG)
        self.assertEqual(result['overall'], '未發現')

    def test_decided_question_still_called_pending_is_found_in_both_places(self):
        handoff = HANDOFF + '- Q2：還在等。\n'
        agents = '# A\n\nQ2 仍待使用者決定。\n'
        result = check(docs(**{'HANDOFF.md': handoff, 'AGENTS.md': agents}), CONFIG)
        found = sorted((f['doc'], f['code'], f['id']) for f in result['findings'])
        self.assertEqual(found, [('AGENTS.md', 'decided-still-pending', 'Q2'),
                                 ('HANDOFF.md', 'decided-still-pending', 'Q2')])

    def test_registry_entry_may_say_it_used_to_be_pending(self):
        registry = REGISTRY.replace('舊問題？', '舊問題，原本待使用者決定？')
        self.assertEqual(check(docs(**{'decision.md': registry}), CONFIG)['overall'], '未發現')

    def test_mentioning_a_decided_id_without_pending_words_is_fine(self):
        result = check(docs(**{'AGENTS.md': '# A\n\n見 Q2 的結論。\n'}), CONFIG)
        self.assertEqual(result['overall'], '未發現')

    def test_indented_detail_under_an_entry_is_not_an_entry(self):
        # 2026-11-10 Q7 (b): decided items carry 採用理由／未選 sub-bullets.
        registry = REGISTRY.replace('使用者）\n', '使用者）\n  - 未選 (b) 乙：太貴\n')
        self.assertIn('  - 未選', registry)
        self.assertNotIn('registry-entry-malformed',
                         codes(check(docs(**{'decision.md': registry}), CONFIG)))

    def test_registry_problems_are_reported_not_ignored(self):
        broken = REGISTRY.replace('狀態：已決', '狀態：不明') + '\n'
        result = check(docs(**{'decision.md': broken}), CONFIG)
        self.assertIn('registry-entry-malformed', codes(result))
        dup = REGISTRY.replace('**Q2**', '**Q1**')
        self.assertIn('registry-duplicate-id', codes(check(docs(**{'decision.md': dup}), CONFIG)))
        missing = check(docs(**{'decision.md': '# 決策書\n\n## 5. 別的\n'}), CONFIG)
        self.assertIn(('decision.md', 'registry-section-missing'), missing['unknown'])
        self.assertIn('pending-unregistered', codes(missing))

    def test_unreadable_or_silent_documents_are_unknown_not_passing(self):
        result = check(docs(**{'README.md': None}), CONFIG)
        self.assertEqual(result['overall'], '未知')
        self.assertIn(('README.md', 'doc-unreadable'), result['unknown'])
        self.assertIn(('README.md', 'required-doc-unreadable:core-priority'), result['unknown'])
        silent = check(docs(**{'README.md': '# R\n\n沒提優先序。\n'}), CONFIG)
        self.assertEqual(silent['unknown'], [('README.md', 'rule-absent:core-priority')])
        gone = check(docs(**{'HANDOFF.md': None}), CONFIG)
        self.assertIn(('HANDOFF.md', 'pending-doc-unreadable'), gone['unknown'])

    def test_rule_limited_to_documents_ignores_others(self):
        rule = dict(RULE, docs=['README.md'])
        result = check(docs(**{'AGENTS.md': '# A\n\n衝突時以協定為準。\n'}),
                       dict(CONFIG, rules=[rule]))
        self.assertEqual(result['overall'], '未發現')

    def test_skips_are_reported_and_fences_can_be_scanned(self):
        readme = '# R\n\n**核心優先序：SKILL.md**。\n\n```\n衝突時以協定為準\n```\n'
        hidden = check(docs(**{'README.md': readme}), CONFIG)
        self.assertEqual((hidden['overall'], hidden['skipped']),
                         ('未發現', [('README.md', 'code-fence', 1)]))
        scanned = check(docs(**{'README.md': readme}), dict(CONFIG, scan_fences=['README.md']))
        self.assertIn('reverse-rule', codes(scanned))

    def test_history_sections_are_skipped_but_counted(self):
        agents = '# A\n\n## 舊版紀錄\n\n衝突時以協定為準。\n'
        config = dict(CONFIG, history=[{'doc': 'AGENTS.md', 'heading': '舊版紀錄'}])
        result = check(docs(**{'AGENTS.md': agents}), config)
        self.assertEqual((result['overall'], result['skipped']),
                         ('未發現', [('AGENTS.md', 'history-section', 2)]))
        self.assertIn('reverse-rule', codes(check(docs(**{'AGENTS.md': agents}), CONFIG)))

    def test_dated_log_lines_can_be_marked_history_by_pattern(self):
        agents = '# A\n\n> 2026-11-01 當時衝突時以協定為準。\n\n衝突時以協定為準。\n'
        config = dict(CONFIG, history=[{'doc': 'AGENTS.md', 'line': r'^> \d{4}-'}])
        result = check(docs(**{'AGENTS.md': agents}), config)
        self.assertEqual([f['line'] for f in result['findings'] if f['code'] == 'reverse-rule'], [5])
        self.assertEqual(result['skipped'], [('AGENTS.md', 'history-section', 1)])

    def test_section_paths_follow_heading_levels(self):
        rows, skipped = sections('# A\n\n## B\n\nx\n\n### C\n\ny\n\n## D\n\nz\n')
        self.assertEqual([(r[0], r[2]) for r in rows if r[2]],
                         [('A > B', 'x'), ('A > B > C', 'y'), ('A > D', 'z')])
        self.assertEqual(skipped, 0)


    def test_version_rule_flags_claims_but_not_negations_or_quotes(self):
        rule = next(r for r in REPO_CONFIG['rules'] if r['id'] == 'version-follows-skill')
        config = {'rules': [dict(rule, required_in=[], docs=None)]}
        base = '# P\n\n版本行與 `VERSION` 只跟著 `SKILL.md` 走。\n'
        # The canonical wording alone counts as present, not as an absent rule.
        present = check({'P.md': base}, {'rules': [dict(rule, docs=None, required_in=['P.md'])]})
        self.assertEqual((present['findings'], present['unknown']), ([], []))
        quiet = ['`VERSION` 不跟著動，落後偵測不會替你講。',
                 '舊稿寫過「改到範本就要跳 VERSION」，已更正。',
                 '沒動到 hook 就不要跳 VERSION。']
        for line in quiet:
            with self.subTest(line=line):
                result = check({'P.md': base + line + '\n'}, config)
                self.assertEqual(result['findings'], [])
        for line in ('改到範本就要跳 VERSION。', '動了 hook 都要跳 `VERSION`。',
                     '`VERSION` 跟著 `source:` 標記走。'):
            with self.subTest(line=line):
                result = check({'P.md': base + line + '\n'}, config)
                self.assertIn('reverse-rule', codes(result))

if __name__ == '__main__':
    unittest.main()
