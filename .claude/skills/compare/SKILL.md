---
name: compare
description: Side-by-side comparison of two or more active opportunities across weighted dimensions. Reads tracker pages, Fit Assessments, debrief notes, and company research. Read-only — produces a Markdown comparison document, no Notion writes.
---

# Decision Comparison Framework

Compare two or more active opportunities when offers overlap or Greg needs a structured decision framework. This is the final analytical step before Greg makes a career decision.

## Prerequisites

- Two or more tracker pages with at least a Fit Assessment (from `/analyze`)
- Richer output when debrief data (from `/debrief`) and reassessed scores (from `/reassess`) exist, but not required

## Instructions

### Step 1: Load Context

- Read WORKFLOW.md and CONTEXT.md if not already loaded this session
- Read `.claude/skills/scoring/SKILL.md` for the scoring component weights

### Step 2: Identify Companies to Compare

Greg says something like "compare Bandcamp and Cozero" or "compare my top three." Parse the company names from the request.

If Greg says "compare my active ones" or similar, query the tracker for all "In Progress (Interviewing)" pages and compare those.

### Step 3: Gather Data for Each Company

Use Notion MCP read tools (`notion-fetch`, `notion-search`) to collect from each tracker page:

1. **Properties** — Status, Open Position, Salary (Range), Environment, Company Focus, Score
2. **Fit Assessment** — Score, reasoning, green/red flags, gaps
3. **Company Research** — Funding, headcount, Glassdoor, tech stack, recent news
4. **Experience to Highlight** — What was identified as relevant
5. **Interviews DB** — All interview entries with debrief data, vibe ratings, outcomes
6. **Outreach Contacts** — Who Greg has connected with (signals relationship depth)

### Step 4: Score Each Dimension

Evaluate each company across seven weighted dimensions. Use evidence from the tracker data — don't speculate.

| Dimension | Weight | What to Evaluate |
|-----------|--------|------------------|
| Compensation | High | Salary property, negotiation signals from debriefs, equity/VSOP if mentioned, benefits |
| Technical Fit | High | Fit Assessment score, tech stack match from research, debrief impressions of engineering quality |
| Team & Culture | Medium | Debrief vibe scores (averaged), interviewer quality impressions, company research (Glassdoor, culture signals) |
| Mission Alignment | Medium | Company Focus tags, domain match to Greg's interests (cleantech, sustainability, platform eng), Vision/Mission properties |
| Growth Trajectory | Medium | Role scope from debriefs (did it expand or shrink?), company funding/headcount trajectory from research, career path signals |
| Remote & Location | Low | Environment property, entity/visa situation, timezone compatibility, any location changes surfaced in interviews |
| Risk Factors | Low | Red flags from Fit Assessment, Glassdoor concerns, debrief red flags, attrition signals, funding runway concerns |

For each dimension, assign a qualitative rating:

- **Strong** — clear advantage, well-evidenced
- **Good** — positive signal, some evidence
- **Neutral** — no strong signal either way, or mixed
- **Concern** — negative signal with evidence
- **Unknown** — insufficient data to evaluate

### Step 5: Produce the Comparison

Format as a structured Markdown document with three sections:

**1. Summary Table**

A quick-scan grid with each dimension scored per company:

```
| Dimension          | Weight | Company A      | Company B      |
|--------------------|--------|----------------|----------------|
| Compensation       | High   | Strong (€140K) | Concern (€110K)|
| Technical Fit      | High   | Good (score 78)| Strong (score 85)|
| Team & Culture     | Medium | Strong (vibe 4.5)| Neutral (vibe 3)|
| Mission Alignment  | Medium | Strong         | Good           |
| Growth Trajectory  | Medium | Good           | Concern        |
| Remote & Location  | Low    | Strong (remote)| Good (hybrid)  |
| Risk Factors       | Low    | Neutral        | Concern        |
```

**2. Dimension Deep-Dives**

For each dimension, a paragraph per company with specific evidence from the tracker:

```
### Compensation

**Company A:** Salary range €130K–€150K confirmed in recruiter screen (debrief Feb 20).
VSOP mentioned but details pending. Above Greg's €135K floor.

**Company B:** Posting listed €100K–€130K. No negotiation signals in debriefs.
Series A funding (€6.5M) suggests limited room. Below floor at bottom of range.
```

