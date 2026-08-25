"""Generate deterministic company-style internal documents for testing the RAG pipeline.

Usage (repo root)::

    python documents/generate_test_documents.py [target_dir]

Writes 12 markdown files across four access tiers (general / hr / restricted /
management, 3 per tier). Content is fully deterministic — no randomness — so
tests can rely on exact file names and wording. Front matter carries the
``access_level`` metadata required by the ingestion service.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "documents" / "generated_test_documents"

GENERAL_BODY = """\
Welcome to the company. This section collects reference material every \
employee is expected to know during their first weeks.

Office hours run from 09:00 to 17:30 local time, with a company-wide lunch \
window between 12:00 and 14:00. Meeting rooms can be booked through the \
calendar tool, and hot desks are available on every floor without reservation.

For everyday IT problems contact the helpdesk portal at help.internal. \
Password resets, VPN setup and laptop requests are handled within one business \
day. New starters receive their accounts on or before day one.

The employee handbook covers the dress code, travel booking guidelines and \
the basic expense reimbursement flow. Expenses under 50 units are auto-approved \
when submitted within 30 days with a receipt attached.
"""

HR_BODY = """\
This human resources memo describes leave entitlements and benefits for all \
staff. HR policies in this document are confidential to employees and must not \
be shared outside the company.

Vacation policy: full-time employees accrue 25 vacation days per calendar year. \
Up to five unused days may be carried into the first quarter of the next year. \
Requests longer than two weeks need manager approval at least one month ahead.

Parental leave provides 16 fully paid weeks for each primary caregiver and \
8 weeks for secondary caregivers. Benefits enrollment opens every November; \
the pension plan matches contributions up to 6 percent of base pay.

Salary reviews happen once per year after the performance cycle closes. \
Compensation bands by level are maintained by HR and shared only with managers.
"""

RESTRICTED_BODY = """\
RESTRICTED — INTERNAL ONLY. This document contains commercially sensitive \
material. Distribution outside the named custodians is a disciplinary offense.

The Meridian account renewal is capped at 480,000 units for the next term; the \
internal floor for negotiations is 415,000 units. Under no circumstance may the \
floor be disclosed to the customer procurement team.

Security incidents: the March intrusion was traced to an exposed staging token. \
The postmortem lists two unpatched services and recommends rotating all service \
credentials quarterly. Findings remain embargoed until legal signs off.

Unreleased financial projections forecast revenue of 9.3 million units for Q4. \
These numbers differ from the board deck and must not be quoted externally.
"""

MANAGEMENT_BODY = """\
Management briefing — for people managers and above. Decisions summarized here \
are confidential and preliminary until announced.

Budget planning: department leads submit draft budgets by the 15th; finance \
consolidates before the steering committee reviews variances above 10 percent. \
Any new recurring spend above 20,000 units requires VP sign-off.

Headcount planning for next year assumes flat overall growth. Requisitions for \
senior roles route through the talent committee; backfills below senior level \
are approved inside the department.

Performance calibration guidance asks managers to propose ratings independently \
before the calibration session, and reminds them that promotion cases require \
evidence across two consecutive cycles.
"""

# (file name, access_level, title, body)
DOCUMENTS: list[tuple[str, str, str, str]] = [
    ("general_onboarding_basics.md", "general", "Onboarding Basics", GENERAL_BODY),
    (
        "general_it_helpdesk.md",
        "general",
        "IT Helpdesk Guide",
        GENERAL_BODY.replace("everyday IT problems", "routine IT issues"),
    ),
    (
        "general_office_faq.md",
        "general",
        "Office FAQ",
        GENERAL_BODY.replace("hot desks", "shared desks"),
    ),
    ("hr_leave_and_benefits.md", "hr", "Leave and Benefits", HR_BODY),
    (
        "hr_vacation_policy.md",
        "hr",
        "Vacation Policy Details",
        HR_BODY.replace("Benefits enrollment", "Enrollment windows"),
    ),
    (
        "hr_compensation_process.md",
        "hr",
        "Compensation Review Process",
        HR_BODY.replace("pension plan matches", "retirement plan matches"),
    ),
    ("restricted_meridian_account.md", "restricted", "Meridian Account Notes", RESTRICTED_BODY),
    (
        "restricted_security_incidents.md",
        "restricted",
        "Security Incident Postmortem",
        RESTRICTED_BODY.replace("Unreleased financial projections", "Confidential forecasts"),
    ),
    (
        "restricted_financial_forecasts.md",
        "restricted",
        "Forecast Drafts",
        RESTRICTED_BODY.replace("March intrusion", "spring breach"),
    ),
    ("management_budget_cycle.md", "management", "Budget Cycle Briefing", MANAGEMENT_BODY),
    (
        "management_headcount_plan.md",
        "management",
        "Headcount Planning",
        MANAGEMENT_BODY.replace("steering committee", "leadership council"),
    ),
    (
        "management_calibration_guide.md",
        "management",
        "Calibration Guidance",
        MANAGEMENT_BODY.replace("talent committee", "hiring panel"),
    ),
]


def build_markdown(title: str, access_level: str, body: str) -> str:
    """Render one document as markdown with ``key: value`` front matter."""
    return f"---\ntitle: {title}\naccess_level: {access_level}\n---\n\n{body}"


def write_documents(target_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    """Write every generated document into *target_dir* and return the paths."""
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for file_name, access_level, title, body in DOCUMENTS:
        path = target_dir / file_name
        path.write_text(build_markdown(title, access_level, body), encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT_DIR
    paths = write_documents(destination)
    print(f"Wrote {len(paths)} documents to {destination}")

