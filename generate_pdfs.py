#!/usr/bin/env python3
"""
Generic PDF generator for job applications.

Usage:
    python3 generate_pdfs.py <company>
    python3 generate_pdfs.py dash0
    python3 generate_pdfs.py dash0 --output-dir /path/to/output
    python3 generate_pdfs.py dash0 --cv-only
    python3 generate_pdfs.py dash0 --cl-only

Reads companies/{company}/{company}.json and generates PDFs in the same directory:
    companies/{company}/{COMPANY}-CV.pdf
    companies/{company}/{COMPANY}-CL.pdf
"""

import argparse
import json
import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily


# ============================================================================
# FONT REGISTRATION
# ============================================================================

DEJAVU_PATHS = [
    "/usr/share/fonts/truetype/dejavu",   # Linux / Cowork VM
    "/usr/share/fonts/dejavu",            # Some Linux distros
]

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_BOLD_ITALIC = "Helvetica-BoldOblique"

for _base in DEJAVU_PATHS:
    _regular = os.path.join(_base, "DejaVuSans.ttf")
    if os.path.exists(_regular):
        pdfmetrics.registerFont(TTFont("DejaVuSans", _regular))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", os.path.join(_base, "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", os.path.join(_base, "DejaVuSans-Oblique.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVuSans-BoldOblique", os.path.join(_base, "DejaVuSans-BoldOblique.ttf")))
        registerFontFamily("DejaVuSans",
            normal="DejaVuSans",
            bold="DejaVuSans-Bold",
            italic="DejaVuSans-Oblique",
            boldItalic="DejaVuSans-BoldOblique"
        )
        FONT_REGULAR = "DejaVuSans"
        FONT_BOLD = "DejaVuSans-Bold"
        FONT_ITALIC = "DejaVuSans-Oblique"
        FONT_BOLD_ITALIC = "DejaVuSans-BoldOblique"
        break


# ============================================================================
# COLORS
# ============================================================================

COLOR_BLACK = "#000000"
COLOR_LINK = "#1155CC"
COLOR_GRAY = "#555555"


# ============================================================================
# CV GENERATION
# ============================================================================

