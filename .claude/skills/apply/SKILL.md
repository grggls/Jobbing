---
name: apply
description: Execute the full application workflow after /analyze approval. Creates Obsidian hub file, adds board card, generates tailored CV and cover letter JSON, renders PDFs, and runs ATS keyword check.
---

# Generate Application Documents

Execute the full application workflow: hub file creation, tailored JSON, PDFs, and ATS check. Run this after `/analyze` and Greg's go decision.

## Prerequisites
- `/analyze` has been run and Greg has approved the Experience to Highlight bullets
- `WORKFLOW.md` and `CONTEXT.md` are loaded

## Instructions

### Step 1: Create Hub File and Board Card

**1a. Create the company hub file** at `kanban/companies/{Company Name}.md`:

```markdown
---
company: Company Name
position: Role Title
status: Targeted
date: YYYY-MM-DD
url: https://...
environment: Remote, Berlin office
salary: €130K–€170K
focus:
  - Domain1
  - Domain2
vision: Company vision statement
mission: Company mission statement
score: 75
conclusion: ""
---

## Documents

<!-- Updated automatically by `jobbing pdf {company}` -->

## Interviews

<!-- Interview files linked here as they are created -->

## Fit Assessment

**Score: 75**

2–3 sentence summary of fit reasoning from /analyze.

**Green flags:**
- Strong alignment signal 1
- Signal 2

**Red flags:**
- Concern 1

**Gaps:**
- Missing skill 1

**Keywords missing:** keyword1, keyword2

## Company Research

- Founded 20XX, Series X ($XM raised)
- Headcount, HQ location
- Glassdoor rating, culture notes

## Experience to Highlight

- Approved bullet 1 from /analyze
- Approved bullet 2
- Approved bullet 3

## Job Description

Full job posting text here...

## Outreach Contacts

<!-- Populated by /outreach -->

## Questions I Might Get Asked

<!-- Populated by /prep -->

## Questions to Ask

<!-- Populated by /prep -->

## Conclusion

<!-- Populated when closing out the application -->
```

**1b. Add a board card** to `kanban/Job Tracker.md` in the Targeted lane:

```
- [ ] [[companies/Company Name|Company Name]] — Role Title · Score: 75 · YYYY-MM-DD
```

### Step 2: Present Tailoring Plan — CHECKPOINT

Before generating any documents, present Greg with the tailoring strategy:

**CV tailoring plan:**
- **Summary angle:** How the opening paragraphs will be framed for this role
- **Key roles to emphasize:** Which positions get the most space and why
- **Domain signals:** Specific experience being highlighted (e.g., crypto exchange work for fintech roles, cleantech for sustainability roles)
- **Keywords to weave in:** Terms from the posting that will appear in the CV
- **Earlier Experience:** Whether TradingScreen/JP Morgan/other older roles add value and should be included
- **Location line:** Berlin, New York, or both

**Cover letter angle:**
- **Opening framing:** How the 20+ years will be positioned
- **Paragraph plan:** Which roles/achievements map to which paragraphs
- **Domain-specific callouts:** Specific experience being highlighted in the narrative

**STOP and wait for Greg's approval.** Greg may want to adjust emphasis, add/remove domain signals, or change the angle. Do not generate the JSON until Greg confirms.

### Step 3: Generate Tailored JSON

After Greg approves the tailoring plan, create `companies/{company}/{company}.json`:

1. **Use `examples/example_company.json` as the structural template** (read it for the exact schema)
2. **Tailor the CV data:**
   - Rewrite summary to lead with the role's core requirements — include the domain signals Greg approved
   - Reorder/rewrite core skills to front-load what matters
   - Rewrite key achievements using X-Y-Z formula ("Accomplished X as measured by Y, by doing Z")
   - Add role-specific bullets to relevant jobs (draw from CONTEXT.md for older roles)
   - Work in missing keywords naturally
   - Set location per WORKFLOW.md Location Logic
   - Include `earlierExperience` when approved in the tailoring plan
