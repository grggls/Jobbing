"""Notion API tracker backend.

Clean OO rewrite of the original notion_update.py. Key improvements:
- Single _to_properties() method (was duplicated 3x)
- Raises NotionAPIError instead of sys.exit(1)
- Takes Application/Contact objects, not argparse.Namespace
- Queue processing reuses the same methods
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import date
from typing import Any

from jobbing.config import Config
from jobbing.models import Application, Contact, LinkedInStatus, Status


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class NotionAPIError(Exception):
    """Raised when the Notion API returns an error."""

    def __init__(self, status_code: int, message: str, url: str = ""):
        self.status_code = status_code
        self.url = url
        super().__init__(f"Notion API HTTP {status_code}: {message}")


class NotionConnectionError(Exception):
    """Raised when the Notion API is unreachable."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"


# ---------------------------------------------------------------------------
# Notion property/block builders (pure functions)
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


def _heading2_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }


def _heading3_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }


def _paragraph_block(text: str) -> dict:
    """A paragraph block. Splits text at the 2000-char Notion rich_text limit."""
    chunks = [text[i : i + 2000] for i in range(0, max(len(text), 1), 2000)]
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": chunk}} for chunk in chunks
            ],
        },
    }


def _toggle_heading3_block(text: str, children: list[dict]) -> dict:
    """A heading_3 with is_toggleable=true and nested children."""
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "is_toggleable": True,
            "children": children,
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


