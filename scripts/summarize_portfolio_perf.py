"""Summarize COPILOT_PERF records downloaded from Streamlit Cloud logs."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
import sys

PREFIX = 'COPILOT_PERF '


def parse_records(lines):
    records = []
    for line in lines:
        if not line.startswith(PREFIX):
            continue
        try:
            record = json.loads(line[len(PREFIX):])
        except ValueError:
            continue
        if record.get('event') in {'script_run', 'navigation_callback'}:
            records.append(record)
    return records


def _stats(values):
    values = sorted(values)
    if not values:
        return None
    return {
        'n': len(values),
        'p50_ms': round(values[math.ceil(len(values) * .50) - 1], 2),
        'p95_ms': round(values[math.ceil(len(values) * .95) - 1], 2),
        'max_ms': round(values[-1], 2),
    }


def summarize(records):
    runs = [record for record in records if record['event'] == 'script_run']
    callbacks = [record for record in records if record['event'] == 'navigation_callback']
    by_page = defaultdict(list)
    phase_values = defaultdict(lambda: defaultdict(list))
    navigation_runs = defaultdict(int)
    peak_rss = []
    for run in runs:
        by_page[run.get('page', 'unknown')].append(run)
        if run.get('navigation', 0):
            navigation_runs[(run.get('session'), run['navigation'])] += 1
        peak_rss.append(run.get('process_peak_rss_mb', 0))
        for name, samples in run.get('phases', {}).items():
            for sample in samples:
                phase_values[run.get('page', 'unknown')][name].append(sample['elapsed_ms'])
    pages = {}
    for page, page_runs in sorted(by_page.items()):
        phases = {
            name: _stats(values)
            for name, values in sorted(phase_values[page].items())
        }
        pages[page] = {
            'runs': len(page_runs),
            'server_elapsed': _stats([run['elapsed_ms'] for run in page_runs]),
            'script_thread_cpu': _stats([run['thread_cpu_ms'] for run in page_runs]),
            'phases': phases,
        }
    nav_counts = list(navigation_runs.values())
    return {
        'script_runs': len(runs),
        'navigation_callbacks': len(callbacks),
        'script_runs_per_navigation': _stats(nav_counts),
        'process_peak_rss_mb_max': round(max(peak_rss), 2) if peak_rss else None,
        'pages': pages,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logfile', nargs='?', help='Downloaded Cloud log; reads stdin if omitted.')
    args = parser.parse_args()
    lines = Path(args.logfile).open() if args.logfile else sys.stdin
    print(json.dumps(summarize(parse_records(lines)), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
