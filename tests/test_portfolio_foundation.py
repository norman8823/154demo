import ast
from copy import deepcopy
from dataclasses import replace
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
import pytest
from streamlit.testing.v1 import AppTest
from engine import ROOT
from portfolio_data import load_companies
from portfolio_comparison import comparison
from portfolio_foundation import export_foundation, foundation_records, SCHEMA


@pytest.fixture(scope='module')
def package():
    companies=load_companies();data=export_foundation(companies)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:files={name:archive.read(name) for name in archive.namelist()}
    return companies,data,files


def read_csv(data):
    return list(csv.DictReader(io.StringIO(data.decode('utf8'))))


def test_schema_lineage_and_every_retained_normalized_observation_reconcile(package):
    companies,data,files=package
    assert set(files)=={'financial_facts.csv','metric_definitions.json','source_lineage.csv','quality_report.json','example_consumer.py','README.md'}
    facts=read_csv(files['financial_facts.csv']);lineage=read_csv(files['source_lineage.csv'])
    definitions=json.loads(files['metric_definitions.json']);quality=json.loads(files['quality_report.json'])
    assert definitions['schema_version']==quality['schema_version']==SCHEMA
    assert len(facts)==len(lineage)==quality['normalized_observations']==1002
    assert quality['source_observations_verified']==996
    assert quality['blank_observations']==6
    assert quality['unresolved_mappings']==204
    assert quality['human_approved_mappings']==0
    assert quality['new_model_calls']==0 and quality['synthetic_investment_ledger_included'] is False
    indexed={r['fact_key']:r for r in lineage}
    originals={(c.id,c.run,n['fact_id']):(c,n) for c in companies for n in c.review.normalized}
    assert len(indexed)==len(facts)
    for row in facts:
        c,n=originals[(row['company_id'],row['approved_run'],row['source_fact_id'])]
        assert row['fact_key']==c.id+':'+c.run+':'+n['fact_id']
        assert row['metric_id'] in definitions['metrics']
        assert row['metric_definition']==definitions['metrics'][row['metric_id']]
        assert row['human_approval_status']=='not_recorded'
        assert row['mapping_accepted']==str(n['accepted']).lower()
        assert row['mapping_status']==n['mapping_status']
        assert row['provenance_class']=='prepared_operating_observation'
        for export,original in [('period','period'),('period_grain','grain'),('scenario','scenario'),('accounting_basis','basis'),('currency','currency'),('role','role'),('source_label','label'),('workbook_reference','source_ref')]:assert row[export]==n[original]
        if n['value'] is None:
            assert row['value']=='' and row['verification_status']=='blank_source_no_numeric_value'
        else:
            assert float(row['value'])==n['value']
            assert float(row['raw_source_value'])==n['raw_value']
            assert row['verification_status']=='source_observation_verified'
        origin=indexed[row['fact_key']]
        assert origin['source_reference']==n['source_ref'] and origin['source_cell']==n['cell'] and origin['source_sheet']==n['source_sheet']
        assert origin['canonical_workbook']==c.provenance['workbook']
        for key in ('workbook_sha256','snapshot_sha256'):assert row[key]==origin[key]==c.provenance[key]
        assert json.loads(origin['original_source_value_json'])==n['raw_value']
        if n['raw'] is not None and isinstance(n['raw'],str) and n['raw'].startswith('='):
            assert json.loads(origin['original_formula_json'])==n['raw']
    assert sum(f['comparison_selected']=='true' for f in facts)==12
    assert {f['period_grain'] for f in facts}=={'month','fiscal_quarter','annual'}
    assert {f['accounting_basis'] for f in facts}=={'unknown','accrual'}
    assert {f['currency'] for f in facts}=={'$','USD'}
    assert export_foundation(companies)==data