def generate_cv(data, output_path):
    """Generate CV PDF from data dictionary."""

    margin = 0.75 * inch
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=margin,
        bottomMargin=margin,
        leftMargin=margin,
        rightMargin=margin
    )

    styles = {
        "name": ParagraphStyle(
            "NameStyle",
            fontSize=22, leading=28, bold=True,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_BOLD,
            spaceAfter=4, alignment=TA_LEFT
        ),
        "location": ParagraphStyle(
            "LocationStyle",
            fontSize=10, bold=True,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_BOLD,
            spaceAfter=3, alignment=TA_LEFT
        ),
        "link": ParagraphStyle(
            "LinkStyle",
            fontSize=10,
            textColor=colors.HexColor(COLOR_LINK),
            fontName=FONT_REGULAR,
            spaceAfter=2, alignment=TA_LEFT
        ),
        "body": ParagraphStyle(
            "BodyStyle",
            fontSize=10,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_REGULAR,
            spaceAfter=8, alignment=TA_LEFT
        ),
        "heading": ParagraphStyle(
            "HeadingStyle",
            fontSize=11, bold=True,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_BOLD,
            spaceAfter=6, spaceBefore=12, alignment=TA_LEFT
        ),
        "jobTitle": ParagraphStyle(
            "JobTitleStyle",
            fontSize=10.5, bold=True,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_BOLD,
            spaceAfter=0, spaceBefore=8, alignment=TA_LEFT
        ),
        "jobCompany": ParagraphStyle(
            "JobCompanyStyle",
            fontSize=10,
            textColor=colors.HexColor(COLOR_GRAY),
            fontName=FONT_REGULAR,
            spaceAfter=0, alignment=TA_LEFT
        ),
        "jobDates": ParagraphStyle(
            "JobDatesStyle",
            fontSize=10,
            textColor=colors.HexColor(COLOR_GRAY),
            fontName=FONT_REGULAR,
            spaceAfter=4, alignment=TA_LEFT
        ),
        "bullet": ParagraphStyle(
            "BulletStyle",
            fontSize=10,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_REGULAR,
            spaceAfter=4, leftIndent=18, alignment=TA_LEFT
        ),
        "education": ParagraphStyle(
            "EducationStyle",
            fontSize=10, bold=True,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_BOLD,
            spaceAfter=0, spaceBefore=8, alignment=TA_LEFT
        ),
        "educationSchool": ParagraphStyle(
            "EducationSchoolStyle",
            fontSize=10,
            textColor=colors.HexColor(COLOR_GRAY),
            fontName=FONT_REGULAR,
            spaceAfter=0, alignment=TA_LEFT
        ),
        "educationDetail": ParagraphStyle(
            "EducationDetailStyle",
            fontSize=9,
            textColor=colors.HexColor(COLOR_GRAY),
            fontName=FONT_ITALIC,
            spaceAfter=4, alignment=TA_LEFT
        ),
        "skillCategory": ParagraphStyle(
            "SkillCategoryStyle",
            fontSize=10, bold=True,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_BOLD,
            spaceAfter=4, alignment=TA_LEFT
        ),
    }

    story = []

    # Header
    story.append(Paragraph(data["name"], styles["name"]))
    story.append(Paragraph(data["location"], styles["location"]))
    story.append(Paragraph(f'<a href="mailto:{data["email"]}">{data["email"]}</a>', styles["link"]))
    story.append(Paragraph(f'<a href="{data["github"]}">{data["github"]}</a>', styles["link"]))
    story.append(Paragraph(f'<a href="{data["linkedin"]}">{data["linkedin"]}</a>', styles["link"]))
    story.append(Spacer(1, 0.1 * inch))

    # Summary
    for para_text in data["summary"]:
        story.append(Paragraph(para_text, styles["body"]))
    story.append(Spacer(1, 0.08 * inch))

    # Core Skills
    story.append(Paragraph("CORE SKILLS", styles["heading"]))
    for skill in data["coreSkills"]:
        story.append(Paragraph(f"\u2022 {skill}", styles["bullet"]))

    # Key Achievements
    story.append(Paragraph("KEY ACHIEVEMENTS", styles["heading"]))
    for achievement in data["keyAchievements"]:
        story.append(Paragraph(f"\u2022 {achievement}", styles["bullet"]))

    # Employment History
    story.append(Paragraph("EMPLOYMENT HISTORY", styles["heading"]))
    for job in data["jobs"]:
        story.append(Paragraph(job["title"], styles["jobTitle"]))
        story.append(Paragraph(job["company"], styles["jobCompany"]))
        story.append(Paragraph(job["dates"], styles["jobDates"]))
        for bullet in job.get("bullets", []):
            story.append(Paragraph(f"\u2022 {bullet}", styles["bullet"]))

    # Earlier Experience (optional)
    if data.get("earlierExperience"):
        story.append(Paragraph("EARLIER EXPERIENCE", styles["heading"]))
        for job in data["earlierExperience"]:
            story.append(Paragraph(job["title"], styles["jobTitle"]))
            story.append(Paragraph(job["company"], styles["jobCompany"]))
            if job.get("dates"):
                story.append(Paragraph(job["dates"], styles["jobDates"]))
            for bullet in job.get("bullets", []):
                story.append(Paragraph(f"\u2022 {bullet}", styles["bullet"]))

    # Education
    story.append(Paragraph("EDUCATION", styles["heading"]))
    for edu in data["education"]:
        story.append(Paragraph(edu["degree"], styles["education"]))
        story.append(Paragraph(edu["school"], styles["educationSchool"]))
        if edu.get("detail"):
            story.append(Paragraph(edu["detail"], styles["educationDetail"]))

    # Skills
    story.append(Paragraph("SKILLS", styles["heading"]))
    for category, items in data["skills"].items():
        story.append(Paragraph(f"<b>{category}:</b> {items}", styles["skillCategory"]))

    doc.build(story)
    print(f"CV written to {output_path}")


