# Findings — Australian health providers and the December 2026 ADM obligation
Scan date 22 August 2026. **110 days to commencement.**

## Headline

| | |
|---|---|
| Domains scanned | **81** |
| Privacy policies located | **63 (77%)** |
| **No automated-decision disclosure** | **61 of 63 — 96%** |
| Running detectable automation *and* no disclosure | **44** |
| Address AI scribes but still no ADM disclosure | **36** |
| Genuinely disclose ADM | **2** |

## The root cause — it is upstream of the practices

**The RACGP's own privacy policy template contains no automated-decision language.**

Retrieved 22 Aug from racgp.org.au, 1,986 words. Occurrences of:

| Term | Count |
|---|---|
| automated decision | **0** |
| artificial intelligence / AI | **0** |
| algorithm | **0** |
| computer program | **0** |
| APP 1.7 | **0** |

The template opens: *"The Royal Australian College of General Practitioners (RACGP) has developed a privacy policy template for general practices to adapt, for compliance with the requirements of the Australian Privacy Principles."*

Dozens of the scanned practices publish this template close to verbatim — several host it under its original filename.

**So the 96% is not negligence. It is inheritance.** Practices did the responsible thing, adopted the college's template, and the template predates the 2024 amendments. Every practice that adopted it carries the same gap by construction.

That reframes the whole market: this is not a compliance-shaming story, it is a **sector-wide template lag**. Which is a far better thing to be first to say, and a far easier conversation to have with a practice manager.

## The second finding — scribes are not decisions

**36 of the 61 exposed practices have detailed AI language in their policies.** Consent before recording, audio destroyed after transcription, no offshore transfer, no training on patient data. Clearly drafted by someone competent, aligned to RACGP AI-scribe guidance.

None of it satisfies APPs 1.7–1.9, which require disclosing **which decisions a program makes or substantially assists, and which information feeds them.**

One practice states its AI systems *"are administrative support tools only and do not replace clinical judgement or decision-making"* — while running online booking, recalls and reminders, which is precisely the substantial-assistance the provision covers.

**Those 36 are the warmest prospects in the market.** They have already engaged someone on AI, already paid for policy work, already demonstrated they act. And they are still exposed.

## Method and limitations

- Policy discovery follows privacy links from the homepage, falling back to common paths. 77% located.
- The 23% missed are mostly **PDF policies**, one **cross-domain** policy, and one site returning **HTTP 500**. Not scraper limitations.
- Automation signals match against **raw HTML** — booking widgets are injected via `<script src>` and are invisible in stripped text. This was a bug; detection went from 0 to 44 when fixed.
- Scribe language and decision language are classified separately. Conflating them overstates compliance by roughly 5x.
- Sample is convenience-based, drawn from search. Not random. Treat 96% as indicative of practices with a web presence, not of the sector as a whole.

## What this does not say

The obligation **has not commenced**. Nobody scanned is in breach. This measures preparedness against a fixed future date. Output language must remain "not yet addressed", never "non-compliant".

---

# Stage 3 — judge run, 22 August 2026

The deterministic scanner answers *"is decision language present?"*. The judge answers *"is the disclosure adequate?"*. They disagreed, and the judge was right both times.

## Result

| | |
|---|---|
| Policies judged | 14 (both "compliant" + 10 scribe-aware + 4 plain-gap controls) |
| Scanner / judge agreement | **12 / 14 — 85%** |
| **False positives** | **2** |
| False negatives | 0 |

## The two false positives

**A Western Australian practice** — the scanner matched:

> *"AI systems used by our practice are administrative support tools only and do not replace clinical judgement or **decision-making**"*

That is a **denial** of automated decision-making, matched as a disclosure of it. The policy describes AI assisting with document processing and indexing — administrative support, not decisions affecting rights or interests.

**A New South Wales paediatric practice** — the scanner matched:

> *"giving access would reveal internal evaluative information in connection with a commercially sensitive **decision-making process**"*

Standard APP access-refusal boilerplate about human commercial decisions. Nothing automated.

## Corrected sector figure

**63 of 63 located policies — 100% — have no adequate automated-decision disclosure.**

Every earlier number understated it. The measure was wrong in the same direction three times:

| Measure | Apparent compliance |
|---|---|
| Any AI mention | 7 / 33 |
| Refined decision regex | 2 / 63 |
| **Judge reading the text** | **0 / 63** |

## The closest thing to a disclosure found

**One practice** was the only policy in the sample that names its own automation:

> *"Use of electronic automated recall and appointment systems"*

It still does not state that a program makes or assists decisions, which decisions, or which information feeds them. Useful as the worked example of *the minimum that still falls short* — it will be the clearest illustration in any client conversation.

## Why this is the argument for the architecture

Three passes, three different answers, converging only when a model read the text. The regex was not merely imprecise — it was **wrong in the compliance-favouring direction**, which is the dangerous one. A false positive tells a healthcare provider it is prepared when it is not.

This is precisely why stage 2 stays deterministic and stage 3 is a model. Neither could have produced this result alone: the scanner covers 81 domains in 28 seconds and cannot read; the judge reads and would be absurd to run over every page of every site.

## Calibration status
This run is **model-labelled only**. Nathan should hand-label the same 14 independently, then compute agreement. Until that exists, the 100% figure is defensible as *"judged by an LLM reading the policies, method published"* — not yet as *"human-verified"*. State it that way.


---

## Naming policy

No scanned organisation is named in this repository or in any public output. The obligation does not commence until 10 December 2026 — nothing found here is a breach, and identifying practices against a gap they inherited from a public template would be indefensible.

Aggregates and method are published. Identities are not.
