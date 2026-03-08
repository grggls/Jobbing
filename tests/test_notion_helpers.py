"""Tests for pure helper functions in jobbing.tracker.notion.

Covers all module-level property builders, block builders, inline markdown
parsing, and markdown-to-blocks conversion. No I/O or mocking required.
"""

from __future__ import annotations

from jobbing.models import Contact
from jobbing.tracker.notion import (
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
# Property builders
# ---------------------------------------------------------------------------


class TestTitle:
    def test_basic(self) -> None:
        result = _title("Acme Corp")
        assert result == {"title": [{"text": {"content": "Acme Corp"}}]}

    def test_empty_string(self) -> None:
        result = _title("")
        assert result == {"title": [{"text": {"content": ""}}]}

    def test_special_characters(self) -> None:
        result = _title("Foo & Bar — 'Test'")
        assert result["title"][0]["text"]["content"] == "Foo & Bar — 'Test'"

    def test_unicode(self) -> None:
        result = _title("Uber Eats")
        assert result["title"][0]["text"]["content"] == "Uber Eats"


class TestRichText:
    def test_basic(self) -> None:
        result = _rich_text("hello world")
        assert result == {"rich_text": [{"text": {"content": "hello world"}}]}

    def test_empty_string(self) -> None:
        result = _rich_text("")
        assert result["rich_text"][0]["text"]["content"] == ""

    def test_long_string(self) -> None:
        long = "x" * 5000
        result = _rich_text(long)
        assert result["rich_text"][0]["text"]["content"] == long


class TestSelect:
    def test_basic(self) -> None:
        result = _select("Applied")
        assert result == {"select": {"name": "Applied"}}

    def test_empty_string(self) -> None:
        result = _select("")
        assert result == {"select": {"name": ""}}


class TestMultiSelect:
    def test_single(self) -> None:
        result = _multi_select(["Remote"])
        assert result == {"multi_select": [{"name": "Remote"}]}

    def test_multiple(self) -> None:
        result = _multi_select(["Remote", "Berlin", "NYC"])
        assert result == {
            "multi_select": [
                {"name": "Remote"},
                {"name": "Berlin"},
                {"name": "NYC"},
            ]
        }

    def test_empty_list(self) -> None:
        result = _multi_select([])
        assert result == {"multi_select": []}


class TestNumber:
    def test_integer(self) -> None:
        result = _number(85)
        assert result == {"number": 85}

    def test_float(self) -> None:
        result = _number(3.14)
        assert result == {"number": 3.14}

    def test_zero(self) -> None:
        result = _number(0)
        assert result == {"number": 0}

    def test_negative(self) -> None:
        result = _number(-10)
        assert result == {"number": -10}


class TestDate:
    def test_iso_date(self) -> None:
        result = _date("2026-03-08")
        assert result == {"date": {"start": "2026-03-08"}}

    def test_empty_string(self) -> None:
        result = _date("")
        assert result == {"date": {"start": ""}}


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------


class TestDividerBlock:
    def test_structure(self) -> None:
        result = _divider_block()
        assert result == {"object": "block", "type": "divider", "divider": {}}


class TestHeading2Block:
    def test_basic(self) -> None:
        result = _heading2_block("Company Research")
        assert result["object"] == "block"
        assert result["type"] == "heading_2"
        rt = result["heading_2"]["rich_text"]
        assert len(rt) == 1
        assert rt[0]["text"]["content"] == "Company Research"

    def test_empty_string(self) -> None:
        result = _heading2_block("")
        assert result["heading_2"]["rich_text"][0]["text"]["content"] == ""


class TestHeading3Block:
    def test_basic(self) -> None:
        result = _heading3_block("Fit Assessment")
        assert result["object"] == "block"
        assert result["type"] == "heading_3"
        rt = result["heading_3"]["rich_text"]
        assert len(rt) == 1
        assert rt[0]["text"]["content"] == "Fit Assessment"

    def test_special_chars(self) -> None:
        result = _heading3_block("Q&A — Round 1")
        assert result["heading_3"]["rich_text"][0]["text"]["content"] == "Q&A — Round 1"


class TestParagraphBlock:
    def test_plain_text(self) -> None:
        result = _paragraph_block("Hello world")
        assert result["object"] == "block"
        assert result["type"] == "paragraph"
        rt = result["paragraph"]["rich_text"]
        assert len(rt) == 1
        assert rt[0]["text"]["content"] == "Hello world"

    def test_with_bold(self) -> None:
        result = _paragraph_block("This is **bold** text")
        rt = result["paragraph"]["rich_text"]
        assert len(rt) == 3
        assert rt[0]["text"]["content"] == "This is "
        assert rt[1]["text"]["content"] == "bold"
        assert rt[1]["annotations"]["bold"] is True
        assert rt[2]["text"]["content"] == " text"

    def test_empty_string(self) -> None:
        result = _paragraph_block("")
        rt = result["paragraph"]["rich_text"]
        assert len(rt) == 1
        assert rt[0]["text"]["content"] == ""


class TestToggleHeading3Block:
    def test_basic(self) -> None:
        children = [_bullet_block("Item 1"), _bullet_block("Item 2")]
        result = _toggle_heading3_block("Job Description", children)
        assert result["object"] == "block"
        assert result["type"] == "heading_3"
        h3 = result["heading_3"]
        assert h3["is_toggleable"] is True
        assert h3["rich_text"][0]["text"]["content"] == "Job Description"
        assert len(h3["children"]) == 2

    def test_empty_children(self) -> None:
        result = _toggle_heading3_block("Empty Section", [])
        assert result["heading_3"]["children"] == []


class TestBulletBlock:
    def test_plain(self) -> None:
        result = _bullet_block("A bullet point")
        assert result["object"] == "block"
        assert result["type"] == "bulleted_list_item"
        rt = result["bulleted_list_item"]["rich_text"]
        assert len(rt) == 1
        assert rt[0]["text"]["content"] == "A bullet point"

    def test_with_bold_and_italic(self) -> None:
        result = _bullet_block("**Bold** and *italic*")
        rt = result["bulleted_list_item"]["rich_text"]
        assert rt[0]["text"]["content"] == "Bold"
        assert rt[0]["annotations"]["bold"] is True
        assert rt[1]["text"]["content"] == " and "
        assert rt[2]["text"]["content"] == "italic"
        assert rt[2]["annotations"]["italic"] is True

    def test_empty(self) -> None:
        result = _bullet_block("")
        rt = result["bulleted_list_item"]["rich_text"]
        assert rt[0]["text"]["content"] == ""


class TestQaBulletBlock:
    def test_basic(self) -> None:
        result = _qa_bullet_block("What is X?", "X is a thing.")
        assert result["type"] == "bulleted_list_item"
        rt = result["bulleted_list_item"]["rich_text"]
        assert rt[0]["text"]["content"] == "What is X?"
        children = result["bulleted_list_item"]["children"]
        assert len(children) == 1
        child_rt = children[0]["bulleted_list_item"]["rich_text"]
        assert child_rt[0]["text"]["content"] == "X is a thing."

    def test_empty_answer(self) -> None:
        result = _qa_bullet_block("Question?", "")
        child_rt = result["bulleted_list_item"]["children"][0]["bulleted_list_item"]["rich_text"]
        assert child_rt[0]["text"]["content"] == ""


# ---------------------------------------------------------------------------
# _contact_bullet_block
# ---------------------------------------------------------------------------


class TestContactBulletBlock:
    def test_name_only(self) -> None:
        contact = Contact(name="Jane Doe", title="", linkedin="")
        result = _contact_bullet_block(contact)
        assert result["type"] == "bulleted_list_item"
        rt = result["bulleted_list_item"]["rich_text"]
        assert len(rt) == 1
        assert rt[0]["text"]["content"] == "Jane Doe"
        assert rt[0]["annotations"]["bold"] is True
        assert "children" not in result["bulleted_list_item"]

    def test_name_and_title(self) -> None:
        contact = Contact(name="Jane Doe", title="VP Eng", linkedin="")
        result = _contact_bullet_block(contact)
        rt = result["bulleted_list_item"]["rich_text"]
        assert len(rt) == 2
        assert rt[0]["text"]["content"] == "Jane Doe"
        assert rt[1]["text"]["content"] == " — VP Eng"

    def test_name_title_linkedin(self) -> None:
        contact = Contact(
            name="Jane Doe",
            title="VP Eng",
            linkedin="https://www.linkedin.com/in/janedoe",
        )
        result = _contact_bullet_block(contact)
        rt = result["bulleted_list_item"]["rich_text"]
        assert len(rt) == 4
        assert rt[0]["text"]["content"] == "Jane Doe"
        assert rt[1]["text"]["content"] == " — VP Eng"
        assert rt[2]["text"]["content"] == " — "
        assert rt[3]["text"]["content"] == "linkedin.com/in/janedoe"
        assert rt[3]["text"]["link"]["url"] == "https://www.linkedin.com/in/janedoe"

    def test_linkedin_url_strip_http(self) -> None:
        contact = Contact(
            name="Bob",
            title="",
            linkedin="http://linkedin.com/in/bob",
        )
        result = _contact_bullet_block(contact)
        rt = result["bulleted_list_item"]["rich_text"]
        link_segment = rt[-1]
        assert link_segment["text"]["content"] == "linkedin.com/in/bob"
        assert link_segment["text"]["link"]["url"] == "http://linkedin.com/in/bob"

    def test_linkedin_url_strip_https_no_www(self) -> None:
        contact = Contact(
            name="Bob",
            title="",
            linkedin="https://linkedin.com/in/bob",
        )
        result = _contact_bullet_block(contact)
        rt = result["bulleted_list_item"]["rich_text"]
        link_segment = rt[-1]
        assert link_segment["text"]["content"] == "linkedin.com/in/bob"

    def test_with_note(self) -> None:
        contact = Contact(
            name="Jane Doe",
            title="VP Eng",
            linkedin="",
            note="Ex-Google SRE",
        )
        result = _contact_bullet_block(contact)
        children = result["bulleted_list_item"]["children"]
        assert len(children) == 1
        child_rt = children[0]["bulleted_list_item"]["rich_text"]
        assert child_rt[0]["text"]["content"] == "Ex-Google SRE"

    def test_with_message(self) -> None:
        contact = Contact(
            name="Jane Doe",
            title="VP Eng",
            linkedin="",
            message="Hi Jane, ...",
        )
        result = _contact_bullet_block(contact)
        children = result["bulleted_list_item"]["children"]
        assert len(children) == 1
        child_rt = children[0]["bulleted_list_item"]["rich_text"]
        assert child_rt[0]["text"]["content"] == "Hi Jane, ..."
        assert child_rt[0]["annotations"]["italic"] is True

    def test_with_note_and_message(self) -> None:
        contact = Contact(
            name="Jane Doe",
            title="VP Eng",
            linkedin="",
            note="Leads platform team",
            message="Hi Jane, ...",
        )
        result = _contact_bullet_block(contact)
        children = result["bulleted_list_item"]["children"]
        assert len(children) == 2
        assert children[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == (
            "Leads platform team"
        )
        assert children[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == (
            "Hi Jane, ..."
        )
        assert children[1]["bulleted_list_item"]["rich_text"][0]["annotations"]["italic"] is True

    def test_no_children_when_no_note_or_message(self) -> None:
        contact = Contact(
            name="Jane Doe",
            title="VP Eng",
            linkedin="https://www.linkedin.com/in/janedoe",
        )
        result = _contact_bullet_block(contact)
        assert "children" not in result["bulleted_list_item"]


# ---------------------------------------------------------------------------
# _parse_inline_markdown
# ---------------------------------------------------------------------------


class TestParseInlineMarkdown:
    def test_plain_text(self) -> None:
        segments = _parse_inline_markdown("no markdown here")
        assert len(segments) == 1
        assert segments[0]["text"]["content"] == "no markdown here"
        assert "annotations" not in segments[0]

    def test_empty_string(self) -> None:
        segments = _parse_inline_markdown("")
        assert len(segments) == 1
        assert segments[0]["text"]["content"] == ""

    def test_bold_only(self) -> None:
        segments = _parse_inline_markdown("**bold text**")
        assert len(segments) == 1
        assert segments[0]["text"]["content"] == "bold text"
        assert segments[0]["annotations"]["bold"] is True

    def test_italic_only(self) -> None:
        segments = _parse_inline_markdown("*italic text*")
        assert len(segments) == 1
        assert segments[0]["text"]["content"] == "italic text"
        assert segments[0]["annotations"]["italic"] is True

    def test_bold_in_middle(self) -> None:
        segments = _parse_inline_markdown("before **bold** after")
        assert len(segments) == 3
        assert segments[0]["text"]["content"] == "before "
        assert "annotations" not in segments[0]
        assert segments[1]["text"]["content"] == "bold"
        assert segments[1]["annotations"]["bold"] is True
        assert segments[2]["text"]["content"] == " after"
        assert "annotations" not in segments[2]

    def test_italic_in_middle(self) -> None:
        segments = _parse_inline_markdown("before *italic* after")
        assert len(segments) == 3
        assert segments[0]["text"]["content"] == "before "
        assert segments[1]["text"]["content"] == "italic"
        assert segments[1]["annotations"]["italic"] is True
        assert segments[2]["text"]["content"] == " after"

    def test_bold_and_italic_mixed(self) -> None:
        segments = _parse_inline_markdown("**bold** and *italic*")
        assert len(segments) == 3
        assert segments[0]["text"]["content"] == "bold"
        assert segments[0]["annotations"]["bold"] is True
        assert segments[1]["text"]["content"] == " and "
        assert segments[2]["text"]["content"] == "italic"
        assert segments[2]["annotations"]["italic"] is True

    def test_multiple_bolds(self) -> None:
        segments = _parse_inline_markdown("**a** then **b**")
        assert len(segments) == 3
        assert segments[0]["text"]["content"] == "a"
        assert segments[0]["annotations"]["bold"] is True
        assert segments[1]["text"]["content"] == " then "
        assert segments[2]["text"]["content"] == "b"
        assert segments[2]["annotations"]["bold"] is True

    def test_bold_at_start(self) -> None:
        segments = _parse_inline_markdown("**start** rest")
        assert len(segments) == 2
        assert segments[0]["text"]["content"] == "start"
        assert segments[0]["annotations"]["bold"] is True
        assert segments[1]["text"]["content"] == " rest"

    def test_bold_at_end(self) -> None:
        segments = _parse_inline_markdown("start **end**")
        assert len(segments) == 2
        assert segments[0]["text"]["content"] == "start "
        assert segments[1]["text"]["content"] == "end"
        assert segments[1]["annotations"]["bold"] is True

    def test_italic_at_start(self) -> None:
        segments = _parse_inline_markdown("*start* rest")
        assert len(segments) == 2
        assert segments[0]["text"]["content"] == "start"
        assert segments[0]["annotations"]["italic"] is True
        assert segments[1]["text"]["content"] == " rest"

    def test_consecutive_bold_italic(self) -> None:
        segments = _parse_inline_markdown("**bold***italic*")
        assert len(segments) == 2
        assert segments[0]["text"]["content"] == "bold"
        assert segments[0]["annotations"]["bold"] is True
        assert segments[1]["text"]["content"] == "italic"
        assert segments[1]["annotations"]["italic"] is True

    def test_special_characters_in_bold(self) -> None:
        segments = _parse_inline_markdown("**foo & bar**")
        assert segments[0]["text"]["content"] == "foo & bar"
        assert segments[0]["annotations"]["bold"] is True

    def test_asterisks_without_closing(self) -> None:
        """Unmatched asterisks pass through as plain text."""
        segments = _parse_inline_markdown("not **bold")
        assert len(segments) == 1
        assert segments[0]["text"]["content"] == "not **bold"


# ---------------------------------------------------------------------------
# _markdown_to_blocks
# ---------------------------------------------------------------------------


class TestMarkdownToBlocks:
    # --- Headings ---

    def test_h1_becomes_heading2(self) -> None:
        blocks = _markdown_to_blocks("# Main Title")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "heading_2"
        assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Main Title"

    def test_h2_becomes_heading3(self) -> None:
        blocks = _markdown_to_blocks("## Sub Title")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "heading_3"
        assert blocks[0]["heading_3"]["rich_text"][0]["text"]["content"] == "Sub Title"

    def test_h3_becomes_heading3(self) -> None:
        blocks = _markdown_to_blocks("### Sub Sub Title")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "heading_3"
        assert blocks[0]["heading_3"]["rich_text"][0]["text"]["content"] == "Sub Sub Title"

    def test_heading_order_h3_before_h2_before_h1(self) -> None:
        """Verify ### is matched before ## before # to avoid prefix collisions."""
        md = "### Three\n## Two\n# One"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 3
        assert blocks[0]["type"] == "heading_3"
        assert blocks[0]["heading_3"]["rich_text"][0]["text"]["content"] == "Three"
        assert blocks[1]["type"] == "heading_3"
        assert blocks[1]["heading_3"]["rich_text"][0]["text"]["content"] == "Two"
        assert blocks[2]["type"] == "heading_2"
        assert blocks[2]["heading_2"]["rich_text"][0]["text"]["content"] == "One"

    # --- Bullets ---

    def test_single_bullet(self) -> None:
        blocks = _markdown_to_blocks("- Item one")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "bulleted_list_item"
        rt = blocks[0]["bulleted_list_item"]["rich_text"]
        assert rt[0]["text"]["content"] == "Item one"

    def test_multiple_bullets(self) -> None:
        md = "- First\n- Second\n- Third"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 3
        assert all(b["type"] == "bulleted_list_item" for b in blocks)

    def test_nested_bullet(self) -> None:
        md = "- Parent\n  - Child"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 1
        parent = blocks[0]
        assert parent["type"] == "bulleted_list_item"
        assert parent["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Parent"
        children = parent["bulleted_list_item"]["children"]
        assert len(children) == 1
        assert children[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Child"

    def test_multiple_nested_bullets(self) -> None:
        md = "- Parent\n  - Child 1\n  - Child 2"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 1
        children = blocks[0]["bulleted_list_item"]["children"]
        assert len(children) == 2
        assert children[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Child 1"
        assert children[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Child 2"

    def test_nested_bullet_without_parent_becomes_top_level(self) -> None:
        """An indented bullet with no preceding top-level bullet is a standalone."""
        blocks = _markdown_to_blocks("  - Orphan child")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "bulleted_list_item"
        assert blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Orphan child"

    def test_nested_bullet_after_non_bullet_becomes_standalone(self) -> None:
        """An indented bullet after a heading (not a bullet) becomes standalone."""
        md = "# Heading\n  - Indented"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 2
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "bulleted_list_item"

    def test_bullet_with_bold_inline(self) -> None:
        blocks = _markdown_to_blocks("- This is **bold** text")
        rt = blocks[0]["bulleted_list_item"]["rich_text"]
        assert len(rt) == 3
        assert rt[1]["text"]["content"] == "bold"
        assert rt[1]["annotations"]["bold"] is True

    def test_bullet_with_italic_inline(self) -> None:
        blocks = _markdown_to_blocks("- This is *italic* text")
        rt = blocks[0]["bulleted_list_item"]["rich_text"]
        assert len(rt) == 3
        assert rt[1]["text"]["content"] == "italic"
        assert rt[1]["annotations"]["italic"] is True

    # --- Paragraphs ---

    def test_plain_paragraph(self) -> None:
        blocks = _markdown_to_blocks("Just some text")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"
        rt = blocks[0]["paragraph"]["rich_text"]
        assert rt[0]["text"]["content"] == "Just some text"

    def test_multiline_paragraph(self) -> None:
        """Each non-blank line becomes its own paragraph (no <br> artifacts)."""
        md = "Line one\nLine two\nLine three"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 3
        for block in blocks:
            assert block["type"] == "paragraph"
        assert blocks[0]["paragraph"]["rich_text"][0]["text"]["content"] == "Line one"
        assert blocks[1]["paragraph"]["rich_text"][0]["text"]["content"] == "Line two"
        assert blocks[2]["paragraph"]["rich_text"][0]["text"]["content"] == "Line three"

    def test_blank_lines_separate_paragraphs(self) -> None:
        md = "First paragraph\n\nSecond paragraph"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 2
        assert blocks[0]["type"] == "paragraph"
        assert blocks[1]["type"] == "paragraph"
        assert blocks[0]["paragraph"]["rich_text"][0]["text"]["content"] == "First paragraph"
        assert blocks[1]["paragraph"]["rich_text"][0]["text"]["content"] == "Second paragraph"

    def test_paragraph_with_bold(self) -> None:
        blocks = _markdown_to_blocks("This is **important** info")
        rt = blocks[0]["paragraph"]["rich_text"]
        assert len(rt) == 3
        assert rt[1]["annotations"]["bold"] is True

    # --- Empty / edge cases ---

    def test_empty_string(self) -> None:
        blocks = _markdown_to_blocks("")
        assert blocks == []

    def test_only_blank_lines(self) -> None:
        blocks = _markdown_to_blocks("\n\n\n")
        assert blocks == []

    def test_only_whitespace(self) -> None:
        blocks = _markdown_to_blocks("   \n   \n   ")
        assert blocks == []

    # --- Mixed content ---

    def test_heading_then_bullets(self) -> None:
        md = "# Key Topics\n- Topic A\n- Topic B"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 3
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "bulleted_list_item"
        assert blocks[2]["type"] == "bulleted_list_item"

    def test_heading_paragraph_bullets(self) -> None:
        md = "## Section\nSome intro text\n\n- Bullet 1\n- Bullet 2"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 4
        assert blocks[0]["type"] == "heading_3"
        assert blocks[1]["type"] == "paragraph"
        assert blocks[2]["type"] == "bulleted_list_item"
        assert blocks[3]["type"] == "bulleted_list_item"

    def test_multiple_sections(self) -> None:
        md = "# Section One\n- Item A\n\n## Section Two\n- Item B"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 4
        assert blocks[0]["type"] == "heading_2"
        assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Section One"
        assert blocks[1]["type"] == "bulleted_list_item"
        assert blocks[2]["type"] == "heading_3"
        assert blocks[2]["heading_3"]["rich_text"][0]["text"]["content"] == "Section Two"
        assert blocks[3]["type"] == "bulleted_list_item"

    def test_complex_mixed_document(self) -> None:
        md = (
            "# Main Title\n"
            "Introduction text here.\n"
            "\n"
            "## Details\n"
            "- **Bold bullet** with extra\n"
            "  - Nested child\n"
            "- Second bullet\n"
            "\n"
            "### Notes\n"
            "Final paragraph."
        )
        blocks = _markdown_to_blocks(md)
        assert blocks[0]["type"] == "heading_2"
        assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Main Title"
        assert blocks[1]["type"] == "paragraph"
        assert blocks[2]["type"] == "heading_3"
        # Bold bullet with nested child
        assert blocks[3]["type"] == "bulleted_list_item"
        children = blocks[3]["bulleted_list_item"].get("children", [])
        assert len(children) == 1
        # Second bullet
        assert blocks[4]["type"] == "bulleted_list_item"
        # ### Notes heading
        assert blocks[5]["type"] == "heading_3"
        assert blocks[5]["heading_3"]["rich_text"][0]["text"]["content"] == "Notes"
        # Final paragraph
        assert blocks[6]["type"] == "paragraph"

    def test_tab_indented_bullet_treated_as_nested(self) -> None:
        """Tabs produce indentation, so line != line.lstrip() is true."""
        md = "- Parent\n\t- Child"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 1
        children = blocks[0]["bulleted_list_item"].get("children", [])
        assert len(children) == 1

    def test_four_space_indented_bullet(self) -> None:
        md = "- Parent\n    - Child"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 1
        children = blocks[0]["bulleted_list_item"]["children"]
        assert len(children) == 1
        assert children[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Child"

    def test_paragraph_flushed_before_heading(self) -> None:
        """Paragraph lines are flushed when a heading is encountered."""
        md = "Some text\n# Heading"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 2
        assert blocks[0]["type"] == "paragraph"
        assert blocks[1]["type"] == "heading_2"

    def test_paragraph_flushed_before_bullet(self) -> None:
        md = "Some text\n- Bullet"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 2
        assert blocks[0]["type"] == "paragraph"
        assert blocks[1]["type"] == "bulleted_list_item"

    def test_trailing_newline(self) -> None:
        md = "- Item\n"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "bulleted_list_item"

    def test_multiple_blank_lines_between_content(self) -> None:
        md = "Para 1\n\n\n\nPara 2"
        blocks = _markdown_to_blocks(md)
        assert len(blocks) == 2
        assert blocks[0]["type"] == "paragraph"
        assert blocks[1]["type"] == "paragraph"
