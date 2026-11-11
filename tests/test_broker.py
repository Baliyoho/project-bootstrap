import json
from pathlib import Path
import tempfile
import unittest

from project_bootstrap.broker import Broker, Channel, MAX_REQUEST_BYTES
from project_bootstrap.contracts import Lab


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-broker-test-')
        self.lab = Lab(Path(self.temp.name) / 'private.sqlite')
        self.broker = Broker(self.lab)
        self.a = self.broker.attach('line-a', ('note-a', 'budget'))
        self.b = self.broker.attach('line-b', ('note-b',))

    def tearDown(self):
        self.lab.close()
        self.temp.cleanup()

    def dispatch(self, channel, **fields):
        raw = json.dumps(fields).encode()
        return json.loads(self.broker.dispatch(channel, raw))

    def write_request(self, request_id=1, **extra):
        request = dict(id=request_id, method='write', resource='note-a', base=None, text='content', epoch=0)
        request.update(extra)
        return request

    def test_identity_comes_from_channel_and_full_event_is_preserved(self):
        result = self.dispatch(self.a, **self.write_request())
        event = self.lab.event(result['event'])
        self.assertEqual((event['actor'], event['before'], event['after']), ('line-a', None, b'content'))
        second = self.dispatch(self.a, **self.write_request(2, base=result['digest'], text='second'))
        self.assertEqual(self.lab.event(second['event'])['before'], b'content')

    def test_actor_capability_and_other_resource_are_rejected(self):
        for request_id, extra in enumerate(({'actor': 'line-b'}, {'capability': self.b.capability},
                                            {'resource': 'note-b'}), 1):
            result = self.dispatch(self.a, **self.write_request(request_id, **extra))
            self.assertIn(result['code'], ('unexpected-fields', 'resource-not-authorized'))
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 0)

    def test_admin_and_arbitrary_commands_not_exposed(self):
        for request_id, method in enumerate(('register', 'grant', 'revoke', 'attach', 'exec', 'shell'), 1):
            result = self.dispatch(self.a, id=request_id, method=method)
            self.assertEqual(result['code'], 'unknown-method')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM grants').fetchone()[0], 0)

    def test_exact_retry_does_not_repeat_effect_and_changed_retry_is_rejected(self):
        self.lab.grant('line-a', 'paid-api', 'budget', 2, 'synthetic-human-authorization')
        request = dict(id=1, method='effect', resource='budget', kind='paid-api', epoch=0)
        first = self.dispatch(self.a, **request)
        self.assertEqual(first, self.dispatch(self.a, **request))
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM effects').fetchone()[0], 1)
        request['kind'] = 'extra-model'
        self.assertEqual(self.dispatch(self.a, **request)['code'], 'changed-retry')
        request['id'] = 3
        self.assertEqual(self.dispatch(self.a, **request)['code'], 'out-of-sequence')

    def test_dead_or_forged_channel_cannot_restore_access(self):
        forged = Channel(self.a.capability, self.a.resources)
        self.assertEqual(self.dispatch(forged, **self.write_request())['code'], 'closed-channel')
        self.broker.detach(self.a)
        self.assertEqual(self.dispatch(self.a, **self.write_request())['code'], 'closed-channel')

    def test_pending_epoch_rejects_writes_and_effects_in_transaction(self):
        self.lab.grant('line-a', 'paid-api', 'budget', 1, 'synthetic-human-authorization')
        self.lab.propose('new-premise')
        self.assertEqual(self.dispatch(self.a, **self.write_request())['code'], 'premise-not-current')
        result = self.dispatch(self.a, id=2, method='effect', resource='budget', kind='paid-api', epoch=0)
        self.assertEqual(result['code'], 'premise-not-current')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 0)
        self.assertEqual(self.lab.db.execute('SELECT remaining FROM grants').fetchone()[0], 1)

    def test_malformed_duplicate_and_oversized_requests_have_no_effect(self):
        for raw in (b'not-json', b'{"id":1,"id":2}', b'[]', b'{}',
                    b'x' * (MAX_REQUEST_BYTES + 1), b'{"id":true}', b'[' * 2000 + b']' * 2000):
            with self.subTest(raw=raw[:30]):
                result = json.loads(self.broker.dispatch(self.a, raw))
                self.assertNotEqual(result['code'], 'ok')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 0)
        self.assertEqual(self.dispatch(self.a, **self.write_request())['code'], 'ok')

    def test_each_malformed_input_gets_its_own_code_without_effect(self):
        for raw, code in ((b'x' * (MAX_REQUEST_BYTES + 1), 'request-too-large-or-invalid'),
                          ('{"id":1}', 'request-too-large-or-invalid'),
                          (b'{"id":0,"method":"write"}', 'invalid-sequence'),
                          (b'{"id":-3}', 'invalid-sequence'),
                          (b'{"id":1,"id":1}', 'invalid-json')):
            with self.subTest(raw=raw[:30]):
                self.assertEqual(json.loads(self.broker.dispatch(self.a, raw))['code'], code)
        cases = [(dict(epoch=-1), 'invalid-epoch'), (dict(epoch='0'), 'invalid-epoch'),
                 (dict(base='a' * 63), 'invalid-base'), (dict(base='g' * 64), 'invalid-base'),
                 (dict(text=5), 'invalid-content'), (dict(text='\ud800'), 'invalid-request')]
        for request_id, (extra, code) in enumerate(cases, 1):
            with self.subTest(extra=extra):
                self.assertEqual(self.dispatch(self.a, **self.write_request(request_id, **extra))['code'],
                                 code)
        effect = dict(id=len(cases) + 1, method='effect', resource='budget', kind='launch', epoch=0)
        self.assertEqual(self.dispatch(self.a, **effect)['code'], 'unknown-action')
        self.assertFalse(self.a.closed)
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 0)

    def test_revoked_authority_closes_the_channel(self):
        from project_bootstrap.contracts import Denied

        def revoked(channel):
            raise Denied('ticket-expired')
        self.a.authorize = revoked
        result = self.dispatch(self.a, **self.write_request())
        self.assertEqual(result['code'], 'session-no-longer-valid')
        self.assertTrue(self.a.closed)
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 0)

    def test_authority_is_rechecked_before_applying_to_disk(self):
        from project_bootstrap.contracts import Denied

        class Disk:
            applied = []

            def ensure_ready(self, resource):
                pass

            def apply(self, event):
                self.applied.append(event)
        disk = Disk()
        broker = Broker(self.lab, materializer=disk)
        channel = broker.attach('line-c', ('note-c',))
        calls = []

        def expires_after_acceptance(_):
            calls.append(1)
            if len(calls) > 1:
                raise Denied('ticket-expired')
        channel.authorize = expires_after_acceptance
        request = dict(id=1, method='write', resource='note-c', base=None, text='x', epoch=0)
        result = json.loads(broker.dispatch(channel, json.dumps(request).encode()))
        self.assertEqual((result['code'], result['reason'], disk.applied),
                         ('materialization-pending', 'ticket-expired', []))

    def test_exception_does_not_leak_payload_and_closes_channel(self):
        def fail(*args, **kwargs):
            raise RuntimeError('SYNTHETIC_PRIVATE_EXCEPTION')
        self.lab.write = fail
        result = self.dispatch(self.a, **self.write_request())
        self.assertEqual(result['code'], 'broker-error-channel-closed')
        self.assertNotIn('SYNTHETIC_PRIVATE_EXCEPTION', str(result))
        self.assertTrue(self.a.closed)


if __name__ == '__main__':
    unittest.main()
