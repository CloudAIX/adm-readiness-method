"""Stage 3 - the policy-reader agent.

The deterministic scanner answers "is automated-decision language present?".
That is a regex question and it is answered in scan.py without an LLM.

This stage answers a different question: "is the disclosure ADEQUATE?" - which
is judgement, not pattern matching. It exists because the naive measure was
wrong twice on 22 Aug 2026:

  1. Counting any AI mention scored 7/33 policies as compliant.
  2. Reading them showed all 7 were AI-scribe consent, not ADM disclosure.
     One explicitly said its AI does "not replace clinical judgement or
     decision-making" while running online booking and recalls.

Design follows the ECOS calibration approach used in the 3f-it-support-agent
evaluation: each judge answers ONE narrow question and is scored as a binary
classifier against human labels, rather than one judge re-doing the work and
marking its own homework.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

# APPs 1.7-1.9 require three distinct disclosures. A policy can satisfy one and
# miss the others, which is why they are judged separately.
JUDGES = {
    "mentions_automated_decisions": (
        "Does this privacy policy state that a computer program, algorithm or "
        "automated system makes, or substantially assists in making, decisions "
        "about individuals?\n\n"
        "Answer NO if it only describes AI used to transcribe, record or draft "
        "notes - that is scribe consent under RACGP guidance, a different "
        "obligation. Answer NO if it only mentions AI in a security or "
        "general-technology context."
    ),
    "names_the_decisions": (
        "Does the policy state WHICH KINDS OF DECISIONS are made or assisted by "
        "a program? APP 1.7 requires the kinds of decisions to be identified, "
        "not merely that automation exists.\n\n"
        "Generic statements such as 'we use technology to improve services' are NO."
    ),
    "names_the_information": (
        "Does the policy state WHICH KINDS OF PERSONAL INFORMATION are used by "
        "the automated process? APP 1.7 requires the kinds of information to be "
        "identified.\n\n"
        "A general list of collected information elsewhere in the policy does NOT "
        "count unless it is tied to the automated processing."
    ),
}

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "enum": ["YES", "NO", "UNCLEAR"]},
        "evidence": {
            "type": "string",
            "description": "Exact quote from the policy supporting the answer, or empty if NO.",
        },
        "reasoning": {"type": "string"},
    },
    "required": ["answer", "evidence", "reasoning"],
}


@dataclass
class JudgeVerdict:
    judge: str
    answer: str
    evidence: str = ""
    reasoning: str = ""


@dataclass
class PolicyJudgement:
    domain: str
    verdicts: list[JudgeVerdict] = field(default_factory=list)
    adequate: bool = False
    partial: bool = False

    def summarise(self) -> None:
        yes = [v for v in self.verdicts if v.answer == "YES"]
        # All three required for adequacy. Anything less is partial or absent.
        self.adequate = len(yes) == len(JUDGES)
        self.partial = 0 < len(yes) < len(JUDGES)

    def as_dict(self) -> dict:
        return asdict(self)


def build_prompt(judge_key: str, policy_text: str, max_chars: int = 18000) -> str:
    """Prompt for one judge. Deliberately narrow - one question, one answer."""
    question = JUDGES[judge_key]
    text = policy_text[:max_chars]
    return (
        "You are assessing an Australian privacy policy against Australian "
        "Privacy Principles 1.7-1.9, which commence 10 December 2026.\n\n"
        f"QUESTION\n{question}\n\n"
        "Answer YES, NO or UNCLEAR. Quote exact supporting text as evidence. "
        "Default to NO when uncertain - a false YES tells a healthcare provider "
        "they are prepared when they are not, which is the costlier error.\n\n"
        f"POLICY TEXT\n---\n{text}\n---"
    )


def human_label_template(domain: str) -> dict:
    """Blank row for the calibration set. Judges are scored against these."""
    return {
        "domain": domain,
        **{k: "" for k in JUDGES},
        "labelled_by": "",
        "notes": "",
    }
