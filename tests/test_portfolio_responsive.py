from html import unescape
import pandas as pd
from streamlit.testing.v1 import AppTest
from engine import ROOT
from portfolio_tables import visible_records,table_html
from portfolio_data import load_companies
from portfolio_dashboard import operating_rows


def test_table_sort_filter_and_pagination_preserve_all_original_values():
    frame=pd.DataFrame([{'Source':f'cell-{n}','Value':n} for n in range(204)])
    original=frame.copy(deep=True)
    seen=[]
    for page in range(1,22):
        rows,count,pages,actual=visible_records(frame,page=page,page_size=10)
        assert count==204 and pages==21 and page==actual
        seen.extend(rows.Value.tolist())
    assert seen==list(range(204))
    rows,count,_,_=visible_records(frame,sort='Value',descending=True,page_size=10)
    assert rows.Value.tolist()==list(range(203,193,-1))
    rows,count,_,_=visible_records(frame,search='cell-203')
    assert count==1 and rows.iloc[0].Value==203
    pd.testing.assert_frame_equal(frame,original)


def test_table_escapes_source_content_and_reveals_original_details_without_scroll_panels():
    frame=pd.DataFrame([{'ID':'source1','Cell':"'P&L'!A1",'Value':47000,'Formula':'=A2-A3','Note':'<script>unsafe</script>'}])
    html=table_html(frame,details=True)
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert '<details' in html and '=A2-A3' in html and '47' in html
    assert 'overflow' not in html and 'height:' not in html
    assert 'data-label="Value"' in html


def test_legacy_comparison_route_redirects_to_adaptive_cards_without_duplicate_table():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
    at.query_params['page']='comparison';at.run()
    assert not at.exception and at.query_params['page']=='overview'
    assert not any(b.label=='Company Comparison' for b in at.button)
    html='\n'.join(m.value for m in at.markdown if not m.value.startswith('<style>'))
    assert 'gp-holdings' not in html and 'holdings-head' not in html
    assert html.count('v3-card-returns')==3
    for row in operating_rows(load_companies()):
        assert row['Company'] in html
        assert f'{row["Gross MOIC (illustrative)"]:.2f}x' in html


def test_large_issue_pages_without_dataframe_and_catalog_is_compact():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
    at.query_params['page']='foundation';at.run()
    assert not at.exception and not at.dataframe
    html=next(m.value for m in at.markdown if 'gp-catalog-sources' in m.value and '<table' in m.value)
    assert html.count('<tr>')==4
    assert len(at.selectbox(key='foundation_metric').options)==10
    page=at.selectbox(key='issue_records_tallis:unresolved_page')
    assert len(page.options)==21
    page.set_value(21).run()
    assert not at.exception
    assert any('Rows 201–204 of 204' in c.value for c in at.caption)
