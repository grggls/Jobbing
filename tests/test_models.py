"""Tests for jobbing.models — enums, dataclasses, and JSON round-trip."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from jobbing.models import (
    Application,
    CLData,
    CompanyData,
    Contact,
    CVData,
    Education,
    Interview,
    Job,
    LinkedInStatus,
    ScoringResult,
    Status,
)


class TestEnums:
    def test_status_values(self) -> None:
        assert Status.TARGETED.value == "Targeted"
        assert Status.APPLIED.value == "Applied"
        assert Status.FOLLOWED_UP.value == "Followed-Up"
        assert Status.IN_PROGRESS.value == "In Progress (Interviewing)"
        assert Status.DONE.value == "Done"

    def test_status_is_str(self) -> None:
        assert isinstance(Status.TARGETED, str)
        assert Status.TARGETED == "Targeted"

    def test_linkedin_status_values(self) -> None:
        assert LinkedInStatus.NO.value == "No"
        assert LinkedInStatus.YES.value == "Yes"
        assert LinkedInStatus.NA.value == "n/a"


class TestContact:
    def test_defaults(self) -> None:
        c = Contact(name="Jane", title="VP Eng", linkedin="https://linkedin.com/in/jane")
        assert c.note == ""
        assert c.message == ""

    def test_full(self) -> None:
        c = Contact(
            name="Jane",
            title="VP Eng",
            linkedin="https://linkedin.com/in/jane",
            note="Ex-Google",
            message="Hi Jane",
        )
        assert c.note == "Ex-Google"
        assert c.message == "Hi Jane"


class TestInterview:
    def test_defaults(self) -> None:
        i = Interview(date="2026-03-15")
        assert i.interview_type == ""
        assert i.interviewers == []
        assert i.vibe == 0

    def test_full(self) -> None:
        i = Interview(
            date="2026-03-15",
            interview_type="Technical",
            interviewers=["Alice"],
            outcome="Passed",
            vibe=4,
        )
        assert i.outcome == "Passed"
        assert i.vibe == 4


class TestScoringResult:
    def test_defaults(self) -> None:
        s = ScoringResult(score=75, reasoning="Good fit")
        assert s.green_flags == []
        assert s.red_flags == []
        assert s.gaps == []
        assert s.keywords_missing == []

    def test_full(self) -> None:
        s = ScoringResult(
            score=82,
            reasoning="Strong match",
            green_flags=["Remote", "Climate"],
            red_flags=["Junior scope"],
            gaps=["Rust"],
            keywords_missing=["kubernetes"],
        )
        assert s.score == 82
        assert len(s.green_flags) == 2


class TestApplication:
    def test_minimal(self) -> None:
        a = Application(name="Acme")
        assert a.status == Status.TARGETED
        assert a.contacts == []
        assert a.interviews == []
        assert a.scoring is None
        assert a.page_id is None

    def test_full(self) -> None:
        a = Application(
            name="Acme",
            position="Senior Engineer",
            status=Status.APPLIED,
            start_date=date(2026, 3, 1),
            url="https://acme.com/jobs/1",
            highlights=["Led platform migration"],
        )
        assert a.position == "Senior Engineer"
        assert a.start_date == date(2026, 3, 1)


class TestCompanyDataRoundTrip:
    def _sample_data(self) -> CompanyData:
        cv = CVData(
            name="Greg",
            location="Berlin",
            email="greg@example.com",
            github="github.com/greg",
            linkedin="linkedin.com/in/greg",
            summary=["Summary line"],
            core_skills=["Python", "Go"],
            key_achievements=["Built platform"],
            jobs=[
                Job(
                    title="Senior Engineer",
                    company="Acme",
                    dates="2024-present",
                    bullets=["Did things"],
                ),
            ],
            earlier_experience=[
                Job(title="Engineer", company="OldCo", dates="2020-2024", bullets=["Stuff"]),
            ],
            education=[Education(degree="MSc", school="MIT", detail="CS")],
            skills={"Languages": "Python, Go"},
        )
        cl = CLData(
            date="2026-03-08",
            recipient="Hiring Manager",
            company="Acme",
            greeting="Dear Hiring Manager",
            paragraphs=["I am writing to apply."],
            closing="Sincerely",
            name="Greg",
            email="greg@example.com",
            linkedin="linkedin.com/in/greg",
        )
        return CompanyData(company_upper="ACME", cv=cv, cl=cl)

    def test_round_trip(self, tmp_path: Path) -> None:
        original = self._sample_data()
        path = tmp_path / "acme.json"

        original.to_json_file(path)
        loaded = CompanyData.from_json_file(path)

        assert loaded.company_upper == "ACME"
        assert loaded.cv.name == "Greg"
        assert loaded.cv.core_skills == ["Python", "Go"]
        assert len(loaded.cv.jobs) == 1
        assert loaded.cv.jobs[0].title == "Senior Engineer"
        assert len(loaded.cv.earlier_experience) == 1
        assert len(loaded.cv.education) == 1
        assert loaded.cv.skills == {"Languages": "Python, Go"}
        assert loaded.cl.paragraphs == ["I am writing to apply."]

    def test_json_uses_camel_case(self, tmp_path: Path) -> None:
        original = self._sample_data()
        path = tmp_path / "acme.json"
        original.to_json_file(path)

        with open(path) as f:
            raw = json.load(f)

        assert "companyUpper" in raw
        assert "coreSkills" in raw["cv"]
        assert "keyAchievements" in raw["cv"]
        assert "earlierExperience" in raw["cv"]

    def test_minimal_cv(self, tmp_path: Path) -> None:
        """Round-trip with no optional CV fields (earlier_experience, education, skills)."""
        cv = CVData(
            name="Greg",
            location="Berlin",
            email="g@e.com",
            github="gh",
            linkedin="li",
            summary=["s"],
            core_skills=["Python"],
            key_achievements=["a"],
            jobs=[Job(title="E", company="C", bullets=["b"])],
        )
        cl = CLData(
            date="2026-01-01",
            recipient="HM",
            company="C",
            greeting="Hi",
            paragraphs=["p"],
            closing="Thanks",
            name="Greg",
            email="g@e.com",
            linkedin="li",
        )
        data = CompanyData(company_upper="C", cv=cv, cl=cl)
        path = tmp_path / "minimal.json"
        data.to_json_file(path)
        loaded = CompanyData.from_json_file(path)

        assert loaded.cv.earlier_experience == []
        assert loaded.cv.education == []
        assert loaded.cv.skills == {}
