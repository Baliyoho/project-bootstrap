"""F50 deterministic transitions. Receipts must come from a trusted adapter.

This module neither writes HANDOFF nor invokes a provider. A transition is an
intention, not proof that a provider changed the title. Persist the returned
state before retrying a failed rename, to avoid counting a handoff twice.
"""
from dataclasses import dataclass, replace
import re
from typing import Tuple


@dataclass(frozen=True)
class HandoffReceipt:
    event_id: str
    final_checks_passed: bool
    push_succeeded: bool
    remote_released: bool
    upstream_aligned: bool

    def valid(self):
        return bool(self.event_id) and all(value is True for value in (
            self.final_checks_passed, self.push_succeeded,
            self.remote_released, self.upstream_aligned))


@dataclass(frozen=True)
class Session:
    started: str
    topic: str
    count: int = 0
    at_least: bool = False
    state: str = 'working'
    completed: Tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, 'completed', tuple(self.completed))
        if not re.fullmatch(r'\d{8}', self.started):
            raise ValueError('start must be the original YYMMDDHH')
        if not self.topic or len(self.topic) > 10 or any(
                ch in self.topic for ch in '\n\r｜'):
            raise ValueError('topic must contain 1–10 characters without separators')
        if type(self.count) is not int or self.count < 0:
            raise ValueError('invalid handoff count')
        if self.state not in ('working', 'waiting', 'handed_off'):
            raise ValueError('invalid session state')
        if len(set(self.completed)) != len(self.completed) or any(
                not isinstance(event, str) or not event for event in self.completed):
            raise ValueError('invalid completion history')

    def title(self):
        symbol, label = {
            'working': ('㊣', '工作中'),
            'waiting': ('※', '待你決定'),
            'handed_off': ('↗', '已交棒'),
        }[self.state]
        count = ('≥' if self.at_least else '') + str(self.count)
        return f'{symbol}　{self.started}｜{self.topic}｜{label}｜交棒{count}次'

    def transition(self, event, receipt=None):
        if event in ('start', 'message'):
            return replace(self, state='working')
        if event == 'wait_for_user':
            return replace(self, state='waiting')
        if event == 'checkpoint':
            return self
        if event != 'handoff':
            raise ValueError('unknown session event')
        if receipt is None or not receipt.valid():
            raise ValueError('handoff lacks successful final/remote evidence')
        if receipt.event_id in self.completed:
            return self
        if self.state == 'handed_off':
            raise ValueError('resume before a new handoff')
        return replace(self, state='handed_off', count=self.count + 1,
                       completed=self.completed + (receipt.event_id,))

    @classmethod
    def from_title(cls, title):
        match = re.fullmatch(
            r'([㊣※↗])[ 　](\d{8})｜([^｜]+)｜(工作中|待你決定|已交棒)｜交棒(≥?)(\d+)次',
            title)
        if not match:
            raise ValueError('cannot recover count; inspect this chat history')
        symbol, started, topic, label, lower_bound, count = match.groups()
        state = {'工作中': 'working', '待你決定': 'waiting', '已交棒': 'handed_off'}[label]
        instance = cls(started, topic, int(count), bool(lower_bound), state)
        if instance.title()[0] != symbol:
            raise ValueError('symbol contradicts status')
        return instance


def rename(session, adapter):
    """Adapter exposes set_title/get_title; failures never become success.

    Some UIs normalize U+3000 to a space. Accept exactly that normalization,
    while preserving all meaningful fields. Exceptions are not printed: a
    provider exception can contain credentials or private request payloads.
    """
    target = session.title()
    if adapter is None:
        return {'status': 'unavailable', 'requested': target, 'observed': None}
    try:
        adapter.set_title(target)
        observed = adapter.get_title()
    except Exception:
        return {'status': 'error', 'requested': target, 'observed': None}
    if observed not in (target, target.replace('　', ' ', 1)):
        return {'status': 'mismatch', 'requested': target, 'observed': None}
    return {'status': 'applied', 'requested': target, 'observed': observed}
