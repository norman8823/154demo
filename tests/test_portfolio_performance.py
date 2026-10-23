"""Private performance log format and summary coverage."""
import json

from portfolio_performance import PerformanceRun, record_navigation, start_run
from scripts.summarize_portfolio_perf import parse_records, summarize


def test_run_and_navigation_logs_contain_timing_without_user_data(capsys):
    state = {}
    run = start_run(state, 'company')
    with run.measure('company_workbook_cache_lookup_and_deserialization'):
        pass
    run.finish()
    record_navigation(state, 'company')
    records = parse_records(capsys.readouterr().out.splitlines())
    assert [r['event'] for r in records] == ['script_run', 'navigation_callback']
    assert records[0]['page'] == 'company'
    assert records[0]['run'] == 1 and records[0]['navigation'] == 0
    assert records[0]['phases']['company_workbook_cache_lookup_and_deserialization'][0]['elapsed_ms'] >= 0
    assert records[1]['navigation'] == 1 and records[1]['destination'] == 'company'
    serialized = json.dumps(records)
    assert 'company_id' not in serialized and 'source_id' not in serialized
    assert 'cookie' not in serialized and 'email' not in serialized


def test_summary_groups_pages_phases_and_repeated_runs_per_navigation():
    records = [
        {'event': 'navigation_callback', 'session': 's1', 'navigation': 1, 'destination': 'foundation'},
        {'event': 'script_run', 'session': 's1', 'run': 2, 'navigation': 1, 'page': 'foundation',
         'elapsed_ms': 900, 'thread_cpu_ms': 120, 'process_peak_rss_mb': 250,
         'phases': {'page_render': [{'elapsed_ms': 600, 'thread_cpu_ms': 80}]}},
        {'event': 'script_run', 'session': 's1', 'run': 3, 'navigation': 1, 'page': 'foundation',
         'elapsed_ms': 300, 'thread_cpu_ms': 90, 'process_peak_rss_mb': 251, 'phases': {}},
    ]
    result = summarize(parse_records(['noise\n', *['COPILOT_PERF '+json.dumps(r) for r in records]]))
    assert result['script_runs'] == 2
    assert result['navigation_callbacks'] == 1
    assert result['script_runs_per_navigation']['max_ms'] == 2
    assert result['process_peak_rss_mb_max'] == 251
    assert result['pages']['foundation']['server_elapsed']['p50_ms'] == 300
    assert result['pages']['foundation']['phases']['page_render']['p50_ms'] == 600
