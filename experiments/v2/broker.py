"""P0 parent-owned agent RPC. Identity comes from the inherited pipe, not JSON.

Only the launcher registers sessions and grants authority. Agent requests have
no admin method, actor/capability field, arbitrary command or filesystem path.
The backing store remains Lab's transactional content store, not a deployed
filesystem materializer. OS containment and process isolation must be tested
separately; this class alone is not an unbypassable security boundary.
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
    sequence: int = 0
    last_digest: str = ''
    last_response: bytes = b''
    closed: bool = False


class Broker:
    def __init__(self, lab):
        self.lab = lab
        self.channels = set()
        self.lock = threading.RLock()

    def attach(self, actor, resources):
        """Trusted launcher operation, intentionally absent from dispatch."""
        with self.lock:
            capability = self.lab.register(actor)
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

        Each channel accepts the next integer sequence or an exact retry of its
        last request. Content-changing reuse, old requests and gaps are denied.
        A dead channel cannot be reattached by sending an identifier in JSON.
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
            if request_id == channel.sequence:
                if fingerprint == channel.last_digest:
                    return channel.last_response
                return self.response(request_id, 'changed-retry')
            if request_id != channel.sequence + 1:
                return self.response(request_id, 'out-of-sequence')
            try:
                fields = self.execute(channel, request)
                response = self.response(request_id, 'ok', **fields)
            except Denied as error:
                # Only fixed codes raised in this module/Lab are exposed.
                response = self.response(request_id, str(error))
            except (TypeError, ValueError, UnicodeError):
                response = self.response(request_id, 'invalid-request')
            except Exception:
                channel.closed = True
                return self.response(request_id, 'broker-error-channel-closed')
            channel.sequence, channel.last_digest, channel.last_response = request_id, fingerprint, response
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
