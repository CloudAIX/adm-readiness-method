"""ADM readiness report generator — stage 5 of the ship ladder.

Turns one ScanResult into the client-ready PDF a practice pays for:
findings, what APPs 1.7-1.9 actually require, and a drafted disclosure
paragraph tuned to the automation signals found on their site.

Usage:
    python3 report/generate.py example-clinic.com.au [--out DIR] [--name "Practice Name"]

Framing rules (non-negotiable): the obligation has not commenced, so output
says "not yet addressed", never "non-compliant". No other practice is ever
named. This is governance support, not legal advice.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scanner.scan import ScanResult, scan  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
COMMENCEMENT = _dt.date(2026, 12, 10)

# Disclosure draft fragments keyed by automation signal. The assembled
# paragraph is a STARTING DRAFT for the practice's policy, tuned to what the
# scan actually saw - the report labels it as a draft requiring review.
_SIGNAL_ACTIVITIES = {
    "hotdoc": "online appointment booking, recalls and reminders (HotDoc)",
    "automed": "online appointment booking (AutoMed)",
    "healthengine": "online appointment booking (HealthEngine)",
    "appointuit": "online appointment booking (Appointuit)",
    "online booking": "online appointment booking",
    "automated reminder": "automated appointment reminders",
    "recall system": "automated recalls",
    "sms reminder": "SMS appointment reminders",
    "patient portal": "the patient portal",
    "triage": "triage questionnaires",
}


def _activities(res: ScanResult) -> list[str]:
    seen: list[str] = []
    for sig in res.automation_signals:
        label = _SIGNAL_ACTIVITIES.get(sig)
        if label and label not in seen:
            seen.append(label)
    return seen or ["online appointment booking, recalls and reminders"]


def draft_disclosure(res: ScanResult) -> str:
    acts = _activities(res)
    if len(acts) == 1:
        acts_text = acts[0]
    else:
        acts_text = ", ".join(acts[:-1]) + " and " + acts[-1]
    return (
        "Our practice uses computer programs to assist with administrative "
        f"decisions that may affect you, including {acts_text}. These systems "
        "use information such as your contact details, appointment history and "
        "the reason for your visit to schedule appointments, send reminders and "
        "identify patients due for follow-up care. They assist our staff; "
        "decisions about your clinical care are always made by your treating "
        "practitioner. You can ask our reception team how a decision involving "
        "you was made, or request that a staff member review it."
    )


def _findings_rows(res: ScanResult) -> str:
    def yn(v, good_when=False):
        ok = (v == good_when) if isinstance(good_when, bool) else False
        colour = "#1E7B3C" if (bool(v) == good_when) else "#A05E0B"
        word = "Yes" if v else "No"
        return f'<span style="color:{colour};font-weight:700">{word}</span>'

    rows = [
        ("Privacy policy located", yn(res.policy_found, good_when=True),
         html.escape(res.policy_url or "Not found at common locations")),
        ("Automated-decision disclosure (APPs 1.7&ndash;1.9)",
         yn(res.decision_language, good_when=True),
         "The disclosure the amended Privacy Act requires from 10 December 2026."),
        ("AI-scribe consent language", yn(res.scribe_language, good_when=True),
         "A different obligation (RACGP guidance); it does not satisfy APPs 1.7&ndash;1.9."),
        ("Automated patient-facing processing detected",
         yn(bool(res.automation_signals), good_when=False),
         html.escape(", ".join(res.automation_signals) or "None detected server-side "
                     "(booking widgets injected in the browser can be missed)")),
    ]
    if res.policy_year:
        colour = "#A05E0B" if res.policy_year < 2026 else "#1E7B3C"
        rows.append(("Policy last updated",
                     f'<span style="color:{colour};font-weight:700">{res.policy_year}</span>',
                     "The amendments creating this obligation were made in 2024."))
    if res.racgp_template_markers >= 3:
        rows.append(("RACGP template detected",
                     f'<span style="color:#A05E0B;font-weight:700">{res.racgp_template_markers}/5 markers</span>',
                     "The college template itself contains no automated-decision language, "
                     "so this gap is inherited with the template rather than introduced by "
                     "the practice."))
    return "\n".join(
        f'<tr><td class="k">{k}</td><td class="v">{v}</td><td class="d">{d}</td></tr>'
        for k, v, d in rows)


def render_html(res: ScanResult, practice_name: str | None = None) -> str:
    today = _dt.date.today()
    days = (COMMENCEMENT - today).days
    name = html.escape(practice_name or res.domain)
    if res.gap:
        verdict = "Not yet addressed"
        verdict_colour = "#A05E0B"
        verdict_line = ("Your privacy policy does not yet contain the automated-decision "
                       "disclosure that APPs 1.7&ndash;1.9 require from 10 December 2026. "
                       "The obligation has not commenced, so this is preparedness, not breach.")
    elif not res.policy_found:
        verdict = "Policy not located"
        verdict_colour = "#A05E0B"
        verdict_line = ("We could not locate a privacy policy at your website's common "
                       "locations. If one exists, it may be published as a PDF or behind "
                       "scripts; either way, patients and regulators may have the same difficulty.")
    else:
        verdict = "Disclosure language found"
        verdict_colour = "#1E7B3C"
        verdict_line = ("Your policy already contains automated-decision language. This report "
                       "reviews its coverage against what commences on 10 December 2026.")

    disclosure = html.escape(draft_disclosure(res))

    return f"""<!DOCTYPE html>
