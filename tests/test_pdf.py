"""Tests for jobbing.pdf — PDF generation for CVs and cover letters."""

from __future__ import annotations

from pathlib import Path

import pytest

from jobbing.models import CLData, CompanyData, CVData, Education, Job
from jobbing.pdf import PDFGenerator, PDFStyles

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def generator() -> PDFGenerator:
    """Create a PDFGenerator instance (uses Helvetica fallback on macOS)."""
    return PDFGenerator()


@pytest.fixture()
def sample_cv() -> CVData:
    """A minimal but complete CVData for testing."""
    return CVData(
        name="Test User",
        location="Berlin, Germany",
        email="test@example.com",
        github="https://github.com/testuser",
        linkedin="https://linkedin.com/in/testuser",
        summary=["Experienced engineer with a focus on platform systems."],
        core_skills=["Python", "Go", "Kubernetes"],
        key_achievements=["Reduced deploy time by standardizing CI pipelines"],
        jobs=[
            Job(
                title="Senior Engineer",
                company="Current Corp",
                dates="2024 - present",
                bullets=[
                    "Built internal platform serving 50 engineers",
                    "Migrated monolith to microservices",
                ],
            ),
            Job(
                title="Engineer",
                company="Previous Inc",
                dates="2021 - 2024",
                bullets=["Developed REST APIs", "Improved test coverage"],
            ),
        ],
        earlier_experience=[
            Job(
                title="Junior Developer",
                company="Early Stage Co",
                dates="2019 - 2021",
                bullets=["Frontend development"],
            ),
        ],
        education=[
            Education(
                degree="MSc Computer Science",
                school="Technical University Berlin",
                detail="Focus on distributed systems",
            ),
            Education(
                degree="BSc Computer Science",
                school="University of Example",
            ),
        ],
        skills={
            "Languages": "Python, Go, TypeScript",
            "Infrastructure": "Kubernetes, Terraform, AWS",
        },
    )


@pytest.fixture()
def sample_cl() -> CLData:
    """A minimal but complete CLData for testing."""
    return CLData(
        date="March 8, 2026",
        recipient="Hiring Manager",
        company="Target Corp",
        greeting="Dear Hiring Manager,",
        paragraphs=[
            "I am writing to express my interest in the Senior Engineer position.",
            "In my current role, I lead platform development for a 50-person engineering team.",
            "I would welcome the opportunity to discuss how my experience relates to your needs.",
        ],
        closing="Sincerely,",
        name="Test User",
        email="test@example.com",
        linkedin="https://linkedin.com/in/testuser",
    )


@pytest.fixture()
def sample_company_data(sample_cv: CVData, sample_cl: CLData) -> CompanyData:
    """A complete CompanyData for testing the generate() method."""
    return CompanyData(company_upper="TARGETCORP", cv=sample_cv, cl=sample_cl)


# ---------------------------------------------------------------------------
# PDFStyles
# ---------------------------------------------------------------------------


class TestPDFStyles:
    def test_creation_with_helvetica(self) -> None:
        styles = PDFStyles(
            font_regular="Helvetica",
            font_bold="Helvetica-Bold",
            font_italic="Helvetica-Oblique",
            font_bold_italic="Helvetica-BoldOblique",
        )
        assert styles.font_regular == "Helvetica"
        assert styles.font_bold == "Helvetica-Bold"

    def test_cv_styles_exist(self) -> None:
        styles = PDFStyles(
            "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"
        )
        assert styles.cv_name is not None
        assert styles.cv_location is not None
        assert styles.cv_link is not None
        assert styles.cv_body is not None
        assert styles.cv_heading is not None
        assert styles.cv_job_title is not None
        assert styles.cv_job_company is not None
        assert styles.cv_job_dates is not None
        assert styles.cv_bullet is not None
        assert styles.cv_education is not None
        assert styles.cv_education_school is not None
        assert styles.cv_education_detail is not None
        assert styles.cv_skill_category is not None

    def test_cl_styles_exist(self) -> None:
        styles = PDFStyles(
            "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"
        )
        assert styles.cl_body is not None
        assert styles.cl_date is not None
        assert styles.cl_closing is not None
        assert styles.cl_contact is not None