def test_standalone_consumer_has_no_excel_app_network_or_credential_access(package,tmp_path):
    companies,data,files=package
    for name,body in files.items():(tmp_path/name).write_bytes(body)
    # Python -I -S excludes the checkout, site packages and environment imports.
    # Audit hooks additionally refuse nonstdlib imports, any workbook/outside
    # data access, and socket creation. Only the extracted six files are needed.
    harness=r'''
import sys, pathlib, runpy, json
target=pathlib.Path(sys.argv[1]).resolve()
root=target.parent
base=pathlib.Path(sys.base_prefix).resolve()
events={'socket_calls':0,'workbook_reads':0,'nonstdlib_imports':0}
def audit(event,args):
    if event.startswith('socket.'):
        events['socket_calls']+=1
        raise AssertionError('Network access forbidden')
    if event=='import' and args[0].split('.')[0] not in sys.stdlib_module_names:
        events['nonstdlib_imports']+=1
        raise AssertionError('Application/third-party import forbidden')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=pathlib.Path(args[0].decode() if isinstance(args[0],bytes) else args[0]).resolve()
        if p.suffix.lower() in ('.xlsx','.xls','.xlsm'):
            events['workbook_reads']+=1
            raise AssertionError('Excel access forbidden')
        if not (p.is_relative_to(root) or p.is_relative_to(base)):
            raise AssertionError('Data access outside exported package/stdlib forbidden')
sys.addaudithook(audit)
sys.argv=[str(target)]
runpy.run_path(str(target),run_name='__main__')
print(json.dumps(events),file=sys.stderr)
'''
    completed=subprocess.run([sys.executable,'-I','-S','-c',harness,str(tmp_path/'example_consumer.py')],cwd=tmp_path,env={'PATH':os.defpath},capture_output=True,text=True,timeout=30,check=True)
    assert json.loads(completed.stderr)=={'socket_calls':0,'workbook_reads':0,'nonstdlib_imports':0}
    output=json.loads(completed.stdout)
    assert len(output['comparison'])==3
    for row in output['comparison']:
        company=next(c for c in companies if c.id==row['company_id']);view=comparison(company)
        assert row['revenue']==view['revenue'].actual
        assert row['reported_ebitda']==view['ebitda'].actual
        assert row['revenue_budget']==view['revenue'].budget
        assert row['ebitda_budget']==view['ebitda'].budget
        assert row['ebitda_margin']==pytest.approx(view['margin'].actual)
        assert row['ebitda_variance_pct']==pytest.approx(view['ebitda'].variance_pct)
        assert row['period']=='2026-FY' if company.id=='harrow' else row['period']=='2026-09'
        assert row['human_approval_status']=='not_recorded'
    imports={n.names[0].name if isinstance(n,ast.Import) else n.module for n in ast.walk(ast.parse(files['example_consumer.py'])) if isinstance(n,(ast.Import,ast.ImportFrom))}
    assert imports<={'argparse','csv','hashlib','json','decimal','pathlib'}


def test_corrupted_normalized_values_and_source_identity_fail_safely():
    companies=list(load_companies());review=deepcopy(companies[0].review)
    review.normalized[0]['value']+=1
    companies[0]=replace(companies[0],review=review)
    with pytest.raises(ValueError,match='arithmetic'):export_foundation(companies)
    review.normalized[0]['value']-=1;review.normalized[0]['source_ref']="'Wrong'!A1"
    with pytest.raises(ValueError,match='source identity'):export_foundation(companies)


def test_data_foundation_page_exposes_approval_distinctions_and_real_preview():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60).run()
    at.button(key='nav_foundation').click().run()
    assert not at.exception
    assert at.title[0].value=='Data Landscape'
    table=next(m.value for m in at.markdown if 'gp-catalog-sources' in m.value and '<table' in m.value)
    assert table.count('<tr>')==4
    assert len(at.selectbox(key='foundation_metric').options)==10
    assert any('Human approval: not_recorded' in c.value for c in at.caption)
    at.selectbox(key='foundation_company').set_value('Tallis Brook Accounting').run()
    assert not at.exception
    assert all('Tallis Brook Accounting' in o for o in at.selectbox(key='foundation_mapping').options)
    at.selectbox(key='foundation_scenario').set_value('budget').run()
    assert not at.exception
    assert any('204 unresolved mapping rows' in c.value for c in at.caption)


def test_data_package_immutable_resource_cache_preserves_exact_export(package):
    from portfolio_foundation_ui import foundation_package, _foundation_identity
    companies,data,_files=package
    foundation_package.clear()
    identity=_foundation_identity(companies)
    first=foundation_package(identity,companies)
    second=foundation_package(identity,companies)
    assert first==data and second==data
    assert first is second
    foundation_package.clear()
