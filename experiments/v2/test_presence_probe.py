"""Offline tests for how the presence probe reads its helper's output.

The helper itself (Swift, Secure Enclave) is not run here: it needs a Mac with
Xcode tools and takes several seconds to compile. Run it with
`python3 -X utf8 -m experiments.v2.presence_probe`.
"""
import unittest

from experiments.v2.presence_probe import INTERACTION_REQUIRED, assess

REFUSED = INTERACTION_REQUIRED


def output(enclave='available', control='signed valid', presence=REFUSED, biometry=REFUSED,
           extra=()):
    lines = [f'ENCLAVE {enclave}']
    for name, value in (('CONTROL', control), ('PRESENCE', presence), ('BIOMETRY', biometry)):
        if value is not None:
            lines.append(f'{name} {value}')
    return '\n'.join([*lines, *extra]) + '\n'


class PresenceAssessmentTests(unittest.TestCase):
    def test_refused_gated_signing_is_only_a_candidate(self):
        report = assess(output())
        self.assertEqual(report['result'], '候選可用但未驗收')
        self.assertTrue(report['biometry_only'])
        self.assertNotIn('通過', report['result'])

    def test_biometry_gate_may_be_missing_without_losing_the_candidate(self):
        report = assess(output(biometry='key-error NSOSStatusErrorDomain -25293'))
        self.assertEqual(report['result'], '候選可用但未驗收')
        self.assertFalse(report['biometry_only'])

    def test_gated_key_that_signs_unattended_is_a_counterexample(self):
        for field in ('presence', 'biometry'):
            with self.subTest(gate=field):
                self.assertEqual(assess(output(**{field: 'signed valid'}))['result'], '反例')
                self.assertEqual(assess(output(**{field: 'signed invalid'}))['result'], '反例')

    def test_refusal_for_another_reason_proves_nothing(self):
        cases = {
            'different error': output(presence='refused com.apple.LocalAuthentication -1'),
            'key not created': output(presence='key-error CryptoKitError 2'),
            'presence missing': output(presence=None),
            'control broken': output(control='refused com.apple.LocalAuthentication -1004'),
            'control invalid': output(control='signed invalid'),
            'control missing': output(control=None),
            'unknown line': output(extra=['PRESENCE_OK yes']),
            'duplicate line': output(extra=[f'PRESENCE {REFUSED}']),
            'empty': '',
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                self.assertEqual(assess(text)['result'], '未驗證')

    def test_no_enclave_is_reported_as_unavailable(self):
        self.assertEqual(assess('ENCLAVE unavailable\n')['result'], '無法使用')


if __name__ == '__main__':
    unittest.main()