<html lang="en-AU"><head><meta charset="UTF-8"><style>
  @page {{ size: A4; margin: 0; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',-apple-system,'Helvetica Neue',sans-serif; background:#F5F7FA;
         color:#3D4F6F; font-size:9.8pt; line-height:1.55; }}
  .page {{ width:210mm; min-height:297mm; padding:16mm 18mm 12mm; display:flex;
           flex-direction:column; page-break-after:always; }}
  .page:last-child {{ page-break-after:auto; }}
  .eyebrow {{ font-size:8pt; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#2A9D8F; }}
  h1 {{ color:#1B2A4A; font-size:19pt; font-weight:800; letter-spacing:-.02em; margin:2mm 0 1mm; }}
  h2 {{ color:#1B2A4A; font-size:12pt; font-weight:700; margin:6mm 0 2.5mm; letter-spacing:-.01em; }}
  .verdict {{ background:#fff; border:1px solid #E2E6EC; border-left:none; border-radius:12px;
              padding:5mm 6mm; margin-top:5mm; box-shadow:0 1px 3px rgba(27,42,74,.08); }}
  .verdict b {{ font-size:13pt; color:{verdict_colour}; display:block; margin-bottom:1mm; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border:1px solid #E2E6EC;
           border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(27,42,74,.08); }}
  td {{ padding:2.8mm 4mm; border-bottom:1px solid #E2E6EC; vertical-align:top; font-size:9pt; }}
  tr:last-child td {{ border-bottom:none; }}
  td.k {{ width:52mm; color:#1B2A4A; font-weight:700; }}
  td.v {{ width:24mm; }}
  td.d {{ color:#6B7C99; font-size:8.3pt; }}
  .draft {{ background:#fff; border:1px solid #E2E6EC; border-radius:12px; padding:5mm 6mm;
            font-size:9.4pt; color:#1B2A4A; box-shadow:0 1px 3px rgba(27,42,74,.08); }}
  .draft .tag {{ font-size:7.5pt; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
                 color:#A05E0B; display:block; margin-bottom:2mm; }}
  ol {{ margin:2mm 0 0 5mm; }}
  ol li {{ margin-bottom:1.8mm; }}
  ol li b {{ color:#1B2A4A; }}
  .fine {{ font-size:7.8pt; color:#6B7C99; margin-top:4mm; line-height:1.5; }}
  footer {{ margin-top:auto; padding-top:4mm; border-top:1px solid #E2E6EC; display:flex;
            justify-content:space-between; font-size:8pt; color:#6B7C99; }}
  footer b {{ color:#1B2A4A; }}
</style></head><body>

<div class="page">
  <div class="eyebrow">GVRN-AI &middot; Automated-decision readiness report</div>
  <h1>{name}</h1>
  <p style="color:#6B7C99;font-size:8.5pt">Prepared {today.strftime('%-d %B %Y')} &middot; {days} days until APPs 1.7&ndash;1.9 commence (10 December 2026) &middot; scan of publicly available website content only</p>

  <div class="verdict"><b>{verdict}</b>{verdict_line}</div>

  <h2>What we found</h2>
  <table>{_findings_rows(res)}</table>

  <h2>What the obligation requires</h2>
  <p>From 10 December 2026, an organisation's privacy policy must disclose the kinds of
  decisions a computer program makes, or substantially assists in making, that could
  significantly affect an individual's rights or interests, and the kinds of personal
  information those programs use. The provision explicitly captures rule-based tools,
  not only artificial intelligence: online booking, recall and reminder systems are the
  everyday examples in general practice. Health service providers are bound by the
  Australian Privacy Principles regardless of turnover.</p>

  <footer><div><b>GVRN-AI</b> &middot; Melbourne, Australia</div>
  <div>nathan@gvrn-ai.com &middot; gvrn-ai.com &middot; page 1 of 2</div></footer>
</div>

<div class="page">
  <div class="eyebrow">GVRN-AI &middot; Automated-decision readiness report</div>

  <h2 style="margin-top:2mm">A starting draft for your policy</h2>
  <p style="margin-bottom:3mm">Drafted from the automation observed on your website. Review it
  against your actual systems before adopting: anything we could not see from outside
  (clinical software, scribes, internal tools) needs to be added, and your practice
  remains responsible for the final wording.</p>
  <div class="draft"><span class="tag">Draft &middot; requires review before adoption</span>
  {disclosure}</div>

  <h2>Recommended next steps</h2>
  <ol>
    <li><b>Build an AI and automation use register.</b> List every tool that touches patient
        information and the decisions each influences. The register is what makes the
        disclosure accurate, and it is the artefact an assessor asks for first.</li>
    <li><b>Update the privacy policy before 10 December 2026.</b> Adapt the draft above once
        the register is complete, and date the revision.</li>
    <li><b>Check scribe consent separately.</b> AI-scribe consent follows RACGP guidance and
        sits alongside, not inside, the automated-decision disclosure.</li>
    <li><b>Set a staff rule for general-purpose chatbots.</b> Patient information must never
        be entered into public AI tools; one written paragraph prevents the most common
        real-world incident.</li>
    <li><b>Revisit at each accreditation cycle.</b> New tools mean new register entries and,
        where they assist decisions, new disclosure lines.</li>
  </ol>

  <p class="fine">This report supports your compliance program; it is not legal advice and does
  not of itself constitute compliance with any law or standard. Findings reflect the public
  website at the scan date only; systems not visible externally are out of scope until
  registered. The commencement obligation described is current as at September 2026.
  GVRN-AI provides governance consulting and technical assessment services.</p>

  <footer><div><b>GVRN-AI</b> &middot; Melbourne, Australia</div>
  <div>nathan@gvrn-ai.com &middot; gvrn-ai.com &middot; page 2 of 2</div></footer>
</div>

</body></html>"""


def generate(domain: str, out_dir: str | pathlib.Path = ".", practice_name: str | None = None,
             result: ScanResult | None = None) -> pathlib.Path:
    res = result or scan(domain)
    out = pathlib.Path(out_dir) / f"adm-readiness-{res.domain.replace('.', '-')}.pdf"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(render_html(res, practice_name))
        tmp = f.name
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={out}", f"file://{tmp}"],
        capture_output=True, check=True)
    pathlib.Path(tmp).unlink(missing_ok=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("domain")
    p.add_argument("--out", default=".")
    p.add_argument("--name", default=None)
    a = p.parse_args()
    path = generate(a.domain, a.out, a.name)
    print(path)
