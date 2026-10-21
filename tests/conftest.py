"""Regression tests must never make a real provider request, including fallback paths."""
import pytest

@pytest.fixture(autouse=True)
def no_real_provider(monkeypatch,tmp_path):
    monkeypatch.setenv('COPILOT_ENV_FILE','')
    monkeypatch.setenv('COPILOT_REPORT_CACHE_DIR',str(tmp_path/'report-cache'))
    monkeypatch.setenv('COPILOT_DIAGNOSTIC_DIR',str(tmp_path/'diagnostics'))
    def reject(*args,**kwargs):raise AssertionError('Offline test attempted a real HTTP request')
    monkeypatch.setattr('urllib.request.urlopen',reject)
