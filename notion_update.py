#!/usr/bin/env python3
"""Notion database page manager for job application tracking.

Creates, updates, and manages pages in a Notion database via the REST API.
Designed to be called by Claude Cowork during job application workflows.

Usage:
    python3 notion_update.py create --name "Company" --position "Role" ...
    python3 notion_update.py update --page-id "id" --status "Applied" ...
    python3 notion_update.py highlights --page-id "id" --highlights "Bullet 1" "Bullet 2"
    python3 notion_update.py research --name "Company" --research "Bullet 1" "Bullet 2"
    python3 notion_update.py outreach --name "Company" --contacts-json contacts.json
    python3 notion_update.py run-queue [--queue-dir notion_queue/]
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATABASE_ID = "734d746c43b149298993464f5ccc23e7"
NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

VALID_STATUSES = [
    "Targeted",
    "Applied",
    "Followed-Up",
    "In Progress (Interviewing)",
    "Done",
]

VALID_LINKEDIN = ["No", "Yes", "n/a"]


# ---------------------------------------------------------------------------
# API key loading
# ---------------------------------------------------------------------------


def _load_api_key() -> str:
    """Retrieve the Notion API key from the environment, .env file, or ~/.zshrc-secrets."""
    key = os.environ.get("NOTION_API_KEY")
    if key:
        return key

    # Check .env in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("NOTION_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if key:
                        return key

    # Fallback: source ~/.zshrc-secrets
    secrets_path = os.path.expanduser("~/.zshrc-secrets")
    if os.path.isfile(secrets_path):
        try:
            result = subprocess.run(
                ["bash", "-c", f"source {secrets_path} && echo $NOTION_API_KEY"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            key = result.stdout.strip()
            if key:
                return key
        except (subprocess.TimeoutExpired, OSError):
            pass

    print("Error: NOTION_API_KEY not found in environment, .env, or ~/.zshrc-secrets", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }


def _request(method: str, url: str, api_key: str, payload: dict | None = None) -> dict:
    """Send an HTTP request to the Notion API and return the parsed response."""
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=_headers(api_key), method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8") if exc.fp else ""
        print(f"Error: Notion API returned HTTP {exc.code}", file=sys.stderr)
        print(f"URL: {url}", file=sys.stderr)
        if error_body:
            try:
                detail = json.loads(error_body)
                print(f"Message: {detail.get('message', error_body)}", file=sys.stderr)
            except json.JSONDecodeError:
                print(f"Response: {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Error: Could not reach Notion API — {exc.reason}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Property builders
# ---------------------------------------------------------------------------


def _title(text: str) -> dict:
    return {"title": [{"text": {"content": text}}]}


def _rich_text(text: str) -> dict:
    return {"rich_text": [{"text": {"content": text}}]}


def _select(name: str) -> dict:
    return {"select": {"name": name}}


def _multi_select(names: list[str]) -> dict:
    return {"multi_select": [{"name": n} for n in names]}


def _date(iso_date: str) -> dict:
    return {"date": {"start": iso_date}}


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------


def _heading3_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }


def _bullet_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }


def _contact_bullet_block(contact: dict) -> dict:
    """Build a bullet block for a contact with nested sub-bullets for note and message.

    Renders as:
      - **Name** — Title — linkedin.com/in/handle
        - Context about why this person is relevant
        - "Draft connection request message"
    """
    parts: list[dict] = [
        {"type": "text", "text": {"content": contact["name"]}, "annotations": {"bold": True}},
    ]
    if contact.get("title"):
        parts.append({"type": "text", "text": {"content": f" — {contact['title']}"}})
    if contact.get("linkedin"):
        url = contact["linkedin"]
        display = url.replace("https://www.", "").replace("https://", "").replace("http://", "")
        parts.append({"type": "text", "text": {"content": " — "}})
        parts.append({"type": "text", "text": {"content": display, "link": {"url": url}}})

    block: dict = {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": parts},
    }

    children: list[dict] = []
    if contact.get("note"):
        children.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [
                {"type": "text", "text": {"content": contact["note"]}},
            ]},
        })
    if contact.get("message"):
        children.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [
                {"type": "text", "text": {"content": contact["message"]},
                 "annotations": {"italic": True}},
            ]},
        })
    if children:
        block["bulleted_list_item"]["children"] = children

    return block


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


def _find_existing_page(api_key: str, name: str) -> dict | None:
    """Query the database for a page matching the given company name (case-insensitive).

    Returns the page object if found, or None.
    """
    payload = {
        "filter": {
            "property": "Name",
            "title": {"equals": name},
        },
        "page_size": 5,
    }
    result = _request("POST", f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query", api_key, payload)
    pages = [p for p in result.get("results", []) if not p.get("archived")]
    return pages[0] if pages else None


def _resolve_page_id(api_key: str, args: argparse.Namespace) -> str:
    """Resolve a page ID from either --page-id or --name."""
    if getattr(args, "page_id", None):
        return args.page_id.replace("-", "")
    if getattr(args, "name", None):
        page = _find_existing_page(api_key, args.name)
        if page:
            return page["id"]
        raise ValueError(f"No page found for company '{args.name}'")
    raise ValueError("Either --page-id or --name is required")


# ---------------------------------------------------------------------------
# Section management (generic)
# ---------------------------------------------------------------------------


def _remove_section(api_key: str, page_id: str, heading_text: str) -> None:
    """Remove a heading_3 section and its subsequent bullet items from a page."""
    url = f"{NOTION_BASE_URL}/blocks/{page_id}/children?page_size=100"
    result = _request("GET", url, api_key)
    blocks = result.get("results", [])

    ids_to_delete: list[str] = []
    in_section = False

    for block in blocks:
        block_type = block.get("type", "")
        if block_type == "heading_3":
            rt = block.get("heading_3", {}).get("rich_text", [])
            text = rt[0].get("text", {}).get("content", "") if rt else ""
            if text == heading_text:
                in_section = True
                ids_to_delete.append(block["id"])
                continue
            elif in_section:
                break
        if in_section:
            if block_type == "bulleted_list_item":
                ids_to_delete.append(block["id"])
            else:
                break

    for block_id in ids_to_delete:
        _request("DELETE", f"{NOTION_BASE_URL}/blocks/{block_id}", api_key)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def _build_properties(args: argparse.Namespace, *, include_name: bool = True, default_status: str | None = None) -> dict:
    """Build the properties dict from parsed arguments."""
    properties: dict = {}

    if include_name and args.name:
        properties["Name"] = _title(args.name)
    if args.status:
        properties["Status"] = _select(args.status)
    elif default_status:
        properties["Status"] = _select(default_status)
    if args.date:
        properties["Start Date"] = _date(args.date)
    if args.url:
        properties["URL"] = _rich_text(args.url)
    if args.position:
        properties["Open Position"] = _rich_text(args.position)
    if args.environment:
        properties["Environment"] = _multi_select(args.environment)
    if args.salary:
        properties["Salary (Range)"] = _rich_text(args.salary)
    if args.focus:
        properties["Company Focus"] = _multi_select(args.focus)
    if args.vision:
        properties["Vision"] = _rich_text(args.vision)
    if args.mission:
        properties["Mission"] = _rich_text(args.mission)
    if getattr(args, "linkedin", None):
        properties["Follow on Linkedin"] = _select(args.linkedin)
    if getattr(args, "conclusion", None):
        properties["Conclusion"] = _rich_text(args.conclusion)

    return properties


def cmd_create(args: argparse.Namespace) -> None:
    """Create a new page in the Notion database, or update if one already exists."""
    api_key = _load_api_key()

    # Check for existing page with the same company name
    if not args.dry_run:
        existing = _find_existing_page(api_key, args.name)
        if existing:
            page_id = existing["id"]
            page_url = existing["url"]
            print(f"Found existing page for '{args.name}': {page_id}")
            print(f"URL: {page_url}")
            print("Updating instead of creating duplicate.")

            # Build properties without overwriting name, and don't reset status
            properties = _build_properties(args, include_name=False, default_status=None)
            if properties:
                _request("PATCH", f"{NOTION_BASE_URL}/pages/{page_id}", api_key, {"properties": properties})
                print("Properties updated.")

            if args.highlights:
                _remove_existing_highlights(api_key, page_id)
                _append_highlights(api_key, page_id, args.highlights, dry_run=False)
            return

    properties = _build_properties(args, include_name=True, default_status="Targeted")

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties,
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return

    result = _request("POST", f"{NOTION_BASE_URL}/pages", api_key, payload)
    page_id = result["id"]
    page_url = result["url"]
    print(f"Created page: {page_id}")
    print(f"URL: {page_url}")

    # Append highlights if provided
    if args.highlights:
        _append_highlights(api_key, page_id, args.highlights, dry_run=False)


def cmd_update(args: argparse.Namespace) -> None:
    """Update properties on an existing Notion page."""
    api_key = _load_api_key()

    properties: dict = {}

    if args.name:
        properties["Name"] = _title(args.name)
    if args.status:
        properties["Status"] = _select(args.status)
    if args.date:
        properties["Start Date"] = _date(args.date)
    if args.url:
        properties["URL"] = _rich_text(args.url)
    if args.position:
        properties["Open Position"] = _rich_text(args.position)
    if args.environment:
        properties["Environment"] = _multi_select(args.environment)
    if args.salary:
        properties["Salary (Range)"] = _rich_text(args.salary)
    if args.focus:
        properties["Company Focus"] = _multi_select(args.focus)
    if args.vision:
        properties["Vision"] = _rich_text(args.vision)
    if args.mission:
        properties["Mission"] = _rich_text(args.mission)
    if args.linkedin:
        properties["Follow on Linkedin"] = _select(args.linkedin)
    if args.conclusion:
        properties["Conclusion"] = _rich_text(args.conclusion)

    if not properties:
        print("Error: No properties to update. Provide at least one field.", file=sys.stderr)
        sys.exit(1)

    payload = {"properties": properties}

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return

    page_id = args.page_id.replace("-", "")
    result = _request("PATCH", f"{NOTION_BASE_URL}/pages/{page_id}", api_key, payload)
    print(f"Updated page: {result['id']}")
    print(f"URL: {result['url']}")


def cmd_highlights(args: argparse.Namespace) -> None:
    """Append or replace 'Experience to Highlight' blocks on an existing page."""
    api_key = _load_api_key()
    page_id = args.page_id.replace("-", "")

    if args.dry_run:
        blocks = _build_highlight_blocks(args.highlights)
        print(json.dumps({"children": blocks}, indent=2))
        return

    # Remove existing highlight blocks before appending new ones
    _remove_existing_highlights(api_key, page_id)
    _append_highlights(api_key, page_id, args.highlights, dry_run=False)
    print(f"Highlights updated on page: {page_id}")


# ---------------------------------------------------------------------------
# Highlight helpers
# ---------------------------------------------------------------------------


def _build_highlight_blocks(highlights: list[str]) -> list[dict]:
    """Build the list of block objects for highlights."""
    blocks: list[dict] = [_heading3_block("Experience to Highlight")]
    for item in highlights:
        blocks.append(_bullet_block(item))
    return blocks


def _append_highlights(api_key: str, page_id: str, highlights: list[str], *, dry_run: bool) -> None:
    """Append highlight blocks to a page."""
    blocks = _build_highlight_blocks(highlights)
    payload = {"children": blocks}

    if dry_run:
        print(json.dumps(payload, indent=2))
        return

    _request("PATCH", f"{NOTION_BASE_URL}/blocks/{page_id}/children", api_key, payload)
    print("Highlights appended.")


def _remove_existing_highlights(api_key: str, page_id: str) -> None:
    """Remove existing 'Experience to Highlight' heading and subsequent bullets."""
    _remove_section(api_key, page_id, "Experience to Highlight")


# ---------------------------------------------------------------------------
# Research helpers
# ---------------------------------------------------------------------------


def _build_research_blocks(items: list[str]) -> list[dict]:
    """Build block objects for the Company Research section."""
    blocks: list[dict] = [_heading3_block("Company Research")]
    for item in items:
        blocks.append(_bullet_block(item))
    return blocks


def cmd_research(args: argparse.Namespace) -> None:
    """Append or replace 'Company Research' blocks on a page."""
    blocks = _build_research_blocks(args.research)

    if args.dry_run:
        print(json.dumps({"children": blocks}, indent=2))
        return

    api_key = _load_api_key()
    page_id = _resolve_page_id(api_key, args)
    _remove_section(api_key, page_id, "Company Research")
    _request("PATCH", f"{NOTION_BASE_URL}/blocks/{page_id}/children", api_key, {"children": blocks})
    print(f"Company research updated on page: {page_id}")


# ---------------------------------------------------------------------------
# Outreach helpers
# ---------------------------------------------------------------------------


def _build_outreach_blocks(contacts: list[dict]) -> list[dict]:
    """Build block objects for the Outreach Contacts section."""
    blocks: list[dict] = [_heading3_block("Outreach Contacts")]
    for contact in contacts:
        blocks.append(_contact_bullet_block(contact))
    return blocks


def cmd_outreach(args: argparse.Namespace) -> None:
    """Append or replace 'Outreach Contacts' blocks on a page and set Follow on Linkedin to 'No'."""
    # Load contacts from JSON file if using CLI
    contacts = getattr(args, "contacts", None)
    if not contacts and getattr(args, "contacts_json", None):
        with open(args.contacts_json) as f:
            contacts = json.load(f)

    if not contacts:
        print("Error: No contacts provided.", file=sys.stderr)
        sys.exit(1)

    blocks = _build_outreach_blocks(contacts)

    if args.dry_run:
        print(json.dumps({"children": blocks}, indent=2))
        return

    api_key = _load_api_key()
    page_id = _resolve_page_id(api_key, args)
    _remove_section(api_key, page_id, "Outreach Contacts")
    _request("PATCH", f"{NOTION_BASE_URL}/blocks/{page_id}/children", api_key, {"children": blocks})

    # Set "Follow on Linkedin" to "No" (contacts identified, follow-up pending)
    _request("PATCH", f"{NOTION_BASE_URL}/pages/{page_id}", api_key, {
        "properties": {"Follow on Linkedin": _select("No")}
    })
    print(f"Outreach contacts updated on page: {page_id}")
    print(f"  Follow on Linkedin set to: No")


# ---------------------------------------------------------------------------
# Queue processing
# ---------------------------------------------------------------------------

QUEUE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notion_queue")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notion_queue_results")


def _process_queue_file(api_key: str, filepath: str) -> dict:
    """Process a single queue file and return a result dict."""
    filename = os.path.basename(filepath)
    with open(filepath) as f:
        task = json.load(f)

    command = task.get("command")
    if command not in ("create", "update", "highlights", "research", "outreach"):
        return {"file": filename, "status": "error", "message": f"Unknown command: {command}"}

    # Build an argparse.Namespace from the JSON task
    args = argparse.Namespace(dry_run=False)
    for key, value in task.items():
        if key == "command":
            continue
        # Convert kebab-case keys to underscore (e.g., page-id → page_id)
        attr = key.replace("-", "_")
        setattr(args, attr, value)

    # Ensure optional fields have defaults so attribute lookups don't fail
    for field in ("name", "status", "date", "url", "position", "environment",
                  "salary", "focus", "vision", "mission", "linkedin", "highlights",
                  "page_id", "conclusion", "research", "contacts", "contacts_json",
                  "message"):
        if not hasattr(args, field):
            setattr(args, field, None)

    try:
        if command == "create":
            result = _queue_create(api_key, args)
        elif command == "update":
            result = _queue_update(api_key, args)
        elif command == "highlights":
            result = _queue_highlights(api_key, args)
        elif command == "research":
            result = _queue_research(api_key, args)
        elif command == "outreach":
            result = _queue_outreach(api_key, args)
        return {"file": filename, "status": "ok", **result}
    except SystemExit:
        return {"file": filename, "status": "error", "message": "API call failed (see stderr)"}
    except Exception as exc:
        return {"file": filename, "status": "error", "message": str(exc)}


def _queue_create(api_key: str, args: argparse.Namespace) -> dict:
    """Create (or update-if-exists) from queue task."""
    existing = _find_existing_page(api_key, args.name)
    if existing:
        page_id = existing["id"]
        properties = _build_properties(args, include_name=False, default_status=None)
        if properties:
            _request("PATCH", f"{NOTION_BASE_URL}/pages/{page_id}", api_key, {"properties": properties})
        if args.highlights:
            _remove_existing_highlights(api_key, page_id)
            _append_highlights(api_key, page_id, args.highlights, dry_run=False)
        return {"action": "updated_existing", "page_id": page_id, "url": existing["url"]}

    properties = _build_properties(args, include_name=True, default_status="Targeted")
    payload = {"parent": {"database_id": DATABASE_ID}, "properties": properties}
    result = _request("POST", f"{NOTION_BASE_URL}/pages", api_key, payload)
    page_id = result["id"]
    if args.highlights:
        _append_highlights(api_key, page_id, args.highlights, dry_run=False)
    return {"action": "created", "page_id": page_id, "url": result["url"]}


def _queue_update(api_key: str, args: argparse.Namespace) -> dict:
    """Update properties from queue task."""
    if not args.page_id:
        raise ValueError("update command requires page_id")
    page_id = args.page_id.replace("-", "")

    properties: dict = {}
    if args.name:
        properties["Name"] = _title(args.name)
    if args.status:
        properties["Status"] = _select(args.status)
    if args.date:
        properties["Start Date"] = _date(args.date)
    if args.url:
        properties["URL"] = _rich_text(args.url)
    if args.position:
        properties["Open Position"] = _rich_text(args.position)
    if args.environment:
        properties["Environment"] = _multi_select(args.environment)
    if args.salary:
        properties["Salary (Range)"] = _rich_text(args.salary)
    if args.focus:
        properties["Company Focus"] = _multi_select(args.focus)
    if args.vision:
        properties["Vision"] = _rich_text(args.vision)
    if args.mission:
        properties["Mission"] = _rich_text(args.mission)
    if args.linkedin:
        properties["Follow on Linkedin"] = _select(args.linkedin)
    if args.conclusion:
        properties["Conclusion"] = _rich_text(args.conclusion)

    if not properties:
        raise ValueError("No properties to update")

    result = _request("PATCH", f"{NOTION_BASE_URL}/pages/{page_id}", api_key, {"properties": properties})
    return {"action": "updated", "page_id": result["id"], "url": result["url"]}


def _queue_highlights(api_key: str, args: argparse.Namespace) -> dict:
    """Replace highlights from queue task."""
    if not args.page_id:
        raise ValueError("highlights command requires page_id")
    if not args.highlights:
        raise ValueError("highlights command requires highlights list")
    page_id = args.page_id.replace("-", "")
    _remove_existing_highlights(api_key, page_id)
    _append_highlights(api_key, page_id, args.highlights, dry_run=False)
    return {"action": "highlights_replaced", "page_id": page_id}


def _queue_research(api_key: str, args: argparse.Namespace) -> dict:
    """Replace Company Research section from queue task."""
    if not args.name and not args.page_id:
        raise ValueError("research command requires name or page_id")
    if not args.research:
        raise ValueError("research command requires research list")
    page_id = _resolve_page_id(api_key, args)
    blocks = _build_research_blocks(args.research)
    _remove_section(api_key, page_id, "Company Research")
    _request("PATCH", f"{NOTION_BASE_URL}/blocks/{page_id}/children", api_key, {"children": blocks})
    return {"action": "research_replaced", "page_id": page_id}


def _queue_outreach(api_key: str, args: argparse.Namespace) -> dict:
    """Replace Outreach Contacts section from queue task."""
    if not args.name and not args.page_id:
        raise ValueError("outreach command requires name or page_id")
    contacts = args.contacts
    if not contacts:
        raise ValueError("outreach command requires contacts list")
    page_id = _resolve_page_id(api_key, args)
    blocks = _build_outreach_blocks(contacts)
    _remove_section(api_key, page_id, "Outreach Contacts")
    _request("PATCH", f"{NOTION_BASE_URL}/blocks/{page_id}/children", api_key, {"children": blocks})
    _request("PATCH", f"{NOTION_BASE_URL}/pages/{page_id}", api_key, {
        "properties": {"Follow on Linkedin": _select("No")}
    })
    return {"action": "outreach_replaced", "page_id": page_id}


def cmd_run_queue(args: argparse.Namespace) -> None:
    """Process all JSON files in the queue directory."""
    queue_dir = args.queue_dir or QUEUE_DIR
    results_dir = args.results_dir or RESULTS_DIR

    os.makedirs(queue_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(queue_dir, "*.json")))
    if not files:
        print("No queue files to process.")
        return

    api_key = _load_api_key()
    print(f"Processing {len(files)} queue file(s)...")

    for filepath in files:
        filename = os.path.basename(filepath)
        print(f"\n--- {filename} ---")
        result = _process_queue_file(api_key, filepath)

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
        result_filename = f"{timestamp}_{filename}"
        result_path = os.path.join(results_dir, result_filename)
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)

        # Move processed queue file to results dir (preserving original for audit)
        processed_path = os.path.join(results_dir, f"{timestamp}_input_{filename}")
        shutil.move(filepath, processed_path)
        print(f"  Moved to: {result_filename}")

    print(f"\nDone. Results in: {results_dir}")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage job application pages in a Notion database.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the API payload without sending it.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- create ---
    p_create = subparsers.add_parser("create", help="Create a new page in the database.")
    p_create.add_argument("--name", required=True, help="Company name (required).")
    p_create.add_argument("--position", help="Open position / role title.")
    p_create.add_argument("--date", help="Start date in YYYY-MM-DD format.")
    p_create.add_argument("--url", help="Job posting URL.")
    p_create.add_argument("--status", choices=VALID_STATUSES, help="Application status.")
    p_create.add_argument("--environment", nargs="+", help="Environment tags (e.g. Remote, Hybrid).")
    p_create.add_argument("--salary", help="Salary range as free text.")
    p_create.add_argument("--focus", nargs="+", help="Company focus tags (e.g. AI, FinTech).")
    p_create.add_argument("--vision", help="Company vision statement.")
    p_create.add_argument("--mission", help="Company mission statement.")
    p_create.add_argument("--linkedin", choices=VALID_LINKEDIN, help="Follow on LinkedIn.")
    p_create.add_argument("--conclusion", help="Conclusion / outcome notes.")
    p_create.add_argument("--highlights", nargs="+", help="Experience to Highlight bullets.")
    p_create.add_argument("--dry-run", action="store_true", dest="dry_run", help="Print payload only.")

    # --- update ---
    p_update = subparsers.add_parser("update", help="Update properties on an existing page.")
    p_update.add_argument("--page-id", required=True, help="Notion page ID to update.")
    p_update.add_argument("--name", help="Company name.")
    p_update.add_argument("--position", help="Open position / role title.")
    p_update.add_argument("--date", help="Start date in YYYY-MM-DD format.")
    p_update.add_argument("--url", help="Job posting URL.")
    p_update.add_argument("--status", choices=VALID_STATUSES, help="Application status.")
    p_update.add_argument("--environment", nargs="+", help="Environment tags.")
    p_update.add_argument("--salary", help="Salary range as free text.")
    p_update.add_argument("--focus", nargs="+", help="Company focus tags.")
    p_update.add_argument("--vision", help="Company vision statement.")
    p_update.add_argument("--mission", help="Company mission statement.")
    p_update.add_argument("--linkedin", choices=VALID_LINKEDIN, help="Follow on LinkedIn.")
    p_update.add_argument("--conclusion", help="Conclusion / outcome notes.")
    p_update.add_argument("--dry-run", action="store_true", dest="dry_run", help="Print payload only.")

    # --- highlights ---
    p_hl = subparsers.add_parser("highlights", help="Add/replace highlights on an existing page.")
    p_hl.add_argument("--page-id", required=True, help="Notion page ID.")
    p_hl.add_argument("--highlights", nargs="+", required=True, help="Highlight bullets.")
    p_hl.add_argument("--dry-run", action="store_true", dest="dry_run", help="Print payload only.")

    # --- research ---
    p_research = subparsers.add_parser("research", help="Add/replace Company Research on a page.")
    p_research_id = p_research.add_mutually_exclusive_group(required=True)
    p_research_id.add_argument("--page-id", help="Notion page ID.")
    p_research_id.add_argument("--name", help="Company name (looks up page ID).")
    p_research.add_argument("--research", nargs="+", required=True, help="Research bullets.")
    p_research.add_argument("--dry-run", action="store_true", dest="dry_run", help="Print payload only.")

    # --- outreach ---
    p_outreach = subparsers.add_parser("outreach", help="Add/replace Outreach Contacts on a page.")
    p_outreach_id = p_outreach.add_mutually_exclusive_group(required=True)
    p_outreach_id.add_argument("--page-id", help="Notion page ID.")
    p_outreach_id.add_argument("--name", help="Company name (looks up page ID).")
    p_outreach.add_argument("--contacts-json", help="Path to JSON file with contacts array.")
    p_outreach.add_argument("--dry-run", action="store_true", dest="dry_run", help="Print payload only.")

    # --- run-queue ---
    p_queue = subparsers.add_parser("run-queue", help="Process all JSON files in the queue directory.")
    p_queue.add_argument("--queue-dir", help=f"Queue directory (default: {QUEUE_DIR}).")
    p_queue.add_argument("--results-dir", help=f"Results directory (default: {RESULTS_DIR}).")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    dispatch = {
        "create": cmd_create,
        "update": cmd_update,
        "highlights": cmd_highlights,
        "research": cmd_research,
        "outreach": cmd_outreach,
        "run-queue": cmd_run_queue,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