# ---------------------------------------------------------------------------
# PDFGenerator initialization
# ---------------------------------------------------------------------------


class TestPDFGeneratorInit:
    def test_init_succeeds(self) -> None:
        gen = PDFGenerator()
        assert gen._styles is not None

    def test_font_fallback_to_helvetica(self) -> None:
        """On macOS (no DejaVu fonts), falls back to Helvetica family."""
        gen = PDFGenerator()
        # Either DejaVu or Helvetica is acceptable
        assert gen._styles.font_regular in ("DejaVuSans", "Helvetica")
        assert gen._styles.font_bold in ("DejaVuSans-Bold", "Helvetica-Bold")


# ---------------------------------------------------------------------------
# generate_cv()
# ---------------------------------------------------------------------------


class TestGenerateCV:
    def test_creates_file(self, generator: PDFGenerator, sample_cv: CVData, tmp_path: Path) -> None:
        output = tmp_path / "TEST-CV.pdf"
        result = generator.generate_cv(sample_cv, output)
        assert result == output
        assert output.is_file()

    def test_nonzero_size(self, generator: PDFGenerator, sample_cv: CVData, tmp_path: Path) -> None:
        output = tmp_path / "TEST-CV.pdf"
        generator.generate_cv(sample_cv, output)
        assert output.stat().st_size > 0

    def test_creates_parent_directories(
        self, generator: PDFGenerator, sample_cv: CVData, tmp_path: Path
    ) -> None:
        output = tmp_path / "nested" / "dir" / "TEST-CV.pdf"
        generator.generate_cv(sample_cv, output)
        assert output.is_file()

    def test_minimal_cv(self, generator: PDFGenerator, tmp_path: Path) -> None:
        """A CV with no optional sections still generates."""
        cv = CVData(
            name="Minimal",
            location="Anywhere",
            email="min@test.com",
            github="gh.com/min",
            linkedin="li.com/in/min",
            summary=["Short summary."],
            core_skills=["Python"],
            key_achievements=["Something"],
            jobs=[Job(title="Eng", company="Co", bullets=["Work"])],
        )
        output = tmp_path / "MINIMAL-CV.pdf"
        generator.generate_cv(cv, output)
        assert output.is_file()
        assert output.stat().st_size > 0

    def test_cv_with_no_dates(self, generator: PDFGenerator, tmp_path: Path) -> None:
        """Jobs without dates render without errors."""
        cv = CVData(
            name="NoDates",
            location="Berlin",
            email="nd@test.com",
            github="gh.com/nd",
            linkedin="li.com/in/nd",
            summary=["Summary."],
            core_skills=["Python"],
            key_achievements=["Achievement"],
            jobs=[Job(title="Eng", company="Co", bullets=["Bullet"])],
        )
        output = tmp_path / "NODATES-CV.pdf"
        generator.generate_cv(cv, output)
        assert output.is_file()

    def test_cv_with_education_no_detail(self, generator: PDFGenerator, tmp_path: Path) -> None:
        """Education without detail field renders without errors."""
        cv = CVData(
            name="EduTest",
            location="Berlin",
            email="e@t.com",
            github="gh",
            linkedin="li",
            summary=["S"],
            core_skills=["P"],
            key_achievements=["A"],
            jobs=[Job(title="E", company="C", bullets=["B"])],
            education=[Education(degree="MSc", school="Uni")],
        )
        output = tmp_path / "EDU-CV.pdf"
        generator.generate_cv(cv, output)
        assert output.is_file()

    def test_cv_returns_path_object(
        self, generator: PDFGenerator, sample_cv: CVData, tmp_path: Path
    ) -> None:
        output = tmp_path / "test.pdf"
        result = generator.generate_cv(sample_cv, output)
        assert isinstance(result, Path)

    def test_cv_accepts_string_path(
        self, generator: PDFGenerator, sample_cv: CVData, tmp_path: Path
    ) -> None:
        output = str(tmp_path / "string-path.pdf")
        result = generator.generate_cv(sample_cv, output)
        assert isinstance(result, Path)
        assert result.is_file()


