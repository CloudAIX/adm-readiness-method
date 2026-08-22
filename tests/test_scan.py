"""Offline tests for the ADM scanner. No network calls."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scanner.scan import DATE_RE, ADM_RE, AUTOMATION_RE, _strip_html, ScanResult


def test_date_patterns():
    for s, yr in [
        ("Current as of July 2022", 2022),
        ("Last updated: 3 March 2025", 2025),
        ("Reviewed: 04/06/2026", 2026),
        ("This policy is effective from January 2024", 2024),
    ]:
        m = DATE_RE.search(s)
        assert m, f"no date matched in {s!r}"
        assert int(m.group(2)) == yr


def test_adm_language_detected():
    hits = "We use automated decision making and artificial intelligence."
    assert len(ADM_RE.findall(hits)) >= 2


def test_ai_word_boundary_no_false_positives():
    """'AI' must not match inside ordinary words - the substring bug."""
    assert ADM_RE.findall("said detail maintain certain") == []


def test_policy_with_no_adm_language():
    txt = "We collect your name, Medicare number and health information."
    assert ADM_RE.findall(txt) == []


def test_automation_signals():
    assert AUTOMATION_RE.findall("Book online with HotDoc today") != []
    assert AUTOMATION_RE.findall("We send an SMS reminder") != []


def test_strip_html_removes_scripts():
    out = _strip_html("<script>var x=1</script><p>Privacy Policy</p>")
    assert "var x" not in out and "Privacy Policy" in out


def test_result_serialises():
    r = ScanResult(domain="example.com.au", gap=True)
    d = r.as_dict()
    assert d["domain"] == "example.com.au" and d["gap"] is True


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")


def test_scribe_language_is_not_decision_language():
    from scanner.scan import SCRIBE_RE, DECISION_RE
    scribe = ("Your Healthcare Practitioners may choose to use artificial intelligence "
              "to record, transcribe and produce notes of the consultation.")
    assert SCRIBE_RE.search(scribe)
    assert not DECISION_RE.search(scribe), "scribe consent must not count as ADM disclosure"


def test_decision_language_detected():
    from scanner.scan import DECISION_RE
    real = "We disclose where automated decision making affects your rights."
    assert DECISION_RE.search(real)


def test_automation_signal_found_in_script_tag():
    """Booking widgets are injected via script src, not visible text."""
    from scanner.scan import AUTOMATION_RE, _strip_html
    raw = '<script src="https://hotdoc.com.au/static/assets/js/hotdoc.js"></script>'
    assert AUTOMATION_RE.findall(raw), "must match in raw html"
    assert not AUTOMATION_RE.findall(_strip_html(raw)), "stripped text loses it - the bug"


def test_racgp_template_markers():
    from scanner.scan import RACGP_TEMPLATE_MARKERS
    sample = ("This privacy policy is to provide information to you, our patient, on how "
              "your personal information is collected. Why and when your consent is "
              "necessary. Our practice will need to collect your personal information.")
    low = sample.lower()
    assert sum(m in low for m in RACGP_TEMPLATE_MARKERS) >= 3
