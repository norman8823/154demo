"""Build approved downloadable report assets from the verified release checkpoint."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import ROOT
from portfolio_data import load_companies
from portfolio_excel import export_portfolio
from portfolio_financial_reporting import export_company_report
from portfolio_report_assets import (
    FILENAMES, FORMAT, REPORT_CODE, _company_identity, _prepared_manifest,
    _sha256, _source_identities,
)


def build():
    companies = load_companies()  # performs fail-closed prepared-source verification
    approved_manifest, prepared_hash = _prepared_manifest()
    output = ROOT / 'demo_assets' / 'reports'
    output.mkdir(parents=True, exist_ok=True)

    reports = {}
    payloads = {'gp_portfolio': (export_portfolio(companies), ())}
    by_id = {company.id: company for company in companies}
    for company_id in ('summit', 'tallis', 'harrow'):
        data, filename, warnings = export_company_report(by_id[company_id].review)
        if filename != FILENAMES[company_id]:
            raise ValueError('Approved company report filename changed: ' + company_id)
        payloads[company_id] = (data, warnings)

    for report_id, (data, warnings) in payloads.items():
        filename = FILENAMES[report_id]
        path = output / filename
        path.write_bytes(data)
        reports[report_id] = {
            'filename': filename,
            'sha256': _sha256(data),
            'source_checkpoints': _source_identities(report_id, companies, approved_manifest),
            'warnings': list(warnings),
            'report_code_sha256': {
                name: _sha256((ROOT / name).read_bytes()) for name in REPORT_CODE[report_id]
            },
        }

    # Keep complete source identity alongside the artifact-specific identities.
    # This is intentional: a new approved manifest always requires a rebuild.
    package = {
        'format': FORMAT,
        'prepared_manifest_sha256': prepared_hash,
        'source_runs': {
            company.id: _company_identity(company) for company in companies
        },
        'reports': reports,
    }
    (output / 'manifest.json').write_text(json.dumps(package, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: value['sha256'] for key, value in reports.items()}, indent=2))


if __name__ == '__main__':
    build()