# ---------------------------------------------------------------------------
# generate_cover_letter()
# ---------------------------------------------------------------------------


class TestGenerateCoverLetter:
    def test_creates_file(self, generator: PDFGenerator, sample_cl: CLData, tmp_path: Path) -> None:
        output = tmp_path / "TEST-CL.pdf"
        result = generator.generate_cover_letter(sample_cl, output)
        assert result == output
        assert output.is_file()

    def test_nonzero_size(self, generator: PDFGenerator, sample_cl: CLData, tmp_path: Path) -> None:
        output = tmp_path / "TEST-CL.pdf"
        generator.generate_cover_letter(sample_cl, output)
        assert output.stat().st_size > 0

    def test_creates_parent_directories(
        self, generator: PDFGenerator, sample_cl: CLData, tmp_path: Path
    ) -> None:
        output = tmp_path / "deep" / "nested" / "TEST-CL.pdf"
        generator.generate_cover_letter(sample_cl, output)
        assert output.is_file()

    def test_returns_path_object(
        self, generator: PDFGenerator, sample_cl: CLData, tmp_path: Path
    ) -> None:
        output = tmp_path / "cl.pdf"
        result = generator.generate_cover_letter(sample_cl, output)
        assert isinstance(result, Path)

    def test_accepts_string_path(
        self, generator: PDFGenerator, sample_cl: CLData, tmp_path: Path
    ) -> None:
        output = str(tmp_path / "string-cl.pdf")
        result = generator.generate_cover_letter(sample_cl, output)
        assert isinstance(result, Path)
        assert result.is_file()

    def test_single_paragraph(self, generator: PDFGenerator, tmp_path: Path) -> None:
        """Cover letter with a single paragraph renders without errors."""
        cl = CLData(
            date="March 1, 2026",
            recipient="HM",
            company="Co",
            greeting="Dear HM,",
            paragraphs=["Single paragraph body."],
            closing="Thanks,",
            name="Test",
            email="t@t.com",
            linkedin="https://linkedin.com/in/test",
        )
        output = tmp_path / "SINGLE-CL.pdf"
        generator.generate_cover_letter(cl, output)
        assert output.is_file()


# ---------------------------------------------------------------------------
# generate() — combined CV + CL
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_both_generated(
        self, generator: PDFGenerator, sample_company_data: CompanyData, tmp_path: Path
    ) -> None:
        results = generator.generate(sample_company_data, tmp_path)
        assert len(results) == 2
        cv_path, cl_path = results
        assert cv_path.name == "TARGETCORP-CV.pdf"
        assert cl_path.name == "TARGETCORP-CL.pdf"
        assert cv_path.is_file()
        assert cl_path.is_file()

    def test_cv_only(
        self, generator: PDFGenerator, sample_company_data: CompanyData, tmp_path: Path
    ) -> None:
        results = generator.generate(sample_company_data, tmp_path, cv_only=True)
        assert len(results) == 1
        assert results[0].name == "TARGETCORP-CV.pdf"
        assert results[0].is_file()

    def test_cl_only(
        self, generator: PDFGenerator, sample_company_data: CompanyData, tmp_path: Path
    ) -> None:
        results = generator.generate(sample_company_data, tmp_path, cl_only=True)
        assert len(results) == 1
        assert results[0].name == "TARGETCORP-CL.pdf"
        assert results[0].is_file()

    def test_creates_output_directory(
        self, generator: PDFGenerator, sample_company_data: CompanyData, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "new_dir"
        generator.generate(sample_company_data, output_dir)
        assert output_dir.is_dir()

    def test_both_nonzero_size(
        self, generator: PDFGenerator, sample_company_data: CompanyData, tmp_path: Path
    ) -> None:
        results = generator.generate(sample_company_data, tmp_path)
        for path in results:
            assert path.stat().st_size > 0

    def test_string_output_dir(
        self, generator: PDFGenerator, sample_company_data: CompanyData, tmp_path: Path
    ) -> None:
        results = generator.generate(sample_company_data, str(tmp_path))
        assert len(results) == 2
        assert all(p.is_file() for p in results)
