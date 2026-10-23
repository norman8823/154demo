"""Private, low-overhead timing records for deployed portfolio page runs."""
from contextlib import contextmanager
import json
import resource
import sys
import time
from uuid import uuid4


_ROUTES = frozenset({'overview', 'company', 'foundation', 'excel', 'issues', 'source'})
_SESSION_KEY = '_copilot_perf_session'
_RUN_KEY = '_copilot_perf_run'
_NAV_KEY = '_copilot_perf_navigation'


def _emit(record):
    # Community Cloud app logs are developer-only. Records deliberately exclude
    # company names/IDs, query strings, source references, cookies and IPs.
    print('COPILOT_PERF ' + json.dumps(record, separators=(',', ':')), flush=True)


def route_name(value):
    return value if value in _ROUTES else 'other'


def start_run(session_state, page):
    """Assign an ephemeral session counter and begin one script-run sample."""
    if _SESSION_KEY not in session_state:
        session_state[_SESSION_KEY] = uuid4().hex[:8]
        session_state[_RUN_KEY] = 0
        session_state[_NAV_KEY] = 0
    session_state[_RUN_KEY] += 1
    return PerformanceRun(
        session=session_state[_SESSION_KEY],
        run=session_state[_RUN_KEY],
        navigation=session_state[_NAV_KEY],
        page=route_name(page),
    )


def record_navigation(session_state, destination):
    """Log one button callback without recording its company/finding arguments."""
    if _SESSION_KEY not in session_state:
        session_state[_SESSION_KEY] = uuid4().hex[:8]
        session_state[_RUN_KEY] = 0
        session_state[_NAV_KEY] = 0
    session_state[_NAV_KEY] += 1
    _emit({
        'event': 'navigation_callback',
        'session': session_state[_SESSION_KEY],
        'navigation': session_state[_NAV_KEY],
        'destination': route_name(destination),
    })


class PerformanceRun:
    def __init__(self, *, session, run, navigation, page):
        self.session = session
        self.run = run
        self.navigation = navigation
        self.page = page
        self.started = time.perf_counter()
        self.cpu_started = time.thread_time()
        self.phases = {}

    @contextmanager
    def measure(self, name):
        started = time.perf_counter()
        cpu_started = time.thread_time()
        try:
            yield
        finally:
            sample = {
                'elapsed_ms': round((time.perf_counter() - started) * 1000, 2),
                'thread_cpu_ms': round((time.thread_time() - cpu_started) * 1000, 2),
            }
            self.phases.setdefault(name, []).append(sample)

    def finish(self):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # getrusage is bytes on macOS and KiB on Linux.
        peak_rss_mb = usage.ru_maxrss / (1024 * 1024 if sys.platform == 'darwin' else 1024)
        _emit({
            'event': 'script_run',
            'session': self.session,
            'run': self.run,
            'navigation': self.navigation,
            'page': self.page,
            'elapsed_ms': round((time.perf_counter() - self.started) * 1000, 2),
            'thread_cpu_ms': round((time.thread_time() - self.cpu_started) * 1000, 2),
            'process_peak_rss_mb': round(peak_rss_mb, 2),
            'phases': self.phases,
        })
