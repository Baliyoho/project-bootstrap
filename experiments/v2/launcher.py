"""P0 trusted-parent launch authority and durable request outbox.

Only synthetic fixtures use this module. The parent must protect the database
and ticket and bind the returned channel to a confined child pipe. Neither
this Python API nor a source string authenticates a human. No arbitrary agent
command, identity, grant or resume RPC is exposed by the broker.
"""
import hashlib
import json
import math
import secrets

from experiments.v2.broker import MAX_REQUEST_BYTES
from experiments.v2.contracts import Denied


class LaunchAuthority:
    def __init__(self, broker):
        self.broker = broker
        self.lab = broker.lab
        self.lab.db.executescript('''
            CREATE TABLE IF NOT EXISTS launch_permits (
                ticket_hash TEXT PRIMARY KEY, actor TEXT NOT NULL UNIQUE,
                resources TEXT NOT NULL, source TEXT NOT NULL,
                expires REAL NOT NULL, revoked INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS client_cursor (
                actor TEXT PRIMARY KEY, next_id INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS client_requests (
                actor TEXT NOT NULL, request_id INTEGER NOT NULL,
                raw BLOB NOT NULL, digest TEXT NOT NULL, completed INTEGER NOT NULL,
                PRIMARY KEY(actor, request_id));
        ''')

    @staticmethod
    def ticket_hash(ticket):
        if not isinstance(ticket, str) or len(ticket) != 64:
            raise Denied('invalid-launch-ticket')
        return hashlib.sha256(ticket.encode('utf-8')).hexdigest()

    def permit(self, ticket_hash):
        row = self.lab.db.execute('SELECT * FROM launch_permits WHERE ticket_hash=?',
                                  (ticket_hash,)).fetchone()
        now = self.lab.authority_now()
        if row is None or row['revoked'] or now >= row['expires']:
            raise Denied('launch-not-authorized')
        return row

    def issue(self, resources, source, expires_at):
        """Trusted administration only. Return a parent-private recovery ticket.

        The principal is generated here, never selected from an agent label.
        Source is a fixture provenance label, NOT proof of human approval.
        """
        if (not isinstance(resources, (tuple, list, set, frozenset)) or not resources
                or any(not isinstance(r, str) or not r for r in resources)
                or not isinstance(source, str) or not source):
            raise Denied('invalid-launch-scope')
        ticket, actor = secrets.token_hex(32), secrets.token_hex(32)
        with self.broker.lock, self.lab.transaction():
            now = self.lab.authority_now()
            if (type(expires_at) not in (int, float) or not math.isfinite(expires_at)
                    or expires_at <= now):
                raise Denied('invalid-launch-deadline')
            self.lab.register(actor)
            self.lab.db.execute('INSERT INTO launch_permits VALUES (?, ?, ?, ?, ?, 0)',
                (self.ticket_hash(ticket), actor, json.dumps(sorted(set(resources))), source, expires_at))
            self.lab.db.execute('INSERT INTO client_cursor VALUES (?, 1)', (actor,))
        return ticket

    def connect(self, ticket):
        """Resume only with the private ticket; rotate the old channel capability.

        Scope comes exclusively from the durable permit. The parent must have
        stopped the previous child before connecting its replacement.
        """
        key = self.ticket_hash(ticket)
        with self.broker.lock, self.lab.transaction():
            permit = self.permit(key)
            channel = self.broker.attach(permit['actor'], json.loads(permit['resources']), resume=True)

            def authorize(candidate):
                current = self.permit(key)
                if (self.lab.actor(candidate.capability) != current['actor']
                        or candidate.resources != frozenset(json.loads(current['resources']))):
                    raise Denied('launch-scope-mismatch')

            channel.authorize = authorize
        return channel

    def revoke(self, ticket):
        with self.broker.lock, self.lab.transaction():
            self.lab.db.execute('UPDATE launch_permits SET revoked=1 WHERE ticket_hash=?',
                                (self.ticket_hash(ticket),))

    def grant(self, ticket, kind, resource, uses, source, expires_at):
        with self.broker.lock, self.lab.transaction():
            permit = self.permit(self.ticket_hash(ticket))
            if resource not in json.loads(permit['resources']):
                raise Denied('resource-not-authorized')
            if (type(expires_at) not in (int, float) or not math.isfinite(expires_at)
                    or expires_at > permit['expires']):
                raise Denied('invalid-grant-deadline')
            return self.lab.grant(permit['actor'], kind, resource, uses, source, expires_at)


