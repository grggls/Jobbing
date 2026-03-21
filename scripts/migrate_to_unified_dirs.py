#!/usr/bin/env python3
"""Migrate Jobbing project to unified per-company directories.

BEFORE:
    kanban/companies/{Company}.md                  ← hub file (flat)
    kanban/interviews/{Company}/{date}-{Name}.md   ← interview files
    companies/{company}/*.pdf, *.json              ← PDFs + JSON (lowercase dir)

AFTER:
    kanban/companies/{Company}/{Company}.md         ← hub file
    kanban/companies/{Company}/{date}-{Name}.md     ← interview files (flat)
    kanban/companies/{Company}/*.pdf, *.json        ← PDFs + JSON

Also updates board wikilinks:
    [[companies/{Company}|{Display}]] → [[{Company}|{Display}]]

Usage:
    python scripts/migrate_to_unified_dirs.py [--dry-run]
    python scripts/migrate_to_unified_dirs.py          # live run (creates dirs, moves files)
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_name(name: str) -> str:
    """Convert company name to safe filesystem stem (same logic as obsidian.py)."""
    return name.replace("/", "-").replace("\\", "-").replace(":", " -").strip()


def _find_companies_dir(companies_lowercase_dir: Path, hub_stem: str) -> Path | None:
    """Find the matching lowercase companies/ subdir for a hub file stem.

    Tries: exact lowercase match, then normalized (strip parentheticals).
    """
    stem_lower = hub_stem.lower()
    stem_normalized = re.sub(r"\s*\([^)]*\)\s*$", "", hub_stem).strip().lower()

    for d in companies_lowercase_dir.iterdir():
        if not d.is_dir():
            continue
        name_lower = d.name.lower()
        if name_lower == stem_lower or name_lower == stem_normalized:
            return d
    return None


def log(msg: str, dry: bool) -> None:
    prefix = "[DRY RUN] " if dry else ""
    print(f"{prefix}{msg}")


# ---------------------------------------------------------------------------
# Main migration
# ---------------------------------------------------------------------------


def migrate(project_dir: Path, dry_run: bool) -> None:
    kanban_companies = project_dir / "kanban" / "companies"
    kanban_interviews = project_dir / "kanban" / "interviews"
    old_companies = project_dir / "companies"
    board_path = project_dir / "kanban" / "Job Tracker.md"

    if not kanban_companies.is_dir():
        print(f"ERROR: {kanban_companies} not found", file=sys.stderr)
        sys.exit(1)

    # Collect flat hub files (skip directories — already migrated)
    hub_files = [f for f in kanban_companies.iterdir() if f.is_file() and f.suffix == ".md"]
    print(f"Found {len(hub_files)} hub files to migrate")

    moved_count = 0
    skipped_count = 0

    for hub in sorted(hub_files):
        company_stem = hub.stem  # e.g. "Acme Corp"
        safe_stem = _safe_name(company_stem)  # e.g. "Acme Corp" (usually same)

        target_dir = kanban_companies / safe_stem
        target_hub = target_dir / f"{safe_stem}.md"

        # Skip if already migrated
        if target_dir.is_dir() and target_hub.is_file():
            log(f"  SKIP (already migrated): {company_stem}", dry=dry_run)
            skipped_count += 1
            continue

        log(f"  MIGRATE: {hub.name} → {safe_stem}/{safe_stem}.md", dry=dry_run)

        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(hub), str(target_hub))

        moved_count += 1

        # Move interview files for this company
        interview_company_dir = kanban_interviews / company_stem
        if interview_company_dir.is_dir():
            interview_files = list(interview_company_dir.glob("*.md"))
            log(
                f"    → {len(interview_files)} interview file(s)"
                f" from kanban/interviews/{company_stem}/",
                dry=dry_run,
            )
            for ifile in sorted(interview_files):
                dest = target_dir / ifile.name
                log(f"      {ifile.name}", dry=dry_run)
                if not dry_run:
                    shutil.move(str(ifile), str(dest))
            if not dry_run and not list(interview_company_dir.iterdir()):
                interview_company_dir.rmdir()

        # Move PDF/JSON from companies/{lowercase}/
        if old_companies.is_dir():
            src_company_dir = _find_companies_dir(old_companies, company_stem)
            if src_company_dir:
                company_assets = [
                    f
                    for f in src_company_dir.iterdir()
                    if f.is_file() and f.suffix in {".pdf", ".json", ".md"}
                ]
                if company_assets:
                    log(
                        f"    → {len(company_assets)} asset(s)"
                        f" from companies/{src_company_dir.name}/",
                        dry=dry_run,
                    )
                    for asset in sorted(company_assets):
                        dest = target_dir / asset.name
                        log(f"      {asset.name}", dry=dry_run)
                        if not dry_run:
                            shutil.move(str(asset), str(dest))
                    if not dry_run:
                        # Remove empty .gitkeep or dir
                        remaining = list(src_company_dir.iterdir())
                        if not remaining:
                            src_company_dir.rmdir()
                        elif len(remaining) == 1 and remaining[0].name == ".gitkeep":
                            remaining[0].unlink()
                            src_company_dir.rmdir()

    print(f"\nHub files: {moved_count} migrated, {skipped_count} already done")

    # Update board wikilinks
    _update_board_wikilinks(board_path, dry_run)

    # Clean up empty kanban/interviews/
    if not dry_run and kanban_interviews.is_dir():
        remaining_dirs = [d for d in kanban_interviews.iterdir() if d.is_dir()]
        if not remaining_dirs:
            log("Removing empty kanban/interviews/ directory", dry=dry_run)
            if not dry_run:
                kanban_interviews.rmdir()
        else:
            log(
                f"kanban/interviews/ still has {len(remaining_dirs)} dirs (may have non-.md files)",
                dry=dry_run,
            )


def _update_board_wikilinks(board_path: Path, dry_run: bool) -> None:
    """Update board card wikilinks from [[companies/Name|Display]] to [[Name|Display]]."""
    if not board_path.is_file():
        log("Board file not found, skipping wikilink update", dry=dry_run)
        return

    text = board_path.read_text(encoding="utf-8")
    # Pattern: [[companies/Acme Corp|Acme Corp]] → [[Acme Corp|Acme Corp]]
    new_text = re.sub(r"\[\[companies/([^\|]+)\|([^\]]+)\]\]", r"[[\2|\2]]", text)

    if new_text == text:
        log("Board wikilinks: no changes needed", dry=dry_run)
        return

    changes = len(re.findall(r"\[\[companies/", text))
    log(f"Board wikilinks: updating {changes} card link(s)", dry=dry_run)
    if not dry_run:
        board_path.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument(
        "--project-dir",
        default=None,
        help="Path to Jobbing project root (default: script's parent dir)",
    )
    args = parser.parse_args()

    if args.project_dir:
        project_dir = Path(args.project_dir).resolve()
    else:
        project_dir = Path(__file__).resolve().parent.parent

    print(f"Project: {project_dir}")
    if args.dry_run:
        print("DRY RUN — no files will be changed\n")
    else:
        print("LIVE RUN — files will be moved\n")

    migrate(project_dir, dry_run=args.dry_run)

    if not args.dry_run:
        print("\nMigration complete.")
        print("Next steps:")
        print("  1. git add -A kanban/companies/ kanban/interviews/")
        print("  2. git rm --cached companies/  (if any assets were tracked)")
        print("  3. Run: jobbing track sync      (to rebuild board from hub frontmatter)")
        print("  4. Run: jobbing track validate  (to check integrity)")


if __name__ == "__main__":
    main()