3. **Tailor the CL data:**
   - Opening: 20+ years + role-specific framing
   - Para 1: Current work (Solo Recon + Modern Electric) — chronology is sacred
   - Para 2: Most relevant leadership role for this posting
   - Para 3: Largest-scale infrastructure leadership (usually Mobimeo)
   - Para 4: Cross-functional / people leadership highlights
   - Closing: Available for conversation
   - Single page, professional, keyword-rich
4. **Verify your own work:** Before moving on, re-read the generated JSON and confirm that every domain signal and keyword from the approved tailoring plan actually appears where you said it would. If you said "Aluna Social crypto exchange in the summary," it must be in the summary.

### Step 4: Generate PDFs

```bash
jobbing pdf {company}
```

Or if not installed: `.venv/bin/python3 -m jobbing.cli pdf {company}`

This command automatically updates the `## Documents` section of the hub file with the generated PDF paths.

### Step 5: ATS Check

Extract text from the generated PDF and verify:
- Clean text extraction (no garbled characters)
- Key terms from the posting appear in the CV
- Count keyword frequencies for the most important terms

### Step 6: Present Results

Show Greg:
- File paths and sizes for the generated PDFs
- ATS keyword frequency summary
- Any concerns about the documents

**Do NOT auto-mark as "Applied."** Status updates are Greg's decision. When Greg says to mark as Applied, edit the hub file's frontmatter:

```yaml
status: Applied
```

And update the board card in `kanban/Job Tracker.md` — move it to the Applied lane or check its checkbox as appropriate.

## Critical Rules
- **"Most recently" = Solo Recon/Modern Electric.** Never lead with Mobimeo as most recent.
- **People management started mid-2017.** 8+ years as of 2026. Never write "6+ years."
- **No AI tells.** No "aligns perfectly" or summative self-congratulation. Show, don't tell.
- **No fake metrics.** Only use numbers from CONTEXT.md.
- **No TODO comments or placeholder content** in the JSON.
- **All tracker writes are direct file edits.** Edit the hub file at `kanban/companies/{Company}.md` using Read/Edit/Write tools. No queue files, no launchd, no Notion MCP.

## Do Not
### Process
- Skip the tailoring plan checkpoint (Step 2) — present the strategy and STOP until Greg approves
- Generate the JSON before Greg has reviewed and approved the tailoring plan
- Skip reading `examples/example_company.json` before generating JSON — it's the structural template
- Auto-mark "Applied" or change any status without Greg's explicit instruction
- Claim you included a domain signal or keyword and then not actually include it — verify your own work (Step 3.4)

### CV Writing
- Use banned AI-tell phrases: "aligns perfectly", "uniquely positioned", "proven track record", "passionate about", "thrilled to", "excited to bring", "making me an ideal candidate"
- Write summative sentences that restate the obvious connection between Greg's experience and the role — the reader connects the dots
- Invent metrics not in CONTEXT.md — no fake percentages, team sizes, cost savings, or time improvements
- Write "6+ years of people management" — it's 8+ (started mid-2017)
- Lead with Mobimeo in the summary or as "most recent" — Solo Recon and Modern Electric are current
- Present German language as a qualification — it's A2
- Claim management responsibility at IC-only roles (BuzzFeed, Yara, TradingScreen were IC)
- Describe Solo Recon as having customers, revenue, or traction beyond ~12 users
- Say "led a team of 23" for any role other than Mobimeo
- Use the same generic bullet points across different company JSONs — every JSON must be tailored
- Add filler content to pad length — be concise and substantive
- Use marketing superlatives: "world-class", "cutting-edge", "unparalleled", "blazingly fast"

### Cover Letter Writing
- Use the same CL structure for every role — each one maps to the approved paragraph plan
- Write opening paragraphs that are indistinguishable from one company to the next
- End with "I look forward to discussing how my experience aligns with your needs" or similar AI boilerplate
- Write more than one page — cover letters must be single page
- Address the letter "Dear Sir/Madam" — use "Dear Hiring Team," or the hiring manager's name if known

### Technical
- Leave TODO, FIXME, or placeholder comments in the JSON
- Generate JSON that doesn't match the example_company.json schema structure
- Use queue files or launchd for any tracker writes — all writes are direct file edits to markdown files using Read/Edit/Write tools