class RequestJournal:
    """Parent-private write-ahead outbox; never reconstruct a missing request.

    Request bytes are durable before dispatch. Lost responses leave the exact
    bytes pending. Keep the entire history so loss/disagreement is detected;
    pruning, database restore and cross-device recovery are not implemented.
    """
    def __init__(self, authority, channel):
        self.authority, self.channel = authority, channel
        self.broker, self.lab = authority.broker, authority.lab

    def validate(self):
        if self.channel not in self.broker.channels or self.channel.closed or self.channel.authorize is None:
            raise Denied('closed-channel')
        self.channel.authorize(self.channel)
        actor = self.lab.actor(self.channel.capability)
        cursor = self.lab.db.execute('SELECT next_id FROM client_cursor WHERE actor=?', (actor,)).fetchone()
        rows = list(self.lab.db.execute('SELECT * FROM client_requests WHERE actor=? ORDER BY request_id', (actor,)))
        if cursor is None or [r['request_id'] for r in rows] != list(range(1, cursor[0])):
            raise Denied('request-journal-incomplete')
        receipts = {r['request_id']: r for r in self.lab.db.execute('SELECT * FROM receipts WHERE actor=?', (actor,))}
        if set(receipts) - {r['request_id'] for r in rows}:
            raise Denied('request-journal-incomplete')
        for index, row in enumerate(rows):
            receipt = receipts.get(row['request_id'])
            if (hashlib.sha256(row['raw']).hexdigest() != row['digest']
                    or (receipt is not None and receipt['digest'] != row['digest'])
                    or (row['completed'] and receipt is None)
                    or (not row['completed'] and index != len(rows) - 1)):
                raise Denied('request-journal-inconsistent')
        return actor, cursor[0], rows

    def prepare(self, fields):
        with self.broker.lock, self.lab.transaction():
            actor, next_id, rows = self.validate()
            if rows and not rows[-1]['completed']:
                raise Denied('request-already-pending')
            if not isinstance(fields, dict) or 'id' in fields:
                raise Denied('client-sequence-is-managed')
            raw = (json.dumps(dict(fields, id=next_id), sort_keys=True,
                              separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
            if len(raw) > MAX_REQUEST_BYTES:
                raise Denied('request-too-large-or-invalid')
            self.lab.db.execute('INSERT INTO client_requests VALUES (?, ?, ?, ?, 0)',
                               (actor, next_id, raw, hashlib.sha256(raw).hexdigest()))
            self.lab.db.execute('UPDATE client_cursor SET next_id=? WHERE actor=?', (next_id + 1, actor))
        return next_id

    def send(self):
        with self.broker.lock:
            with self.lab.transaction():
                actor, _, rows = self.validate()
                if not rows or rows[-1]['completed']:
                    raise Denied('no-pending-request')
                pending = rows[-1]
            # Deliberately OUTSIDE the journal transaction: a parent crash after
            # broker commit must retain both receipt and pending request.
            response = self.broker.dispatch(self.channel, pending['raw'])
            with self.lab.transaction():
                receipt = self.lab.db.execute('SELECT response FROM receipts WHERE actor=? AND request_id=?',
                                             (actor, pending['request_id'])).fetchone()
                if receipt is not None and receipt['response'] == response:
                    self.lab.db.execute('UPDATE client_requests SET completed=1 WHERE actor=? AND request_id=?',
                                        (actor, pending['request_id']))
            return response
