---
name: reassess
description: Update a Fit Assessment score based on interview learnings. Reads existing score, debrief notes, and Greg's input, then produces a revised score with reasoning. Preserves original score for comparison.
---

# Living Fit Assessment

Re-score an application after interviews reveal new information. The original `/analyze` score is a cold read based on a job posting. After one or more interview rounds, Greg knows things the posting never said. This skill updates the score to reflect that.

## Prerequisites

- Company hub exists at `kanban/companies/{Company}.md` with a Fit Assessment (from `/analyze`)
- At least one interview file with a populated `## Debrief` section (from `/debrief`), OR Greg providing verbal input on what's changed

## Instructions

### Step 1: Load Context

- Read WORKFLOW.md and CONTEXT.md if not already loaded this session
- Read `.claude/skills/scoring/SKILL.md` for the scoring component weights

### Step 2: Gather Existing Data

Read `kanban/companies/{Company}.md` to collect:

1. **Current score** — the `score:` field in YAML frontmatter
2. **Existing Fit Assessment** — the `## Fit Assessment` section: current reasoning, green/red flags, gaps, and missing keywords
3. **Experience to Highlight** — what was originally identified as relevant
4. **Company Research** — existing research plus any new intel Greg mentions
5. **Interviews section** — the list of wikilinks to interview files

For each interview file listed in `## Interviews`:
- Read `kanban/interviews/{Company}/{filename}.md`
- Extract from the `## Debrief` section:
  - What they asked and what the role actually involves
  - What landed and what stumbled
  - What Greg learned about the team, tech stack, culture, scope
  - `vibe:` rating from YAML frontmatter
  - Any follow-up notes that reveal new information

### Step 3: Get Greg's Input

Ask Greg what's changed. Common inputs:

- Team size or structure differs from the posting ("they said the team is actually 3 people, not 8")
- Tech stack is different from what was described ("they're still on Jenkins, not GitHub Actions")
- Role scope expanded or contracted ("the CTO wants this to be a VP-level role" or "it's more execution than strategy")
- Culture or management signals ("the engineering culture is stronger than Glassdoor suggested")
- Compensation clarity ("they confirmed the range is €120K–€140K")
- Red flags surfaced ("the last two people in this role left within a year")
- Green flags surfaced ("the CTO was impressive, much stronger than I expected")

Greg may provide this unprompted when invoking the skill, or you may need to ask.

### Step 4: Re-Score

Apply the same scoring components from `/scoring` (domain fit, technical match, seniority/scope, location/remote, company signals) but now informed by interview data:

1. **Start from the original component scores** — don't re-derive from scratch
2. **Adjust each component based on new evidence:**
   - Domain fit: Did interviews confirm or contradict the domain alignment?
   - Technical match: Is the actual stack what the posting described?
   - Seniority/scope: Is the real scope what was advertised?
   - Location/remote: Any changes to remote flexibility or location expectations?
   - Company signals: New intel on funding, leadership quality, team health, attrition?
3. **Weight debrief evidence appropriately:**
   - Multiple consistent signals (e.g., two interviewers both mentioned a weak engineering culture) carry more weight than a single data point
   - Vibe ratings of 1-2 across multiple interviews are a strong negative signal
   - Vibe ratings of 4-5 across multiple interviews are a strong positive signal
   - Greg's verbal input on specific facts (team size, stack, scope) overrides posting claims

### Step 5: Produce Updated Assessment

Generate a revised Fit Assessment with:

- **Updated score** (0–100)
- **Score delta** — how much and in which direction it changed
- **Reasoning** — must explicitly state:
  - The original score and when it was set
  - What new information changed the picture
  - Which scoring components moved and why
- **Updated green flags** — incorporating interview learnings
- **Updated red flags** — incorporating interview learnings
- **Updated gaps** — some gaps may have been resolved ("they don't actually need Rust experience") or new ones may have appeared ("they want someone who's done SOC 2 from scratch, not just maintained it")
- **Updated keywords** — adjust based on what the interviews revealed about actual priorities

### Step 6: Present for Review — CHECKPOINT

Show Greg the updated assessment with a clear before/after:

```
Original score: 72 (from /analyze on Feb 15)
Updated score: 81 (+9)

What changed:
- Technical match: +5 (stack is actually GCP/Terraform-heavy, closer to Greg's core than the posting suggested)
- Company signals: +4 (CTO interview was strong, team seems healthy despite Glassdoor noise)
- Seniority/scope: unchanged (role scope matches expectations)

Updated reasoning: ...
```

Wait for Greg's approval before writing.

### Step 7: Write to Hub File

After Greg approves:

1. Use the Edit tool to replace the content of the `## Fit Assessment` section in `kanban/companies/{Company}.md` with the updated assessment
2. Use the Edit tool to update the `score:` field in the YAML frontmatter to the new score

The updated Fit Assessment section should contain the full reasoning including the before/after comparison so the history is preserved inline.

## Reassessment Delta Tracking

When the updated score differs from the original by 15+ points, explicitly note:

1. What the original `/analyze` missed
2. Whether this suggests a tuning opportunity for the `/scoring` guidelines
3. Which scoring component had the largest swing

This helps calibrate the initial scoring over time. Greg reviews these notes and manually adjusts `/scoring` SKILL.md when a pattern emerges.

## Critical Rules

- **Preserve the original score** in the reasoning text — always state what it was and when it was set
- **Use the same scoring components** as `/scoring` — don't invent new dimensions
- **Evidence over intuition** — every score adjustment must cite specific interview data or Greg's input
- **Don't auto-inflate** — interviews often reveal problems. A downward revision is just as valid as an upward one.
- **Greg approves before writing** — present the updated assessment and wait for confirmation
- **Chronology is sacred** — same rules as `/analyze` apply to any experience claims in the reasoning

## Do Not

- Overwrite the Fit Assessment without Greg's explicit approval
- Adjust the score based on vibes alone — cite specific evidence for each component change
- Ignore negative signals from debriefs to keep the score high
- Re-derive the score from scratch without reference to the original — this is an update, not a fresh analysis
- Write reasoning that's vague about what changed — "score improved based on interviews" is not acceptable; name the specific new information
- Invent metrics, team sizes, or achievements not confirmed by Greg or the debrief data
- Proceed without reading the existing Fit Assessment first — you need the baseline

## Related Skills

- `/analyze` — Produces the original Fit Assessment (always comes first)
- `/scoring` — Scoring component weights and guidelines (used for both initial and reassessment)
- `/debrief` — Captures the interview data that feeds reassessment
- `/followup` — May trigger a reassessment prompt ("this company has been stale — worth reassessing?")
- `/compare` — Consumes reassessed scores for offer comparison
