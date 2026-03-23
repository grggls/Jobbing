"""Unified CLI entry point for the Jobbing package.

Replaces the separate notion_update.py and generate_pdfs.py scripts
with a single `jobbing` command:

    jobbing track create --name "Company" --position "Role" --date 2026-02-22
    jobbing track update --name "Company" --status "Applied"
    jobbing track highlights --name "Company" --highlights "Bullet 1" "Bullet 2"
    jobbing track research --name "Company" --research "Finding 1" "Finding 2"
    jobbing track outreach --name "Company" --contacts-json contacts.json
    jobbing pdf <company> [--cv-only] [--cl-only] [--output-dir path]
    jobbing scan bookmarks [--categories CAT1 CAT2]
    jobbing scan fetch [--categories CAT1 CAT2] [--limit N]
    jobbing scan existing
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from jobbing.config import Config
from jobbing.models import Application, Contact, LinkedInStatus, Status

# ---------------------------------------------------------------------------
# Status/LinkedIn choice values (for argparse validation)
# ---------------------------------------------------------------------------

VALID_STATUSES = [s.value for s in Status]
VALID_LINKEDIN = [ls.value for ls in LinkedInStatus]


# ---------------------------------------------------------------------------
# Track subcommands
# ---------------------------------------------------------------------------


def _track_create(args: argparse.Namespace, config: Config) -> None:
    """Create a new tracker entry (or update if exists)."""
    from jobbing.tracker import get_tracker

    app = _args_to_application(args)
    tracker = get_tracker(config.tracker_backend, config)

    if args.dry_run:
        print(json.dumps(_preview_application(app), indent=2))
        return

    page_id, _sections = tracker.create(app)
    print(f"Created/updated entry: {page_id}")


def _track_update(args: argparse.Namespace, config: Config) -> None:
    """Update properties on an existing tracker entry."""
    from jobbing.tracker import get_tracker

    app = _args_to_application(args)
    tracker = get_tracker(config.tracker_backend, config)

    if args.dry_run:
        print(json.dumps(_preview_application(app), indent=2))
        return

    tracker.update(app)
    print(f"Updated entry: {app.name}")


def _track_highlights(args: argparse.Namespace, config: Config) -> None:
    """Replace highlights on a tracker entry."""
    from jobbing.tracker import get_tracker

    tracker = get_tracker(config.tracker_backend, config)

    if args.dry_run:
        print(json.dumps({"name": args.name, "highlights": args.highlights}, indent=2))
        return

    tracker.set_highlights(args.name, args.highlights)
    print(f"Highlights updated on: {args.name}")


def _track_research(args: argparse.Namespace, config: Config) -> None:
    """Replace research on a tracker entry."""
    from jobbing.tracker import get_tracker

    tracker = get_tracker(config.tracker_backend, config)
    app_id = args.name

    if args.dry_run:
        print(json.dumps({"name": app_id, "research": args.research}, indent=2))
        return

    tracker.set_research(app_id, args.research)
    print(f"Research updated on: {app_id}")


def _track_followup(args: argparse.Namespace, config: Config) -> None:
    """Check active interview processes for staleness."""
    from datetime import date as date_type

    from jobbing.tracker import get_tracker

    tracker = get_tracker(config.tracker_backend, config)
    threshold = args.threshold or config.followup_threshold_days

    apps = tracker.list_all()
    in_progress = [a for a in apps if a.status and a.status.value == "In Progress (Interviewing)"]

    if not in_progress:
        print("No applications currently in progress.")
        return

    today = date_type.today()
    stale: list[tuple[Application, int]] = []
    active: list[tuple[Application, int]] = []

    for app in in_progress:
        days = (today - app.start_date).days if app.start_date else 0
        if days >= threshold:
            stale.append((app, days))
        else:
            active.append((app, days))

    lines: list[str] = [
        f"Follow-up Report (threshold: {threshold}d) — {today.isoformat()}",
        f"In Progress: {len(in_progress)}  |  Stale (≥{threshold}d): {len(stale)}",
        "",
    ]

    if stale:
        lines.append("## Stale — needs follow-up")
        lines.append("")
        for app, days in sorted(stale, key=lambda x: -x[1]):
            lines.append(f"- {app.name} — {app.position or '?'} ({days}d since {app.start_date})")
        lines.append("")

    if active:
        lines.append("## Active — within threshold")
        lines.append("")
        for app, days in sorted(active, key=lambda x: -x[1]):
            lines.append(f"- {app.name} — {app.position or '?'} ({days}d since {app.start_date})")

    report = "\n".join(lines)
    print(report)

    if args.save:
        results_dir = config.scan_results_dir
        results_dir.mkdir(parents=True, exist_ok=True)
        filename = f"followup-{today.isoformat()}.md"
        filepath = results_dir / filename
        filepath.write_text(report + "\n")
        print(f"\nSaved to: {filepath}")


def _track_validate(args: argparse.Namespace, config: Config) -> None:
    """Validate all hub files for data integrity issues."""
    from jobbing.tracker.obsidian import ObsidianTracker

    tracker = ObsidianTracker(config)
    issues = tracker.validate_hubs()

    if not issues:
        print("All hub files OK — no issues found.")
        return

    print(f"Found {len(issues)} issue(s):\n")
    for issue in issues:
        print(f"  - {issue}")
    sys.exit(1)


def _track_sync(args: argparse.Namespace, config: Config) -> None:
    """Reconcile the kanban board with hub frontmatter for all companies."""
    from jobbing.tracker.obsidian import ObsidianTracker

    tracker = ObsidianTracker(config)

    if args.from_board:
        # Reverse sync: board lanes → hub frontmatter
        if args.dry_run:
            print("Would sync hub frontmatter from board lane positions.")
            return

        changes = tracker.sync_from_board()
        if changes:
            for c in changes:
                print(c)
            print(f"\nUpdated {len(changes)} hub(s) from board.")
        else:
            print("All hubs already match board.")
        return

    if args.dry_run:
        # Only show companies currently on the board
        board_text = tracker._board_path.read_text(encoding="utf-8")
        on_board = set()
        for line in board_text.splitlines():
            if line.strip().startswith("- [") and "[[" in line:
                import re as _re

                m = _re.search(r"\[\[[^\|]+\|([^\]]+)\]\]", line)
                if m:
                    on_board.add(m.group(1))
        apps = [a for a in tracker.list_all() if a.name in on_board]
        print(f"Would sync {len(apps)} companies to board.")
        for app in apps:
            status = app.status.value if app.status else "?"
            score = app.scoring.score if app.scoring else 0
            print(f"  {app.name} — status={status!r}, score={score}")
        return

    changes = tracker.sync_board()
    if changes:
        for c in changes:
            print(c)
        print(f"\nSynced {len(changes)} cards.")
    else:
        print("Board already up to date.")


def _track_outreach(args: argparse.Namespace, config: Config) -> None:
    """Replace outreach contacts on a tracker entry."""
    from jobbing.tracker import get_tracker

    # Load contacts from JSON file
    contacts_data: list[dict[str, Any]] = []
    if args.contacts_json:
        with open(args.contacts_json) as f:
            contacts_data = json.load(f)
    else:
        print("Error: --contacts-json is required", file=sys.stderr)
        sys.exit(1)

    contacts = [
        Contact(
            name=c.get("name", ""),
            title=c.get("title", ""),
            linkedin=c.get("linkedin", ""),
            note=c.get("note", ""),
            message=c.get("message", ""),
        )
        for c in contacts_data
    ]

    tracker = get_tracker(config.tracker_backend, config)
    app_id = args.name

    if args.dry_run:
        print(json.dumps({"name": app_id, "contacts": contacts_data}, indent=2))
        return

    tracker.set_contacts(app_id, contacts)
    print(f"Outreach contacts updated on: {app_id}")


# ---------------------------------------------------------------------------
# PDF subcommand
# ---------------------------------------------------------------------------


def _cmd_pdf(args: argparse.Namespace, config: Config) -> None:
    """Generate CV and/or cover letter PDFs, then update hub Documents section."""
    from jobbing.models import CompanyData
    from jobbing.pdf import PDFGenerator

    # Find the company directory under kanban/companies/{Company}/
    company_dir = _find_company_dir(args.company, config.kanban_companies_dir)
    if company_dir is None:
        print(
            f"Error: No company directory found for '{args.company}'"
            f" in {config.kanban_companies_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Find the JSON file — try {safe_name}.json then any *.json
    safe_name = _safe_name(args.company)
    json_file = company_dir / f"{safe_name}.json"
    if not json_file.exists():
        # Fall back: any .json in directory
        json_candidates = list(company_dir.glob("*.json"))
        if not json_candidates:
            print(f"Error: No JSON file found in {company_dir}", file=sys.stderr)
            sys.exit(1)
        json_file = json_candidates[0]

    company_data = CompanyData.from_json_file(json_file)
    output_dir = Path(args.output_dir) if args.output_dir else company_dir

    generator = PDFGenerator()
    paths = generator.generate(
        company_data,
        output_dir,
        cv_only=args.cv_only,
        cl_only=args.cl_only,
    )

    for path in paths:
        size = path.stat().st_size
        print(f"{path.name}: {size:,} bytes ({size / 1024:.1f} KB)")

    # Update the Obsidian hub Documents section
    if config.tracker_backend == "obsidian" and paths:
        _update_hub_documents(args.company, paths, config)

    print("\nDone.")


def _safe_name(s: str) -> str:
    """Convert a company name to a safe filesystem stem."""
    return s.replace("/", "-").replace("\\", "-").replace(":", " -").strip()


def _normalize_company_name(s: str) -> str:
    """Strip parenthetical suffixes for fuzzy directory matching.

    e.g. "Talentedge (Anonymous IoT Client)" → "talentedge"
    """
    return re.sub(r"\s*\([^)]*\)\s*$", "", s).strip().lower()


def _find_company_dir(company_input: str, kanban_companies_dir: Path) -> Path | None:
    """Find the per-company subdirectory under kanban/companies/.

    Tries exact safe_name match, then case-insensitive match, then
    normalized (strip parentheticals) match.
    """
    if not kanban_companies_dir.is_dir():
        return None

    input_safe = _safe_name(company_input)
    input_lower = input_safe.lower()
    input_normalized = _normalize_company_name(company_input)

    for d in kanban_companies_dir.iterdir():
        if not d.is_dir():
            continue
        stem_lower = d.name.lower()
        if (
            d.name == input_safe
            or stem_lower == input_lower
            or _normalize_company_name(d.name) == input_normalized
        ):
            return d
    return None


def _update_hub_documents(company_input: str, paths: list[Path], config: Config) -> None:
    """Find the hub file and update its Documents section with CV/CL wikilinks."""
    from jobbing.tracker.obsidian import ObsidianTracker

    company_dir = _find_company_dir(company_input, config.kanban_companies_dir)
    if not company_dir:
        print(f"Warning: No company directory found for '{company_input}'", file=sys.stderr)
        return

    company_name = company_dir.name

    cv_stem = cl_stem = ""
    for path in paths:
        stem = path.stem
        if stem.upper().endswith("-CV"):
            cv_stem = stem
        elif stem.upper().endswith("-CL"):
            cl_stem = stem

    obs_tracker = ObsidianTracker(config)
    obs_tracker.add_documents_section(company_name, cv_stem, cl_stem)
    print(f"Updated Documents section: {company_name}")

    # Remove any Obsidian stub .md files created for unresolved PDF wikilinks
    vault_root = config.project_dir
    for stem in [cv_stem, cl_stem]:
        if stem:
            stub = vault_root / f"{stem}.md"
            if stub.exists() and stub.stat().st_size == 0:
                stub.unlink()
                print(f"Removed Obsidian stub: {stub.name}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Get / Set subcommands — structured API layer for Claude
# ---------------------------------------------------------------------------


def _cmd_get(args: argparse.Namespace, config: Config) -> None:
    """Return all company data as structured JSON.

    Reads hub frontmatter + sections, lists interview files and PDFs.
    Designed so Claude can call `jobbing get "Company"` instead of parsing
    markdown directly, eliminating context loss and stochastic file access.
    """
    from jobbing.tracker.obsidian import _parse_frontmatter

    company_dir = _find_company_dir(args.company, config.kanban_companies_dir)
    if not company_dir:
        print(json.dumps({"error": f"Company '{args.company}' not found"}), file=sys.stderr)
        sys.exit(1)

    hub_path = company_dir / f"{company_dir.name}.md"
    if not hub_path.is_file():
        print(json.dumps({"error": f"Hub file not found: {hub_path}"}), file=sys.stderr)
        sys.exit(1)

    text = hub_path.read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)

    # Extract all sections
    sections: dict[str, str] = {}
    lines = text.splitlines()
    current_section: str | None = None
    section_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_section is not None:
                sections[current_section] = "\n".join(section_lines).strip()
            current_section = line[3:].strip()
            section_lines = []
        elif current_section is not None:
            section_lines.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(section_lines).strip()

    # If --field, return single value
    if getattr(args, "field", None):
        field = args.field
        if field in fm:
            print(json.dumps(fm[field]))
        elif field in sections:
            print(sections[field])
        else:
            print(json.dumps(None))
        return

    # If --section, return section content
    if getattr(args, "section", None):
        section = args.section
        print(sections.get(section, ""))
        return

    # Full output
    interviews = sorted(
        [
            f.name
            for f in company_dir.iterdir()
            if f.is_file() and f.suffix == ".md" and f.name != hub_path.name
        ]
    )
    pdfs = {
        "cv": next((f.name for f in company_dir.glob("*-CV.pdf")), None),
        "cl": next((f.name for f in company_dir.glob("*-CL.pdf")), None),
    }
    json_files = [f.name for f in company_dir.glob("*.json")]

    output = {
        "company": fm.get("company", company_dir.name),
        "position": fm.get("position", ""),
        "status": fm.get("status", "Targeted"),
        "score": fm.get("score", 0),
        "date": str(fm.get("date", "")),
        "url": fm.get("url", ""),
        "salary": fm.get("salary", ""),
        "environment": fm.get("environment", []),
        "focus": fm.get("focus", []),
        "vision": fm.get("vision", ""),
        "mission": fm.get("mission", ""),
        "conclusion": fm.get("conclusion", ""),
        "sections": sections,
        "interviews": interviews,
        "pdfs": pdfs,
        "json_files": json_files,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def _cmd_set(args: argparse.Namespace, config: Config) -> None:
    """Atomically update a frontmatter field or section in a company hub.

    Usage:
        jobbing set "Acme Corp" --field status --value "Applied"
        jobbing set "Acme Corp" --section "Fit Assessment" --content "Score: 78..."
    """
    from jobbing.tracker.obsidian import ObsidianTracker, _replace_section, _write_frontmatter

    company_dir = _find_company_dir(args.company, config.kanban_companies_dir)
    if not company_dir:
        print(f"Error: Company '{args.company}' not found", file=sys.stderr)
        sys.exit(1)

    hub_path = company_dir / f"{company_dir.name}.md"
    if not hub_path.is_file():
        print(f"Error: Hub file not found: {hub_path}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        if getattr(args, "field", None):
            print(f"Would set frontmatter field '{args.field}' = {args.value!r}")
        elif getattr(args, "section", None):
            preview = (args.content[:80] + "...") if len(args.content) > 80 else args.content
            print(f"Would replace section '{args.section}' with: {preview!r}")
        return

    if getattr(args, "field", None) and args.field:
        # Update frontmatter field
        value: Any = args.value
        # Try to coerce numeric strings
        try:
            value = int(args.value)
        except (ValueError, TypeError):
            pass
        _write_frontmatter(hub_path, {args.field: value})
        print(f"Set {company_dir.name}: {args.field} = {value!r}")

        # If status changed, also move board card
        if args.field == "status":
            obs_tracker = ObsidianTracker(config)
            app = obs_tracker.find_by_name(company_dir.name)
            if app and obs_tracker._board_path.is_file():
                from jobbing.tracker.obsidian import _board_add_or_move_card

                _board_add_or_move_card(obs_tracker._board_path, app)
                print(f"Board card moved to: {value}")

    elif getattr(args, "section", None) and args.section:
        # Replace section content
        content_lines = args.content.splitlines()
        _replace_section(hub_path, args.section, content_lines)
        print(f"Updated section '{args.section}' in {company_dir.name}")
    else:
        print("Error: must specify --field or --section", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Scan subcommand
# ---------------------------------------------------------------------------


def _cmd_scan(args: argparse.Namespace, config: Config) -> None:
    """Fetch job boards or list bookmarks for Claude to process."""
    scan_sub = getattr(args, "scan_command", None)

    if scan_sub == "bookmarks":
        _scan_bookmarks(args, config)
    elif scan_sub == "fetch":
        _scan_fetch(args, config)
    elif scan_sub == "existing":
        _scan_existing(args, config)
    else:
        print("Usage: jobbing scan {bookmarks,fetch,existing}", file=sys.stderr)
        sys.exit(1)


def _scan_bookmarks(args: argparse.Namespace, config: Config) -> None:
    """List parsed bookmarks from BOOKMARKS.md."""
    from jobbing.scanner import Bookmark, parse_bookmarks

    bookmarks = parse_bookmarks(config.bookmarks_path)

    # Filter by category
    if args.categories:
        cat_lower = [c.lower() for c in args.categories]
        bookmarks = [b for b in bookmarks if b.category.lower() in cat_lower]

    # Group by category
    by_cat: dict[str, list[Bookmark]] = {}
    for b in bookmarks:
        by_cat.setdefault(b.category, []).append(b)

    total = len(bookmarks)
    print(f"Bookmarks: {total} across {len(by_cat)} categories\n")

    for cat, bms in by_cat.items():
        print(f"## {cat} ({len(bms)})")
        for b in bms:
            print(f"  - {b.label}")
        print()


def _scan_fetch(args: argparse.Namespace, config: Config) -> None:
    """Fetch board pages and save content for Claude to process."""
    from jobbing.scanner import fetch_boards, parse_bookmarks, save_fetch_results

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    bookmarks = parse_bookmarks(config.bookmarks_path)

    # Filter by category
    if args.categories:
        cat_lower = [c.lower() for c in args.categories]
        bookmarks = [b for b in bookmarks if b.category.lower() in cat_lower]

    # Apply limit
    if args.limit:
        bookmarks = bookmarks[: args.limit]

    if not bookmarks:
        print("No bookmarks match the filter.")
        return

    print(f"Fetching {len(bookmarks)} boards...")
    result = fetch_boards(bookmarks)

    # Save to scan_results/
    filepath = save_fetch_results(result, config.scan_results_dir)

    print(f"\nFetch complete: {filepath}")
    print(f"  Fetched: {result.boards_fetched}/{result.boards_requested}")
    if result.boards_failed:
        print(f"  Failed: {result.boards_failed}")

    # Summary of content sizes
    for fb in result.boards:
        status = f"{fb.char_count:,} chars" if not fb.error else f"FAILED: {fb.error}"
        print(f"  {fb.bookmark.label}: {status}")


def _scan_existing(args: argparse.Namespace, config: Config) -> None:
    """List companies and positions already in the tracker."""
    apps: list[Application] = []
    source = "tracker"

    try:
        from jobbing.tracker import get_tracker

        tracker = get_tracker(config.tracker_backend, config)
        apps = tracker.list_all()
    except Exception as e:
        logging.getLogger(__name__).warning(
            "Tracker query failed (%s), falling back to kanban/companies/ directory", e
        )
        source = "kanban/companies/"
        companies_dir = config.kanban_companies_dir
        if companies_dir.is_dir():
            for d in sorted(companies_dir.iterdir()):
                if d.is_dir() and not d.name.startswith("."):
                    apps.append(Application(name=d.name))

    if not apps:
        print("No existing applications found.")
        return

    print(f"Existing applications ({len(apps)}, source: {source}):\n")
    for app in apps:
        status = app.status.value if app.status else "?"
        position = app.position or "(no position)"
        print(f"  [{status}] {app.name} — {position}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _args_to_application(args: argparse.Namespace) -> Application:
    """Convert CLI args to an Application."""
    status = Status.TARGETED
    if getattr(args, "status", None):
        status = Status(args.status)

    start_date = None
    if getattr(args, "date", None):
        start_date = date.fromisoformat(args.date)

    linkedin = LinkedInStatus.NA
    if getattr(args, "linkedin", None):
        linkedin = LinkedInStatus(args.linkedin)

    return Application(
        name=getattr(args, "name", "") or "",
        position=getattr(args, "position", "") or "",
        status=status,
        start_date=start_date,
        url=getattr(args, "url", "") or "",
        environment=getattr(args, "environment", []) or [],
        salary=getattr(args, "salary", "") or "",
        focus=getattr(args, "focus", []) or [],
        vision=getattr(args, "vision", "") or "",
        mission=getattr(args, "mission", "") or "",
        linkedin=linkedin,
        conclusion=getattr(args, "conclusion", "") or "",
        highlights=getattr(args, "highlights", []) or [],
        job_description=getattr(args, "job_description", "") or "",
    )


def _preview_application(app: Application) -> dict[str, Any]:
    """Build a preview dict for dry-run output."""
    d: dict[str, Any] = {"name": app.name}
    if app.position:
        d["position"] = app.position
    if app.status:
        d["status"] = app.status.value
    if app.start_date:
        d["start_date"] = app.start_date.isoformat()
    if app.url:
        d["url"] = app.url
    if app.environment:
        d["environment"] = app.environment
    if app.salary:
        d["salary"] = app.salary
    if app.focus:
        d["focus"] = app.focus
    if app.vision:
        d["vision"] = app.vision
    if app.mission:
        d["mission"] = app.mission
    if app.highlights:
        d["highlights"] = app.highlights
    if app.job_description:
        d["job_description"] = (
            app.job_description[:100] + "..."
            if len(app.job_description) > 100
            else app.job_description
        )
    return d


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jobbing",
        description="AI-assisted job application workflow.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- track ---
    p_track = subparsers.add_parser("track", help="Tracker operations")
    track_subs = p_track.add_subparsers(dest="track_command", required=True)

    # track create
    p_create = track_subs.add_parser("create", help="Create a new tracker entry")
    p_create.add_argument("--name", required=True, help="Company name")
    p_create.add_argument("--position", help="Role title")
    p_create.add_argument("--date", help="Start date (YYYY-MM-DD)")
    p_create.add_argument("--url", help="Job posting URL")
    p_create.add_argument("--status", choices=VALID_STATUSES, help="Status")
    p_create.add_argument("--environment", nargs="+", help="Environment tags")
    p_create.add_argument("--salary", help="Salary range")
    p_create.add_argument("--focus", nargs="+", help="Company focus tags")
    p_create.add_argument("--vision", help="Company vision")
    p_create.add_argument("--mission", help="Company mission")
    p_create.add_argument("--linkedin", choices=VALID_LINKEDIN, help="LinkedIn status")
    p_create.add_argument("--conclusion", help="Conclusion notes")
    p_create.add_argument("--highlights", nargs="+", help="Experience to Highlight")
    p_create.add_argument("--job-description", dest="job_description", help="Full job posting text")
    p_create.add_argument("--dry-run", action="store_true", dest="dry_run")

    # track update
    p_update = track_subs.add_parser("update", help="Update an existing entry")
    p_update.add_argument("--name", required=True, help="Company name")
    p_update.add_argument("--position", help="Role title")
    p_update.add_argument("--date", help="Start date (YYYY-MM-DD)")
    p_update.add_argument("--url", help="Job posting URL")
    p_update.add_argument("--status", choices=VALID_STATUSES, help="Status")
    p_update.add_argument("--environment", nargs="+", help="Environment tags")
    p_update.add_argument("--salary", help="Salary range")
    p_update.add_argument("--focus", nargs="+", help="Company focus tags")
    p_update.add_argument("--vision", help="Company vision")
    p_update.add_argument("--mission", help="Company mission")
    p_update.add_argument("--linkedin", choices=VALID_LINKEDIN, help="LinkedIn status")
    p_update.add_argument("--conclusion", help="Conclusion notes")
    p_update.add_argument("--dry-run", action="store_true", dest="dry_run")

    # track highlights
    p_hl = track_subs.add_parser("highlights", help="Replace highlights")
    p_hl.add_argument("--name", required=True, help="Company name")
    p_hl.add_argument("--highlights", nargs="+", required=True, help="Bullets")
    p_hl.add_argument("--dry-run", action="store_true", dest="dry_run")

    # track research
    p_research = track_subs.add_parser("research", help="Replace research")
    p_research.add_argument("--name", required=True, help="Company name")
    p_research.add_argument("--research", nargs="+", required=True, help="Research bullets")
    p_research.add_argument("--dry-run", action="store_true", dest="dry_run")

    # track followup
    p_followup = track_subs.add_parser("followup", help="Check for stale interview processes")
    p_followup.add_argument(
        "--threshold",
        type=int,
        help="Days before flagging as stale (default: from .env or 5)",
    )
    p_followup.add_argument(
        "--save",
        action="store_true",
        help="Save report to notion_queue_results/",
    )

    # track outreach
    p_outreach = track_subs.add_parser("outreach", help="Replace outreach contacts")
    p_outreach.add_argument("--name", required=True, help="Company name")
    p_outreach.add_argument("--contacts-json", required=True, help="Path to contacts JSON")
    p_outreach.add_argument("--dry-run", action="store_true", dest="dry_run")

    # track validate
    track_subs.add_parser("validate", help="Validate all hub files for integrity issues")

    # track sync
    p_sync = track_subs.add_parser("sync", help="Reconcile board cards with hub frontmatter")
    p_sync.add_argument("--dry-run", action="store_true", dest="dry_run")
    p_sync.add_argument(
        "--from-board",
        action="store_true",
        dest="from_board",
        help="Reverse sync: update hub frontmatter from board lane positions",
    )

    # --- pdf ---
    p_pdf = subparsers.add_parser("pdf", help="Generate PDF documents")
    p_pdf.add_argument("company", help="Company name")
    p_pdf.add_argument("--output-dir", help="Output directory")
    p_pdf.add_argument("--cv-only", action="store_true", help="CV only")
    p_pdf.add_argument("--cl-only", action="store_true", help="Cover letter only")

    # --- scan ---
    p_scan = subparsers.add_parser("scan", help="Job board scanning utilities")
    scan_subs = p_scan.add_subparsers(dest="scan_command", required=True)

    # scan bookmarks
    p_scan_bm = scan_subs.add_parser("bookmarks", help="List parsed bookmarks")
    p_scan_bm.add_argument("--categories", nargs="+", help="Filter to categories")

    # scan fetch
    p_scan_fetch = scan_subs.add_parser("fetch", help="Fetch board pages")
    p_scan_fetch.add_argument("--categories", nargs="+", help="Filter to categories")
    p_scan_fetch.add_argument("--limit", type=int, help="Max boards to fetch")

    # scan existing
    scan_subs.add_parser("existing", help="List companies already in tracker")

    # --- get ---
    p_get = subparsers.add_parser("get", help="Read company data as structured JSON")
    p_get.add_argument("company", help="Company name (fuzzy match)")
    p_get.add_argument("--field", help="Return a single frontmatter field value")
    p_get.add_argument("--section", help="Return a single section's content")

    # --- set ---
    p_set = subparsers.add_parser("set", help="Atomically update a company hub field or section")
    p_set.add_argument("company", help="Company name (fuzzy match)")
    p_set.add_argument("--field", help="Frontmatter field name to update")
    p_set.add_argument("--value", help="New value for the field")
    p_set.add_argument("--section", help="Section heading to replace")
    p_set.add_argument("--content", help="New content for the section")
    p_set.add_argument("--dry-run", action="store_true", dest="dry_run")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    config = Config.load()

    if args.command == "track":
        dispatch = {
            "create": _track_create,
            "update": _track_update,
            "highlights": _track_highlights,
            "research": _track_research,
            "outreach": _track_outreach,
            "followup": _track_followup,
            "validate": _track_validate,
            "sync": _track_sync,
        }
        handler = dispatch[args.track_command]
        handler(args, config)

    elif args.command == "pdf":
        _cmd_pdf(args, config)

    elif args.command == "scan":
        _cmd_scan(args, config)

    elif args.command == "get":
        _cmd_get(args, config)

    elif args.command == "set":
        _cmd_set(args, config)


if __name__ == "__main__":
    main()
