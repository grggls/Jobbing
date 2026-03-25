---
name: analyze
description: Analyze a job posting for fit against Greg's profile. Scores 0-100, identifies green/red flags, gaps, salary benchmarks, company intel, and drafts Experience to Highlight bullets. Always the first step before any application work.
---

# Role Fit Assessment

Analyze a job posting for fit against Greg's profile. This is always the first step before any application work.

## Instructions

1. **Read required context files** (if not already loaded this session):
   - `WORKFLOW.md` — authoritative workflow (this skill implements Step 1)
   - `CONTEXT.md` — Greg's profile, career timeline, skills, salary benchmarks
   - `.claude/skills/scoring/SKILL.md` — scoring guidelines (the `/scoring` skill)

2. **The user will paste a job posting.** Analyze it and present:

### Fit Assessment
- **Fit:** Underqualified / right in the pocket / overqualified
- **Match score:** 0–100 (follow the `/scoring` skill and Title Flexibility rules in WORKFLOW.md)
- **Green flags:** Strong alignment — cite specific roles, achievements, and skills from CONTEXT.md
- **Red flags:** Concerns about the role, company, or posting. Look for:
  - Vague titles masking lower-level work
  - Unrealistic scope for one person
  - "Startup" roles that are really contractor gigs
  - Poor Glassdoor reviews or recent layoffs
  - Salary below market for the level
- **Gaps:** Skills or experience the posting asks for that Greg lacks or is light on
- **Missing keywords:** Terms to weave into the CV if we proceed
- **Location:** Which location line to use (Berlin, New York, or both) — see WORKFLOW.md Location Logic

### Salary Read
- Benchmark against CONTEXT.md salary data
- Research via web search if the posting doesn't include a range

### Company Intel
- Web search for: company size, funding stage, recent news, Glassdoor sentiment, tech stack
- Be specific — don't guess at headcount, funding, or culture

### Experience to Highlight
- Draft bullet points for the hub file's "Experience to Highlight" section
- Pay special attention to:
  - Cleantech and sustainability experience (1KOMMA5°/Modern Electric, energy sector work)
  - Education background and how it maps to the role
  - Correct framing of domain-specific experience
  - Accuracy of technical claims and role characterizations

3. **Present the analysis and Experience to Highlight bullets explicitly.** This is a review checkpoint — wait for Greg's feedback before proceeding. Greg may correct, reframe, or add items.

4. **Greg decides: proceed or skip.** If proceeding, run `/apply` next. The `/apply` skill will create the Obsidian hub file at `kanban/companies/{Company}.md` and populate it with the fit assessment data, company research, job description, and Experience to Highlight bullets.

5. **Keep scoring data available for `/apply`.** When Greg says go, the scoring output (score, reasoning, green/red flags, gaps, keywords) must be ready for `/apply` to write into the hub file's `## Fit Assessment` section and `score:` frontmatter field.

## Critical Rules
- **Use `jobbing browse <url>` to fetch JDs.** LinkedIn, Greenhouse, Lever, SmartRecruiters, Workable, and most job boards are blocked from WebFetch/WebSearch. Use `jobbing browse <url>` to fetch via headless Playwright+stealth. For complex multi-step interactions (login walls, paginated search), fall back to Chrome MCP.
- **Chronology is sacred.** Solo Recon and Modern Electric are CURRENT roles (2024–present). Never lead with Mobimeo as most recent.
- **People management started mid-2017.** That's 8+ years as of 2026. Never write "6+ years."
- **No fake metrics.** Don't invent percentages or impact numbers not in CONTEXT.md.
- **Be critical.** A skip is better than a wasted application. Flag weak matches honestly.
- **Be circumspect.** Verify before you claim. Check CONTEXT.md before asserting dates, titles, team sizes, or achievements.

## Do Not
- Inflate the fit score to be encouraging — Greg trusts the score to make go/skip decisions
- Guess at company headcount, funding stage, or culture — web search or say "not found"
- Describe company intel with vague phrases like "well-funded startup" without specifics — find the actual number
- Skip the Experience to Highlight checkpoint — present the bullets and wait for Greg's feedback before moving on
- Rubber-stamp the analysis — if something is weak, say so plainly
- Apply to or positively assess defense contractors, military tech, or weapons companies — firm exclusion
- Claim Greg speaks German professionally — it's A2 (studying), flag any German-language requirement as a gap
- Assert team sizes, dates, or achievements without checking CONTEXT.md — every number must be verified
- Write Experience to Highlight bullets that exaggerate or reframe experience beyond what CONTEXT.md supports
- Move to `/apply` without explicit go from Greg — the analysis is a decision point, not a formality
