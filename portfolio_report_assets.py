"""Hash-pinned, immutable Excel assets for the approved portfolio release."""
import hashlib
import json
from pathlib import Path

from engine import ROOT, InputError

ASSET_DIRECTORY = ROOT / 'demo_assets' / 'reports'
ASSET_MANIFEST = ASSET_DIRECTORY / 'manifest.json'
FORMAT = 1

# Changes to any report builder dependency invalidate the packaged reports. The
# original frozen exporter and its dependencies are independently source-pinned
# by demo_results/manifest.json.
REPORT_CODE = {
    'gp_portfolio': (
        'portfolio_excel.py', 'portfolio_comparison.py', 'portfolio_dashboard.py',
        'portfolio_watchlist.py', 'portfolio_sources.py', 'portfolio_financial_reporting.py',
        'portfolio_gp_presentation.py', 'portfolio_investments.py', 'portfolio_outlook.py',
        'portfolio_investment_excel.py', 'portfolio_company_excel.py',
    ),
    'summit': (
        'reports.py', 'portfolio_financial_reporting.py', 'portfolio_comparison.py',
        'portfolio_company_excel.py', 'excel_layout.py',
    ),
    'tallis': (
        'reports.py', 'portfolio_financial_reporting.py', 'portfolio_comparison.py',
        'portfolio_company_excel.py', 'excel_layout.py',
    ),
    'harrow': (
        'reports.py', 'portfolio_financial_reporting.py', 'portfolio_comparison.py',
        'portfolio_company_excel.py', 'excel_layout.py',
    ),
}

FILENAMES = {
    'gp_portfolio': 'GP_Portfolio_Review_Sep2026_FY2026.xlsx',
    'summit': 'Summit_Home_Services_Sep2026_MonthlyReview.xlsx',
    'tallis': 'Tallis_Brook_Accounting_Sep2026_MonthlyReview.xlsx',
    'harrow': 'Harrow_Ridge_Environmental_FY2026_AnnualReview.xlsx',
}


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _code_identity(report_id):
    return {name: _sha256((ROOT / name).read_bytes()) for name in REPORT_CODE[report_id]}


def _prepared_manifest():
    path = ROOT / 'demo_results' / 'manifest.json'
    raw = path.read_bytes()
    return json.loads(raw), _sha256(raw)


def _company_identity(company):
    return {
        'run': company.run,
        'workbook': company.provenance['workbook'],
        'workbook_sha256': company.provenance['workbook_sha256'],
        'snapshot': company.provenance['snapshot'],
        'snapshot_sha256': company.provenance['snapshot_sha256'],
    }


def _source_identities(report_id, companies, prepared_manifest):
    by_id = {company.id: company for company in companies}
    ids = ('summit', 'tallis', 'harrow') if report_id == 'gp_portfolio' else (report_id,)
    entries = {entry['run']: entry for entry in prepared_manifest['runs']}
    result = {}
    for company_id in ids:
        company = by_id.get(company_id)
        if company is None:
            raise InputError('Verified source company is unavailable for report: ' + company_id)
        actual = _company_identity(company)
        approved = entries.get(company.run)
        if approved is None or any(actual[key] != approved[key] for key in actual):
            raise InputError('Report source identity differs from the approved checkpoint: ' + company_id)
        result[company_id] = actual
    return result


def report_asset(report_id, companies):
    """Return verified packaged bytes; never serialize Reviews or build Excel here."""
    if report_id not in FILENAMES:
        raise InputError('Unknown packaged report.')
    try:
        manifest, prepared_hash = _prepared_manifest()
        package = json.loads(ASSET_MANIFEST.read_text())
        if package.get('format') != FORMAT or package.get('prepared_manifest_sha256') != prepared_hash:
            raise InputError('Packaged Excel reports do not match the approved source manifest.')
        record = package.get('reports', {}).get(report_id)
        if not isinstance(record, dict) or record.get('filename') != FILENAMES[report_id]:
            raise InputError('Required packaged Excel report is missing or incompatible.')
        if record.get('source_checkpoints') != _source_identities(report_id, companies, manifest):
            raise InputError('Packaged Excel report checkpoint identity has changed.')
        if record.get('report_code_sha256') != _code_identity(report_id):
            raise InputError('Packaged Excel report builder has changed; rebuild release assets.')
        path = (ASSET_DIRECTORY / record['filename']).resolve()
        if not path.is_relative_to(ASSET_DIRECTORY.resolve()) or not path.is_file():
            raise InputError('Required packaged Excel report is missing.')
        data = path.read_bytes()
        if _sha256(data) != record.get('sha256'):
            raise InputError('Packaged Excel report hash verification failed.')
        if not data.startswith(b'PK'):
            raise InputError('Packaged Excel report is not a valid XLSX container.')
        warnings = record.get('warnings', [])
        if type(warnings) is not list or any(type(item) is not str for item in warnings):
            raise InputError('Packaged Excel report metadata is invalid.')
        return data, record['filename'], tuple(warnings)
    except InputError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise InputError('Packaged Excel report verification failed.') from exc
