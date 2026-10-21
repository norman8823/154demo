"""Responsive, page-scrolling views of existing records; no data calculations.

Semantic HTML tables become labeled cards at narrow widths. Native Streamlit
controls preserve sorting/search/paging without iframe or dataframe scroll traps.
"""
import hashlib
from html import escape
import json
import math
import re
import pandas as pd
import streamlit as st


def text(value):
    if value is None or (isinstance(value,float) and math.isnan(value)):
        return 'Unavailable'
    return str(value)


def safe(value):
    return escape(text(value)).replace('$','&#36;')


def table_html(frame, *, formatters=None, labels=None, css_class='', details=False, links=None):
    """All values are escaped; long text remains available in native disclosures."""
    formatters=formatters or {};labels=labels or {};links=links or {}
    columns=list(frame.columns)
    main=columns[:3] if details and len(columns)>3 else columns
    extra=[c for c in columns if c not in main]
    headings=[labels.get(c,c) for c in main]+(['Details'] if extra else [])
    rows=[]
    for _,row in frame.iterrows():
        cells=[]
        for col in main:
            raw=row[col];value=formatters[col](raw) if col in formatters else text(raw)
            content=safe(value)
            if col=='Status':
                tone='checked' if text(value) in ('Available','Source checked · auto-mapped') else 'review'
                content='<span class="gp-status '+tone+'">'+content+'</span>'
            if len(text(value))>220:
                content='<details class="gp-cell-detail"><summary>Read full text</summary><div>'+content+'</div></details>'
            elif col in links and text(raw) in links[col]:
                content='<a target="_self" href="'+escape(links[col][text(raw)],quote=True)+'">'+content+'</a>'
            cells.append('<td data-label="'+safe(labels.get(col,col))+'">'+content+'</td>')
        if extra:
            content=''.join('<dt>'+safe(labels.get(c,c))+'</dt><dd>'+safe(formatters[c](row[c]) if c in formatters else row[c])+'</dd>' for c in extra)
            cells.append('<td data-label="Details"><details class="gp-cell-detail"><summary>Inspect record</summary><dl>'+content+'</dl></details></td>')
        rows.append('<tr>'+''.join(cells)+'</tr>')
    if not rows:
        return '<p class="gp-empty">No records match this selection.</p>'
    return '<div class="gp-table-wrap '+css_class+'"><table class="gp-table"><thead><tr>'+''.join('<th scope="col">'+safe(c)+'</th>' for c in headings)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def visible_records(frame, *, search='', sort=None, descending=False, page=1, page_size=10):
    """Pure presentation selection; never mutate source frames or sum accounts."""
    result=frame.copy()
    if search:
        mask=result.astype(str).apply(lambda col:col.str.contains(search,case=False,regex=False)).any(axis=1)
        result=result[mask]
    if sort in result.columns:
        result=result.sort_values(sort,ascending=not descending,kind='stable',key=lambda s:s if pd.api.types.is_numeric_dtype(s) else s.astype(str).str.casefold())
    count=len(result);pages=max(1,math.ceil(count/page_size));page=max(1,min(page,pages))
    return result.iloc[(page-1)*page_size:page*page_size],count,pages,page


def responsive_table(data, *, key, page_size=10, formatters=None, labels=None, css_class='', details=None, links=None, **ignored):
    frame=data.copy() if isinstance(data,pd.DataFrame) else pd.DataFrame(data)
    with st.expander('Table options · '+str(len(frame))+' records'):
        sort,order=st.columns([2,1])
        sort_key=sort.selectbox('Sort by',['Original order']+list(frame.columns),key=key+'_sort')
        descending=order.toggle('Descending',key=key+'_descending')
        search=st.text_input('Filter records',key=key+'_search') if len(frame)>page_size else ''
        # Keep the original dataframe toolbar's CSV handoff available.
        filename=re.sub(r'[^A-Za-z0-9_-]+','_',key)[:80]+'.csv'
        st.download_button('Download table CSV',frame.to_csv(index=False).encode('utf-8-sig'),file_name=filename,mime='text/csv',key=key+'_csv',on_click='ignore')
    _,count,pages,_=visible_records(frame,search=search,sort=sort_key,descending=descending,page_size=page_size)
    if pages>1:
        if st.session_state.get(key+'_page',1) not in range(1,pages+1):
            st.session_state.pop(key+'_page',None)
        page=st.selectbox('Page',range(1,pages+1),format_func=lambda p:f'{p} of {pages}',key=key+'_page')
    else:page=1
    selected,_,_,page=visible_records(frame,search=search,sort=sort_key,descending=descending,page=page,page_size=page_size)
    if details is None:details=len(frame.columns)>6
    st.markdown(table_html(selected,formatters=formatters,labels=labels,css_class=css_class,details=details,links=links),unsafe_allow_html=True)
    if count>page_size or search:
        start=(page-1)*page_size+1 if count else 0
        st.caption(f'Rows {start}–{min(page*page_size,count)} of {count} · Filter and sort in Table options')
    return selected


def json_records(value, *, key):
    rows=[{'Field':k,'Value':json.dumps(v,ensure_ascii=False,indent=2,default=str)} for k,v in value.items()] if isinstance(value,dict) else [{'Value':json.dumps(value,ensure_ascii=False,indent=2,default=str)}]
    responsive_table(rows,key=key,page_size=8)


class CompanyPresentation:
    """Only replace display widgets in the frozen, allowlisted company views."""
    def __getattr__(self,name):
        return getattr(st,name)

    def title(self,value,**kwargs):
        # The portfolio shell already supplies the company H1.
        return st.subheader(value)

    def dataframe(self,data,**kwargs):
        frame=data.copy() if isinstance(data,pd.DataFrame) else pd.DataFrame(data)
        columns=kwargs.get('column_order')
        if columns:frame=frame[[c for c in columns if c in frame.columns]]
        identity=hashlib.sha256(frame.to_json(default_handler=str).encode()).hexdigest()[:12]
        return responsive_table(frame,key='company_records_'+identity,page_size=8)

    def json(self,value,**kwargs):
        identity=hashlib.sha256(json.dumps(value,default=str,sort_keys=True).encode()).hexdigest()[:12]
        return json_records(value,key='company_json_'+identity)
