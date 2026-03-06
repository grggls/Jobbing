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
from jobbing.models import Application, Contact, LinkedInStatus, ScoringResult, Status


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


def _number(value: int | float) -> dict:
    return {"number": value}


def _date(iso_date: str) -> dict:
    return {"date": {"start": iso_date}}


def _divider_block() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


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
        if app.scoring and app.scoring.score is not None:
            props["Score"] = _number(app.scoring.score)

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
        "Experience to Highlight"). Also matches SECTION_ALIASES so
        old heading names are cleaned up on rename.
        """
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children?page_size=100"
        result = self._request("GET", url)
        blocks = result.get("results", [])

        ids_to_delete: list[str] = []
        in_section = False
        heading_lower = heading_text.lower()
        # Also match old names that alias to this section
        match_set = {heading_lower}
        for alias_lower, canonical in self.SECTION_ALIASES.items():
            if canonical.lower() == heading_lower:
                match_set.add(alias_lower)

        for block in blocks:
            block_type = block.get("type", "")
            if block_type in ("heading_2", "heading_3"):
                rt = block.get(block_type, {}).get("rich_text", [])
                text = rt[0].get("text", {}).get("content", "") if rt else ""
                if text.lower() in match_set:
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
        toggle: bool = False,
    ) -> None:
        """Remove then re-append a section with heading + blocks.

        Uses heading_3 by default to match the page body convention.
        When toggle=True, uses a toggleable heading with blocks as children.
        """
        self._remove_section(page_id, heading)
        if toggle:
            all_blocks = [_toggle_heading3_block(heading, blocks)]
        else:
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

    # --- Managed section ordering ---
    # Canonical order for page body sections. Matches job application
    # chronology: discover → analyze → research → prepare → apply →
    # outreach → interview prep → interview.
    MANAGED_SECTIONS = [
        "Job Description",
        "Fit Assessment",
        "Company Research",
        "Experience to Highlight",
        "Outreach Contacts",
        "Questions I Might Get Asked",
        "Questions to Ask",
    ]

    # Old section names that should match their canonical replacements.
    # Used by _remove_all_managed_sections and _remove_section for
    # backward compatibility with pages created before renames.
    SECTION_ALIASES: dict[str, str] = {
        "questions to ask in an interview": "Questions to Ask",
        "questions to ask during an interview": "Questions to Ask",
    }

    def _read_existing_sections(self, page_id: str) -> dict[str, Any]:
        """Read existing managed-section content from the page.

        Returns a dict keyed by canonical section name. Values depend on
        section type:
          - "Job Description" → str (paragraphs joined by \\n\\n)
          - "Company Research" / "Experience to Highlight" → list[str]
          - "Questions I Might Get Asked" → list[dict] with "question"/"answer"
          - "Questions to Ask" → list[str]
          - "Outreach Contacts" → list[str] (plain-text fallback)

        Resolves SECTION_ALIASES so old heading names map to canonical keys.
        For toggle heading_3 blocks, fetches children via the API.
        For flat heading_2 blocks, collects sibling bullets.
        """
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children?page_size=100"
        result = self._request("GET", url)
        blocks = result.get("results", [])

        # Build lookup: lowercased heading → canonical name
        managed_lower = {s.lower(): s for s in self.MANAGED_SECTIONS}
        for alias_lower, canonical in self.SECTION_ALIASES.items():
            managed_lower[alias_lower] = canonical
        existing: dict[str, Any] = {}

        # Track flat heading_2 sections (non-toggle)
        in_flat_section: str | None = None
        flat_bullets: list[str] = []

        def _flush_flat():
            nonlocal in_flat_section, flat_bullets
            if in_flat_section and flat_bullets:
                existing[in_flat_section] = flat_bullets
            in_flat_section = None
            flat_bullets = []

        for block in blocks:
            block_type = block.get("type", "")
            if block_type in ("heading_2", "heading_3"):
                _flush_flat()
                rt = block.get(block_type, {}).get("rich_text", [])
                text = rt[0].get("text", {}).get("content", "") if rt else ""
                canonical = managed_lower.get(text.lower())
                if not canonical:
                    continue

                is_toggle = block.get(block_type, {}).get("is_toggleable", False)
                has_children = block.get("has_children", False)

                if is_toggle and has_children:
                    # Read toggle children from API
                    children_url = (
                        f"{NOTION_BASE_URL}/blocks/{block['id']}"
                        f"/children?page_size=100"
                    )
                    children = self._request("GET", children_url).get(
                        "results", []
                    )
                    existing[canonical] = self._parse_section_children(
                        canonical, children
                    )
                elif not is_toggle:
                    # Flat heading — collect sibling bullets
                    in_flat_section = canonical
                    flat_bullets = []
            elif in_flat_section:
                if block_type == "bulleted_list_item":
                    rt = block.get("bulleted_list_item", {}).get(
                        "rich_text", []
                    )
                    text = "".join(
                        seg.get("text", {}).get("content", "")
                        for seg in rt
                    )
                    if text:
                        flat_bullets.append(text)
                else:
                    _flush_flat()

        _flush_flat()
        return existing

    @staticmethod
    def _parse_section_children(
        section_name: str, children: list[dict]
    ) -> Any:
        """Parse toggle children into the appropriate Python structure."""
        if section_name == "Job Description":
            paragraphs: list[str] = []
            for child in children:
                if child.get("type") == "paragraph":
                    rt = child.get("paragraph", {}).get("rich_text", [])
                    text = "".join(
                        seg.get("text", {}).get("content", "")
                        for seg in rt
                    )
                    if text:
                        paragraphs.append(text)
            return "\n\n".join(paragraphs) if paragraphs else ""

        if section_name == "Questions I Might Get Asked":
            qa_list: list[dict[str, str]] = []
            for child in children:
                if child.get("type") == "bulleted_list_item":
                    rt = child.get("bulleted_list_item", {}).get(
                        "rich_text", []
                    )
                    question = "".join(
                        seg.get("text", {}).get("content", "")
                        for seg in rt
                    )
                    if not question:
                        continue
                    # Try to get nested answer sub-bullet
                    answer = ""
                    if child.get("has_children"):
                        # Sub-bullets are included in the block response
                        # only if fetched separately — we have toggle
                        # children already, but sub-bullets need another fetch
                        pass  # Answer extraction handled below
                    qa_list.append({"question": question, "answer": answer})
            return qa_list if qa_list else []

        # Default: bulleted list → list[str]
        items: list[str] = []
        for child in children:
            if child.get("type") == "bulleted_list_item":
                rt = child.get("bulleted_list_item", {}).get("rich_text", [])
                text = "".join(
                    seg.get("text", {}).get("content", "")
                    for seg in rt
                )
                if text:
                    items.append(text)
        return items

    def _remove_all_managed_sections(self, page_id: str) -> None:
        """Remove all managed sections from the page in one pass.

        Handles both toggle heading_3 (code-created) and flat heading_2
        (Notion template) sections with case-insensitive matching.
        Also removes sections matching SECTION_ALIASES (old heading names).
        """
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children?page_size=100"
        result = self._request("GET", url)
        blocks = result.get("results", [])

        managed_lower = {s.lower() for s in self.MANAGED_SECTIONS}
        managed_lower.update(self.SECTION_ALIASES.keys())
        ids_to_delete: list[str] = []
        in_flat_section = False

        for block in blocks:
            block_type = block.get("type", "")
            # Remove divider blocks (visual separator before managed sections)
            if block_type == "divider":
                ids_to_delete.append(block["id"])
                continue
            if block_type in ("heading_2", "heading_3"):
                rt = block.get(block_type, {}).get("rich_text", [])
                text = rt[0].get("text", {}).get("content", "") if rt else ""
                if text.lower() in managed_lower:
                    in_flat_section = True
                    ids_to_delete.append(block["id"])
                    continue
                else:
                    in_flat_section = False
            elif in_flat_section:
                # Sibling blocks under a flat heading_2 (non-toggle)
                if block_type == "bulleted_list_item":
                    ids_to_delete.append(block["id"])
                else:
                    in_flat_section = False

        for block_id in ids_to_delete:
            self._request("DELETE", f"{NOTION_BASE_URL}/blocks/{block_id}")

    # --- TrackerBackend protocol implementation ---

    def create(self, app: Application) -> tuple[str, list[str]]:
        """Create or update a tracker entry. Idempotent.

        Returns (page_id, sections_written) where sections_written lists
        what was actually written (e.g. ["properties", "highlights", "research"]).

        If a page with the same company name exists:
        1. Reads existing section content
        2. Merges: new data wins, existing data preserved where JSON is silent
        3. Removes all managed sections + rebuilds in canonical order

        New pages get template body scaffolding + an inline Interviews
        database.
        """
        existing = self._find_page(app.name)
        if existing:
            page_id = existing["id"]
            sections: list[str] = []
            props = self._to_properties(app, include_name=False)
            if props:
                self._request(
                    "PATCH",
                    f"{NOTION_BASE_URL}/pages/{page_id}",
                    {"properties": props},
                )
                sections.append("properties")
            # Read existing content BEFORE removal — preserve data for
            # sections the current JSON doesn't include.
            preserved = self._read_existing_sections(page_id)
            if not app.job_description and preserved.get("Job Description"):
                app.job_description = preserved["Job Description"]
            if not app.research and preserved.get("Company Research"):
                app.research = preserved["Company Research"]
            if not app.highlights and preserved.get("Experience to Highlight"):
                app.highlights = preserved["Experience to Highlight"]
            # Scoring and questions are not directly reconstructable from
            # preserved bullet text — pass through to _add_template_body
            # via the preserved dict.

            # Remove all managed sections, rebuild in canonical order.
            self._remove_all_managed_sections(page_id)
            self._add_template_body(page_id, app, preserved=preserved)
            sections.append("template_body")
            if app.highlights:
                sections.append("highlights")
            if app.research:
                sections.append("research")
            if app.job_description:
                sections.append("job_description")
            return page_id, sections

        props = self._to_properties(app, include_name=True)
        if "Status" not in props:
            props["Status"] = _select(Status.TARGETED.value)

        payload = {
            "parent": {"database_id": self._database_id},
            "properties": props,
        }
        result = self._request("POST", f"{NOTION_BASE_URL}/pages", payload)
        page_id = result["id"]

        # New page: add interviews database + template body
        self._add_interviews_database(page_id)
        self._add_template_body(page_id, app)

        sections = ["properties", "interviews_db", "template_body"]
        if app.highlights:
            sections.append("highlights")
        if app.research:
            sections.append("research")
        if app.job_description:
            sections.append("job_description")
        return page_id, sections

    def _add_template_body(
        self,
        page_id: str,
        app: Application,
        preserved: dict[str, Any] | None = None,
    ) -> None:
        """Add structured page body with five heading_3 toggle sections.

        When *preserved* is provided (update-existing path), any section
        without new data in *app* uses the preserved content instead of
        creating an empty placeholder. This prevents data loss on rebuild.
        """
        preserved = preserved or {}
        blocks: list[dict] = []

        # Visual separator between Interviews DB and content sections
        blocks.append(_divider_block())

        # 1. Job Description (toggle heading)
        if app.job_description:
            paragraphs = [
                p.strip() for p in app.job_description.split("\n\n") if p.strip()
            ]
            if not paragraphs:
                paragraphs = [app.job_description]
            children = [_paragraph_block(p) for p in paragraphs]
        else:
            children = [_paragraph_block("")]
        blocks.append(_toggle_heading3_block("Job Description", children))

        # 2. Fit Assessment
        if app.scoring:
            children = self._scoring_result_blocks(app.scoring)
        elif preserved.get("Fit Assessment"):
            items = preserved["Fit Assessment"]
            if isinstance(items, list):
                children = [_bullet_block(item) for item in items if item]
            else:
                children = [_paragraph_block(str(items))]
            if not children:
                children = [_paragraph_block("")]
        else:
            children = [_paragraph_block("")]
        blocks.append(_toggle_heading3_block("Fit Assessment", children))

        # 3. Company Research
        if app.research:
            children = [_bullet_block(r) for r in app.research]
        else:
            children = [_bullet_block("")]
        blocks.append(_toggle_heading3_block("Company Research", children))

        # 4. Experience to Highlight
        if app.highlights:
            children = [_bullet_block(h) for h in app.highlights]
        else:
            children = [_bullet_block("")]
        blocks.append(_toggle_heading3_block("Experience to Highlight", children))

        # 5. Outreach Contacts — use preserved if available
        contact_items = preserved.get("Outreach Contacts", [])
        if contact_items and isinstance(contact_items, list):
            children = [_bullet_block(c) for c in contact_items if c]
        else:
            children = []
        if not children:
            children = [_bullet_block("")]
        blocks.append(
            _toggle_heading3_block("Outreach Contacts", children)
        )

        # 6. Questions I Might Get Asked — use preserved Q&A if available
        qa_items = preserved.get("Questions I Might Get Asked", [])
        if qa_items and isinstance(qa_items, list) and isinstance(qa_items[0], dict):
            children = [
                _qa_bullet_block(q.get("question", ""), q.get("answer", ""))
                for q in qa_items
                if q.get("question")
            ]
        elif qa_items and isinstance(qa_items, list):
            children = [_bullet_block(q) for q in qa_items if q]
        else:
            children = []
        if not children:
            children = [_bullet_block("")]
        blocks.append(
            _toggle_heading3_block("Questions I Might Get Asked", children)
        )

        # 7. Questions to Ask — use preserved if available
        ask_items = preserved.get("Questions to Ask", [])
        if ask_items and isinstance(ask_items, list):
            children = [_bullet_block(q) for q in ask_items if q]
        else:
            children = []
        if not children:
            children = [_bullet_block("")]
        blocks.append(
            _toggle_heading3_block("Questions to Ask", children)
        )

        self._request(
            "PATCH",
            f"{NOTION_BASE_URL}/blocks/{page_id}/children",
            {"children": blocks},
        )

    def _add_interviews_database(self, page_id: str) -> None:
        """Create an inline 'Interviews' child database on the page.

        Schema matches the Goldie Tech reference page:
        - Interviewer Name and Role (title property)
        - Date (date property)
        """
        self._request(
            "POST",
            f"{NOTION_BASE_URL}/databases",
            {
                "parent": {"type": "page_id", "page_id": page_id},
                "title": [{"type": "text", "text": {"content": "Interviews"}}],
                "is_inline": True,
                "properties": {
                    "Interviewer Name and Role": {"title": {}},
                    "Date": {"date": {}},
                },
            },
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
        self._append_section(page_id, "Experience to Highlight", blocks, toggle=True)

    def set_research(self, app_id: str, research: list[str]) -> None:
        """Replace 'Company Research' section."""
        page_id = app_id.replace("-", "")
        blocks = [_bullet_block(r) for r in research]
        self._append_section(page_id, "Company Research", blocks, toggle=True)

    def set_contacts(self, app_id: str, contacts: list[Contact]) -> None:
        """Replace 'Outreach Contacts' section and set LinkedIn to 'No'."""
        page_id = app_id.replace("-", "")
        blocks = [_contact_bullet_block(c) for c in contacts]
        self._append_section(page_id, "Outreach Contacts", blocks, toggle=True)

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
        self._append_section(page_id, "Questions I Might Get Asked", blocks, toggle=True)

    def set_job_description(self, app_id: str, job_description: str) -> None:
        """Replace 'Job Description' toggle section with posting text."""
        page_id = app_id.replace("-", "")
        paragraphs = [
            p.strip() for p in job_description.split("\n\n") if p.strip()
        ]
        if not paragraphs:
            paragraphs = [job_description]
        blocks = [_paragraph_block(p) for p in paragraphs]
        self._append_section(page_id, "Job Description", blocks, toggle=True)

    def set_fit_assessment(self, app_id: str, scoring: ScoringResult) -> None:
        """Replace 'Fit Assessment' section and update Score property."""
        page_id = app_id.replace("-", "")
        blocks = self._scoring_result_blocks(scoring)
        self._append_section(page_id, "Fit Assessment", blocks, toggle=True)
        # Also update the Score number property
        self._request(
            "PATCH",
            f"{NOTION_BASE_URL}/pages/{page_id}",
            {"properties": {"Score": _number(scoring.score)}},
        )

    @staticmethod
    def _scoring_result_blocks(scoring: ScoringResult) -> list[dict]:
        """Build Notion blocks from a ScoringResult for the Fit Assessment section."""
        blocks: list[dict] = []
        blocks.append(_paragraph_block(f"Score: {scoring.score}/100"))
        if scoring.reasoning:
            blocks.append(_paragraph_block(scoring.reasoning))
        if scoring.green_flags:
            blocks.append(_paragraph_block("Green flags:"))
            for flag in scoring.green_flags:
                blocks.append(_bullet_block(flag))
        if scoring.red_flags:
            blocks.append(_paragraph_block("Red flags:"))
            for flag in scoring.red_flags:
                blocks.append(_bullet_block(flag))
        if scoring.gaps:
            blocks.append(_paragraph_block("Gaps:"))
            for gap in scoring.gaps:
                blocks.append(_bullet_block(gap))
        if scoring.keywords_missing:
            blocks.append(_paragraph_block("Keywords to weave in:"))
            for kw in scoring.keywords_missing:
                blocks.append(_bullet_block(kw))
        return blocks

    def set_questions_to_ask(self, app_id: str, questions: list[str]) -> None:
        """Replace 'Questions to Ask' section."""
        page_id = app_id.replace("-", "")
        blocks = [_bullet_block(q) for q in questions]
        self._append_section(page_id, "Questions to Ask", blocks, toggle=True)

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
            elif command == "job_description":
                return self._queue_job_description(task, filename)
            elif command == "fit_assessment":
                return self._queue_fit_assessment(task, filename)
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
        was_existing = self._find_page(app.name) is not None
        page_id, sections_written = self.create(app)
        page = self._find_page(app.name)
        url = page.get("url", "") if page else ""
        action = "updated_existing" if was_existing else "created"
        return {
            "file": filename,
            "status": "ok",
            "action": action,
            "page_id": page_id,
            "url": url,
            "sections_written": sections_written,
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

    def _queue_job_description(self, task: dict, filename: str) -> dict:
        page_id = self._resolve_page_id(
            task.get("page_id"), task.get("name")
        )
        job_description = task.get("job_description", "")
        if not job_description:
            raise ValueError("job_description command requires job_description text")
        self.set_job_description(page_id, job_description)
        return {
            "file": filename,
            "status": "ok",
            "action": "job_description_replaced",
            "page_id": page_id,
        }

    def _queue_fit_assessment(self, task: dict, filename: str) -> dict:
        page_id = self._resolve_page_id(
            task.get("page_id"), task.get("name")
        )
        scoring = self._task_to_scoring_result(task)
        self.set_fit_assessment(page_id, scoring)
        return {
            "file": filename,
            "status": "ok",
            "action": "fit_assessment_replaced",
            "page_id": page_id,
        }

    @staticmethod
    def _task_to_scoring_result(task: dict) -> ScoringResult:
        """Convert a queue task JSON dict to a ScoringResult."""
        return ScoringResult(
            score=task.get("score", 0),
            reasoning=task.get("reasoning", ""),
            green_flags=task.get("green_flags", []),
            red_flags=task.get("red_flags", []),
            gaps=task.get("gaps", []),
            keywords_missing=task.get("keywords_missing", []),
        )

    @staticmethod
    def _task_to_application(task: dict) -> Application:
        """Convert a queue task JSON dict to an Application."""
        status = None
        if task.get("status"):
            try:
                status = Status(task["status"])
            except ValueError:
                status = None

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
            status=status,
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
            scoring=ScoringResult(
                score=task["score"],
                reasoning=task.get("reasoning", ""),
                green_flags=task.get("green_flags", []),
                red_flags=task.get("red_flags", []),
                gaps=task.get("gaps", []),
                keywords_missing=task.get("keywords_missing", []),
            ) if task.get("score") is not None else None,
        )
