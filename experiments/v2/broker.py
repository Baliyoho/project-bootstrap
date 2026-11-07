"""P0 parent-owned agent RPC. Identity comes from the inherited pipe, not JSON.

Only the launcher registers sessions and grants authority. Agent requests have
no admin method, actor/capability field, arbitrary command or filesystem path.
The backing store is Lab's transactional content store; an optional P0 POSIX
materializer applies accepted events before reporting success. OS containment
must be tested separately; this class alone is not a security boundary.
"""
from dataclasses import dataclass
import hashlib
import json
import threading

from experiments.v2.contracts import Denied


MAX_REQUEST_BYTES = 8192


@dataclass(eq=False)
class Channel:
    # Parent-only object: never serialized or passed to the worker.
    capability: str
    resources: frozenset
    closed: bool = False
    authorize: object = None


class Broker:
    def __init__(self, lab, materializer=None):
        self.lab = lab
        self.materializer = materializer
        self.channels = set()
        self.lock = threading.RLock()

    def attach(self, actor, resources, resume=False):
        """Trusted launcher operation, intentionally absent from dispatch."""
        with self.lock:
            capability = self.lab.resume(actor) if resume else self.lab.register(actor)
            channel = Channel(capability, frozenset(resources))
            self.channels.add(channel)
            return channel

    def detach(self, channel):
        with self.lock:
            if channel in self.channels:
                channel.closed = True

    @staticmethod
    def response(request_id, code, **fields):
        return (json.dumps(dict(id=request_id, code=code, **fields), sort_keys=True,
                           separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')

    def dispatch(self, channel, raw):
        """Synchronous, bounded, fail-closed requests; retries never repeat effects.

        Receipts are persisted with the content/effect in one transaction. A
        trusted resume rotates capability and preserves the principal's receipt
        history. Exact retries return receipts, including after lost responses.
        Sending a principal name in JSON never restores access.
        """
        with self.lock:
            if channel not in self.channels or channel.closed:
                return self.response(None, 'closed-channel')
            if not isinstance(raw, bytes) or len(raw) > MAX_REQUEST_BYTES:
                return self.response(None, 'request-too-large-or-invalid')
            try:
                request = json.loads(raw.decode('utf-8'), object_pairs_hook=self.unique_keys)
            except (ValueError, UnicodeError, RecursionError):
                return self.response(None, 'invalid-json')
            if not isinstance(request, dict) or type(request.get('id')) is not int or request['id'] < 1:
                return self.response(None, 'invalid-sequence')
            request_id = request['id']
            fingerprint = hashlib.sha256(raw).hexdigest()
            try:
                with self.lab.transaction():
                    actor = self.lab.actor(channel.capability)
                    if channel.authorize is not None:
                        channel.authorize(channel)
                    previous = self.lab.db.execute('SELECT digest, response FROM receipts '
                        'WHERE actor=? AND request_id=?', (actor, request_id)).fetchone()
                    if previous is not None:
                        if previous['digest'] != fingerprint:
                            return self.response(request_id, 'changed-retry')
                        response = previous['response']
                    else:
                        last = self.lab.db.execute('SELECT COALESCE(MAX(request_id), 0) '
                            'FROM receipts WHERE actor=?', (actor,)).fetchone()[0]
                        if request_id != last + 1:
                            return self.response(request_id, 'out-of-sequence')
                        try:
                            fields = self.execute(channel, request)
                            response = self.response(request_id, 'ok', **fields)
                        except Denied as error:
                            response = self.response(request_id, str(error))
                        except (TypeError, ValueError, UnicodeError):
                            response = self.response(request_id, 'invalid-request')
                        self.lab.db.execute('INSERT INTO receipts VALUES (?, ?, ?, ?)',
                                            (actor, request_id, fingerprint, response))
            except Denied:
                channel.closed = True
                return self.response(request_id, 'session-no-longer-valid')
            except Exception:
                channel.closed = True
                return self.response(request_id, 'broker-error-channel-closed')
            # The receipt means the store accepted the operation. With a disk
            # target attached, do not report success until its recovery protocol
            # confirms application. Replays reuse the SAME content event.
            message = json.loads(response)
            if self.materializer is not None and message['code'] == 'ok' and 'event' in message:
                # A durable acceptance receipt is not current disk-write authority.
                # Resume may narrow this principal's channel scope. Keep the
                # original receipt intact so an authorized recovery can retry it.
                if request.get('resource') not in channel.resources:
                    return self.response(request_id, 'resource-not-authorized')
                try:
                    if channel.authorize is not None:
                        with self.lab.transaction():
                            channel.authorize(channel)
                    self.materializer.apply(message['event'])
                except Denied as error:
                    return self.response(request_id, 'materialization-pending', event=message['event'], reason=str(error))
                except Exception:
                    return self.response(request_id, 'materialization-pending', event=message['event'], reason='filesystem-or-journal-error')
            return response

    @staticmethod
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate-key')
            result[key] = value
        return result

    def execute(self, channel, request):
        method = request.get('method')
        schemas = {
            'write': {'id', 'method', 'resource', 'base', 'text', 'epoch'},
            'effect': {'id', 'method', 'resource', 'kind', 'epoch'},
        }
        if method not in schemas:
            raise Denied('unknown-method')
        if set(request) != schemas[method]:
            raise Denied('unexpected-fields')
        resource = request['resource']
        if not isinstance(resource, str) or resource not in channel.resources:
            raise Denied('resource-not-authorized')
        if type(request['epoch']) is not int or request['epoch'] < 0:
            raise Denied('invalid-epoch')
        if method == 'write':
            if self.materializer is not None:
                self.materializer.ensure_ready(resource)
            base = request['base']
            if base is not None and (not isinstance(base, str) or len(base) != 64
                                     or any(ch not in '0123456789abcdef' for ch in base)):
                raise Denied('invalid-base')
            if not isinstance(request['text'], str):
                raise Denied('invalid-content')
            content = request['text'].encode('utf-8')
            event = self.lab.write(channel.capability, resource, base, content, epoch=request['epoch'])
            return {'event': event, 'digest': hashlib.sha256(content).hexdigest()}
        if request['kind'] not in ('delete', 'rewrite-history', 'force-push', 'batch-data',
                'schema', 'move-credential', 'extra-model', 'paid-api', 'cloud-resource'):
            raise Denied('unknown-action')
        self.lab.effect(channel.capability, request['kind'], resource, epoch=request['epoch'])
        return {'effect': 'synthetic-record-only'}
