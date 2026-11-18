"""F16b: missing tool, missing config and connection failure are reported apart, values never."""

import json
import unittest

from project_bootstrap.doctor import diagnose

FAKE = 'SYNTHETIC_VALUE_do_not_print_123'


class DoctorTests(unittest.TestCase):
    def which(self, name):
        return '/bin/' + name if name in self.installed else None

    def setUp(self):
        self.installed = {'git', 'ssh-keygen'}
        self.calls = []

    def probe(self, result):
        def call():
            self.calls.append(result)
            if isinstance(result, Exception):
                raise result
            return result
        return call

    def test_three_kinds_of_gap_are_separate(self):
        report = diagnose(
            tools=['git', 'uv'], configs=['SERVICE_KEY', 'EMPTY_KEY', 'UNSET_KEY'],
            connections={'service': (['git'], ['SERVICE_KEY'], self.probe(False)),
                         'raises': (['git'], [], self.probe(ConnectionError(FAKE))),
                         'truthy': (['git'], [], self.probe('yes')),
                         'fine': (['git'], [], self.probe(True)),
                         'needs-uv': (['uv'], ['SERVICE_KEY'], self.probe(True)),
                         'needs-key': (['git'], ['UNSET_KEY'], self.probe(True))},
            environ={'SERVICE_KEY': FAKE, 'EMPTY_KEY': '   '}, which=self.which)
        states = {row['item']: row['state'] for row in report['rows']}
        self.assertEqual(states, {'git': 'ok', 'uv': 'missing-tool', 'SERVICE_KEY': 'ok',
                                  'EMPTY_KEY': 'missing-config', 'UNSET_KEY': 'missing-config',
                                  'service': 'connection-failed', 'raises': 'connection-failed',
                                  'truthy': 'connection-failed', 'fine': 'ok',
                                  'needs-uv': 'not-attempted', 'needs-key': 'not-attempted'})
        becauses = {row['item']: row.get('because') for row in report['rows']}
        self.assertEqual((becauses['needs-uv'], becauses['needs-key']), (['uv'], ['UNSET_KEY']))
        # A missing prerequisite never triggers the call, so it is not an outage.
        self.assertEqual(len(self.calls), 4)
        self.assertFalse(report['ok'])
        self.assertNotIn(FAKE, json.dumps(report))

    def test_all_present_is_ok(self):
        report = diagnose(['git'], ['K'], {'c': (['git'], ['K'], self.probe(True))},
                          {'K': 'v'}, which=self.which)
        self.assertTrue(report['ok'])
        self.assertTrue(diagnose([], [], {}, {})['ok'])


if __name__ == '__main__':
    unittest.main()
