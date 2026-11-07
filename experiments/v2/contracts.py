"""P0 transactional model, using synthetic content only.

The administrator and agent APIs intentionally share one Python process for
contract testing. They are NOT an OS security boundary or real identity proof.
Do not put real credentials/content here or expose this object to agents.
"""
import hashlib
import secrets
import sqlite3
from datetime import datetime, timezone


class Denied(Exception):
    """Safe fixed-code rejection; no submitted content in the message."""


def digest(content):
    return hashlib.sha256(content).hexdigest()


class Lab:
    def __init__(self, path, clock=None):
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (
                capability TEXT PRIMARY KEY, actor TEXT NOT NULL UNIQUE);
            CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, content BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS writes (
                seq INTEGER PRIMARY KEY, event TEXT NOT NULL UNIQUE,
                actor TEXT NOT NULL, at TEXT NOT NULL, path TEXT NOT NULL,
                before BLOB, after BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS state (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                epoch INTEGER NOT NULL, pending INTEGER, change TEXT);
            INSERT OR IGNORE INTO state VALUES (1, 0, NULL, NULL);
            CREATE TABLE IF NOT EXISTS notices (
                actor TEXT, epoch INTEGER, change TEXT NOT NULL, acknowledged INTEGER NOT NULL,
                PRIMARY KEY(actor, epoch));
            CREATE TABLE IF NOT EXISTS operations (
                ticket TEXT PRIMARY KEY, actor TEXT NOT NULL,
                epoch INTEGER NOT NULL, status TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS grants (
                id TEXT PRIMARY KEY, actor TEXT NOT NULL, kind TEXT NOT NULL,
                resource TEXT NOT NULL, remaining INTEGER NOT NULL,
                source TEXT NOT NULL, revoked INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS effects (
                seq INTEGER PRIMARY KEY, actor TEXT, kind TEXT, resource TEXT, grant_id TEXT);
        ''')

    def close(self):
        self.db.close()

    def register(self, actor):
        """Trusted launcher stand-in; never an agent-supplied actor parameter."""
        capability = secrets.token_hex(32)
        with self.db:
            self.db.execute('INSERT INTO sessions VALUES (?, ?)', (capability, actor))
            state = self.db.execute('SELECT * FROM state').fetchone()
            if state['pending'] is not None:
                self.db.execute('INSERT INTO notices VALUES (?, ?, ?, 0)',
                                (actor, state['pending'], state['change']))
        return capability

    def actor(self, capability):
        row = self.db.execute('SELECT actor FROM sessions WHERE capability=?',
                              (capability,)).fetchone()
        if row is None:
            raise Denied('unknown-session')
        return row['actor']

    def write(self, capability, path, expected, content):
        """Journal and content commit together; concurrent stale bases are rejected.

        This models a broker-owned content store, not arbitrary filesystem edits.
        A filesystem materializer/recovery protocol is deliberately not claimed.
        """
        actor = self.actor(capability)
        if not isinstance(content, bytes):
            raise Denied('bytes-required')
        event = secrets.token_hex(16)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self.db.execute('SELECT content FROM files WHERE path=?', (path,)).fetchone()
            before = None if row is None else row['content']
            if expected != (None if before is None else digest(before)):
                raise Denied('stale-base')
            self.db.execute('INSERT INTO writes(event, actor, at, path, before, after) '
                            'VALUES (?, ?, ?, ?, ?, ?)',
                            (event, actor, self.clock(), path, before, content))
            self.db.execute('INSERT OR REPLACE INTO files VALUES (?, ?)', (path, content))
        return event

    def event(self, event_id):
        row = self.db.execute('SELECT * FROM writes WHERE event=?', (event_id,)).fetchone()
        return None if row is None else dict(row)

    def begin(self, capability, epoch):
        actor = self.actor(capability)
        ticket = secrets.token_hex(16)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            state = self.db.execute('SELECT * FROM state').fetchone()
            if state['pending'] is not None or epoch != state['epoch']:
                raise Denied('premise-not-current')
            self.db.execute('INSERT INTO operations VALUES (?, ?, ?, ?)',
                            (ticket, actor, epoch, 'running'))
        return ticket

    def propose(self, change):
        """Persist the notification and invalidate work in one transaction.

        All registered sessions are recipients, including unknown dependencies.
        The durable inbox is not a push transport or a model context reset.
        """
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            state = self.db.execute('SELECT * FROM state').fetchone()
            if state['pending'] is not None:
                raise Denied('change-already-pending')
            pending = state['epoch'] + 1
            self.db.execute('UPDATE state SET pending=?, change=?', (pending, change))
            self.db.execute('INSERT INTO notices SELECT actor, ?, ?, 0 FROM sessions',
                            (pending, change))
            self.db.execute("UPDATE operations SET status='invalid' WHERE status='running'")
        return pending

    def inbox(self, capability):
        actor = self.actor(capability)
        return [dict(row) for row in self.db.execute(
            'SELECT epoch, change, acknowledged FROM notices WHERE actor=? ORDER BY epoch',
            (actor,))]

    def acknowledge(self, capability, epoch, change, application=False):
        actor = self.actor(capability)
        if application is not True:
            raise Denied('transport-ack-is-not-application-ack')
        with self.db:
            row = self.db.execute('SELECT change FROM notices WHERE actor=? AND epoch=?',
                                  (actor, epoch)).fetchone()
            if row is None or row['change'] != change:
                raise Denied('wrong-notice')
            self.db.execute('UPDATE notices SET acknowledged=1 WHERE actor=? AND epoch=?',
                            (actor, epoch))

    def activate(self):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            state = self.db.execute('SELECT * FROM state').fetchone()
            if state['pending'] is None:
                raise Denied('no-pending-change')
            if self.db.execute('SELECT 1 FROM notices WHERE epoch=? AND acknowledged=0',
                               (state['pending'],)).fetchone():
                raise Denied('unacknowledged-line')
            self.db.execute('UPDATE state SET epoch=pending, pending=NULL, change=NULL')

    def complete(self, capability, ticket):
        actor = self.actor(capability)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            op = self.db.execute('SELECT * FROM operations WHERE ticket=?', (ticket,)).fetchone()
            state = self.db.execute('SELECT * FROM state').fetchone()
            if (op is None or op['actor'] != actor or op['status'] != 'running'
                    or state['pending'] is not None or op['epoch'] != state['epoch']):
                raise Denied('invalid-operation')
            self.db.execute("UPDATE operations SET status='completed' WHERE ticket=?", (ticket,))

    def grant(self, actor, kind, resource, uses, source):
        """Human authorization stand-in; outside the agent API in a real broker."""
        if type(uses) is not int or uses < 1 or not source:
            raise Denied('invalid-grant')
        grant_id = secrets.token_hex(16)
        with self.db:
            self.db.execute('INSERT INTO grants VALUES (?, ?, ?, ?, ?, ?, 0)',
                            (grant_id, actor, kind, resource, uses, source))
        return grant_id

    def revoke(self, grant_id):
        with self.db:
            self.db.execute('UPDATE grants SET revoked=1 WHERE id=?', (grant_id,))

    def effect(self, capability, kind, resource):
        """Record a synthetic effect only; no paid or destructive action executes."""
        actor = self.actor(capability)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            grant = self.db.execute('SELECT * FROM grants WHERE actor=? AND kind=? '
                'AND resource=? AND revoked=0 AND remaining>0 ORDER BY id LIMIT 1',
                (actor, kind, resource)).fetchone()
            if grant is None:
                raise Denied('not-authorized')
            self.db.execute('UPDATE grants SET remaining=remaining-1 WHERE id=?', (grant['id'],))
            self.db.execute('INSERT INTO effects(actor, kind, resource, grant_id) VALUES (?, ?, ?, ?)',
                            (actor, kind, resource, grant['id']))


def scan_snapshot(files, message, forbidden):
    """Freeze and scan ALL candidates before any caller writes Git objects.

    This is a known-value fixture scanner, not Gitleaks or a semantic detector.
    Returns immutable bytes; the caller must never reopen mutable source files.
    """
    if not forbidden or any(not isinstance(value, bytes) or not value for value in forbidden):
        raise Denied('missing-scanner-policy')
    snapshot = tuple((name, bytes(content)) for name, content in sorted(files.items()))
    for name, content in snapshot:
        if not name or name.startswith('/') or '..' in name.split('/') or '\\' in name:
            raise Denied('invalid-path')
        if any(value in name.encode('utf-8') or value in content for value in forbidden):
            raise Denied('sensitive-candidate')
    if any(value in message.encode('utf-8') for value in forbidden):
        raise Denied('sensitive-message')
    return snapshot


def mask_summary(content, forbidden, limit):
    for value in sorted(forbidden, key=len, reverse=True):
        content = content.replace(value, b'***')
    return content[:limit]
