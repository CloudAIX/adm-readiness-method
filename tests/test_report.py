"""Offline tests for the report generator. No network, no Chrome."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from report.generate import draft_disclosure, render_html  # noqa: E402
from scanner.scan import ScanResult  # noqa: E402


def _gap_result():
    return ScanResult(
        domain="example-clinic.com.au", policy_url="https://example-clinic.com.au/privacy/",
        policy_found=True, policy_year=2022, adm_mentions=0, scribe_language=True,
        racgp_template_markers=5, decision_language=False,
        automation_signals=["hotdoc", "sms reminder"], gap=True)


def test_disclosure_names_detected_signals():
    d = draft_disclosure(_gap_result())
    assert "HotDoc" in d and "SMS appointment reminders" in d
    assert "treating practitioner" in d  # clinical decisions stay human


def test_disclosure_has_generic_fallback():
    r = _gap_result()
    r.automation_signals = []
    assert "online appointment booking" in draft_disclosure(r)


def test_html_framing_rules():
    h = render_html(_gap_result(), "Example Clinic")
    assert "Not yet addressed" in h
    assert "non-compliant" not in h.lower()
    assert "not legal advice" in h
    assert "Example Clinic" in h
    assert "inherited" in h  # RACGP template framing present at 5/5 markers


def test_html_no_policy_variant():
    r = ScanResult(domain="nosite.com.au", policy_found=False, gap=False,
                   notes=["No privacy policy located at common paths."])
    h = render_html(r)
    assert "Policy not located" in h


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
