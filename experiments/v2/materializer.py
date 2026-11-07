"""P0 POSIX materialization with a durable intent and recoverable replacement.

Only for an exclusively broker-owned synthetic tree. The OS boundary must
exclude other writers; digest comparisons are not a filesystem CAS against
arbitrary concurrent humans. No real repository is modified by the probes.
"""
import os
import json
from pathlib import Path
import re
import stat
import unicodedata
from contextlib import contextmanager
from types import MappingProxyType

from experiments.v2.contracts import Denied


MAX_CONTENT = 1024 * 1024


def supported():
    return os.name == 'posix' and hasattr(os, 'O_NOFOLLOW') and hasattr(os, 'O_DIRECTORY')


class Materializer:
    def __init__(self, lab, root, resources, fault=None):
        if not supported():
            raise Denied('materializer-platform-unverified')
        self.lab, self.root = lab, Path(root).absolute()
        self.resources = MappingProxyType(dict(resources))
        self.fault = fault or (lambda stage, event: None)
        for path in self.resources.values():
            parts = path.split('/') if isinstance(path, str) else []
            if (not parts or any(not part or part in ('.', '..') or part.casefold() == '.git' or '\\' in part
                                 or '\0' in part or part.casefold().startswith('.bootstrap-') for part in parts)):
                raise Denied('unsafe-resource-mapping')
        normalized = {unicodedata.normalize('NFC', path).casefold() for path in self.resources.values()}
        if len(normalized) != len(self.resources):
            raise Denied('aliased-resources')
        if any(not isinstance(resource, str) or not resource for resource in self.resources):
            raise Denied('invalid-resource-id')
        descriptor = os.open(str(self.root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            metadata = os.fstat(descriptor)
            self.root_identity = (metadata.st_dev, metadata.st_ino)
        finally:
            os.close(descriptor)
        binding = json.dumps([self.root_identity, dict(self.resources)], sort_keys=True)
        with self.lab.transaction():
            self.lab.db.execute('''CREATE TABLE IF NOT EXISTS materializer_binding (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1), binding TEXT NOT NULL)''')
            previous = self.lab.db.execute('SELECT binding FROM materializer_binding').fetchone()
            if previous is None:
                # A pre-binding journal cannot prove where earlier events belonged.
                # Do not silently adopt its pending writes under today's mapping.
                if self.lab.db.execute('SELECT 1 FROM writes LIMIT 1').fetchone():
                    raise Denied('missing-materializer-binding')
                self.lab.db.execute('INSERT INTO materializer_binding VALUES (1, ?)', (binding,))
            elif previous[0] != binding:
                raise Denied('materializer-binding-conflict')
            self.lab.db.execute('''CREATE TABLE IF NOT EXISTS materializations (
                event TEXT PRIMARY KEY, resource TEXT NOT NULL, phase TEXT NOT NULL,
                mode INTEGER NOT NULL)''')

    @contextmanager
    def parent(self, resource):
        if resource not in self.resources:
            raise Denied('unmapped-resource')
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptor = os.open(str(self.root), flags)
        try:
            metadata = os.fstat(descriptor)
            if (metadata.st_dev, metadata.st_ino) != self.root_identity:
                raise Denied('materializer-binding-conflict')
            parts = self.resources[resource].split('/')
            for part in parts[:-1]:
                next_descriptor = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_descriptor
            yield descriptor, parts[-1]
        finally:
            os.close(descriptor)

    @staticmethod
    def read(descriptor, name):
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        except FileNotFoundError:
            return None, 0o644
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise Denied('not-an-exclusive-regular-file')
            if metadata.st_size > MAX_CONTENT or stat.S_IMODE(metadata.st_mode) & 0o7000:
                raise Denied('unsupported-file-size-or-mode')
            chunks, size = [], 0
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_CONTENT:
                    raise Denied('file-grew-beyond-limit')
                chunks.append(chunk)
            return b''.join(chunks), stat.S_IMODE(metadata.st_mode)
        finally:
            os.close(fd)

    def seed(self, resource):
        """Trusted one-time baseline import, before any managed event exists."""
        with self.lab.transaction():
            if (self.lab.db.execute('SELECT 1 FROM files WHERE path=?', (resource,)).fetchone()
                    or self.lab.db.execute('SELECT 1 FROM writes WHERE path=?', (resource,)).fetchone()):
                raise Denied('resource-already-initialized')
            with self.parent(resource) as (descriptor, name):
                content, _ = self.read(descriptor, name)
            if content is not None:
                self.lab.db.execute('INSERT INTO files VALUES (?, ?)', (resource, content))

    def ensure_ready(self, resource):
        if resource not in self.resources:
            raise Denied('unmapped-resource')
        pending = self.lab.db.execute('SELECT 1 FROM writes w LEFT JOIN materializations m '
            'ON w.event=m.event WHERE w.path=? AND (m.phase IS NULL OR m.phase!=?)',
            (resource, 'applied')).fetchone()
        if pending:
            raise Denied('previous-materialization-pending')

    def apply(self, event_id):
        if not re.fullmatch('[0-9a-f]{32}', event_id):
            raise Denied('invalid-event')
        with self.lab.transaction():
            event = self.lab.event(event_id)
            epoch = self.lab.db.execute('SELECT epoch FROM write_epochs WHERE event=?', (event_id,)).fetchone()
            if event is None or epoch is None:
                raise Denied('missing-materialization-evidence')
            state = self.lab.db.execute('SELECT * FROM materializations WHERE event=?', (event_id,)).fetchone()
            if state is not None and (state['phase'] not in ('prepared', 'applied') or state['resource'] != event['path']):
                raise Denied('invalid-materialization-state')
            if state is not None and state['phase'] == 'applied':
                return 'applied'  # A receipt for past work, never a reapply of old content.
            self.lab.require_epoch(epoch[0])
            if len(event['after']) > MAX_CONTENT:
                raise Denied('content-too-large')
            if state is None:
                with self.parent(event['path']) as (descriptor, name):
                    content, mode = self.read(descriptor, name)
                if content != event['before']:
                    raise Denied('disk-base-conflict')
                self.lab.db.execute('INSERT INTO materializations VALUES (?, ?, ?, ?)',
                                    (event_id, event['path'], 'prepared', mode))
        # The intent must survive a process crash BEFORE touching the filesystem.
        self.fault('after_prepare', event_id)
        with self.lab.transaction():
            self.lab.require_epoch(epoch[0])
            state = self.lab.db.execute('SELECT * FROM materializations WHERE event=?', (event_id,)).fetchone()
            with self.parent(event['path']) as (descriptor, name):
                current, mode = self.read(descriptor, name)
                if current == event['after'] and mode == state['mode']:
                    # A crash after rename but before the DB commit is recoverable.
                    pass
                elif current != event['before'] or mode != state['mode']:
                    raise Denied('disk-base-conflict')
                else:
                    stage = '.bootstrap-' + event_id + '.tmp'
                    fd = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                                 0o600, dir_fd=descriptor)
                    try:
                        metadata = os.fstat(fd)
                        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                            raise Denied('unsafe-stage-file')
                        os.ftruncate(fd, 0)
                        remaining = memoryview(event['after'])
                        while remaining:
                            count = os.write(fd, remaining)
                            if count <= 0:
                                raise OSError('stage-write-failed')
                            remaining = remaining[count:]
                        os.fchmod(fd, state['mode'])
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                    self.fault('after_stage_sync', event_id)
                    # Recheck after writing the staging file. Exclusive OS ownership
                    # is still required between this check and replace.
                    if self.read(descriptor, name) != (event['before'], state['mode']):
                        raise Denied('disk-base-conflict')
                    os.replace(stage, name, src_dir_fd=descriptor, dst_dir_fd=descriptor)
                    self.fault('after_replace', event_id)
                # Recovery may observe the renamed file after a crash that
                # happened before directory sync. Seeing bytes is not durability.
                os.fsync(descriptor)
                self.lab.db.execute('UPDATE materializations SET phase=? WHERE event=?', ('applied', event_id))
        self.fault('after_commit', event_id)
        return 'applied'
