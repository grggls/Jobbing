# /apply — Generate Application Documents

Execute the full application workflow: Notion entry, tailored JSON, PDFs, and ATS check. Run this after `/analyze` and Greg's go decision.

## Prerequisites
- `/analyze` has been run and Greg has approved the Experience to Highlight bullets
- `WORKFLOW.md` and `CONTEXT.md` are loaded

## Instructions

### Step 1: Create Notion Tracker Entry

Write a JSON file to `notion_queue/` with a descriptive name (e.g., `notion_queue/20260222_companyname_create.json`):

```json
{
  "command": "create",
  "name": "CompanyName",
  "position": "Role Title",
  "date": "YYYY-MM-DD",
  "url": "https://...",
  "environment": ["Remote", "Berlin office"],
  "salary": "€130K–€170K",
  "focus": ["Domain1", "Domain2"],
  "vision": "Company vision",
  "mission": "Company mission",
  "highlights": ["Bullet 1", "Bullet 2", "Bullet 3"]
}
```

The launchd agent on Greg's Mac processes queue files automatically. Or Greg can run `jobbing queue` manually.

### Step 2: Generate Tailored JSON

Create `companies/{company}/{company}.json` following these rules:

1. **Use `companies/dash0/dash0.json` as the structural template** (read it for the exact schema)
2. **Tailor the CV data:**
   - Rewrite summary to lead with the role's core requirements
   - Reorder/rewrite core skills to front-load what matters
   - Rewrite key achievements using X-Y-Z formula ("Accomplished X as measured by Y, by doing Z")
   - Add role-specific bullets to relevant jobs (draw from CONTEXT.md for older roles)
   - Work in missing keywords naturally
   - Set location per WORKFLOW.md Location Logic
   - Include `earlierExperience` when TradingScreen/JP Morgan add value
3. **Tailor the CL data:**
   - Opening: 20+ years + role-specific framing
   - Para 1: Current work (Solo Recon + Modern Electric) — chronology is sacred
   - Para 2: Most relevant leadership role for this posting
   - Para 3: Largest-scale infrastructure leadership (usually Mobimeo)
   - Para 4: Cross-functional / people leadership highlights
   - Closing: Available for conversation
   - Single page, professional, keyword-rich

### Step 3: Generate PDFs

```bash
jobbing pdf {company}
```

Or if not installed: `.venv/bin/python3 -m jobbing.cli pdf {company}`

### Step 4: ATS Check

Extract text from the generated PDF and verify:
- Clean text extraction (no garbled characters)
- Key terms from the posting appear in the CV
- Count keyword frequencies for the most important terms

### Step 5: Present Results

Show Greg:
- File paths and sizes for the generated PDFs
- ATS keyword frequency summary
- Any concerns about the documents

**Do NOT auto-mark as "Applied."** Status updates are Greg's decision. When Greg says to mark as Applied, write:

```json
{"command": "update", "page_id": "PAGE_ID", "status": "Applied"}
```

## Critical Rules
- **"Most recently" = Solo Recon/Modern Electric.** Never lead with Mobimeo as most recent.
- **People management started mid-2017.** 8+ years as of 2026.
- **No AI tells.** No "aligns perfectly" or summative self-congratulation. Show, don't tell.
- **No fake metrics.** Only use numbers from CONTEXT.md.
- **No TODO comments or placeholder content** in the JSON.
- **Queue-only for Notion writes.** Do not use Notion MCP write tools — they are buggy.
