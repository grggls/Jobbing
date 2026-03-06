"""Domain model for job application tracking and document generation.

Two aggregates:
- Application: the job tracking lifecycle (scoring, status, contacts, interviews)
- CompanyData: document generation data (CV + cover letter content)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Status(str, Enum):
    """Application lifecycle status. Matches Notion select values."""

    TARGETED = "Targeted"
    APPLIED = "Applied"
    FOLLOWED_UP = "Followed-Up"
    IN_PROGRESS = "In Progress (Interviewing)"
    DONE = "Done"


class LinkedInStatus(str, Enum):
    """LinkedIn follow-up tracking. Matches Notion select values."""

    NO = "No"
    YES = "Yes"
    NA = "n/a"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass
class Contact:
    """A LinkedIn outreach contact."""

    name: str
    title: str
    linkedin: str
    note: str = ""
    message: str = ""


@dataclass
class Interview:
    """A single interview or meeting in an application process.

    Lightweight by design — Notion's nested database is the primary UI
    for interview management. This type captures what the agent needs
    for prep generation and outcome tracking.
    """

    date: str  # ISO date
    interview_type: str  # Phone Screen, Technical, System Design, Behavioral, Panel, Final
    interviewers: list[str] = field(default_factory=list)
    prep_notes: str = ""
    questions_to_ask: list[str] = field(default_factory=list)
    outcome: str = ""  # Passed, Rejected, Pending, or freeform notes


@dataclass
class ScoringResult:
    """Full transparency into how a job posting was scored.

    Every scoring decision — including rejections — is preserved with
    the criteria version that produced it, enabling review and tuning.
    """

    score: int  # 0-100
    reasoning: str  # Full LLM reasoning text
    green_flags: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    keywords_missing: list[str] = field(default_factory=list)
    criteria_version: str = ""  # Which SCORING.md version was used
    timestamp: str = ""  # ISO datetime when scored
    model: str = ""  # Which LLM model scored it


# ---------------------------------------------------------------------------
# Application aggregate
# ---------------------------------------------------------------------------


@dataclass
class Application:
    """Aggregate root: a job application being tracked.

    Maps to a Notion database page. The page_id field links to the
    Notion backend; other backends use their own identifiers.
    """

    name: str
    position: str = ""
    status: Status = Status.TARGETED
    start_date: date | None = None
    url: str = ""
    environment: list[str] = field(default_factory=list)
    salary: str = ""
    focus: list[str] = field(default_factory=list)
    vision: str = ""
    mission: str = ""
    linkedin: LinkedInStatus = LinkedInStatus.NA
    conclusion: str = ""
    highlights: list[str] = field(default_factory=list)
    job_description: str = ""
    research: list[str] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)
    interviews: list[Interview] = field(default_factory=list)
    scoring: ScoringResult | None = None
    page_id: str | None = None


# ---------------------------------------------------------------------------
# Scanner types
# ---------------------------------------------------------------------------


@dataclass
class JobPosting:
    """A discovered posting from a job board scan."""

    title: str
    company: str
    url: str
    source: str  # Which bookmark/board produced this
    raw_text: str  # Full posting text for scoring


@dataclass
class ScoredPosting:
    """A posting with its scoring result."""

    posting: JobPosting
    scoring: ScoringResult


# ---------------------------------------------------------------------------
# Document generation types
# ---------------------------------------------------------------------------


@dataclass
class Job:
    """A single job entry on a CV."""

    title: str
    company: str
    dates: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass
class Education:
    """A single education entry on a CV."""

    degree: str
    school: str
    detail: str = ""


@dataclass
class CVData:
    """All data needed to render a CV PDF."""

    name: str
    location: str
    email: str
    github: str
    linkedin: str
    summary: list[str]
    core_skills: list[str]
    key_achievements: list[str]
    jobs: list[Job]
    earlier_experience: list[Job] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    skills: dict[str, str] = field(default_factory=dict)


@dataclass
class CLData:
    """All data needed to render a cover letter PDF."""

    date: str
    recipient: str
    company: str
    greeting: str
    paragraphs: list[str]
    closing: str
    name: str
    email: str
    linkedin: str


@dataclass
class CompanyData:
    """Container for one company's complete document data.

    Reads and writes the existing JSON schema (camelCase keys) used by
    all 49 company directories. No migration needed.
    """

    company_upper: str
    cv: CVData
    cl: CLData

    @classmethod
    def from_json_file(cls, path: str | Path) -> CompanyData:
        """Load from the existing JSON format (companies/{co}/{co}.json)."""
        with open(path) as f:
            data = json.load(f)

        cv_data = data["cv"]
        cv = CVData(
            name=cv_data["name"],
            location=cv_data["location"],
            email=cv_data["email"],
            github=cv_data["github"],
            linkedin=cv_data["linkedin"],
            summary=cv_data["summary"],
            core_skills=cv_data["coreSkills"],
            key_achievements=cv_data["keyAchievements"],
            jobs=[
                Job(
                    title=j["title"],
                    company=j["company"],
                    dates=j.get("dates", ""),
                    bullets=j.get("bullets", []),
                )
                for j in cv_data["jobs"]
            ],
            earlier_experience=[
                Job(
                    title=j["title"],
                    company=j["company"],
                    dates=j.get("dates", ""),
                    bullets=j.get("bullets", []),
                )
                for j in cv_data.get("earlierExperience", [])
            ],
            education=[
                Education(
                    degree=e["degree"],
                    school=e["school"],
                    detail=e.get("detail", ""),
                )
                for e in cv_data.get("education", [])
            ],
            skills=cv_data.get("skills", {}),
        )

        cl_data = data["cl"]
        cl = CLData(
            date=cl_data["date"],
            recipient=cl_data["recipient"],
            company=cl_data["company"],
            greeting=cl_data["greeting"],
            paragraphs=cl_data["paragraphs"],
            closing=cl_data["closing"],
            name=cl_data["name"],
            email=cl_data["email"],
            linkedin=cl_data["linkedin"],
        )

        return cls(company_upper=data["companyUpper"], cv=cv, cl=cl)

    def to_json_file(self, path: str | Path) -> None:
        """Write in the existing JSON format for backward compatibility."""
        data = {
            "companyUpper": self.company_upper,
            "cv": {
                "name": self.cv.name,
                "location": self.cv.location,
                "email": self.cv.email,
                "github": self.cv.github,
                "linkedin": self.cv.linkedin,
                "summary": self.cv.summary,
                "coreSkills": self.cv.core_skills,
                "keyAchievements": self.cv.key_achievements,
                "jobs": [
                    {
                        "title": j.title,
                        "company": j.company,
                        **({"dates": j.dates} if j.dates else {}),
                        "bullets": j.bullets,
                    }
                    for j in self.cv.jobs
                ],
                **(
                    {
                        "earlierExperience": [
                            {
                                "title": j.title,
                                "company": j.company,
                                **({"dates": j.dates} if j.dates else {}),
                                "bullets": j.bullets,
                            }
                            for j in self.cv.earlier_experience
                        ]
                    }
                    if self.cv.earlier_experience
                    else {}
                ),
                **(
                    {
                        "education": [
                            {
                                "degree": e.degree,
                                "school": e.school,
                                **({"detail": e.detail} if e.detail else {}),
                            }
                            for e in self.cv.education
                        ]
                    }
                    if self.cv.education
                    else {}
                ),
                **({"skills": self.cv.skills} if self.cv.skills else {}),
            },
            "cl": {
                "date": self.cl.date,
                "recipient": self.cl.recipient,
                "company": self.cl.company,
                "greeting": self.cl.greeting,
                "paragraphs": self.cl.paragraphs,
                "closing": self.cl.closing,
                "name": self.cl.name,
                "email": self.cl.email,
                "linkedin": self.cl.linkedin,
            },
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
