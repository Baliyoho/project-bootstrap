"""Trusted POSIX direct-child guardian for synthetic P0 fixtures.

The parent owns the sole write end of a lifetime pipe. EOF requests shutdown;
the worker never inherits either control descriptor. Only this live guardian
owns/waits/signals its Popen child. No persisted PID is accepted as authority.
Fork containment belongs to the OS profile, not to this module. Killing this
guardian itself remains an unresolved failure, never a successful stop proof.
"""
import json
import os
import select
import signal
import subprocess
import sys


def run(watch, report, grace, argv):
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    # A dead parent before startup must not cause a fresh worker to be spawned.
    if select.select([watch], [], [], 0)[0]:
        return 1
    child = subprocess.Popen(argv, stdin=sys.stdin.buffer, stdout=sys.stdout.buffer,
                             stderr=subprocess.DEVNULL, close_fds=True)
    try:
        while child.poll() is None and not stopping:
            if select.select([watch], [], [], 0.05)[0]:
                # No messages are valid on this pipe; EOF and unexpected data
                # both fail closed. The descriptor is never passed to worker.
                os.read(watch, 1)
                break
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                child.kill()
        code = child.wait(timeout=grace)
        try:
            os.write(report, ('reaped:%d\n' % code).encode('ascii'))
        except BrokenPipeError:
            # Parent death is the very event this watchdog must handle.
            pass
    return code if code >= 0 else 128 - code


if __name__ == '__main__':
    raise SystemExit(run(int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]),
                         json.loads(sys.argv[4])))
