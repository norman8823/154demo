"""Presentation gate: never mount the desktop worksheet on an unknown/phone viewport."""
import streamlit as st
import streamlit.components.v2 as components

MIN_DESKTOP_WIDTH=1024
MOBILE_MESSAGE='Source inspection is available on desktop.'
_probe=components.component('source_viewport',js='''
export default function({setStateValue}) {
  const query=window.matchMedia('(min-width:1024px)');
  const report=()=>setStateValue('desktop',query.matches);
  report();query.addEventListener('change',report);
  return ()=>query.removeEventListener('change',report);
}
''')


def mount_source_device(perf=None):
    if perf is None:
        result=_probe(key='source_viewport',default={'desktop':None},
                      on_desktop_change=lambda:None,height=1)
    else:
        with perf.measure('viewport_component_update'):
            result=_probe(key='source_viewport',default={'desktop':None},
                          on_desktop_change=lambda:None,height=1)
    st.session_state.source_desktop=result.desktop


def source_desktop():
    return st.session_state.get('source_desktop') is True
