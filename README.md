# ADM Readiness Scanner

Checks whether an Australian organisation's public privacy policy discloses automated decision-making, as required by **Australian Privacy Principles 1.7–1.9 from 10 December 2026**.

Built 22 August 2026. **110 days to the deadline.**

## Why this exists

Every private-sector health service provider in Australia is bound by the APPs **regardless of turnover** — the $3M small-business exemption does not apply to anyone handling health information. That is every GP clinic, dentist, physiotherapist, psychologist, podiatrist and pharmacy in the country.

From 10 December 2026 their privacy policy must disclose where a computer program makes, or substantially assists in making, decisions affecting a person's rights or interests. The obligation explicitly captures **rule-based tools**, not just AI — so online booking, recall and reminder systems are in scope.

## Validation — 22 Aug 2026, n=40

| | Result |
|---|---|
| Domains scanned | 40 |
| Privacy policies located | **33 (82%)** |
| **No automated-decision disclosure** | **32 of 33 — 96%** |
| Of those, address AI scribes only | 13 |
| Genuinely disclose ADM | **1** |

### The finding that matters

The market has responded to **AI scribes** and has not responded to the **automated-decision obligation** at all.

Thirteen policies contain detailed, clearly lawyer-drafted AI language — consent before recording, audio destroyed after transcription, no offshore transfer, no training on patient data. That is RACGP scribe guidance, and it is a **different obligation**.

One policy states outright that its AI systems *"are administrative support tools only and do not replace clinical judgement or decision-making"* — while the same practice runs online booking, recalls and reminders, which is precisely the automated assistance APPs 1.7–1.9 cover.

**Those 13 are the warmest prospects in the dataset, not the coldest.** They have already engaged someone about AI, demonstrated willingness to act and pay, and still have the December gap.

Includes **Healthscope**, one of Australia's largest private hospital operators: no disclosure.

## Important framing

The obligation **has not commenced**. This tool measures *preparedness*, never breach. Output must always say "not yet addressed", never "non-compliant". It supports compliance; it does not confer it, and it is not legal advice.

## Usage

```python
from scanner import scan, scan_many

r = scan("example-clinic.com.au")
print(r.gap, r.policy_year, r.notes)

results = scan_many(["a.com.au", "b.com.au"])
```

## Tests

```bash
python3 tests/test_scan.py
```

7 offline tests, no network. Includes a regression test for the `AI` substring bug — matching "AI" inside "said" or "detail" is the same class of error as matching "hi" inside "this", which is documented in the 3f-it-support-agent evaluation report.

## Known limitations

- **Policy discovery is path-based.** 8 of 14 domains in the first run had policies at paths not in the list, or behind JavaScript. Coverage, not accuracy, is the current weak point.
- **Automation signals are unreliable.** HotDoc and similar are frequently injected client-side, so a server-side fetch misses them. one practice demonstrably runs HotDoc and the scanner did not detect it. Needs headless rendering.
- **No PDF policies.** Some practices publish as PDF.
- Sample size is small. 100+ domains needed before any public claim about the sector.

## Ship ladder

| Stage | By | What ships |
|---|---|---|
| **1. Scanner** | done, 22 Aug | Library + tests + validated signal |
| **2. Scale the scan** | 29 Aug | 100+ domains, headless rendering, real sector statistic |
| **3. Public checker** | done, 6 Sep | Live at [gvrn-ai.com/adm-check.html](https://gvrn-ai.com/adm-check.html) — Cloudflare Worker (`checker/`) ports the scanner, page captures the email |
| **4. Design partner** | 10 Sep | Mercy Family Doctors engagement, paid. First case study. |
| **5. Paid report** | 30 Sep | Full readiness report generated from scan + the `gp_clinic` audit vertical |
| **6. Distribution** | Oct–Nov | Checker as the artefact, newsletter carries it, the deadline sells it |
| **7. Deadline** | 10 Dec | Window closes |

Each stage ships something usable. Nothing waits on the stage after it.
