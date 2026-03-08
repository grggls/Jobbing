"""Comprehensive tests for NotionTracker.

Mocks at the _request level to avoid real HTTP calls while testing
all class methods, error paths, and edge cases.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from jobbing.config import Config
from jobbing.models import (
    Application,
    Contact,
    Interview,
    LinkedInStatus,
    ScoringResult,
    Status,
)
from jobbing.tracker.notion import (
    NotionAPIError,
    NotionConnectionError,
    NotionTracker,
    _bullet_block,
    _contact_bullet_block,
    _date,
    _divider_block,
    _heading2_block,
    _heading3_block,
    _markdown_to_blocks,
    _multi_select,
    _number,
    _paragraph_block,
    _parse_inline_markdown,
    _qa_bullet_block,
    _rich_text,
    _select,
    _title,
    _toggle_heading3_block,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Path) -> Config:
    """Build a Config with a fake API key for testing."""
    return Config(
        project_dir=tmp_path,
        notion_api_key="test-secret-key",
        notion_database_id="db-123",
    )


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "companies").mkdir()
    (tmp_path / "notion_queue").mkdir()
    (tmp_path / "notion_queue_results").mkdir()
    return tmp_path


@pytest.fixture()
def config(tmp_project: Path) -> Config:
    return _make_config(tmp_project)


@pytest.fixture()
def tracker(config: Config) -> NotionTracker:
    return NotionTracker(config)


def _notion_page(
    page_id: str = "page-abc",
    name: str = "Acme Corp",
    status: str = "Targeted",
    position: str = "Senior Engineer",
    url: str = "",
    archived: bool = False,
) -> dict[str, Any]:
    """Build a realistic Notion page response."""
    return {
        "id": page_id,
        "archived": archived,
        "url": f"https://notion.so/{page_id}",
        "properties": {
            "Name": {"title": [{"text": {"content": name}}]},
            "Status": {"select": {"name": status}},
            "Open Position": {"rich_text": [{"text": {"content": position}}]},
            "URL": {"rich_text": [{"text": {"content": url}}] if url else []},
            "Start Date": {"date": {"start": "2026-01-15"}},
            "Environment": {"multi_select": [{"name": "Remote"}]},
            "Salary (Range)": {"rich_text": [{"text": {"content": "120-150k"}}]},
            "Company Focus": {"multi_select": [{"name": "Climate"}]},
            "Vision": {"rich_text": [{"text": {"content": "Save the planet"}}]},
            "Mission": {"rich_text": [{"text": {"content": "Green tech"}}]},
            "Follow on Linkedin": {"select": {"name": "No"}},
            "Conclusion": {"rich_text": []},
            "Score": {"number": 75},
        },
    }


def _empty_blocks_response() -> dict[str, Any]:
    return {"results": []}


def _toggle_section_block(
    block_id: str,
    heading_text: str,
    has_children: bool = True,
    is_toggleable: bool = True,
) -> dict[str, Any]:
    return {
        "id": block_id,
        "type": "heading_3",
        "has_children": has_children,
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": heading_text}}],
            "is_toggleable": is_toggleable,
        },
    }


# ---------------------------------------------------------------------------
# Pure function tests (no mocking needed)
# ---------------------------------------------------------------------------


class TestPropertyBuilders:
    """Tests for the pure Notion property/block builder functions."""

    def test_title(self) -> None:
        result = _title("Hello")
        assert result == {"title": [{"text": {"content": "Hello"}}]}

    def test_rich_text(self) -> None:
        result = _rich_text("some text")
        assert result == {"rich_text": [{"text": {"content": "some text"}}]}

    def test_select(self) -> None:
        result = _select("Applied")
        assert result == {"select": {"name": "Applied"}}

    def test_multi_select(self) -> None:
        result = _multi_select(["A", "B"])
        assert result == {"multi_select": [{"name": "A"}, {"name": "B"}]}

    def test_number(self) -> None:
        assert _number(42) == {"number": 42}
        assert _number(3.14) == {"number": 3.14}

    def test_date(self) -> None:
        assert _date("2026-03-08") == {"date": {"start": "2026-03-08"}}

    def test_divider_block(self) -> None:
        result = _divider_block()
        assert result["type"] == "divider"
        assert result["object"] == "block"

    def test_heading2_block(self) -> None:
        result = _heading2_block("Title")
        assert result["type"] == "heading_2"
        assert result["heading_2"]["rich_text"][0]["text"]["content"] == "Title"

    def test_heading3_block(self) -> None:
        result = _heading3_block("Subtitle")
        assert result["type"] == "heading_3"
        assert result["heading_3"]["rich_text"][0]["text"]["content"] == "Subtitle"

    def test_paragraph_block_plain(self) -> None:
        result = _paragraph_block("Hello world")
        assert result["type"] == "paragraph"
        assert result["paragraph"]["rich_text"][0]["text"]["content"] == "Hello world"

    def test_bullet_block(self) -> None:
        result = _bullet_block("item one")
        assert result["type"] == "bulleted_list_item"

    def test_toggle_heading3_block(self) -> None:
        child = _paragraph_block("inner")
        result = _toggle_heading3_block("Toggle Me", [child])
        assert result["type"] == "heading_3"
        assert result["heading_3"]["is_toggleable"] is True
        assert len(result["heading_3"]["children"]) == 1

    def test_qa_bullet_block(self) -> None:
        result = _qa_bullet_block("Q?", "A.")
        assert result["type"] == "bulleted_list_item"
        children = result["bulleted_list_item"]["children"]
        assert len(children) == 1
        assert children[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "A."


class TestParseInlineMarkdown:
    """Tests for _parse_inline_markdown."""

    def test_plain_text(self) -> None:
        segments = _parse_inline_markdown("no formatting here")
        assert len(segments) == 1
        assert segments[0]["text"]["content"] == "no formatting here"

    def test_bold(self) -> None:
        segments = _parse_inline_markdown("this is **bold** text")
        assert len(segments) == 3
        assert segments[1]["annotations"]["bold"] is True
        assert segments[1]["text"]["content"] == "bold"

    def test_italic(self) -> None:
        segments = _parse_inline_markdown("this is *italic* text")
        assert len(segments) == 3
        assert segments[1]["annotations"]["italic"] is True
        assert segments[1]["text"]["content"] == "italic"

    def test_mixed_bold_and_italic(self) -> None:
        segments = _parse_inline_markdown("**bold** and *italic*")
        bold_segs = [s for s in segments if s.get("annotations", {}).get("bold")]
        italic_segs = [s for s in segments if s.get("annotations", {}).get("italic")]
        assert len(bold_segs) == 1
        assert len(italic_segs) == 1

    def test_empty_string(self) -> None:
        segments = _parse_inline_markdown("")
        assert len(segments) == 1
        assert segments[0]["text"]["content"] == ""


class TestContactBulletBlock:
    """Tests for _contact_bullet_block."""

    def test_full_contact(self) -> None:
        contact = Contact(
            name="Jane",
            title="VP Eng",
            linkedin="https://www.linkedin.com/in/jane",
            note="Key person",
            message="Hi Jane",
        )
        result = _contact_bullet_block(contact)
        assert result["type"] == "bulleted_list_item"
        rt = result["bulleted_list_item"]["rich_text"]
        assert rt[0]["annotations"]["bold"] is True
        assert rt[0]["text"]["content"] == "Jane"
        children = result["bulleted_list_item"]["children"]
        assert len(children) == 2

    def test_minimal_contact(self) -> None:
        contact = Contact(name="Bob", title="", linkedin="")
        result = _contact_bullet_block(contact)
        assert "children" not in result["bulleted_list_item"]

    def test_contact_with_note_only(self) -> None:
        contact = Contact(name="Alice", title="CTO", linkedin="", note="Met at conf")
        result = _contact_bullet_block(contact)
        children = result["bulleted_list_item"]["children"]
        assert len(children) == 1


class TestMarkdownToBlocks:
    """Tests for _markdown_to_blocks."""

    def test_heading1(self) -> None:
        blocks = _markdown_to_blocks("# Big Title")
        assert blocks[0]["type"] == "heading_2"

    def test_heading2(self) -> None:
        blocks = _markdown_to_blocks("## Section")
        assert blocks[0]["type"] == "heading_3"

    def test_heading3(self) -> None:
        blocks = _markdown_to_blocks("### Sub Section")
        assert blocks[0]["type"] == "heading_3"

    def test_bullet(self) -> None:
        blocks = _markdown_to_blocks("- item one\n- item two")
        assert len(blocks) == 2
        assert all(b["type"] == "bulleted_list_item" for b in blocks)

    def test_nested_bullet(self) -> None:
        blocks = _markdown_to_blocks("- parent\n  - child")
        assert len(blocks) == 1
        children = blocks[0]["bulleted_list_item"].get("children", [])
        assert len(children) == 1

    def test_paragraph(self) -> None:
        blocks = _markdown_to_blocks("Just a paragraph.")
        assert blocks[0]["type"] == "paragraph"

    def test_blank_lines_separate_paragraphs(self) -> None:
        blocks = _markdown_to_blocks("First paragraph\n\nSecond paragraph")
        assert len(blocks) == 2
        assert all(b["type"] == "paragraph" for b in blocks)

    def test_mixed_content(self) -> None:
        md = "# Title\n\nSome text\n\n- bullet\n  - nested\n\n## Section\n\nMore text"
        blocks = _markdown_to_blocks(md)
        types = [b["type"] for b in blocks]
        assert "heading_2" in types
        assert "heading_3" in types
        assert "paragraph" in types
        assert "bulleted_list_item" in types

    def test_empty_string(self) -> None:
        blocks = _markdown_to_blocks("")
        assert blocks == []

    def test_indented_bullet_without_parent(self) -> None:
        # Indented bullet with no preceding bullet should just be added as a block
        blocks = _markdown_to_blocks("  - orphan child")
        assert len(blocks) == 1


# ---------------------------------------------------------------------------
# NotionTracker init / headers
# ---------------------------------------------------------------------------


class TestInit:
    """Tests for NotionTracker.__init__ and _headers."""

    def test_init_with_valid_config(self, config: Config) -> None:
        tracker = NotionTracker(config)
        assert tracker._api_key == "test-secret-key"
        assert tracker._database_id == "db-123"

    def test_init_missing_api_key(self, tmp_project: Path) -> None:
        cfg = Config(project_dir=tmp_project, notion_api_key="", notion_database_id="db-x")
        with pytest.raises(ValueError, match="NOTION_API_KEY required"):
            NotionTracker(cfg)

    def test_headers(self, tracker: NotionTracker) -> None:
        headers = tracker._headers()
        assert headers["Authorization"] == "Bearer test-secret-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["Notion-Version"] == "2022-06-28"


# ---------------------------------------------------------------------------
# _to_properties
# ---------------------------------------------------------------------------


class TestToProperties:
    """Tests for the _to_properties mapping method."""

    def test_full_application(self, tracker: NotionTracker) -> None:
        app = Application(
            name="TestCo",
            position="CTO",
            status=Status.APPLIED,
            start_date=date(2026, 3, 1),
            url="https://example.com",
            environment=["Remote", "Hybrid"],
            salary="150-200k",
            focus=["AI"],
            vision="Build AGI",
            mission="Advance science",
            linkedin=LinkedInStatus.YES,
            conclusion="Offer accepted",
            scoring=ScoringResult(score=85, reasoning="Great fit"),
        )
        props = tracker._to_properties(app, include_name=True)
        assert "Name" in props
        assert props["Status"] == {"select": {"name": "Applied"}}
        assert props["Score"] == {"number": 85}
        assert props["Open Position"] == {"rich_text": [{"text": {"content": "CTO"}}]}

    def test_exclude_name(self, tracker: NotionTracker) -> None:
        app = Application(name="TestCo", status=Status.TARGETED)
        props = tracker._to_properties(app, include_name=False)
        assert "Name" not in props

    def test_empty_application(self, tracker: NotionTracker) -> None:
        app = Application(name="")
        props = tracker._to_properties(app, include_name=True)
        # Name is empty so not included
        assert "Name" not in props

    def test_linkedin_na_excluded(self, tracker: NotionTracker) -> None:
        app = Application(name="Co", linkedin=LinkedInStatus.NA)
        props = tracker._to_properties(app, include_name=True)
        assert "Follow on Linkedin" not in props


# ---------------------------------------------------------------------------
# _resolve_page_id
# ---------------------------------------------------------------------------


class TestResolvePageId:
    """Tests for _resolve_page_id."""

    def test_with_direct_id(self, tracker: NotionTracker) -> None:
        result = tracker._resolve_page_id(app_id="abc-def-123")
        assert result == "abcdef123"

    def test_with_name_found(self, tracker: NotionTracker) -> None:
        with patch.object(
            tracker,
            "_find_page",
            return_value={"id": "found-page-id"},
        ):
            result = tracker._resolve_page_id(name="Acme")
            assert result == "found-page-id"

    def test_with_name_not_found(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_find_page", return_value=None):
            with pytest.raises(ValueError, match="No Notion page found"):
                tracker._resolve_page_id(name="Ghost Corp")

    def test_neither_id_nor_name(self, tracker: NotionTracker) -> None:
        with pytest.raises(ValueError, match="Either app_id or name is required"):
            tracker._resolve_page_id()

    def test_id_takes_precedence(self, tracker: NotionTracker) -> None:
        """When both app_id and name are given, app_id wins."""
        result = tracker._resolve_page_id(app_id="direct-id", name="Ignored")
        assert result == "directid"


# ---------------------------------------------------------------------------
# _find_page
# ---------------------------------------------------------------------------


class TestFindPage:
    """Tests for _find_page database query."""

    def test_found(self, tracker: NotionTracker) -> None:
        page = _notion_page()
        with patch.object(tracker, "_request", return_value={"results": [page]}):
            result = tracker._find_page("Acme Corp")
            assert result is not None
            assert result["id"] == "page-abc"

    def test_not_found(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request", return_value={"results": []}):
            assert tracker._find_page("Nobody") is None

    def test_skips_archived(self, tracker: NotionTracker) -> None:
        page = _notion_page(archived=True)
        with patch.object(tracker, "_request", return_value={"results": [page]}):
            assert tracker._find_page("Acme Corp") is None


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestCreate:
    """Tests for the create method."""

    def test_create_new_page(self, tracker: NotionTracker) -> None:
        new_page = {"id": "new-page-1"}
        with (
            patch.object(tracker, "_find_page", return_value=None),
            patch.object(
                tracker,
                "_request",
                return_value=new_page,
            ),
            patch.object(tracker, "_add_interviews_database") as mock_interviews,
            patch.object(tracker, "_add_template_body") as mock_body,
        ):
            app = Application(name="NewCo", position="SWE")
            page_id, sections = tracker.create(app)

            assert page_id == "new-page-1"
            assert "properties" in sections
            assert "interviews_db" in sections
            assert "template_body" in sections
            mock_interviews.assert_called_once_with("new-page-1")
            mock_body.assert_called_once()

    def test_create_sets_default_status(self, tracker: NotionTracker) -> None:
        """New pages without explicit status get Targeted."""
        with (
            patch.object(tracker, "_find_page", return_value=None),
            patch.object(
                tracker,
                "_request",
                return_value={"id": "p1"},
            ) as mock_req,
            patch.object(tracker, "_add_interviews_database"),
            patch.object(tracker, "_add_template_body"),
        ):
            app = Application(name="Co")
            tracker.create(app)
            # The POST call to create the page
            create_call = mock_req.call_args_list[0]
            payload = create_call[0][2]  # third positional arg
            assert payload["properties"]["Status"] == {"select": {"name": "Targeted"}}

    def test_create_updates_existing(self, tracker: NotionTracker) -> None:
        existing = _notion_page(page_id="existing-1")
        with (
            patch.object(tracker, "_find_page", return_value=existing),
            patch.object(tracker, "_request", return_value={}),
            patch.object(
                tracker,
                "_read_existing_sections",
                return_value={},
            ),
            patch.object(tracker, "_remove_all_managed_sections"),
            patch.object(tracker, "_add_template_body"),
        ):
            app = Application(name="Acme Corp", position="Lead")
            page_id, sections = tracker.create(app)
            assert page_id == "existing-1"
            assert "properties" in sections
            assert "template_body" in sections

    def test_create_preserves_existing_data(self, tracker: NotionTracker) -> None:
        existing = _notion_page(page_id="existing-2")
        preserved = {
            "Job Description": "Old JD text",
            "Company Research": ["Research item 1"],
            "Experience to Highlight": ["Highlight 1"],
        }
        with (
            patch.object(tracker, "_find_page", return_value=existing),
            patch.object(tracker, "_request", return_value={}),
            patch.object(tracker, "_read_existing_sections", return_value=preserved),
            patch.object(tracker, "_remove_all_managed_sections"),
            patch.object(tracker, "_add_template_body"),
        ):
            app = Application(name="Acme Corp")
            page_id, sections = tracker.create(app)
            # Application should have been enriched from preserved data
            assert app.job_description == "Old JD text"
            assert app.research == ["Research item 1"]
            assert app.highlights == ["Highlight 1"]
            assert "job_description" in sections
            assert "research" in sections
            assert "highlights" in sections

    def test_create_new_with_highlights_and_research(self, tracker: NotionTracker) -> None:
        with (
            patch.object(tracker, "_find_page", return_value=None),
            patch.object(
                tracker,
                "_request",
                return_value={"id": "p1"},
            ),
            patch.object(tracker, "_add_interviews_database"),
            patch.object(tracker, "_add_template_body"),
        ):
            app = Application(
                name="Co",
                highlights=["h1"],
                research=["r1"],
                job_description="JD text",
            )
            _, sections = tracker.create(app)
            assert "highlights" in sections
            assert "research" in sections
            assert "job_description" in sections


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestUpdate:
    """Tests for the update method."""

    def test_update_success(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request") as mock_req:
            app = Application(
                name="Acme",
                page_id="page-xyz",
                status=Status.APPLIED,
            )
            tracker.update(app)
            mock_req.assert_called_once()
            args = mock_req.call_args
            assert args[0][0] == "PATCH"
            # Hyphens are stripped from page IDs
            assert "pagexyz" in args[0][1]

    def test_update_strips_hyphens(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request") as mock_req:
            app = Application(
                name="Acme",
                page_id="abc-def-123",
                status=Status.DONE,
            )
            tracker.update(app)
            url = mock_req.call_args[0][1]
            assert "abcdef123" in url

    def test_update_no_page_id(self, tracker: NotionTracker) -> None:
        app = Application(name="Acme")
        with pytest.raises(ValueError, match="page_id"):
            tracker.update(app)

    def test_update_empty_properties(self, tracker: NotionTracker) -> None:
        """Application with no fields generates Status=Targeted, so it still
        has properties and won't raise. But a truly empty Application (with
        status somehow not set) should raise.  We can verify by mocking
        _to_properties to return an empty dict."""
        app = Application(name="", page_id="pid")
        with patch.object(tracker, "_to_properties", return_value={}):
            with pytest.raises(ValueError, match="No properties to update"):
                tracker.update(app)


# ---------------------------------------------------------------------------
# find_by_name()
# ---------------------------------------------------------------------------


class TestFindByName:
    """Tests for find_by_name."""

    def test_found(self, tracker: NotionTracker) -> None:
        page = _notion_page(name="TargetCo")
        with patch.object(tracker, "_find_page", return_value=page):
            app = tracker.find_by_name("TargetCo")
            assert app is not None
            assert app.name == "TargetCo"
            assert app.page_id == "page-abc"

    def test_not_found(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_find_page", return_value=None):
            assert tracker.find_by_name("Ghost") is None


# ---------------------------------------------------------------------------
# set_* section methods
# ---------------------------------------------------------------------------


class TestSetSectionMethods:
    """Tests for set_highlights, set_research, set_contacts, etc."""

    def test_set_highlights(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_append_section") as mock_append:
            tracker.set_highlights("page-1", ["bullet 1", "bullet 2"])
            mock_append.assert_called_once()
            args = mock_append.call_args
            assert args[0][0] == "page1"
            assert args[0][1] == "Experience to Highlight"
            assert len(args[0][2]) == 2

    def test_set_research(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_append_section") as mock_append:
            tracker.set_research("page-2", ["finding 1"])
            mock_append.assert_called_once()
            assert mock_append.call_args[0][1] == "Company Research"

    def test_set_contacts(self, tracker: NotionTracker) -> None:
        contacts = [Contact(name="Jane", title="CTO", linkedin="https://linkedin.com/in/jane")]
        with (
            patch.object(tracker, "_append_section") as mock_append,
            patch.object(tracker, "_request") as mock_req,
        ):
            tracker.set_contacts("page-3", contacts)
            mock_append.assert_called_once()
            assert mock_append.call_args[0][1] == "Outreach Contacts"
            # Also sets LinkedIn property
            mock_req.assert_called_once()

    def test_set_interview_questions(self, tracker: NotionTracker) -> None:
        questions = [{"question": "Q1?", "answer": "A1."}]
        with patch.object(tracker, "_append_section") as mock_append:
            tracker.set_interview_questions("page-4", questions)
            mock_append.assert_called_once()
            assert mock_append.call_args[0][1] == "Questions I Might Get Asked"

    def test_set_questions_to_ask(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_append_section") as mock_append:
            tracker.set_questions_to_ask("page-5", ["Q1?", "Q2?"])
            mock_append.assert_called_once()
            assert mock_append.call_args[0][1] == "Questions to Ask"

    def test_set_job_description(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_append_section") as mock_append:
            tracker.set_job_description("page-6", "# Role\n\n- Build things")
            mock_append.assert_called_once()
            assert mock_append.call_args[0][1] == "Job Description"
            assert mock_append.call_args[1]["toggle"] is True

    def test_set_job_description_plain_text(self, tracker: NotionTracker) -> None:
        """If markdown_to_blocks returns empty, falls back to paragraph."""
        with patch.object(tracker, "_append_section") as mock_append:
            tracker.set_job_description("page-7", "")
            # Empty string -> _markdown_to_blocks returns [] -> fallback
            blocks = mock_append.call_args[0][2]
            assert blocks[0]["type"] == "paragraph"

    def test_set_fit_assessment(self, tracker: NotionTracker) -> None:
        scoring = ScoringResult(
            score=72,
            reasoning="Good match",
            green_flags=["strong team"],
            red_flags=["low pay"],
            gaps=["no k8s"],
            keywords_missing=["terraform"],
        )
        with (
            patch.object(tracker, "_append_section") as mock_append,
            patch.object(tracker, "_request") as mock_req,
        ):
            tracker.set_fit_assessment("page-8", scoring)
            mock_append.assert_called_once()
            assert mock_append.call_args[0][1] == "Fit Assessment"
            # Also updates Score property
            mock_req.assert_called_once()
            payload = mock_req.call_args[0][2]
            assert payload["properties"]["Score"] == {"number": 72}


# ---------------------------------------------------------------------------
# _scoring_result_blocks
# ---------------------------------------------------------------------------


class TestScoringResultBlocks:
    """Tests for _scoring_result_blocks static method."""

    def test_full_scoring(self) -> None:
        scoring = ScoringResult(
            score=80,
            reasoning="Strong fit",
            green_flags=["good culture", "remote"],
            red_flags=["low pay"],
            gaps=["no Go"],
            keywords_missing=["kubernetes"],
        )
        blocks = NotionTracker._scoring_result_blocks(scoring)
        types = [b["type"] for b in blocks]
        assert types[0] == "paragraph"  # Score
        assert types[1] == "paragraph"  # Reasoning
        assert "paragraph" in types  # Category headers
        assert "bulleted_list_item" in types

    def test_minimal_scoring(self) -> None:
        scoring = ScoringResult(score=50, reasoning="")
        blocks = NotionTracker._scoring_result_blocks(scoring)
        assert len(blocks) == 1  # Just the score line
        assert "50/100" in blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]


# ---------------------------------------------------------------------------
# _read_existing_sections
# ---------------------------------------------------------------------------


class TestReadExistingSections:
    """Tests for _read_existing_sections."""

    def test_reads_toggle_sections(self, tracker: NotionTracker) -> None:
        page_blocks = [
            _toggle_section_block("b1", "Job Description"),
            _toggle_section_block("b2", "Company Research"),
        ]
        jd_children = [
            {"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "JD text"}}]}}
        ]
        research_children = [
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "finding 1"}}]},
            }
        ]

        def mock_request(method: str, url: str, payload: Any = None) -> dict[str, Any]:
            if "b1/children" in url:
                return {"results": jd_children}
            if "b2/children" in url:
                return {"results": research_children}
            return {"results": page_blocks}

        with patch.object(tracker, "_request", side_effect=mock_request):
            sections = tracker._read_existing_sections("page-1")
            assert sections["Job Description"] == "JD text"
            assert sections["Company Research"] == ["finding 1"]

    def test_reads_flat_heading_sections(self, tracker: NotionTracker) -> None:
        """Test reading old-style flat heading_2 sections with sibling bullets."""
        page_blocks = [
            {
                "id": "h1",
                "type": "heading_2",
                "has_children": False,
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Experience to Highlight"}}],
                    "is_toggleable": False,
                },
            },
            {
                "id": "b1",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "Led team of 10"}}]},
            },
            {
                "id": "b2",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "Shipped v2"}}]},
            },
        ]
        with patch.object(tracker, "_request", return_value={"results": page_blocks}):
            sections = tracker._read_existing_sections("page-1")
            assert sections["Experience to Highlight"] == ["Led team of 10", "Shipped v2"]

    def test_alias_resolution(self, tracker: NotionTracker) -> None:
        """Old heading names should resolve to canonical section names."""
        page_blocks = [
            {
                "id": "h1",
                "type": "heading_2",
                "has_children": False,
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Questions to Ask in an Interview"},
                        }
                    ],
                    "is_toggleable": False,
                },
            },
            {
                "id": "b1",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "What's the team like?"}}]
                },
            },
        ]
        with patch.object(tracker, "_request", return_value={"results": page_blocks}):
            sections = tracker._read_existing_sections("page-1")
            assert "Questions to Ask" in sections
            assert sections["Questions to Ask"] == ["What's the team like?"]

    def test_unrelated_heading_ignored(self, tracker: NotionTracker) -> None:
        page_blocks = [
            {
                "id": "h1",
                "type": "heading_3",
                "has_children": False,
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Random Heading"}}],
                    "is_toggleable": False,
                },
            },
        ]
        with patch.object(tracker, "_request", return_value={"results": page_blocks}):
            sections = tracker._read_existing_sections("page-1")
            assert sections == {}


# ---------------------------------------------------------------------------
# _parse_section_children
# ---------------------------------------------------------------------------


class TestParseSectionChildren:
    """Tests for _parse_section_children (instance method despite pure logic)."""

    def test_job_description_paragraphs(self, tracker: NotionTracker) -> None:
        children = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Para 1"}}]},
            },
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Para 2"}}]},
            },
        ]
        result = tracker._parse_section_children("Job Description", children)
        assert result == "Para 1\n\nPara 2"

    def test_job_description_empty(self, tracker: NotionTracker) -> None:
        result = tracker._parse_section_children("Job Description", [])
        assert result == ""

    def test_questions_might_get_asked(self, tracker: NotionTracker) -> None:
        children = [
            {
                "type": "bulleted_list_item",
                "has_children": False,
                "bulleted_list_item": {"rich_text": [{"text": {"content": "Why us?"}}]},
            }
        ]
        result = tracker._parse_section_children("Questions I Might Get Asked", children)
        assert result == [{"question": "Why us?", "answer": ""}]

    def test_fit_assessment_mixed(self, tracker: NotionTracker) -> None:
        children = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Score: 75/100"}}]},
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "remote friendly"}}]},
            },
        ]
        result = tracker._parse_section_children("Fit Assessment", children)
        assert len(result) == 2
        assert result[0] == {"type": "paragraph", "text": "Score: 75/100"}
        assert result[1] == {"type": "bullet", "text": "remote friendly"}

    def test_default_bullet_list(self, tracker: NotionTracker) -> None:
        children = [
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "item A"}}]},
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "item B"}}]},
            },
        ]
        result = tracker._parse_section_children("Company Research", children)
        assert result == ["item A", "item B"]

    def test_empty_text_skipped(self, tracker: NotionTracker) -> None:
        children = [
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": ""}}]},
            },
        ]
        result = tracker._parse_section_children("Company Research", children)
        assert result == []


# ---------------------------------------------------------------------------
# _remove_section and _remove_all_managed_sections
# ---------------------------------------------------------------------------


class TestRemoveSections:
    """Tests for section removal methods."""

    def test_remove_section_heading_and_bullets(self, tracker: NotionTracker) -> None:
        blocks = [
            {
                "id": "h1",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Company Research"}}]
                },
            },
            {
                "id": "b1",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "item"}}]},
            },
            {
                "id": "h2",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Other Section"}}]
                },
            },
        ]
        deleted: list[str] = []

        def mock_request(method: str, url: str, payload: Any = None) -> dict[str, Any]:
            if method == "GET":
                return {"results": blocks}
            if method == "DELETE":
                deleted.append(url)
                return {}
            return {}

        with patch.object(tracker, "_request", side_effect=mock_request):
            tracker._remove_section("page-1", "Company Research")
            assert len(deleted) == 2  # heading + bullet

    def test_remove_section_alias(self, tracker: NotionTracker) -> None:
        """Removing 'Questions to Ask' should also catch alias headings."""
        blocks = [
            {
                "id": "h1",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Questions to Ask in an Interview"}}
                    ]
                },
            },
            {
                "id": "b1",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "Q1?"}}]},
            },
        ]
        deleted: list[str] = []

        def mock_request(method: str, url: str, payload: Any = None) -> dict[str, Any]:
            if method == "GET":
                return {"results": blocks}
            if method == "DELETE":
                deleted.append(url)
                return {}
            return {}

        with patch.object(tracker, "_request", side_effect=mock_request):
            tracker._remove_section("page-1", "Questions to Ask")
            assert len(deleted) == 2

    def test_remove_all_managed_sections(self, tracker: NotionTracker) -> None:
        blocks = [
            {"id": "d1", "type": "divider", "divider": {}},
            {
                "id": "h1",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Job Description"}}],
                    "is_toggleable": True,
                },
            },
            {
                "id": "h2",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Fit Assessment"}}],
                    "is_toggleable": True,
                },
            },
            {
                "id": "unrelated",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Custom Heading"}}],
                },
            },
        ]
        deleted: list[str] = []

        def mock_request(method: str, url: str, payload: Any = None) -> dict[str, Any]:
            if method == "GET":
                return {"results": blocks}
            if method == "DELETE":
                deleted.append(url.split("/")[-1])
                return {}
            return {}

        with patch.object(tracker, "_request", side_effect=mock_request):
            tracker._remove_all_managed_sections("page-1")
            # Should delete divider + 2 managed headings, NOT "Custom Heading"
            assert "d1" in deleted
            assert "h1" in deleted
            assert "h2" in deleted
            assert "unrelated" not in deleted


# ---------------------------------------------------------------------------
# _append_section
# ---------------------------------------------------------------------------


class TestAppendSection:
    """Tests for _append_section."""

    def test_append_section_toggle(self, tracker: NotionTracker) -> None:
        with (
            patch.object(tracker, "_remove_section"),
            patch.object(tracker, "_request") as mock_req,
        ):
            tracker._append_section("pid", "Title", [_bullet_block("x")], toggle=True)
            args = mock_req.call_args
            payload = args[0][2]
            children = payload["children"]
            assert len(children) == 1
            assert children[0]["heading_3"]["is_toggleable"] is True

    def test_append_section_flat_heading3(self, tracker: NotionTracker) -> None:
        with (
            patch.object(tracker, "_remove_section"),
            patch.object(tracker, "_request") as mock_req,
        ):
            tracker._append_section("pid", "Title", [_bullet_block("x")], heading_level=3)
            payload = mock_req.call_args[0][2]
            children = payload["children"]
            assert children[0]["type"] == "heading_3"
            assert children[1]["type"] == "bulleted_list_item"

    def test_append_section_heading2(self, tracker: NotionTracker) -> None:
        with (
            patch.object(tracker, "_remove_section"),
            patch.object(tracker, "_request") as mock_req,
        ):
            tracker._append_section("pid", "Title", [_bullet_block("x")], heading_level=2)
            payload = mock_req.call_args[0][2]
            children = payload["children"]
            assert children[0]["type"] == "heading_2"


# ---------------------------------------------------------------------------
# _add_template_body
# ---------------------------------------------------------------------------


class TestAddTemplateBody:
    """Tests for the template body builder."""

    def test_empty_application(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request") as mock_req:
            app = Application(name="Co")
            tracker._add_template_body("pid", app)
            payload = mock_req.call_args[0][2]
            children = payload["children"]
            # divider + 7 toggle sections
            assert children[0]["type"] == "divider"
            toggle_count = sum(
                1
                for c in children
                if c.get("type") == "heading_3" and c.get("heading_3", {}).get("is_toggleable")
            )
            assert toggle_count == 7

    def test_with_scoring(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request") as mock_req:
            app = Application(
                name="Co",
                scoring=ScoringResult(score=80, reasoning="Good"),
            )
            tracker._add_template_body("pid", app)
            payload = mock_req.call_args[0][2]
            children = payload["children"]
            # Second toggle (Fit Assessment) should have scoring blocks
            fit_section = children[2]  # divider + JD + Fit Assessment
            assert fit_section["heading_3"]["children"][0]["type"] == "paragraph"

    def test_with_preserved_data(self, tracker: NotionTracker) -> None:
        preserved = {
            "Outreach Contacts": ["Jane — CTO"],
            "Questions I Might Get Asked": [{"question": "Why us?", "answer": "Culture"}],
            "Questions to Ask": ["What's the stack?"],
            "Fit Assessment": [
                {"type": "paragraph", "text": "Score: 90/100"},
                {"type": "bullet", "text": "good match"},
            ],
        }
        with patch.object(tracker, "_request"):
            app = Application(name="Co")
            tracker._add_template_body("pid", app, preserved=preserved)

    def test_preserved_fit_assessment_list_strings(self, tracker: NotionTracker) -> None:
        """Test preserved fit assessment as plain string list (legacy format)."""
        preserved = {
            "Fit Assessment": ["Score: 70/100", "Good culture fit"],
        }
        with patch.object(tracker, "_request"):
            app = Application(name="Co")
            tracker._add_template_body("pid", app, preserved=preserved)

    def test_preserved_fit_assessment_non_list(self, tracker: NotionTracker) -> None:
        """Test preserved fit assessment as single string."""
        preserved = {
            "Fit Assessment": "Some plain text",
        }
        with patch.object(tracker, "_request"):
            app = Application(name="Co")
            tracker._add_template_body("pid", app, preserved=preserved)

    def test_preserved_qa_plain_strings(self, tracker: NotionTracker) -> None:
        """Test preserved Q&A as plain string list (not dict)."""
        preserved = {
            "Questions I Might Get Asked": ["Question one?", "Question two?"],
        }
        with patch.object(tracker, "_request") as mock_req:
            app = Application(name="Co")
            tracker._add_template_body("pid", app, preserved=preserved)
            payload = mock_req.call_args[0][2]
            children = payload["children"]
            # QA section is the 6th toggle (index 6 after divider)
            qa_section = children[6]
            qa_children = qa_section["heading_3"]["children"]
            assert len(qa_children) == 2
            assert all(c["type"] == "bulleted_list_item" for c in qa_children)


# ---------------------------------------------------------------------------
# _add_interviews_database
# ---------------------------------------------------------------------------


class TestAddInterviewsDatabase:
    """Tests for _add_interviews_database."""

    def test_creates_database(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request", return_value={"id": "idb-1"}) as mock_req:
            db_id = tracker._add_interviews_database("page-1")
            assert db_id == "idb-1"
            payload = mock_req.call_args[0][2]
            assert payload["is_inline"] is True
            assert "Interviewer Name and Role" in payload["properties"]
            assert "Type" in payload["properties"]
            assert "Vibe" in payload["properties"]
            assert "Outcome" in payload["properties"]


# ---------------------------------------------------------------------------
# _find_interviews_db
# ---------------------------------------------------------------------------


class TestFindInterviewsDb:
    """Tests for _find_interviews_db."""

    def test_found(self, tracker: NotionTracker) -> None:
        blocks = [
            {
                "id": "db-found",
                "type": "child_database",
                "child_database": {"title": "Interviews"},
            }
        ]
        with patch.object(tracker, "_request", return_value={"results": blocks}):
            result = tracker._find_interviews_db("page-1")
            assert result == "db-found"

    def test_not_found(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request", return_value={"results": []}):
            result = tracker._find_interviews_db("page-1")
            assert result is None

    def test_wrong_title(self, tracker: NotionTracker) -> None:
        blocks = [
            {
                "id": "db-other",
                "type": "child_database",
                "child_database": {"title": "Other DB"},
            }
        ]
        with patch.object(tracker, "_request", return_value={"results": blocks}):
            result = tracker._find_interviews_db("page-1")
            assert result is None


# ---------------------------------------------------------------------------
# add_interview_entry
# ---------------------------------------------------------------------------


class TestAddInterviewEntry:
    """Tests for add_interview_entry."""

    def test_creates_row_with_body(self, tracker: NotionTracker) -> None:
        interview = Interview(
            date="2026-03-15",
            interview_type="Technical",
            interviewers=["Jane Smith"],
            prep_notes="## Topics\n- System design",
            vibe=4,
            outcome="Pending",
        )
        with (
            patch.object(tracker, "_find_interviews_db", return_value="idb-1"),
            patch.object(tracker, "_request", return_value={"id": "entry-1"}) as mock_req,
        ):
            result = tracker.add_interview_entry("page-1", interview)
            assert result == "entry-1"
            # First call: create row, second: append body
            assert mock_req.call_count == 2

    def test_creates_row_no_body(self, tracker: NotionTracker) -> None:
        interview = Interview(date="2026-03-15", interviewers=["Bob"])
        with (
            patch.object(tracker, "_find_interviews_db", return_value="idb-1"),
            patch.object(tracker, "_request", return_value={"id": "entry-2"}) as mock_req,
        ):
            tracker.add_interview_entry("page-1", interview)
            # Only one call: create row, no body
            assert mock_req.call_count == 1

    def test_no_interviews_db_raises(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_find_interviews_db", return_value=None):
            with pytest.raises(ValueError, match="No Interviews database"):
                tracker.add_interview_entry("page-1", Interview(date="2026-01-01"))

    def test_with_debrief_data(self, tracker: NotionTracker) -> None:
        interview = Interview(
            date="2026-03-15",
            debrief="Great conversation",
            questions_they_asked=["Tell me about X"],
            questions_i_asked=["What's the roadmap?"],
            follow_up="Send portfolio",
        )
        with (
            patch.object(tracker, "_find_interviews_db", return_value="idb-1"),
            patch.object(tracker, "_request", return_value={"id": "entry-3"}) as mock_req,
        ):
            tracker.add_interview_entry("page-1", interview)
            # create + body append
            assert mock_req.call_count == 2
            body_payload = mock_req.call_args_list[1][0][2]
            children = body_payload["children"]
            # Should have a Debrief toggle
            assert any(
                c.get("heading_3", {}).get("rich_text", [{}])[0].get("text", {}).get("content")
                == "Debrief"
                for c in children
            )


# ---------------------------------------------------------------------------
# update_interview_entry
# ---------------------------------------------------------------------------


class TestUpdateInterviewEntry:
    """Tests for update_interview_entry."""

    def test_updates_properties(self, tracker: NotionTracker) -> None:
        interview = Interview(
            date="2026-03-15",
            interview_type="Behavioral",
            vibe=3,
            outcome="Passed",
        )
        with patch.object(tracker, "_request") as mock_req:
            tracker.update_interview_entry("entry-1", interview)
            assert mock_req.call_count == 1
            payload = mock_req.call_args[0][2]
            assert "Type" in payload["properties"]
            assert "Vibe" in payload["properties"]
            assert "Outcome" in payload["properties"]

    def test_updates_prep_notes(self, tracker: NotionTracker) -> None:
        interview = Interview(date="", prep_notes="## Topics\n- Arch review")
        with (
            patch.object(tracker, "_request") as mock_req,
            patch.object(tracker, "_remove_entry_section") as mock_remove,
        ):
            tracker.update_interview_entry("entry-1", interview)
            mock_remove.assert_called_once_with("entry1", "Prep Notes")
            # No properties PATCH (no type/vibe/outcome), but prep notes PATCH
            assert mock_req.call_count == 1

    def test_updates_debrief(self, tracker: NotionTracker) -> None:
        interview = Interview(date="", debrief="Good call")
        with (
            patch.object(tracker, "_request"),
            patch.object(tracker, "_remove_entry_section") as mock_remove,
        ):
            tracker.update_interview_entry("entry-1", interview)
            mock_remove.assert_called_once_with("entry1", "Debrief")


# ---------------------------------------------------------------------------
# _strip_debrief_sections
# ---------------------------------------------------------------------------


class TestStripDebriefSections:
    """Tests for _strip_debrief_sections."""

    def test_strips_populated_fields(self, tracker: NotionTracker) -> None:
        text = (
            "Main content\n\n"
            "## Questions They Asked\n"
            "- Q1\n- Q2\n\n"
            "## Questions I Asked\n"
            "- Q3\n\n"
            "## Follow-Up\n"
            "Send docs\n\n"
            "## Final Notes\n"
            "Wrap up"
        )
        interview = Interview(
            date="",
            questions_they_asked=["Q1", "Q2"],
            questions_i_asked=["Q3"],
            follow_up="Send docs",
        )
        result = tracker._strip_debrief_sections(text, interview)
        assert "Questions They Asked" not in result
        assert "Questions I Asked" not in result
        assert "Follow-Up" not in result
        assert "Main content" in result
        # "Final Notes" is under its own heading, not a stripped section,
        # so it survives the stripping
        assert "Final Notes" in result
        assert "Wrap up" in result

    def test_keeps_sections_when_fields_empty(self, tracker: NotionTracker) -> None:
        text = "## Questions They Asked\n- Q1\n\nSome text"
        interview = Interview(date="")  # no structured fields
        result = tracker._strip_debrief_sections(text, interview)
        assert "Questions They Asked" in result

    def test_no_sections_to_strip(self, tracker: NotionTracker) -> None:
        text = "Just plain debrief text"
        interview = Interview(date="")
        result = tracker._strip_debrief_sections(text, interview)
        assert result == text

    def test_follow_up_needed_variant(self, tracker: NotionTracker) -> None:
        text = "## Follow-Up Needed\nDo X"
        interview = Interview(date="", follow_up="Do X")
        result = tracker._strip_debrief_sections(text, interview)
        assert "Follow-Up Needed" not in result


# ---------------------------------------------------------------------------
# _build_debrief_body
# ---------------------------------------------------------------------------


class TestBuildDebriefBody:
    """Tests for _build_debrief_body."""

    def test_full_debrief(self, tracker: NotionTracker) -> None:
        interview = Interview(
            date="2026-03-15",
            debrief="Great conversation about architecture",
            questions_they_asked=["Why this role?"],
            questions_i_asked=["What's the team?"],
            follow_up="Email portfolio",
        )
        blocks = tracker._build_debrief_body(interview)
        types = [b["type"] for b in blocks]
        assert "paragraph" in types
        assert "heading_3" in types
        assert "bulleted_list_item" in types

    def test_empty_debrief(self, tracker: NotionTracker) -> None:
        interview = Interview(date="")
        blocks = tracker._build_debrief_body(interview)
        # Should return placeholder
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"

    def test_debrief_text_only(self, tracker: NotionTracker) -> None:
        interview = Interview(date="", debrief="Just text")
        blocks = tracker._build_debrief_body(interview)
        assert len(blocks) >= 1


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------


class TestListAll:
    """Tests for list_all."""

    def test_single_page(self, tracker: NotionTracker) -> None:
        response = {
            "results": [_notion_page(name="Alpha")],
            "has_more": False,
        }
        with patch.object(tracker, "_request", return_value=response):
            apps = tracker.list_all()
            assert len(apps) == 1
            assert apps[0].name == "Alpha"

    def test_paginated_results(self, tracker: NotionTracker) -> None:
        page1 = {
            "results": [_notion_page(name="Alpha")],
            "has_more": True,
            "next_cursor": "cursor-2",
        }
        page2 = {
            "results": [_notion_page(name="Beta")],
            "has_more": False,
        }
        with patch.object(tracker, "_request", side_effect=[page1, page2]):
            apps = tracker.list_all()
            assert len(apps) == 2
            assert apps[0].name == "Alpha"
            assert apps[1].name == "Beta"

    def test_empty_database(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request", return_value={"results": [], "has_more": False}):
            assert tracker.list_all() == []

    def test_skips_archived(self, tracker: NotionTracker) -> None:
        response = {
            "results": [
                _notion_page(name="Active"),
                _notion_page(name="Archived", archived=True),
            ],
            "has_more": False,
        }
        with patch.object(tracker, "_request", return_value=response):
            apps = tracker.list_all()
            assert len(apps) == 1
            assert apps[0].name == "Active"


# ---------------------------------------------------------------------------
# _page_to_application
# ---------------------------------------------------------------------------


class TestPageToApplication:
    """Tests for the static _page_to_application mapping."""

    def test_full_page(self) -> None:
        page = _notion_page(
            name="TestCo",
            status="Applied",
            position="Lead Engineer",
        )
        app = NotionTracker._page_to_application(page)
        assert app.name == "TestCo"
        assert app.status == Status.APPLIED
        assert app.position == "Lead Engineer"
        assert app.page_id == "page-abc"
        assert app.environment == ["Remote"]
        assert app.salary == "120-150k"

    def test_unknown_status_defaults_to_targeted(self) -> None:
        page = _notion_page(status="SomeWeirdStatus")
        app = NotionTracker._page_to_application(page)
        assert app.status == Status.TARGETED

    def test_unknown_linkedin_defaults_to_na(self) -> None:
        page = _notion_page()
        page["properties"]["Follow on Linkedin"] = {"select": {"name": "Unknown"}}
        app = NotionTracker._page_to_application(page)
        assert app.linkedin == LinkedInStatus.NA

    def test_missing_properties(self) -> None:
        page = {"id": "p1", "properties": {}}
        app = NotionTracker._page_to_application(page)
        assert app.name == ""
        assert app.position == ""
        assert app.status == Status.TARGETED

    def test_empty_select(self) -> None:
        page = _notion_page()
        page["properties"]["Status"] = {"select": None}
        app = NotionTracker._page_to_application(page)
        assert app.status == Status.TARGETED

    def test_date_parsing(self) -> None:
        page = _notion_page()
        app = NotionTracker._page_to_application(page)
        assert app.start_date == date(2026, 1, 15)

    def test_no_date(self) -> None:
        page = _notion_page()
        page["properties"]["Start Date"] = {"date": None}
        app = NotionTracker._page_to_application(page)
        assert app.start_date is None


# ---------------------------------------------------------------------------
# _task_to_application / _task_to_scoring_result (static)
# ---------------------------------------------------------------------------


class TestTaskConversions:
    """Tests for _task_to_application and _task_to_scoring_result."""

    def test_task_to_application_full(self) -> None:
        task = {
            "name": "TestCo",
            "position": "SWE",
            "status": "Applied",
            "date": "2026-01-15",
            "url": "https://example.com",
            "environment": ["Remote"],
            "salary": "100k",
            "focus": ["AI"],
            "vision": "Build AGI",
            "mission": "Science",
            "linkedin": "Yes",
            "conclusion": "Offer",
            "highlights": ["h1"],
            "job_description": "JD text",
            "research": ["r1"],
            "score": 85,
            "reasoning": "Good",
            "green_flags": ["remote"],
            "red_flags": ["low pay"],
            "gaps": ["no Go"],
            "keywords_missing": ["k8s"],
        }
        app = NotionTracker._task_to_application(task)
        assert app.name == "TestCo"
        assert app.status == Status.APPLIED
        assert app.start_date == date(2026, 1, 15)
        assert app.linkedin == LinkedInStatus.YES
        assert app.scoring is not None
        assert app.scoring.score == 85

    def test_task_to_application_minimal(self) -> None:
        task = {"name": "Min"}
        app = NotionTracker._task_to_application(task)
        assert app.name == "Min"
        assert app.status == Status.TARGETED
        assert app.scoring is None

    def test_task_to_application_invalid_status(self) -> None:
        task = {"name": "Co", "status": "InvalidStatus"}
        app = NotionTracker._task_to_application(task)
        assert app.status == Status.TARGETED

    def test_task_to_application_invalid_linkedin(self) -> None:
        task = {"name": "Co", "linkedin": "BadValue"}
        app = NotionTracker._task_to_application(task)
        assert app.linkedin == LinkedInStatus.NA

    def test_task_to_scoring_result(self) -> None:
        task = {
            "score": 72,
            "reasoning": "Decent fit",
            "green_flags": ["team"],
            "red_flags": ["salary"],
            "gaps": ["Rust"],
            "keywords_missing": ["graphql"],
        }
        sr = NotionTracker._task_to_scoring_result(task)
        assert sr.score == 72
        assert sr.reasoning == "Decent fit"
        assert sr.green_flags == ["team"]

    def test_task_to_scoring_result_minimal(self) -> None:
        task = {}
        sr = NotionTracker._task_to_scoring_result(task)
        assert sr.score == 0
        assert sr.reasoning == ""


# ---------------------------------------------------------------------------
# _blocks_to_text / _parse_debrief_body (static)
# ---------------------------------------------------------------------------


class TestBlocksToText:
    """Tests for _blocks_to_text."""

    def test_mixed_blocks(self) -> None:
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Intro"}}]},
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "item"}}]},
            },
            {
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": "Section"}}]},
            },
        ]
        text = NotionTracker._blocks_to_text(blocks)
        assert "Intro" in text
        assert "- item" in text
        assert "## Section" in text

    def test_empty_blocks(self) -> None:
        assert NotionTracker._blocks_to_text([]) == ""

    def test_blocks_with_empty_text(self) -> None:
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": ""}}]},
            },
        ]
        assert NotionTracker._blocks_to_text(blocks) == ""


class TestParseDebriefBody:
    """Tests for _parse_debrief_body."""

    def test_full_debrief_body(self) -> None:
        children = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Good call"}}]},
            },
            {
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": "Questions They Asked"}}]},
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "Why us?"}}]},
            },
            {
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": "Questions I Asked"}}]},
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "What stack?"}}]},
            },
            {
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": "Follow-Up"}}]},
            },
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Send portfolio"}}]},
            },
        ]
        debrief, q_they, q_i, follow = NotionTracker._parse_debrief_body(children)
        assert debrief == "Good call"
        assert q_they == ["Why us?"]
        assert q_i == ["What stack?"]
        assert follow == "Send portfolio"

    def test_empty_children(self) -> None:
        debrief, q_they, q_i, follow = NotionTracker._parse_debrief_body([])
        assert debrief == ""
        assert q_they == []
        assert q_i == []
        assert follow == ""


# ---------------------------------------------------------------------------
# get_interviews
# ---------------------------------------------------------------------------


class TestGetInterviews:
    """Tests for get_interviews."""

    def test_no_db(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_find_interviews_db", return_value=None):
            assert tracker.get_interviews("page-1") == []

    def test_single_interview(self, tracker: NotionTracker) -> None:
        row = {
            "id": "row-1",
            "properties": {
                "Interviewer Name and Role": {"title": [{"text": {"content": "Jane CTO"}}]},
                "Date": {"date": {"start": "2026-03-15"}},
                "Type": {"select": {"name": "Technical"}},
                "Vibe": {"select": {"name": "4"}},
                "Outcome": {"select": {"name": "Passed"}},
            },
        }
        db_query_response = {"results": [row], "has_more": False}
        row_children_response = {"results": []}

        def mock_request(method: str, url: str, payload: Any = None) -> dict[str, Any]:
            if "databases/" in url and "query" in url:
                return db_query_response
            if "row-1/children" in url:
                return row_children_response
            return {"results": []}

        with (
            patch.object(tracker, "_find_interviews_db", return_value="idb-1"),
            patch.object(tracker, "_request", side_effect=mock_request),
        ):
            interviews = tracker.get_interviews("page-1")
            assert len(interviews) == 1
            iv = interviews[0]
            assert iv.interviewers == ["Jane CTO"]
            assert iv.date == "2026-03-15"
            assert iv.interview_type == "Technical"
            assert iv.vibe == 4
            assert iv.outcome == "Passed"

    def test_interview_with_toggle_content(self, tracker: NotionTracker) -> None:
        row = {
            "id": "row-2",
            "properties": {
                "Interviewer Name and Role": {"title": []},
                "Date": {"date": None},
                "Type": {"select": None},
                "Vibe": {"select": None},
                "Outcome": {"select": None},
            },
        }
        row_children = [
            {
                "id": "prep-toggle",
                "type": "heading_3",
                "has_children": True,
                "heading_3": {"rich_text": [{"text": {"content": "Prep Notes"}}]},
            },
        ]
        prep_children = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Study system design"}}]},
            }
        ]

        call_count = 0

        def mock_request(method: str, url: str, payload: Any = None) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if "databases/" in url and "query" in url:
                return {"results": [row], "has_more": False}
            if "row-2/children" in url:
                return {"results": row_children}
            if "prep-toggle/children" in url:
                return {"results": prep_children}
            return {"results": []}

        with (
            patch.object(tracker, "_find_interviews_db", return_value="idb-1"),
            patch.object(tracker, "_request", side_effect=mock_request),
        ):
            interviews = tracker.get_interviews("page-1")
            assert len(interviews) == 1
            assert interviews[0].prep_notes == "Study system design"

    def test_paginated_interviews(self, tracker: NotionTracker) -> None:
        row1 = {
            "id": "r1",
            "properties": {
                "Interviewer Name and Role": {"title": [{"text": {"content": "A"}}]},
                "Date": {"date": None},
                "Type": {"select": None},
                "Vibe": {"select": None},
                "Outcome": {"select": None},
            },
        }
        row2 = {
            "id": "r2",
            "properties": {
                "Interviewer Name and Role": {"title": [{"text": {"content": "B"}}]},
                "Date": {"date": None},
                "Type": {"select": None},
                "Vibe": {"select": None},
                "Outcome": {"select": None},
            },
        }

        def mock_request(method: str, url: str, payload: Any = None) -> dict[str, Any]:
            if "databases/" in url and "query" in url:
                if payload and "start_cursor" in payload:
                    return {"results": [row2], "has_more": False}
                return {"results": [row1], "has_more": True, "next_cursor": "cur2"}
            # Row children
            return {"results": []}

        with (
            patch.object(tracker, "_find_interviews_db", return_value="idb-1"),
            patch.object(tracker, "_request", side_effect=mock_request),
        ):
            interviews = tracker.get_interviews("page-1")
            assert len(interviews) == 2


# ---------------------------------------------------------------------------
# _ensure_interviews_db_schema
# ---------------------------------------------------------------------------


class TestEnsureInterviewsDbSchema:
    """Tests for _ensure_interviews_db_schema."""

    def test_creates_when_missing(self, tracker: NotionTracker) -> None:
        with (
            patch.object(tracker, "_find_interviews_db", return_value=None),
            patch.object(tracker, "_add_interviews_database", return_value="new-db") as mock_add,
        ):
            result = tracker._ensure_interviews_db_schema("page-1")
            assert result == "new-db"
            mock_add.assert_called_once()

    def test_patches_existing(self, tracker: NotionTracker) -> None:
        with (
            patch.object(tracker, "_find_interviews_db", return_value="existing-db"),
            patch.object(tracker, "_request") as mock_req,
        ):
            result = tracker._ensure_interviews_db_schema("page-1")
            assert result == "existing-db"
            mock_req.assert_called_once()
            payload = mock_req.call_args[0][2]
            assert "Type" in payload["properties"]
            assert "Vibe" in payload["properties"]
            assert "Outcome" in payload["properties"]


# ---------------------------------------------------------------------------
# _find_interview_entry
# ---------------------------------------------------------------------------


class TestFindInterviewEntry:
    """Tests for _find_interview_entry."""

    def test_found_by_interviewer_and_date(self, tracker: NotionTracker) -> None:
        with patch.object(
            tracker,
            "_request",
            return_value={"results": [{"id": "entry-found"}]},
        ):
            result = tracker._find_interview_entry("db-1", "Jane", "2026-03-15")
            assert result == "entry-found"

    def test_not_found(self, tracker: NotionTracker) -> None:
        with patch.object(tracker, "_request", return_value={"results": []}):
            result = tracker._find_interview_entry("db-1", "Jane", "2026-03-15")
            assert result is None

    def test_by_interviewer_only(self, tracker: NotionTracker) -> None:
        with patch.object(
            tracker,
            "_request",
            return_value={"results": [{"id": "e1"}]},
        ) as mock_req:
            tracker._find_interview_entry("db-1", "Jane")
            payload = mock_req.call_args[0][2]
            # Single filter, not "and"
            assert "and" not in payload["filter"]

    def test_by_date_only(self, tracker: NotionTracker) -> None:
        with patch.object(
            tracker,
            "_request",
            return_value={"results": [{"id": "e1"}]},
        ) as mock_req:
            tracker._find_interview_entry("db-1", date="2026-03-15")
            payload = mock_req.call_args[0][2]
            assert "and" not in payload["filter"]

    def test_no_filters(self, tracker: NotionTracker) -> None:
        result = tracker._find_interview_entry("db-1")
        assert result is None


# ---------------------------------------------------------------------------
# _remove_entry_section
# ---------------------------------------------------------------------------


class TestRemoveEntrySection:
    """Tests for _remove_entry_section."""

    def test_removes_matching_heading(self, tracker: NotionTracker) -> None:
        blocks = [
            {
                "id": "toggle-1",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": "Prep Notes"}}]},
            },
        ]
        deleted = []

        def mock_request(method: str, url: str, payload: Any = None) -> dict[str, Any]:
            if method == "GET":
                return {"results": blocks}
            if method == "DELETE":
                deleted.append(url)
                return {}
            return {}

        with patch.object(tracker, "_request", side_effect=mock_request):
            tracker._remove_entry_section("entry-1", "Prep Notes")
            assert len(deleted) == 1
            assert "toggle-1" in deleted[0]

    def test_no_match(self, tracker: NotionTracker) -> None:
        blocks = [
            {
                "id": "other",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": "Different"}}]},
            },
        ]
        with patch.object(tracker, "_request", return_value={"results": blocks}):
            # Should not raise, just do nothing
            tracker._remove_entry_section("entry-1", "Prep Notes")


# ---------------------------------------------------------------------------
# check_followups / format_followup_report
# ---------------------------------------------------------------------------


class TestCheckFollowups:
    """Tests for check_followups."""

    def test_stale_interview(self, tracker: NotionTracker) -> None:
        page = _notion_page(status="In Progress (Interviewing)")
        interview = Interview(
            date="2026-02-01",
            interviewers=["Alice"],
            interview_type="Technical",
            follow_up="Send references",
        )
        with (
            patch.object(
                tracker,
                "_request",
                return_value={
                    "results": [page],
                    "has_more": False,
                },
            ),
            patch.object(tracker, "get_interviews", return_value=[interview]),
        ):
            results = tracker.check_followups(threshold_days=5)
            assert len(results) == 1
            assert results[0]["status"] == "stale"
            assert results[0]["follow_up"] == "Send references"

    def test_active_interview(self, tracker: NotionTracker) -> None:
        page = _notion_page(status="In Progress (Interviewing)")
        today = date.today().isoformat()
        interview = Interview(date=today, interviewers=["Bob"])
        with (
            patch.object(
                tracker,
                "_request",
                return_value={"results": [page], "has_more": False},
            ),
            patch.object(tracker, "get_interviews", return_value=[interview]),
        ):
            results = tracker.check_followups(threshold_days=5)
            assert results[0]["status"] == "active"

    def test_upcoming_interview(self, tracker: NotionTracker) -> None:
        page = _notion_page(status="In Progress (Interviewing)")
        interview = Interview(date="2099-12-31", interviewers=["Future"])
        with (
            patch.object(
                tracker,
                "_request",
                return_value={"results": [page], "has_more": False},
            ),
            patch.object(tracker, "get_interviews", return_value=[interview]),
        ):
            results = tracker.check_followups(threshold_days=5)
            assert results[0]["status"] == "upcoming"

    def test_no_interviews(self, tracker: NotionTracker) -> None:
        page = _notion_page(status="In Progress (Interviewing)")
        with (
            patch.object(
                tracker,
                "_request",
                return_value={"results": [page], "has_more": False},
            ),
            patch.object(tracker, "get_interviews", return_value=[]),
        ):
            results = tracker.check_followups()
            assert results[0]["status"] == "no_data"

    def test_no_dated_interviews(self, tracker: NotionTracker) -> None:
        page = _notion_page(status="In Progress (Interviewing)")
        interview = Interview(date="", interviewers=["NoDate"])
        with (
            patch.object(
                tracker,
                "_request",
                return_value={"results": [page], "has_more": False},
            ),
            patch.object(tracker, "get_interviews", return_value=[interview]),
        ):
            results = tracker.check_followups()
            assert results[0]["status"] == "no_data"

    def test_empty_results(self, tracker: NotionTracker) -> None:
        with patch.object(
            tracker,
            "_request",
            return_value={"results": [], "has_more": False},
        ):
            results = tracker.check_followups()
            assert results == []

    def test_sort_order(self, tracker: NotionTracker) -> None:
        """Stale should come before active, active before no_data."""
        p1 = _notion_page(page_id="p1", name="Stale Co", status="In Progress (Interviewing)")
        p2 = _notion_page(page_id="p2", name="Active Co", status="In Progress (Interviewing)")
        today = date.today().isoformat()
        stale_iv = Interview(date="2025-01-01", interviewers=["X"])
        active_iv = Interview(date=today, interviewers=["Y"])

        def mock_get_interviews(page_id: str) -> list[Interview]:
            if page_id == "p1":
                return [stale_iv]
            return [active_iv]

        with (
            patch.object(
                tracker,
                "_request",
                return_value={"results": [p1, p2], "has_more": False},
            ),
            patch.object(tracker, "get_interviews", side_effect=mock_get_interviews),
        ):
            results = tracker.check_followups(threshold_days=5)
            assert results[0]["name"] == "Stale Co"
            assert results[1]["name"] == "Active Co"


class TestFormatFollowupReport:
    """Tests for format_followup_report."""

    def test_stale_report(self, tracker: NotionTracker) -> None:
        results = [
            {
                "name": "StaleCo",
                "page_id": "p1",
                "status": "stale",
                "days_since": 10,
                "last_date": "2026-02-26",
                "last_interviewer": "Alice",
                "last_type": "Technical",
                "follow_up": "Send references",
                "threshold": 5,
            }
        ]
        report = tracker.format_followup_report(results, threshold_days=5)
        assert "Needs Attention" in report
        assert "StaleCo" in report
        assert "10 days" in report
        assert "Send references" in report

    def test_all_active_report(self, tracker: NotionTracker) -> None:
        results = [
            {
                "name": "ActiveCo",
                "page_id": "p1",
                "status": "active",
                "days_since": 2,
                "last_date": "2026-03-06",
                "last_interviewer": "Bob",
                "last_type": None,
                "follow_up": None,
                "threshold": 5,
            }
        ]
        report = tracker.format_followup_report(results)
        assert "Recently Active" in report
        assert "Nothing needs follow-up" in report

    def test_upcoming_report(self, tracker: NotionTracker) -> None:
        results = [
            {
                "name": "UpcomingCo",
                "page_id": "p1",
                "status": "upcoming",
                "days_since": -3,
                "last_date": "2026-03-11",
                "last_interviewer": "Charlie",
                "last_type": "Hiring Manager",
                "follow_up": None,
                "threshold": 5,
            }
        ]
        report = tracker.format_followup_report(results)
        assert "Upcoming Interviews" in report
        assert "3 days" in report

    def test_no_data_report(self, tracker: NotionTracker) -> None:
        results = [
            {
                "name": "MissingCo",
                "page_id": "p1",
                "status": "no_data",
                "days_since": 15,
                "last_date": None,
                "last_interviewer": None,
                "last_type": None,
                "follow_up": None,
                "threshold": 5,
            }
        ]
        report = tracker.format_followup_report(results)
        assert "No Interview Data" in report
        assert "tracked 15 days" in report

    def test_empty_report(self, tracker: NotionTracker) -> None:
        report = tracker.format_followup_report([])
        assert "Nothing needs follow-up" in report


# ---------------------------------------------------------------------------
# process_queue_file and _queue_* methods
# ---------------------------------------------------------------------------


class TestProcessQueueFile:
    """Tests for process_queue_file routing and individual _queue_* methods."""

    def _write_queue_file(self, tmp_project: Path, task: dict[str, Any]) -> str:
        filepath = tmp_project / "notion_queue" / "test_task.json"
        filepath.write_text(json.dumps(task))
        return str(filepath)

    def test_unknown_command(self, tracker: NotionTracker, tmp_project: Path) -> None:
        filepath = self._write_queue_file(tmp_project, {"command": "unknown"})
        result = tracker.process_queue_file(filepath)
        assert result["status"] == "error"
        assert "Unknown command" in result["message"]

    def test_queue_create_new(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "create",
            "name": "NewCo",
            "position": "SWE",
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(
                tracker,
                "_find_page",
                side_effect=[None, {"id": "p1", "url": "https://notion.so/p1"}],
            ),
            patch.object(tracker, "create", return_value=("p1", ["properties"])),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "created"

    def test_queue_create_existing(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "create",
            "name": "ExistingCo",
            "position": "Lead",
        }
        filepath = self._write_queue_file(tmp_project, task)
        existing = {"id": "p2", "url": "https://notion.so/p2"}
        with (
            patch.object(
                tracker,
                "_find_page",
                side_effect=[existing, existing],
            ),
            patch.object(tracker, "create", return_value=("p2", ["properties", "template_body"])),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "updated_existing"

    def test_queue_update(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "update", "page_id": "p1", "status": "Applied"}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "update"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "updated"

    def test_queue_update_missing_page_id(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "update"}
        filepath = self._write_queue_file(tmp_project, task)
        result = tracker.process_queue_file(filepath)
        assert result["status"] == "error"
        assert "page_id" in result["message"]

    def test_queue_highlights(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "highlights",
            "page_id": "p1",
            "highlights": ["h1", "h2"],
        }
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "set_highlights"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "highlights_replaced"

    def test_queue_highlights_empty(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "highlights", "page_id": "p1", "highlights": []}
        filepath = self._write_queue_file(tmp_project, task)
        result = tracker.process_queue_file(filepath)
        assert result["status"] == "error"

    def test_queue_highlights_missing_page_id(
        self, tracker: NotionTracker, tmp_project: Path
    ) -> None:
        task = {"command": "highlights", "highlights": ["h1"]}
        filepath = self._write_queue_file(tmp_project, task)
        result = tracker.process_queue_file(filepath)
        assert result["status"] == "error"

    def test_queue_research(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "research", "name": "TestCo", "research": ["r1"]}
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "set_research"),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "research_replaced"

    def test_queue_research_empty(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "research", "name": "TestCo", "research": []}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "_resolve_page_id", return_value="p1"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "error"

    def test_queue_outreach(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "outreach",
            "name": "TestCo",
            "contacts": [
                {
                    "name": "Jane",
                    "title": "VP",
                    "linkedin": "https://linkedin.com/in/jane",
                    "note": "Key contact",
                    "message": "Hi",
                }
            ],
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "set_contacts") as mock_contacts,
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "outreach_replaced"
            contacts = mock_contacts.call_args[0][1]
            assert len(contacts) == 1
            assert contacts[0].name == "Jane"

    def test_queue_outreach_empty(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "outreach", "name": "TestCo", "contacts": []}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "_resolve_page_id", return_value="p1"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "error"

    def test_queue_interview_questions(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "interview_questions",
            "name": "TestCo",
            "questions": [{"question": "Q1?", "answer": "A1."}],
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "set_interview_questions"),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"

    def test_queue_interview_questions_empty(
        self, tracker: NotionTracker, tmp_project: Path
    ) -> None:
        task = {"command": "interview_questions", "name": "TestCo", "questions": []}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "_resolve_page_id", return_value="p1"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "error"

    def test_queue_questions_to_ask(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "questions_to_ask",
            "name": "TestCo",
            "questions": ["Q1?", "Q2?"],
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "set_questions_to_ask"),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"

    def test_queue_questions_to_ask_empty(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "questions_to_ask", "name": "TestCo", "questions": []}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "_resolve_page_id", return_value="p1"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "error"

    def test_queue_job_description(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "job_description",
            "name": "TestCo",
            "job_description": "Great role for senior engineers",
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "set_job_description"),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"

    def test_queue_job_description_empty(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "job_description", "name": "TestCo", "job_description": ""}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "_resolve_page_id", return_value="p1"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "error"

    def test_queue_fit_assessment(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "fit_assessment",
            "name": "TestCo",
            "score": 80,
            "reasoning": "Good fit",
            "green_flags": ["remote"],
            "red_flags": [],
            "gaps": [],
            "keywords_missing": [],
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "set_fit_assessment"),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "fit_assessment_replaced"

    def test_queue_interview_prep_creates(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "interview_prep",
            "name": "TestCo",
            "date": "2026-03-15",
            "interviewer": "Jane",
            "interview_type": "Technical",
            "prep_notes": "Study arch",
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "_ensure_interviews_db_schema", return_value="idb-1"),
            patch.object(tracker, "_find_interview_entry", return_value=None),
            patch.object(tracker, "add_interview_entry", return_value="entry-1"),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "interview_prep_created"

    def test_queue_interview_prep_updates(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "interview_prep",
            "name": "TestCo",
            "date": "2026-03-15",
            "interviewer": "Jane",
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "_ensure_interviews_db_schema", return_value="idb-1"),
            patch.object(tracker, "_find_interview_entry", return_value="existing-entry"),
            patch.object(tracker, "update_interview_entry"),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "interview_prep_updated"

    def test_queue_interview_prep_no_date(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "interview_prep", "name": "TestCo"}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "_resolve_page_id", return_value="p1"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "error"
            assert "date" in result["message"]

    def test_queue_interview_prep_with_questions(
        self, tracker: NotionTracker, tmp_project: Path
    ) -> None:
        task = {
            "command": "interview_prep",
            "name": "TestCo",
            "date": "2026-03-15",
            "interview_questions": [{"question": "Q1?", "answer": "A1."}],
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "_ensure_interviews_db_schema", return_value="idb-1"),
            patch.object(tracker, "_find_interview_entry", return_value=None),
            patch.object(tracker, "add_interview_entry", return_value="entry-1"),
            patch.object(tracker, "set_interview_questions") as mock_set_q,
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            mock_set_q.assert_called_once()

    def test_queue_debrief_creates(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "debrief",
            "name": "TestCo",
            "date": "2026-03-15",
            "interviewer": "Jane",
            "outcome": "Passed",
            "debrief": "Great call",
            "vibe": 4,
            "questions_they_asked": ["Why?"],
            "questions_i_asked": ["What?"],
            "follow_up": "Send refs",
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "_ensure_interviews_db_schema", return_value="idb-1"),
            patch.object(tracker, "_find_interview_entry", return_value=None),
            patch.object(tracker, "add_interview_entry", return_value="entry-1"),
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "debrief_created"

    def test_queue_debrief_updates(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {
            "command": "debrief",
            "name": "TestCo",
            "date": "2026-03-15",
            "interviewer": "Jane",
            "outcome": "Passed",
            "vibe": "3",  # String vibe
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "_ensure_interviews_db_schema", return_value="idb-1"),
            patch.object(tracker, "_find_interview_entry", return_value="existing-entry"),
            patch.object(tracker, "update_interview_entry") as mock_update,
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "debrief_updated"
            # Vibe should be converted to int
            interview = mock_update.call_args[0][1]
            assert interview.vibe == 3

    def test_queue_debrief_vibe_non_digit_string(
        self, tracker: NotionTracker, tmp_project: Path
    ) -> None:
        task = {
            "command": "debrief",
            "name": "TestCo",
            "date": "2026-03-15",
            "vibe": "bad",
        }
        filepath = self._write_queue_file(tmp_project, task)
        with (
            patch.object(tracker, "_resolve_page_id", return_value="p1"),
            patch.object(tracker, "_ensure_interviews_db_schema", return_value="idb-1"),
            patch.object(tracker, "_find_interview_entry", return_value=None),
            patch.object(tracker, "add_interview_entry", return_value="entry-1") as mock_add,
        ):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            interview = mock_add.call_args[0][1]
            assert interview.vibe == 0

    def test_queue_debrief_no_date(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "debrief", "name": "TestCo"}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "_resolve_page_id", return_value="p1"):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "error"

    def test_queue_migrate_interviews(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "migrate_interviews_schema"}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "migrate_all_interviews_dbs", return_value=[]):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "ok"
            assert result["action"] == "migrate_interviews_schema"

    def test_queue_exception_handling(self, tracker: NotionTracker, tmp_project: Path) -> None:
        task = {"command": "create", "name": "FailCo"}
        filepath = self._write_queue_file(tmp_project, task)
        with patch.object(tracker, "_find_page", side_effect=NotionAPIError(500, "Server error")):
            result = tracker.process_queue_file(filepath)
            assert result["status"] == "error"
            assert "500" in result["message"]


# ---------------------------------------------------------------------------
# migrate_all_interviews_dbs
# ---------------------------------------------------------------------------


class TestMigrateAllInterviewsDbs:
    """Tests for migrate_all_interviews_dbs."""

    def test_migration(self, tracker: NotionTracker) -> None:
        apps = [
            Application(name="A", page_id="p1"),
            Application(name="B", page_id="p2"),
            Application(name="C"),  # no page_id, skipped
        ]
        with (
            patch.object(tracker, "list_all", return_value=apps),
            patch.object(tracker, "_find_interviews_db", side_effect=["db-1", None]),
            patch.object(
                tracker,
                "_ensure_interviews_db_schema",
                side_effect=["db-1", "new-db-2"],
            ),
        ):
            results = tracker.migrate_all_interviews_dbs()
            assert len(results) == 2
            assert results[0]["action"] == "patched_existing_db"
            assert results[1]["action"] == "created_new_db"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestExceptions:
    """Tests for NotionAPIError and NotionConnectionError."""

    def test_notion_api_error(self) -> None:
        err = NotionAPIError(404, "Not found", "https://api.notion.com/v1/pages/x")
        assert err.status_code == 404
        assert err.url == "https://api.notion.com/v1/pages/x"
        assert "404" in str(err)

    def test_notion_connection_error(self) -> None:
        err = NotionConnectionError("Connection refused")
        assert "Connection refused" in str(err)

    def test_notion_api_error_default_url(self) -> None:
        err = NotionAPIError(500, "Internal error")
        assert err.url == ""


# ---------------------------------------------------------------------------
# MANAGED_SECTIONS and SECTION_ALIASES constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify class-level constants."""

    def test_managed_sections_count(self) -> None:
        assert len(NotionTracker.MANAGED_SECTIONS) == 7

    def test_managed_sections_order(self) -> None:
        assert NotionTracker.MANAGED_SECTIONS[0] == "Job Description"
        assert NotionTracker.MANAGED_SECTIONS[-1] == "Questions to Ask"

    def test_section_aliases(self) -> None:
        aliases = NotionTracker.SECTION_ALIASES
        assert aliases["questions to ask in an interview"] == "Questions to Ask"
        assert aliases["questions to ask during an interview"] == "Questions to Ask"
