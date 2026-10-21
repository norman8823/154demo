import hashlib
from dataclasses import replace
from html import unescape
import pytest
from streamlit.testing.v1 import AppTest
from engine import ROOT, InputError
from portfolio_data import load_companies
from portfolio_documents import (original_document, source_books, source_fact,
    cell_record, checked_coordinate, worksheet_html, evidence_locations)


@pytest.fixture(scope='module')
def companies(): return load_companies()


@pytest.mark.parametrize('slug,sheet,cell,raw,standard',[
    ('summit','Income Statement','D15',3298,3298000),
    ('tallis','Practice P&L','G12',3475418,3475418),
    ('harrow','P&L Summary','F13',46650,46650000)])
def test_original_hash_actual_cells_and_highlight(companies,slug,sheet,cell,raw,standard):
    company=next(c for c in companies if c.id==slug)
    doc=original_document(company)
    assert hashlib.sha256(doc.data).hexdigest()==company.provenance['workbook_sha256']
    assert doc.data==(ROOT/company.provenance['workbook']).read_bytes()
    book,cached=source_books(doc)
    for ws in book:
        assert cached[ws.title]['A1'].value==ws['A1'].value
    record=cell_record(company,book[sheet],cached[sheet],cell)
    assert record['value']==raw and record['fact']['value']==standard
    assert record['formula']==book[sheet][cell].value
    fact=source_fact(company,record['fact']['id'])
    assert fact['sheet']==sheet and fact['cell']==cell
    row,col=checked_coordinate(book[sheet],cell)
    html=worksheet_html(company,book[sheet],cached[sheet],max(1,row-5),max(1,col-2),cell)
    assert f'data-coordinate="{cell}"' in html and 'source-target' in html
    assert html.count('<tr>')==13
    assert 'overflow' not in html


def test_allowlist_hash_and_invalid_citations_fail_closed(companies,monkeypatch,tmp_path):
    company=companies[0]
    with pytest.raises(InputError):original_document(replace(company,id='../../arbitrary'))
    with pytest.raises(InputError):original_document(replace(company,run=companies[1].run))
    with pytest.raises(InputError):source_fact(company,'calc_1')
    with pytest.raises(InputError):source_fact(company,'unknown')
    doc=original_document(company);book,_=source_books(doc)
    for coordinate in ('A0','A999999999','../../A1','XFD1','a1','A1:B2','=HYPERLINK("x")'):
        with pytest.raises(InputError):checked_coordinate(book.worksheets[0],coordinate)
    path=tmp_path/'changed.xlsx';path.write_bytes(doc.data+b'changed')
    monkeypatch.setattr('portfolio_documents.canonical_source',lambda _:path)
    with pytest.raises(InputError):original_document(company)


def test_derived_evidence_returns_each_original_operand(companies):
    for company in companies:
        calculation=company.review.package['skill_engine']['calculations'][0]
        originals,derived,unsupported=evidence_locations(company,[calculation['id']])
        assert derived[0]['id']==calculation['id'] and not unsupported
        assert set(calculation['inputs'])<={f['id'] for f in originals}
        assert all(f['sheet']!='Source-linked calculations' for f in originals)
        # Every accepted finding has real original operands, not fabricated cells.
        for finding in company.review.package['ai_insights']:
            originals,_,_=evidence_locations(company,finding['fact_ids'])
            assert originals


def test_formula_fallback_and_html_are_safe(companies):
    company=companies[0];doc=original_document(company);book,cached=source_books(doc)
    ws=book['Income Statement'];cw=cached[ws.title]
    cw['D15']=None
    record=cell_record(company,ws,cw,'D15')
    assert record['value']==3298 and record['origin'].startswith('Retained source-unit')
    ws['A1']='<script>alert(1)</script>'
    html=worksheet_html(company,ws,cw,1,1,'A1')
    assert '<script>' not in html and '&lt;script&gt;' in html


def test_documents_page_preserves_formats_and_removes_fake_preview():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
    at.query_params['page']='excel';at.run()
    assert not at.exception
    assert at.title[0].value=='Documents & Reports'
    assert [s.value for s in at.subheader]==['Source Documents','Generated Reports']
    assert len([b for b in at.button if b.label=='Preview'])==3
    assert not any(s.label=='Worksheet preview' for s in at.selectbox)
    for slug in ('summit','tallis','harrow'):
        at.selectbox(key='documents_company').set_value(slug).run()
        for choice in ('Use supplied firm template','Standard Excel report'):
            at.selectbox(key='documents_format').set_value(choice).run()
            assert not at.exception
    at.button(key='preview_summit').click().run()
    assert not at.exception
    assert any(s.label=='Worksheet' for s in at.selectbox)
    assert any(s.label=='Inspect cell' and s.value=='A1' for s in at.text_input)



def test_foundation_mapping_opens_original_source():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
    at.query_params['page']='foundation';at.run()
    assert not at.exception
    at.button(key='foundation_source_view').click().run()
    assert not at.exception
    assert any(s.label=='Worksheet' and s.value=='Income Statement' for s in at.selectbox)
    assert any(s.label=='Inspect cell' and s.value=='D15' for s in at.text_input)