# ============================================================================
# COVER LETTER GENERATION
# ============================================================================

def generate_cover_letter(data, output_path):
    """Generate Cover Letter PDF from data dictionary."""

    margin = 0.85 * inch
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=margin,
        bottomMargin=margin,
        leftMargin=margin,
        rightMargin=margin
    )

    styles = {
        "body": ParagraphStyle(
            "BodyStyle",
            fontSize=10.5,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_REGULAR,
            spaceAfter=10, alignment=TA_LEFT, leading=13.5
        ),
        "date": ParagraphStyle(
            "DateStyle",
            fontSize=10.5,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_REGULAR,
            spaceAfter=6, alignment=TA_LEFT
        ),
        "closing": ParagraphStyle(
            "ClosingStyle",
            fontSize=10.5,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_REGULAR,
            spaceAfter=0, alignment=TA_LEFT
        ),
        "contact": ParagraphStyle(
            "ContactStyle",
            fontSize=10.5,
            textColor=colors.HexColor(COLOR_BLACK),
            fontName=FONT_REGULAR,
            spaceAfter=0, alignment=TA_LEFT
        ),
    }

    story = []

    # Date
    story.append(Paragraph(data["date"], styles["date"]))

    # Recipient
    story.append(Paragraph(data["recipient"], styles["body"]))
    story.append(Paragraph(data["company"], styles["body"]))
    story.append(Spacer(1, 0.04 * inch))

    # Greeting
    story.append(Paragraph(data["greeting"], styles["body"]))

    # Body paragraphs
    for para_text in data["paragraphs"]:
        story.append(Paragraph(para_text, styles["body"]))

    # Closing
    story.append(Paragraph(data["closing"], styles["closing"]))
    story.append(Paragraph(data["name"], styles["closing"]))
    story.append(Paragraph(
        f'<a href="mailto:{data["email"]}">{data["email"]}</a> | '
        f'<a href="https://www.linkedin.com/in/gregorydamiani/">{data["linkedin"]}</a>',
        styles["contact"]
    ))

    doc.build(story)
    print(f"Cover letter written to {output_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate CV and Cover Letter PDFs from a company JSON data file."
    )
    parser.add_argument("company", help="Company name (reads companies/{company}/{company}.json)")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: companies/{company}/)")
    parser.add_argument("--cv-only", action="store_true", help="Generate only the CV")
    parser.add_argument("--cl-only", action="store_true", help="Generate only the Cover Letter")
    args = parser.parse_args()

    # Resolve paths relative to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    company_lower = args.company.lower()
    company_dir = os.path.join(script_dir, "companies", company_lower)

    # Load company data
    json_file = os.path.join(company_dir, f"{company_lower}.json")
    if not os.path.exists(json_file):
        print(f"ERROR: {json_file} not found.", file=sys.stderr)
        sys.exit(1)

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    company_upper = data.get("companyUpper", args.company.upper())
    output_dir = args.output_dir if args.output_dir else company_dir
    os.makedirs(output_dir, exist_ok=True)

    generate_cv_flag = not args.cl_only
    generate_cl_flag = not args.cv_only

    # Generate CV
    if generate_cv_flag and "cv" in data:
        cv_path = os.path.join(output_dir, f"{company_upper}-CV.pdf")
        generate_cv(data["cv"], cv_path)
        cv_size = os.path.getsize(cv_path)
        print(f"  Size: {cv_size:,} bytes ({cv_size / 1024:.1f} KB)")

    # Generate Cover Letter
    if generate_cl_flag and "cl" in data:
        cl_path = os.path.join(output_dir, f"{company_upper}-CL.pdf")
        generate_cover_letter(data["cl"], cl_path)
        cl_size = os.path.getsize(cl_path)
        print(f"  Size: {cl_size:,} bytes ({cl_size / 1024:.1f} KB)")

    print("\nDone.")


if __name__ == "__main__":
    main()