**3. Synthesis and Recommendation**

- Overall assessment: which opportunity looks strongest and why
- Key tradeoffs: what Greg is giving up with each choice
- Open questions: what still needs to be resolved before deciding
- Not a single "winner" — present the structured tradeoffs and let Greg decide

### Step 6: Save the Output

Write the comparison to `companies/comparison-{company1}-vs-{company2}-{date}.md`.

For three or more companies: `companies/comparison-{date}.md`.

This is a **read-only analysis** — no Notion writes.

### Step 7: Present and Discuss

Show Greg the comparison and discuss. He may want to:

- Adjust dimension weights ("location matters more to me than you think")
- Add context the tracker doesn't capture ("Company A's CEO reached out personally")
- Request a revised comparison with updated weights or new information
- Use this as input for a negotiation strategy

## Dimension Scoring Details

### Compensation (High Weight)

- Primary: Salary (Range) property vs Greg's €135K floor
- Secondary: equity/VSOP signals from debriefs or research
- Tertiary: benefits, bonus structure if mentioned
- Context: Berlin vs US compensation norms (see CONTEXT.md salary benchmarks)

### Technical Fit (High Weight)

- Primary: Fit Assessment score (original or reassessed)
- Secondary: tech stack match from company research and debrief impressions
- Tertiary: architecture ownership, platform focus, infrastructure scope
- Adjustment: debrief data may reveal the actual stack differs from the posting

### Team & Culture (Medium Weight)

- Primary: average vibe rating across all debriefs for this company
- Secondary: Glassdoor sentiment from company research
- Tertiary: interviewer quality (did they ask good questions? were they prepared?)
- Signal: multiple vibe 4-5 ratings = strong culture fit; mixed or low = concern

### Mission Alignment (Medium Weight)

- Primary: Company Focus tags vs Greg's interests (cleantech, sustainability, developer tooling, platform eng)
- Secondary: Vision/Mission properties
- Tertiary: domain excitement signals from debriefs ("I was genuinely interested in their approach to...")

### Growth Trajectory (Medium Weight)

- Primary: role scope as revealed in interviews (expanded beyond posting? contracted?)
- Secondary: company trajectory (funding stage, growth rate, headcount trend)
- Tertiary: career path signals (is there a clear next step? mentorship? scope expansion?)

### Remote & Location (Low Weight)

- Primary: Environment property (remote, hybrid, on-site)
- Secondary: timezone compatibility, travel expectations
- Tertiary: entity/visa situation (EU vs US entity, any sponsorship complications)

### Risk Factors (Low Weight)

- Aggregate red flags from: Fit Assessment, debrief concerns, company research
- Examples: high attrition, recent layoffs, unclear funding runway, management churn, "the last two people in this role left within a year"

## Critical Rules

- **Read-only** — this skill does NOT write to Notion. Output is a Markdown file only.
- **Evidence over opinion** — every rating must cite specific tracker data (debrief quote, property value, research finding). If there's no data, rate as "Unknown," not "Neutral."
- **Greg decides** — present tradeoffs, not a winner. The recommendation section should say "Company A looks stronger on X and Y, while Company B is better on Z" — not "you should take Company A."
- **Compensation floor is sacred** — any company below Greg's €135K floor gets "Concern" on Compensation regardless of other strengths. Note this explicitly.
- **No fabrication** — if salary, headcount, or other data wasn't captured in the tracker or debriefs, say "not available" rather than guessing.

## Do Not

- Write to Notion or the queue — this is read-only
- Declare a winner — present structured tradeoffs for Greg to weigh
- Ignore compensation floor — €135K minimum is non-negotiable
- Speculate on data not in the tracker — use "Unknown" rating and note the gap
- Weight all dimensions equally — follow the High/Medium/Low weights
- Produce a generic comparison that could apply to any two companies — every claim must reference specific tracker data
- Skip companies Greg asked to compare because they have less data — compare what's available and flag gaps

## Related Skills

- `/analyze` — Produces the initial Fit Assessment (feeds into comparison)
- `/reassess` — Updates scores with interview learnings (better comparison input)
- `/debrief` — Captures interview data that enriches the comparison
- `/scoring` — Scoring component weights (same framework, different application)
- `/track` — Status updates after Greg makes a decision
