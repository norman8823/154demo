"""Opt-in phone link; never creates hosting, tunnels or external requests."""
import base64
import io
import ipaddress
import os
import re
from urllib.parse import urlsplit
import streamlit as st


def demo_url(value=None):
    """Retain the exact configured landing URL; reject non-phone destinations."""
    value=os.environ.get('DEMO_PUBLIC_URL','').strip() if value is None else value.strip()
    if not value or len(value)>512 or any(ord(c)<32 for c in value):return None
    try:
        parsed=urlsplit(value);host=(parsed.hostname or '').lower().rstrip('.')
        if parsed.scheme not in ('http','https') or not host or parsed.username or parsed.password:return None
        if parsed.port is not None and not 1<=parsed.port<=65535:return None
        if host=='localhost' or host.endswith('.localhost') or host in ('0.0.0.0','::'):return None
        try:
            address=ipaddress.ip_address(host)
            if address.is_loopback or address.is_unspecified or address.is_multicast or address.is_link_local:return None
            lan=address.is_private
        except ValueError:
            # Browsers interpret abbreviated/integer IPv4 forms as loopback too.
            if re.fullmatch(r'[0-9.]+',host) or host.startswith('0x'):return None
            lan=host.endswith('.local')
        if parsed.scheme=='http' and not lan:return None
    except ValueError:return None
    return value


@st.cache_data(show_spinner=False)
def qr_image(url,size):
    import qrcode
    code=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=8,border=4)
    code.add_data(url);code.make(fit=True)
    # Integral module pixels and a quiet zone preserve scannability at both sizes.
    image=code.make_image(fill_color='#112e42',back_color='white').convert('RGB')
    modules=code.modules_count+8
    scale=max(1,size//modules)
    image=image.resize((modules*scale,modules*scale),resample=0)
    buffer=io.BytesIO();image.save(buffer,format='PNG')
    return buffer.getvalue()


@st.dialog('View on Mobile',width='small',position='center',dismissible=True)
def mobile_dialog(url):
    st.caption('Scan to open the mobile-friendly demo')
    left,center,right=st.columns([1,4,1])
    with center:st.image(qr_image(url,280),width=280)
    st.markdown('**Copy Link**')
    st.code(url,language=None,wrap_lines=True)
    st.caption('Use the copy control above. This configured address must be reachable from your phone; no hosting or tunnel is started by the application.')


def mobile_panel():
    url=demo_url()
    with st.container(key='mobile_access'):
        if not url:
            st.caption('Mobile link not configured')
            return
        data=base64.b64encode(qr_image(url,140)).decode('ascii')
        st.markdown('<style>.st-key-mobile_qr_open button {background-color:white!important;color:#18364a!important;min-height:172px!important;padding:138px 6px 10px!important;justify-content:center!important;background-image:url("data:image/png;base64,'+data+'")!important;background-size:auto 124px!important;background-repeat:no-repeat!important;background-position:center 8px!important;}.st-key-mobile_qr_open button p {color:#18364a!important;}</style>',unsafe_allow_html=True)
        # The QR and label are one native keyboard-accessible button.
        if st.button('View on Mobile',key='mobile_qr_open',width='stretch'):
            mobile_dialog(url)
        st.caption('Scan to open the mobile-friendly demo')