def _qa_bullet_block(question: str, answer: str) -> dict:
    """A bullet for the question with a nested sub-bullet for the answer."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": question}}],
            "children": [
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {"type": "text", "text": {"content": answer}},
                        ],
                    },
                }
            ],
        },
    }


def _contact_bullet_block(contact: Contact) -> dict:
    """Build a rich bullet block for a contact with nested sub-bullets."""
    parts: list[dict] = [
        {
            "type": "text",
            "text": {"content": contact.name},
            "annotations": {"bold": True},
        },
    ]
    if contact.title:
        parts.append({"type": "text", "text": {"content": f" — {contact.title}"}})
    if contact.linkedin:
        url = contact.linkedin
        display = (
            url.replace("https://www.", "")
            .replace("https://", "")
            .replace("http://", "")
        )
        parts.append({"type": "text", "text": {"content": " — "}})
        parts.append(
            {"type": "text", "text": {"content": display, "link": {"url": url}}}
        )

    block: dict = {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": parts},
    }

    children: list[dict] = []
    if contact.note:
        children.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"type": "text", "text": {"content": contact.note}},
                    ]
                },
            }
        )
    if contact.message:
        children.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": contact.message},
                            "annotations": {"italic": True},
                        },
                    ]
                },
            }
        )
    if children:
        block["bulleted_list_item"]["children"] = children

    return block


# ---------------------------------------------------------------------------
# NotionTracker
# ---------------------------------------------------------------------------


class NotionTracker:
    """Notion API tracker implementing TrackerBackend protocol."""

    def __init__(self, config: Config) -> None:
        if not config.notion_api_key:
            raise ValueError(
                "NOTION_API_KEY required for Notion tracker. "
                "Set it in .env, environment, or ~/.zshrc-secrets."
            )
        self._api_key = config.notion_api_key
        self._database_id = config.notion_database_id
        self._config = config

    # --- HTTP ---

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_API_VERSION,
        }

    def _request(
        self, method: str, url: str, payload: dict | None = None
    ) -> dict[str, Any]:
        """Send an HTTP request to the Notion API."""
        data = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(
            url, data=data, headers=self._headers(), method=method
        )

        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else ""
            message = error_body
            try:
                detail = json.loads(error_body)
                message = detail.get("message", error_body)
            except json.JSONDecodeError:
                pass
            raise NotionAPIError(exc.code, message, url) from exc
        except urllib.error.URLError as exc:
            raise NotionConnectionError(
                f"Could not reach Notion API: {exc.reason}"
            ) from exc

    # --- Property mapping (single source of truth) ---

    def _to_properties(
        self, app: Application, *, include_name: bool = True
    ) -> dict[str, Any]:
        """Build Notion properties dict from an Application.

        This is the ONE place that maps domain fields to Notion property names.
        The original script had this logic duplicated in 3 places.
        """
        props: dict[str, Any] = {}

        if include_name and app.name:
            props["Name"] = _title(app.name)
        if app.status:
            props["Status"] = _select(app.status.value)
        if app.start_date:
            props["Start Date"] = _date(app.start_date.isoformat())
        if app.url:
            props["URL"] = _rich_text(app.url)
        if app.position:
            props["Open Position"] = _rich_text(app.position)
        if app.environment:
            props["Environment"] = _multi_select(app.environment)
        if app.salary:
            props["Salary (Range)"] = _rich_text(app.salary)
        if app.focus:
            props["Company Focus"] = _multi_select(app.focus)
        if app.vision:
            props["Vision"] = _rich_text(app.vision)
        if app.mission:
            props["Mission"] = _rich_text(app.mission)
        if app.linkedin != LinkedInStatus.NA:
            props["Follow on Linkedin"] = _select(app.linkedin.value)
        if app.conclusion:
            props["Conclusion"] = _rich_text(app.conclusion)

        return props

    # --- Page lookup ---

    def _find_page(self, name: str) -> dict | None:
        """Query the database for a page matching company name."""
        payload = {
            "filter": {"property": "Name", "title": {"equals": name}},
            "page_size": 5,
        }
        url = f"{NOTION_BASE_URL}/databases/{self._database_id}/query"
        result = self._request("POST", url, payload)
        pages = [p for p in result.get("results", []) if not p.get("archived")]
        return pages[0] if pages else None

    def _resolve_page_id(self, app_id: str | None = None, name: str | None = None) -> str:
        """Resolve a page ID from either a direct ID or company name lookup."""
        if app_id:
            return app_id.replace("-", "")
        if name:
            page = self._find_page(name)
            if page:
                return page["id"]
            raise ValueError(f"No Notion page found for company '{name}'")
        raise ValueError("Either app_id or name is required")

    # --- Section management ---

    def _remove_section(self, page_id: str, heading_text: str) -> None:
        """Remove a heading section and its subsequent bullet items.

        Matches both heading_2 and heading_3 with case-insensitive text
        comparison, so it works with both template-created pages (heading_2,
        "Experience to highlight") and code-created pages (heading_3,
        "Experience to Highlight").
        """
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children?page_size=100"
        result = self._request("GET", url)
        blocks = result.get("results", [])

        ids_to_delete: list[str] = []
        in_section = False
        heading_lower = heading_text.lower()

        for block in blocks:
            block_type = block.get("type", "")
            if block_type in ("heading_2", "heading_3"):
                rt = block.get(block_type, {}).get("rich_text", [])
                text = rt[0].get("text", {}).get("content", "") if rt else ""
                if text.lower() == heading_lower:
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
            self._request("DELETE", f"{NOTION_BASE_URL}/blocks/{block_id}")

    def _append_section(
        self,
        page_id: str,
        heading: str,
        blocks: list[dict],
        heading_level: int = 3,
    ) -> None:
        """Remove then re-append a section with heading + blocks.

        Uses heading_3 by default to match the page body convention.
        """
        self._remove_section(page_id, heading)
        heading_block = (
            _heading2_block(heading) if heading_level == 2
            else _heading3_block(heading)
        )
        all_blocks = [heading_block] + blocks
        self._request(
            "PATCH",
            f"{NOTION_BASE_URL}/blocks/{page_id}/children",
            {"children": all_blocks},
        )

    # --- TrackerBackend protocol implementation ---

    def create(self, app: Application) -> str:
        """Create a tracker entry. Returns the Notion page ID.

        If a page with the same company name exists, updates it instead.
        New pages get template body scaffolding matching the "New Job
        Prospect" Notion template structure.
        """
        existing = self._find_page(app.name)
        if existing:
            page_id = existing["id"]
            props = self._to_properties(app, include_name=False)
            if props:
                self._request(
                    "PATCH",
                    f"{NOTION_BASE_URL}/pages/{page_id}",
                    {"properties": props},
                )
            if app.highlights:
                self.set_highlights(page_id, app.highlights)
            return page_id

        props = self._to_properties(app, include_name=True)
        if "Status" not in props:
            props["Status"] = _select(Status.TARGETED.value)

        payload = {
            "parent": {"database_id": self._database_id},
            "properties": props,
        }
        result = self._request("POST", f"{NOTION_BASE_URL}/pages", payload)
        page_id = result["id"]

        self._add_template_body(page_id, app)

        return page_id

    def _add_template_body(self, page_id: str, app: Application) -> None:
        """Add structured page body to a newly created page.

        Creates five heading_3 sections:
        1. Job Description — toggle (collapsible) with posting text
        2. Experience to Highlight — bulleted list
        3. Company Research — bulleted list
        4. Questions I Might Get Asked — bulleted list (Q + A sub-bullets)
        5. Questions To Ask In An Interview — bulleted list
        """
        blocks: list[dict] = []

        # 1. Job Description (toggle heading)
        if app.job_description:
            # Split into paragraphs for readability inside the toggle
            paragraphs = [
                p.strip() for p in app.job_description.split("\n\n") if p.strip()
            ]
            if not paragraphs:
                paragraphs = [app.job_description]
            children = [_paragraph_block(p) for p in paragraphs]
        else:
            children = [_paragraph_block("")]
        blocks.append(_toggle_heading3_block("Job Description", children))

        # 2. Experience to Highlight
        blocks.append(_heading3_block("Experience to Highlight"))
        if app.highlights:
            blocks.extend(_bullet_block(h) for h in app.highlights)
        else:
            blocks.append(_bullet_block(""))

        # 3. Company Research
        blocks.append(_heading3_block("Company Research"))
        if app.research:
            blocks.extend(_bullet_block(r) for r in app.research)
        else:
            blocks.append(_bullet_block(""))

        # 4. Questions I Might Get Asked (scaffolded empty)
        blocks.append(_heading3_block("Questions I Might Get Asked"))
        blocks.append(_bullet_block(""))

        # 5. Questions To Ask In An Interview
        blocks.append(_heading3_block("Questions To Ask In An Interview"))
        blocks.append(_bullet_block(""))

        self._request(
            "PATCH",
            f"{NOTION_BASE_URL}/blocks/{page_id}/children",
            {"children": blocks},
        )

    def update(self, app: Application) -> None:
        """Update an existing tracker entry."""
        if not app.page_id:
            raise ValueError("Application must have page_id set for update")
        page_id = app.page_id.replace("-", "")

        props = self._to_properties(app, include_name=True)
        if not props:
            raise ValueError("No properties to update")

        self._request(
            "PATCH",
            f"{NOTION_BASE_URL}/pages/{page_id}",
            {"properties": props},
        )

    def find_by_name(self, name: str) -> Application | None:
        """Find an application by company name."""
        page = self._find_page(name)
        if not page:
            return None
        return self._page_to_application(page)

    def set_highlights(self, app_id: str, highlights: list[str]) -> None:
        """Replace 'Experience to Highlight' section."""
        page_id = app_id.replace("-", "")
        blocks = [_bullet_block(h) for h in highlights]
        self._append_section(page_id, "Experience to Highlight", blocks)

    def set_research(self, app_id: str, research: list[str]) -> None:
        """Replace 'Company Research' section."""
        page_id = app_id.replace("-", "")
        blocks = [_bullet_block(r) for r in research]
        self._append_section(page_id, "Company Research", blocks)

    def set_contacts(self, app_id: str, contacts: list[Contact]) -> None:
        """Replace 'Outreach Contacts' section and set LinkedIn to 'No'."""
        page_id = app_id.replace("-", "")
        blocks = [_contact_bullet_block(c) for c in contacts]
        self._append_section(page_id, "Outreach Contacts", blocks)

        # Mark that contacts have been identified (follow-up pending)
        self._request(
            "PATCH",
            f"{NOTION_BASE_URL}/pages/{page_id}",
            {"properties": {"Follow on Linkedin": _select("No")}},
        )

    def set_interview_questions(
        self, app_id: str, questions: list[dict[str, str]]
    ) -> None:
        """Replace 'Questions I Might Get Asked' section.

        Each dict has 'question' and 'answer' keys. Rendered as a bullet
        for the question with a nested sub-bullet for the answer.
        """
        page_id = app_id.replace("-", "")
        blocks = [
            _qa_bullet_block(q["question"], q["answer"]) for q in questions
        ]
        self._append_section(page_id, "Questions I Might Get Asked", blocks)

    def set_questions_to_ask(self, app_id: str, questions: list[str]) -> None:
        """Replace 'Questions To Ask In An Interview' section."""
        page_id = app_id.replace("-", "")
        blocks = [_bullet_block(q) for q in questions]
        self._append_section(page_id, "Questions To Ask In An Interview", blocks)

    def list_all(self) -> list[Application]:
        """List all tracked applications."""
        url = f"{NOTION_BASE_URL}/databases/{self._database_id}/query"
        results: list[Application] = []
        payload: dict[str, Any] = {"page_size": 100}

        while True:
            response = self._request("POST", url, payload)
            for page in response.get("results", []):
                if not page.get("archived"):
                    results.append(self._page_to_application(page))

            if not response.get("has_more"):
                break
            payload["start_cursor"] = response["next_cursor"]

        return results

    # --- Page → Application mapping ---

    @staticmethod
    def _page_to_application(page: dict) -> Application:
        """Convert a Notion page object to an Application."""
        props = page.get("properties", {})

        def _get_title(prop_name: str) -> str:
            prop = props.get(prop_name, {})
            title_list = prop.get("title", [])
            return title_list[0].get("text", {}).get("content", "") if title_list else ""

        def _get_rich_text(prop_name: str) -> str:
            prop = props.get(prop_name, {})
            rt = prop.get("rich_text", [])
            return rt[0].get("text", {}).get("content", "") if rt else ""

        def _get_select(prop_name: str) -> str:
            prop = props.get(prop_name, {})
            sel = prop.get("select")
            return sel.get("name", "") if sel else ""

        def _get_multi_select(prop_name: str) -> list[str]:
            prop = props.get(prop_name, {})
            return [ms.get("name", "") for ms in prop.get("multi_select", [])]

        def _get_date(prop_name: str) -> date | None:
            prop = props.get(prop_name, {})
            d = prop.get("date")
            if d and d.get("start"):
                return date.fromisoformat(d["start"])
            return None

        status_str = _get_select("Status")
        try:
            status = Status(status_str)
        except ValueError:
            status = Status.TARGETED

        linkedin_str = _get_select("Follow on Linkedin")
        try:
            linkedin = LinkedInStatus(linkedin_str)
        except ValueError:
            linkedin = LinkedInStatus.NA

        return Application(
            name=_get_title("Name"),
            position=_get_rich_text("Open Position"),
            status=status,
            start_date=_get_date("Start Date"),
            url=_get_rich_text("URL"),
            environment=_get_multi_select("Environment"),
            salary=_get_rich_text("Salary (Range)"),
            focus=_get_multi_select("Company Focus"),
            vision=_get_rich_text("Vision"),
            mission=_get_rich_text("Mission"),
            linkedin=linkedin,
            conclusion=_get_rich_text("Conclusion"),
            page_id=page.get("id"),
        )

    # --- Queue processing ---

    def process_queue_file(self, filepath: str) -> dict[str, Any]:
        """Process a single queue JSON file. Returns a result dict.

        This replaces the old _process_queue_file() + _queue_* functions,
        routing through the same create/update/set_* methods above.
        """
        import os

        filename = os.path.basename(filepath)
        with open(filepath) as f:
            task = json.load(f)

        command = task.get("command")

        try:
            if command == "create":
                return self._queue_create(task, filename)
            elif command == "update":
                return self._queue_update(task, filename)
            elif command == "highlights":
                return self._queue_highlights(task, filename)
            elif command == "research":
                return self._queue_research(task, filename)
            elif command == "outreach":
                return self._queue_outreach(task, filename)
            elif command == "interview_questions":
                return self._queue_interview_questions(task, filename)
            elif command == "questions_to_ask":
                return self._queue_questions_to_ask(task, filename)
            else:
                return {
                    "file": filename,
                    "status": "error",
                    "message": f"Unknown command: {command}",
                }
        except Exception as exc:
            return {"file": filename, "status": "error", "message": str(exc)}

    def _queue_create(self, task: dict, filename: str) -> dict:
        app = self._task_to_application(task)
        page_id = self.create(app)
        page = self._find_page(app.name)
        url = page.get("url", "") if page else ""
        action = "updated_existing" if self._find_page(app.name) else "created"
        return {
            "file": filename,
            "status": "ok",
            "action": action,
            "page_id": page_id,
            "url": url,
        }

    def _queue_update(self, task: dict, filename: str) -> dict:
        page_id = task.get("page_id")
        if not page_id:
            raise ValueError("update command requires page_id")
        app = self._task_to_application(task)
        app.page_id = page_id
        self.update(app)
        return {
            "file": filename,
            "status": "ok",
            "action": "updated",
            "page_id": page_id.replace("-", ""),
        }

    def _queue_highlights(self, task: dict, filename: str) -> dict:
        page_id = task.get("page_id")
        if not page_id:
            raise ValueError("highlights command requires page_id")
        highlights = task.get("highlights", [])
        if not highlights:
            raise ValueError("highlights command requires highlights list")
        self.set_highlights(page_id, highlights)
        return {
            "file": filename,
            "status": "ok",
            "action": "highlights_replaced",
            "page_id": page_id.replace("-", ""),
        }

    def _queue_research(self, task: dict, filename: str) -> dict:
        page_id = self._resolve_page_id(
            task.get("page_id"), task.get("name")
        )
        research = task.get("research", [])
        if not research:
            raise ValueError("research command requires research list")
        self.set_research(page_id, research)
        return {
            "file": filename,
            "status": "ok",
            "action": "research_replaced",
            "page_id": page_id,
        }

    def _queue_outreach(self, task: dict, filename: str) -> dict:
        page_id = self._resolve_page_id(
            task.get("page_id"), task.get("name")
        )
        raw_contacts = task.get("contacts", [])
        if not raw_contacts:
            raise ValueError("outreach command requires contacts list")
        contacts = [
            Contact(
                name=c.get("name", ""),
                title=c.get("title", ""),
                linkedin=c.get("linkedin", ""),
                note=c.get("note", ""),
                message=c.get("message", ""),
            )
            for c in raw_contacts
        ]
        self.set_contacts(page_id, contacts)
        return {
            "file": filename,
            "status": "ok",
            "action": "outreach_replaced",
            "page_id": page_id,
        }

    def _queue_interview_questions(self, task: dict, filename: str) -> dict:
        page_id = self._resolve_page_id(
            task.get("page_id"), task.get("name")
        )
        questions = task.get("questions", [])
        if not questions:
            raise ValueError("interview_questions command requires questions list")
        self.set_interview_questions(page_id, questions)
        return {
            "file": filename,
            "status": "ok",
            "action": "interview_questions_replaced",
            "page_id": page_id,
        }

    def _queue_questions_to_ask(self, task: dict, filename: str) -> dict:
        page_id = self._resolve_page_id(
            task.get("page_id"), task.get("name")
        )
        questions = task.get("questions", [])
        if not questions:
            raise ValueError("questions_to_ask command requires questions list")
        self.set_questions_to_ask(page_id, questions)
        return {
            "file": filename,
            "status": "ok",
            "action": "questions_to_ask_replaced",
            "page_id": page_id,
        }

    @staticmethod
    def _task_to_application(task: dict) -> Application:
        """Convert a queue task JSON dict to an Application."""
        status = None
        if task.get("status"):
            try:
                status = Status(task["status"])
            except ValueError:
                status = Status.TARGETED

        start_date = None
        if task.get("date"):
            start_date = date.fromisoformat(task["date"])

        linkedin = LinkedInStatus.NA
        if task.get("linkedin"):
            try:
                linkedin = LinkedInStatus(task["linkedin"])
            except ValueError:
                pass

        return Application(
            name=task.get("name", ""),
            position=task.get("position", ""),
            status=status or Status.TARGETED,
            start_date=start_date,
            url=task.get("url", ""),
            environment=task.get("environment", []),
            salary=task.get("salary", ""),
            focus=task.get("focus", []),
            vision=task.get("vision", ""),
            mission=task.get("mission", ""),
            linkedin=linkedin,
            conclusion=task.get("conclusion", ""),
            highlights=task.get("highlights", []),
            job_description=task.get("job_description", ""),
            research=task.get("research", []),
        )
