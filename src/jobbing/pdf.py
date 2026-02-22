"""PDF generation for CVs and cover letters.

Rewrite of generate_pdfs.py as a proper class. Key improvements:
- Font registration in __init__, not at module import
- Styles defined once in PDFStyles, shared across documents
- Takes CompanyData objects, not raw dicts
- No sys.exit — raises exceptions for callers to handle
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from jobbing.models import CLData, CVData, CompanyData


# ---------------------------------------------------------------------------
# Font configuration
# ---------------------------------------------------------------------------

DEJAVU_SEARCH_PATHS = [
    "/usr/share/fonts/truetype/dejavu",  # Linux / Cowork VM
    "/usr/share/fonts/dejavu",  # Some Linux distros
]

# Colors
COLOR_BLACK = "#000000"
COLOR_LINK = "#1155CC"
COLOR_GRAY = "#555555"


# ---------------------------------------------------------------------------
# PDFStyles
# ---------------------------------------------------------------------------


class PDFStyles:
    """Central style definitions for CV and cover letter PDFs."""

    def __init__(
        self,
        font_regular: str,
        font_bold: str,
        font_italic: str,
        font_bold_italic: str,
    ) -> None:
        self.font_regular = font_regular
        self.font_bold = font_bold
        self.font_italic = font_italic

        # CV styles
        self.cv_name = ParagraphStyle(
            "NameStyle",
            fontSize=22,
            leading=28,
            fontName=font_bold,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=4,
            alignment=TA_LEFT,
        )
        self.cv_location = ParagraphStyle(
            "LocationStyle",
            fontSize=10,
            fontName=font_bold,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=3,
            alignment=TA_LEFT,
        )
        self.cv_link = ParagraphStyle(
            "LinkStyle",
            fontSize=10,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_LINK),
            spaceAfter=2,
            alignment=TA_LEFT,
        )
        self.cv_body = ParagraphStyle(
            "BodyStyle",
            fontSize=10,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=8,
            alignment=TA_LEFT,
        )
        self.cv_heading = ParagraphStyle(
            "HeadingStyle",
            fontSize=11,
            fontName=font_bold,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=6,
            spaceBefore=12,
            alignment=TA_LEFT,
        )
        self.cv_job_title = ParagraphStyle(
            "JobTitleStyle",
            fontSize=10.5,
            fontName=font_bold,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=0,
            spaceBefore=8,
            alignment=TA_LEFT,
        )
        self.cv_job_company = ParagraphStyle(
            "JobCompanyStyle",
            fontSize=10,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_GRAY),
            spaceAfter=0,
            alignment=TA_LEFT,
        )
        self.cv_job_dates = ParagraphStyle(
            "JobDatesStyle",
            fontSize=10,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_GRAY),
            spaceAfter=4,
            alignment=TA_LEFT,
        )
        self.cv_bullet = ParagraphStyle(
            "BulletStyle",
            fontSize=10,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=4,
            leftIndent=18,
            alignment=TA_LEFT,
        )
        self.cv_education = ParagraphStyle(
            "EducationStyle",
            fontSize=10,
            fontName=font_bold,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=0,
            spaceBefore=8,
            alignment=TA_LEFT,
        )
        self.cv_education_school = ParagraphStyle(
            "EducationSchoolStyle",
            fontSize=10,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_GRAY),
            spaceAfter=0,
            alignment=TA_LEFT,
        )
        self.cv_education_detail = ParagraphStyle(
            "EducationDetailStyle",
            fontSize=9,
            fontName=font_italic,
            textColor=colors.HexColor(COLOR_GRAY),
            spaceAfter=4,
            alignment=TA_LEFT,
        )
        self.cv_skill_category = ParagraphStyle(
            "SkillCategoryStyle",
            fontSize=10,
            fontName=font_bold,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=4,
            alignment=TA_LEFT,
        )

        # Cover letter styles
        self.cl_body = ParagraphStyle(
            "CLBodyStyle",
            fontSize=10.5,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=10,
            alignment=TA_LEFT,
            leading=13.5,
        )
        self.cl_date = ParagraphStyle(
            "CLDateStyle",
            fontSize=10.5,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=6,
            alignment=TA_LEFT,
        )
        self.cl_closing = ParagraphStyle(
            "CLClosingStyle",
            fontSize=10.5,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=0,
            alignment=TA_LEFT,
        )
        self.cl_contact = ParagraphStyle(
            "CLContactStyle",
            fontSize=10.5,
            fontName=font_regular,
            textColor=colors.HexColor(COLOR_BLACK),
            spaceAfter=0,
            alignment=TA_LEFT,
        )


# ---------------------------------------------------------------------------
# PDFGenerator
# ---------------------------------------------------------------------------


class PDFGenerator:
    """Generates CV and cover letter PDFs from CompanyData."""

    def __init__(self) -> None:
        font_regular, font_bold, font_italic, font_bold_italic = (
            self._register_fonts()
        )
        self._styles = PDFStyles(font_regular, font_bold, font_italic, font_bold_italic)

    @staticmethod
    def _register_fonts() -> tuple[str, str, str, str]:
        """Register DejaVu fonts if available, falling back to Helvetica."""
        for base in DEJAVU_SEARCH_PATHS:
            regular_path = os.path.join(base, "DejaVuSans.ttf")
            if os.path.exists(regular_path):
                pdfmetrics.registerFont(TTFont("DejaVuSans", regular_path))
                pdfmetrics.registerFont(
                    TTFont(
                        "DejaVuSans-Bold",
                        os.path.join(base, "DejaVuSans-Bold.ttf"),
                    )
                )
                pdfmetrics.registerFont(
                    TTFont(
                        "DejaVuSans-Oblique",
                        os.path.join(base, "DejaVuSans-Oblique.ttf"),
                    )
                )
                pdfmetrics.registerFont(
                    TTFont(
                        "DejaVuSans-BoldOblique",
                        os.path.join(base, "DejaVuSans-BoldOblique.ttf"),
                    )
                )
                registerFontFamily(
                    "DejaVuSans",
                    normal="DejaVuSans",
                    bold="DejaVuSans-Bold",
                    italic="DejaVuSans-Oblique",
                    boldItalic="DejaVuSans-BoldOblique",
                )
                return (
                    "DejaVuSans",
                    "DejaVuSans-Bold",
                    "DejaVuSans-Oblique",
                    "DejaVuSans-BoldOblique",
                )

        return ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique")

    def generate_cv(self, cv: CVData, output_path: str | Path) -> Path:
        """Generate a CV PDF. Returns the output path."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        margin = 0.75 * inch
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            topMargin=margin,
            bottomMargin=margin,
            leftMargin=margin,
            rightMargin=margin,
        )

        s = self._styles
        story: list = []

        # Header
        story.append(Paragraph(cv.name, s.cv_name))
        story.append(Paragraph(cv.location, s.cv_location))
        story.append(
            Paragraph(
                f'<a href="mailto:{cv.email}">{cv.email}</a>', s.cv_link
            )
        )
        story.append(
            Paragraph(f'<a href="{cv.github}">{cv.github}</a>', s.cv_link)
        )
        story.append(
            Paragraph(
                f'<a href="{cv.linkedin}">{cv.linkedin}</a>', s.cv_link
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        # Summary
        for para_text in cv.summary:
            story.append(Paragraph(para_text, s.cv_body))
        story.append(Spacer(1, 0.08 * inch))

        # Core Skills
        story.append(Paragraph("CORE SKILLS", s.cv_heading))
        for skill in cv.core_skills:
            story.append(Paragraph(f"\u2022 {skill}", s.cv_bullet))

        # Key Achievements
        story.append(Paragraph("KEY ACHIEVEMENTS", s.cv_heading))
        for achievement in cv.key_achievements:
            story.append(Paragraph(f"\u2022 {achievement}", s.cv_bullet))

        # Employment History
        story.append(Paragraph("EMPLOYMENT HISTORY", s.cv_heading))
        for job in cv.jobs:
            story.append(Paragraph(job.title, s.cv_job_title))
            story.append(Paragraph(job.company, s.cv_job_company))
            if job.dates:
                story.append(Paragraph(job.dates, s.cv_job_dates))
            for bullet in job.bullets:
                story.append(Paragraph(f"\u2022 {bullet}", s.cv_bullet))

        # Earlier Experience
        if cv.earlier_experience:
            story.append(Paragraph("EARLIER EXPERIENCE", s.cv_heading))
            for job in cv.earlier_experience:
                story.append(Paragraph(job.title, s.cv_job_title))
                story.append(Paragraph(job.company, s.cv_job_company))
                if job.dates:
                    story.append(Paragraph(job.dates, s.cv_job_dates))
                for bullet in job.bullets:
                    story.append(Paragraph(f"\u2022 {bullet}", s.cv_bullet))

        # Education
        story.append(Paragraph("EDUCATION", s.cv_heading))
        for edu in cv.education:
            story.append(Paragraph(edu.degree, s.cv_education))
            story.append(Paragraph(edu.school, s.cv_education_school))
            if edu.detail:
                story.append(Paragraph(edu.detail, s.cv_education_detail))

        # Skills
        story.append(Paragraph("SKILLS", s.cv_heading))
        for category, items in cv.skills.items():
            story.append(
                Paragraph(
                    f"<b>{category}:</b> {items}", s.cv_skill_category
                )
            )

        doc.build(story)
        return output_path

    def generate_cover_letter(self, cl: CLData, output_path: str | Path) -> Path:
        """Generate a cover letter PDF. Returns the output path."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        margin = 0.85 * inch
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            topMargin=margin,
            bottomMargin=margin,
            leftMargin=margin,
            rightMargin=margin,
        )

        s = self._styles
        story: list = []

        # Date
        story.append(Paragraph(cl.date, s.cl_date))

        # Recipient
        story.append(Paragraph(cl.recipient, s.cl_body))
        story.append(Paragraph(cl.company, s.cl_body))
        story.append(Spacer(1, 0.04 * inch))

        # Greeting
        story.append(Paragraph(cl.greeting, s.cl_body))

        # Body paragraphs
        for para_text in cl.paragraphs:
            story.append(Paragraph(para_text, s.cl_body))

        # Closing
        story.append(Paragraph(cl.closing, s.cl_closing))
        story.append(Paragraph(cl.name, s.cl_closing))
        story.append(
            Paragraph(
                f'<a href="mailto:{cl.email}">{cl.email}</a> | '
                f'<a href="https://www.linkedin.com/in/{cl.linkedin.rstrip("/").split("/")[-1]}/">{cl.linkedin}</a>',
                s.cl_contact,
            )
        )

        doc.build(story)
        return output_path

    def generate(
        self,
        company_data: CompanyData,
        output_dir: str | Path,
        *,
        cv_only: bool = False,
        cl_only: bool = False,
    ) -> list[Path]:
        """Generate CV and/or cover letter PDFs. Returns list of output paths."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results: list[Path] = []

        if not cl_only:
            cv_path = output_dir / f"{company_data.company_upper}-CV.pdf"
            self.generate_cv(company_data.cv, cv_path)
            results.append(cv_path)

        if not cv_only:
            cl_path = output_dir / f"{company_data.company_upper}-CL.pdf"
            self.generate_cover_letter(company_data.cl, cl_path)
            results.append(cl_path)

        return results
