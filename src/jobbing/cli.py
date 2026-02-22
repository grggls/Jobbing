"""Unified CLI entry point for the Jobbing package.

Replaces the separate notion_update.py and generate_pdfs.py scripts
with a single `jobbing` command:

    jobbing track create --name "Company" --position "Role" --date 2026-02-22
    jobbing track update --page-id ID --status "Applied"
    jobbing track highlights --page-id ID --highlights "Bullet 1" "Bullet 2"
    jobbing track research --name "Company" --research "Finding 1" "Finding 2"
    jobbing track outreach --name "Company" --contacts-json contacts.json
    jobbing queue [--queue-dir path] [--results-dir path]
    jobbing pdf <company> [--cv-only] [--cl-only] [--output-dir path]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import date
from pathlib import Path

from jobbing.config import Config
from jobbing.models import Application, Contact, LinkedInStatus, Status


# ---------------------------------------------------------------------------
# Status/LinkedIn choice values (for argparse validation)
# ---------------------------------------------------------------------------

VALID_STATUSES = [s.value for s in Status]
VALID_LINKEDIN = [l.value for l in LinkedInStatus]


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

    page_id = tracker.create(app)
    print(f"Created/updated entry: {page_id}")


def _track_update(args: argparse.Namespace, config: Config) -> None:
    """Update properties on an existing tracker entry."""
    from jobbing.tracker import get_tracker

    app = _args_to_application(args)
    app.page_id = args.page_id

    tracker = get_tracker(config.tracker_backend, config)

    if args.dry_run:
        print(json.dumps(_preview_application(app), indent=2))
        return

    tracker.update(app)
    print(f"Updated entry: {args.page_id}")


def _track_highlights(args: argparse.Namespace, config: Config) -> None:
    """Replace highlights on a tracker entry."""
    from jobbing.tracker import get_tracker

    tracker = get_tracker(config.tracker_backend, config)

    if args.dry_run:
        print(json.dumps({"page_id": args.page_id, "highlights": args.highlights}, indent=2))
        return

    tracker.set_highlights(args.page_id, args.highlights)
    print(f"Highlights updated on: {args.page_id}")


def _track_research(args: argparse.Namespace, config: Config) -> None:
    """Replace research on a tracker entry."""
    from jobbing.tracker import get_tracker

    tracker = get_tracker(config.tracker_backend, config)

    # Resolve page_id from name if needed
    page_id = args.page_id
    if not page_id and args.name:
        app = tracker.find_by_name(args.name)
        if not app or not app.page_id:
            print(f"Error: No entry found for '{args.name}'", file=sys.stderr)
            sys.exit(1)
        page_id = app.page_id

    if args.dry_run:
        print(json.dumps({"page_id": page_id, "research": args.research}, indent=2))
        return

    tracker.set_research(page_id, args.research)
    print(f"Research updated on: {page_id}")


def _track_outreach(args: argparse.Namespace, config: Config) -> None:
    """Replace outreach contacts on a tracker entry."""
    from jobbing.tracker import get_tracker

    # Load contacts from JSON file
    contacts_data: list[dict] = []
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

    # Resolve page_id from name if needed
    page_id = args.page_id
    if not page_id and args.name:
        app = tracker.find_by_name(args.name)
        if not app or not app.page_id:
            print(f"Error: No entry found for '{args.name}'", file=sys.stderr)
            sys.exit(1)
        page_id = app.page_id

    if args.dry_run:
        print(json.dumps({"page_id": page_id, "contacts": contacts_data}, indent=2))
        return

    tracker.set_contacts(page_id, contacts)
    print(f"Outreach contacts updated on: {page_id}")


# ---------------------------------------------------------------------------
# Queue subcommand
# ---------------------------------------------------------------------------


def _cmd_queue(args: argparse.Namespace, config: Config) -> None:
    """Process all JSON files in the queue directory."""
    from jobbing.tracker.notion import NotionTracker

    queue_dir = Path(args.queue_dir) if args.queue_dir else config.queue_dir
    results_dir = Path(args.results_dir) if args.results_dir else config.queue_results_dir

    queue_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(queue_dir.glob("*.json"))
    if not files:
        print("No queue files to process.")
        return

    tracker = NotionTracker(config)
    print(f"Processing {len(files)} queue file(s)...")

    for filepath in files:
        print(f"\n--- {filepath.name} ---")
        result = tracker.process_queue_file(str(filepath))

        if result["status"] == "ok":
            print(f"  OK: {result.get('action', 'done')}")
            if "page_id" in result:
                print(f"  Page ID: {result['page_id']}")
            if "url" in result:
                print(f"  URL: {result['url']}")
        else:
            print(f"  ERROR: {result.get('message', 'unknown error')}")

        # Write result file and move queue file to results
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        result_filename = f"{timestamp}_{filepath.name}"
        result_path = results_dir / result_filename
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)

        processed_path = results_dir / f"{timestamp}_input_{filepath.name}"
        shutil.move(str(filepath), str(processed_path))
        print(f"  Moved to: {result_filename}")

    print(f"\nDone. Results in: {results_dir}")


# ---------------------------------------------------------------------------
# PDF subcommand
# ---------------------------------------------------------------------------


def _cmd_pdf(args: argparse.Namespace, config: Config) -> None:
    """Generate CV and/or cover letter PDFs."""
    from jobbing.models import CompanyData
    from jobbing.pdf import PDFGenerator

    company_lower = args.company.lower()
    company_dir = config.companies_dir / company_lower

    json_file = company_dir / f"{company_lower}.json"
    if not json_file.exists():
        print(f"Error: {json_file} not found.", file=sys.stderr)
        sys.exit(1)

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

    print("\nDone.")


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
    )


def _preview_application(app: Application) -> dict:
    """Build a preview dict for dry-run output."""
    d: dict = {"name": app.name}
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
    p_create.add_argument("--dry-run", action="store_true", dest="dry_run")

    # track update
    p_update = track_subs.add_parser("update", help="Update an existing entry")
    p_update.add_argument("--page-id", required=True, help="Entry ID")
    p_update.add_argument("--name", help="Company name")
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
    p_hl.add_argument("--page-id", required=True, help="Entry ID")
    p_hl.add_argument("--highlights", nargs="+", required=True, help="Bullets")
    p_hl.add_argument("--dry-run", action="store_true", dest="dry_run")

    # track research
    p_research = track_subs.add_parser("research", help="Replace research")
    p_research_id = p_research.add_mutually_exclusive_group(required=True)
    p_research_id.add_argument("--page-id", help="Entry ID")
    p_research_id.add_argument("--name", help="Company name (looks up ID)")
    p_research.add_argument("--research", nargs="+", required=True, help="Research bullets")
    p_research.add_argument("--dry-run", action="store_true", dest="dry_run")

    # track outreach
    p_outreach = track_subs.add_parser("outreach", help="Replace outreach contacts")
    p_outreach_id = p_outreach.add_mutually_exclusive_group(required=True)
    p_outreach_id.add_argument("--page-id", help="Entry ID")
    p_outreach_id.add_argument("--name", help="Company name (looks up ID)")
    p_outreach.add_argument("--contacts-json", required=True, help="Path to contacts JSON")
    p_outreach.add_argument("--dry-run", action="store_true", dest="dry_run")

    # --- queue ---
    p_queue = subparsers.add_parser("queue", help="Process queue files")
    p_queue.add_argument("--queue-dir", help="Queue directory")
    p_queue.add_argument("--results-dir", help="Results directory")

    # --- pdf ---
    p_pdf = subparsers.add_parser("pdf", help="Generate PDF documents")
    p_pdf.add_argument("company", help="Company name")
    p_pdf.add_argument("--output-dir", help="Output directory")
    p_pdf.add_argument("--cv-only", action="store_true", help="CV only")
    p_pdf.add_argument("--cl-only", action="store_true", help="Cover letter only")

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
        }
        handler = dispatch[args.track_command]
        handler(args, config)

    elif args.command == "queue":
        _cmd_queue(args, config)

    elif args.command == "pdf":
        _cmd_pdf(args, config)


if __name__ == "__main__":
    main()
