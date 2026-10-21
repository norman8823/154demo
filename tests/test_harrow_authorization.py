"""Trust exact synthetic content; the holdout answer key is never an input."""
import ast
import hashlib
from engine import ROOT,demo_files

HARROW_SHA256='bdd9c427e57f4c55fa4a135a0126bd25f5fbdae5781b7c192067bbb937788efb'


def policy():
    # Load only the authorization declarations, without running Streamlit or AI.
    source=ast.parse((ROOT/'app.py').read_text())
    nodes=[n for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SYNTHETIC_DEMO_HASHES' for t in n.targets) or isinstance(n,ast.FunctionDef) and n.name=='synthetic_demo']
    scope={'hashlib':hashlib};exec(compile(ast.Module(body=nodes,type_ignores=[]),'trusted_demo_policy','exec'),scope)
    return scope


def test_harrow_is_explicitly_content_allowlisted():
    assert HARROW_SHA256 in policy()['SYNTHETIC_DEMO_HASHES']


def test_harrow_filename_cannot_authorize_untrusted_contents():
    trusted=policy()['synthetic_demo']
    assert not trusted({'Harrow_Ridge_Environmental_FY2026.xlsx':b'Untrusted private workbook'})
    assert not trusted({})


def test_mixed_and_modified_inputs_keep_authorization_requirement():
    trusted=policy()['synthetic_demo'];files=demo_files()
    assert trusted(files)
    assert not trusted(dict(files,**{'Harrow_Ridge_Environmental_FY2026.xlsx':b'Unknown contents'}))
    name=next(iter(files));modified=dict(files);modified[name]+=b'changed'
    assert not trusted(modified)
