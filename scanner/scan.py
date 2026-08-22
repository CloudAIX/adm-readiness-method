"""ADM readiness scanner.

Checks whether an Australian organisation's public privacy policy discloses
automated decision-making, as required by Australian Privacy Principles
1.7-1.9 from 10 December 2026.

Reports a gap. Does not assert legal non-compliance - the obligation has not
yet commenced, so this measures preparedness, not breach.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, asdict, field

POLICY_PATHS = [
    "privacy-policy", "privacy", "privacy-statement", "privacy-policy.html",
    "about/privacy", "privacy-notice", "our-privacy-policy", "legal/privacy",
]

DATE_RE = re.compile(
    r"(current as of|last updated|last reviewed|updated|effective(?: from)?|reviewed)"
    r"[^.\n]{0,45}((?:19|20)\d{2})", re.I)

# APP 1.7-1.9 language. Word-boundary AI to avoid matching "said", "detail".
ADM_RE = re.compile(
    r"automated decision|automated processing|computer program|artificial intelligence"
    r"|\bAI\b|algorithm|machine learning|automated system", re.I)

# AI-scribe consent language. Common since RACGP guidance - but this is a
# DIFFERENT obligation from APP 1.7-1.9 and does not satisfy it.
SCRIBE_RE = re.compile(
    r"ai scribe|scribe|transcribe|record(?:ing)? (?:of |your )?(?:the )?consultation"
    r"|dictation|clinical note", re.I)

# APP 1.7-1.9 requires disclosure that a program MAKES or SUBSTANTIALLY ASSISTS
# a decision, plus the kinds of information used and decisions made.
DECISION_RE = re.compile(
    r"automated decision|substantially assist|decision[- ]making (?:process|by)"
    r"|decisions (?:are |that are )?made (?:by|using) (?:a |an )?(?:computer|program|system|algorithm)"
    r"|automated processing of your personal information", re.I)

# Verbatim phrases from the RACGP privacy policy template. Practices that
# adopted the college template inherit its gaps - the template itself has no
# automated-decision language (verified 22 Aug 2026).
RACGP_TEMPLATE_MARKERS = [
    "this privacy policy is to provide information to you, our patient",
    "why and when your consent is necessary",
    "our practice will need to collect your personal information",
    "only staff who need to see your personal information will have access",
    "we will not share your personal information with anyone outside australia",
]

# Signals the organisation already runs automated patient-facing processing.
AUTOMATION_RE = re.compile(
    r"hotdoc|automed|healthengine|appointuit|online booking|automated reminder"
    r"|recall system|sms reminder|patient portal|triage", re.I)


@dataclass
class ScanResult:
    domain: str
    policy_url: str | None = None
    policy_found: bool = False
    last_updated: str | None = None
    policy_year: int | None = None
    adm_mentions: int = 0
    scribe_language: bool = False
    racgp_template_markers: int = 0
    decision_language: bool = False
    automation_signals: list[str] = field(default_factory=list)
    gap: bool = False
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _fetch(url: str, timeout: int = 12) -> str:
    """Fetch a URL. Returns empty string on any failure."""
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A", "Mozilla/5.0", url],
            capture_output=True, text=True, errors="ignore",
        )
        return r.stdout or ""
    except Exception:
        return ""


def _strip_html(html: str) -> str:
    txt = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    txt = re.sub(r"<style.*?</style>", " ", txt, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", txt)


def _discover_policy_links(domain: str) -> list[str]:
    """Find privacy-policy links on the homepage. More reliable than guessing paths."""
    html = _fetch(f"https://{domain}/")
    if not html:
        return []
    links = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        href, label = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        if re.search(r"privacy", href + " " + label, re.I):
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = f"https://{domain}{href}"
            elif not href.startswith("http"):
                href = f"https://{domain}/{href.lstrip('./')}"
            links.append(href)
    # de-duplicate, preserve order
    return list(dict.fromkeys(links))[:5]


def scan(domain: str) -> ScanResult:
    domain = domain.strip().replace("https://", "").replace("http://", "").rstrip("/")
    res = ScanResult(domain=domain)

    candidates = _discover_policy_links(domain) + [
        f"https://{domain}/{p}/" for p in POLICY_PATHS]

    for url in candidates:
        html = _fetch(url)
        if len(html) < 2000:
            continue
        if url.lower().endswith(".pdf") or "%PDF" in html[:200]:
            res.notes.append("Policy published as PDF - not parsed.")
            continue
        text = _strip_html(html)
        # Confirm it really is a privacy policy, not a 404 page.
        if text.lower().count("privacy") < 3:
            continue

        res.policy_found = True
        res.policy_url = url

        m = DATE_RE.search(text)
        if m:
            res.last_updated = m.group(0).strip()[:80]
            res.policy_year = int(m.group(2))

        res.adm_mentions = len(ADM_RE.findall(text))
        res.scribe_language = bool(SCRIBE_RE.search(text))
        low = text.lower()
        res.racgp_template_markers = sum(m in low for m in RACGP_TEMPLATE_MARKERS)
        res.decision_language = bool(DECISION_RE.search(text))
        break

    if not res.policy_found:
        res.notes.append("No privacy policy located at common paths.")
        return res

    # Automation signals live in script/link tags, not visible text, so match
    # against RAW html. Booking widgets are injected via <script src=...>.
    home_raw = _fetch(f"https://{domain}/")
    res.automation_signals = sorted({m.lower() for m in AUTOMATION_RE.findall(home_raw)})

    # The gap that matters is DECISION disclosure, not any mention of AI.
    res.gap = not res.decision_language
    if res.gap and res.scribe_language:
        res.notes.append(
            "Policy addresses AI scribes and consent, but contains no "
            "automated-decision disclosure. These are different obligations - "
            "scribe consent follows RACGP guidance; APPs 1.7-1.9 require "
            "disclosing which decisions a program makes or assists.")
    elif res.gap:
        res.notes.append(
            "Privacy policy contains no automated-decision language. "
            "APPs 1.7-1.9 commence 10 December 2026.")
    if res.racgp_template_markers >= 3:
        res.notes.append(
            f"Policy derives from the RACGP template ({res.racgp_template_markers}/5 "
            "marker phrases). The RACGP template itself contains no automated-decision "
            "language, so the gap is inherited rather than introduced.")
    if res.policy_year and res.policy_year < 2026:
        res.notes.append(
            f"Policy appears last updated {res.policy_year}, "
            "before the 2024 amendments were made.")
    if res.automation_signals and res.gap:
        res.notes.append(
            "Automated patient-facing processing detected on the website "
            f"({', '.join(res.automation_signals)}) with no corresponding disclosure.")
    return res


def scan_many(domains: list[str], workers: int = 8) -> list[ScanResult]:
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(scan, domains))
