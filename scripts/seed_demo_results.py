"""Seed approved synthetic provider results into this checkout's private cache.

This is an offline import, never an analysis or provider replay. No API client is
called. The existing application still requires separately configured credentials
to look up its credential-scoped cache. --verify-only needs no credentials.
"""
import argparse
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import ROOT, Review, InputError
from report_cache import ReportCache, cache_key, unpack, successful, reused

DEMO_SETTINGS = {
    'COPILOT_ANALYST_ENGINE': 'skill',
    'COPILOT_AI_MAX_REVIEW_USD': '0.25',
    'COPILOT_AI_TIMEOUT_SECONDS': '300',
    'COPILOT_SKILL_SECONDS': '900',
    'COPILOT_SKILL_REASONING_EFFORT': 'high',
    'COPILOT_SKILL_OUTPUT_TOKENS': '32000',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _exact_json(actual, approved):
    """Type-aware exact equality for provenance and calculation metadata."""
    if type(actual) is not type(approved):
        return False
    if isinstance(approved, dict):
        return (actual.keys() == approved.keys()
                and all(_exact_json(actual[key], approved[key]) for key in approved))
    if isinstance(approved, list):
        return (len(actual) == len(approved)
                and all(_exact_json(a, b) for a, b in zip(actual, approved)))
    return actual == approved


def calculations_match(observed, approved):
    """Compare only calculated numeric values approximately; retain exact provenance.

    Python versions can differ by a few binary floating-point ULPs while
    recomputing the same expression. 1e-12 relative/absolute bounds cover that
    representation noise but reject business-significant numerical changes.
    """
    if type(observed) is not list or type(approved) is not list or len(observed) != len(approved):
        return False
    for actual, expected in zip(observed, approved):
        if type(actual) is not dict or type(expected) is not dict or actual.keys() != expected.keys():
            return False
        for field, wanted in expected.items():
            got = actual[field]
            if field == 'value':
                if (type(got) not in (int, float) or type(wanted) not in (int, float)
                        or not math.isfinite(got) or not math.isfinite(wanted)
                        or not math.isclose(got, wanted, rel_tol=1e-12, abs_tol=1e-12)):
                    return False
            elif not _exact_json(got, wanted):
                return False
    return True


def project_file(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise InputError('Prepared demo path escapes the checkout.')
    return path


def verify_prepared():
    """Verify pinned source/workbook/snapshot identity and retained source arithmetic."""
    from skill_tools import WorkbookTools
    manifest = json.loads((ROOT / 'demo_results/manifest.json').read_text())
    if manifest['format'] != 1:
        raise InputError('Unsupported prepared demo manifest.')
    for name, expected in manifest['source_sha256'].items():
        if digest(project_file(name).read_bytes()) != expected:
            raise InputError('Prepared demo source differs: ' + name)
    verified = []
    for entry in manifest['runs']:
        workbook = project_file(entry['workbook'])
        data = workbook.read_bytes()
        snapshot = project_file('demo_results/' + entry['snapshot']).read_bytes()
        if digest(data) != entry['workbook_sha256'] or digest(snapshot) != entry['snapshot_sha256']:
            raise InputError('Prepared demo content differs: ' + entry['run'])
        with gzip.GzipFile(fileobj=io.BytesIO(snapshot)) as stream:
            raw = stream.read(12_000_001)
        if len(raw) > 12_000_000 or len(raw) != entry['uncompressed_bytes']:
            raise InputError('Prepared snapshot exceeds its declared size.')
        review = Review(**unpack(json.loads(raw)))
        state = review.package['skill_engine']
        receipt = review.package['inference']
        if (not successful(review, require_real=False) or receipt.get('reused')
                or state.get('offline_replay') or state['identity'] != entry['methodology_identity']
                or receipt['model'] != entry['model']):
            raise InputError('Prepared review is not an approved completed provider result.')
        if not any(e.get('transport') == 'provider' and e.get('provider_completed')
                   and e.get('model') == entry['model'] for e in receipt['events']):
            raise InputError('Prepared provider receipt is missing.')
        tools = WorkbookTools({workbook.name: data})
        for event in state['tool_events']:
            try:
                tools.invoke(event['name'], event['arguments'])
            except Exception:
                if event['status'] != 'error':
                    raise
        for fact in tools.facts:
            tools.verify_fact(fact)
        if not calculations_match(tools.calculations, state['calculations']) or tools.errors:
            raise InputError('Prepared calculation/source verification failed.')
        for finding in review.package['ai_insights']:
            if not set(finding['fact_ids']) <= tools.facts.keys() | tools.notes.keys():
                raise InputError('Prepared finding contains an unknown source.')
            for quote in finding['source_quotes']:
                if quote['quote'] not in tools.notes[quote['source_id']]['text']:
                    raise InputError('Prepared source quote differs.')
        verified.append((entry, review, {workbook.name: data}))
    return verified


def seed(verified):
    from ai_runtime import configuration
    from skill_engine import identity
    cfg = configuration()
    if not os.environ.get('OPENAI_API_KEY'):
        raise InputError('Configure the existing local API key separately for credential-scoped cache import; no API request is made. Use --verify-only without a key.')
    # Validate all entries before writing any cache. Never re-label old results as
    # analyses of changed sources, models, methodology or spending configuration.
    for entry, review, _ in verified:
        expected = entry['pricing']
        for name in ('model', 'rates', 'cache_rates', 'limit', 'timeout', 'retries'):
            actual = cfg[name]
            if isinstance(actual, tuple):
                actual = list(actual)
            if actual != expected[name]:
                raise InputError('Prepared demo configuration differs: ' + name)
        if identity() != entry['methodology_identity'] or not successful(review):
            raise InputError('Prepared demo engine or provider identity differs.')
    results = []
    cache = ReportCache()
    for entry, review, files in verified:
        key = cache_key(files, ai_authorized=True, engine_name='skill')
        review.package['prepared_demo'] = dict(run=entry['run'], snapshot_sha256=entry['snapshot_sha256'], new_model_calls=0)
        reused(review, 'prepared-demo-import')
        if not cache.save(key, review) or cache.load(key) is None:
            raise InputError('Prepared demo cache import failed: ' + entry['run'])
        results.append(dict(run=entry['run'], status='completed', cache_key=key, new_model_calls=0, estimated_current_usd=0))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true', help='Verify sources and calculations without credentials or cache writes.')
    args = parser.parse_args()
    # Defense against accidental future provider use in this utility.
    import urllib.request
    def no_network(*a, **k):
        raise InputError('Prepared demo import cannot make network requests.')
    urllib.request.urlopen = no_network
    try:
        verified = verify_prepared()
        if args.verify_only:
            result = [dict(run=e['run'], status='verified', new_model_calls=0) for e, _, _ in verified]
        else:
            from ai_runtime import load_environment
            load_environment()
            os.environ.update(DEMO_SETTINGS)
            result = seed(verified)
        print(json.dumps(result, indent=2))
    except (InputError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
