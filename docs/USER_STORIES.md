# User Stories

How a user interacts with Jobbing across both execution modes.

For workflow mechanics and JSON schemas, see WORKFLOW.md. For system architecture, see ARCHITECTURE.md. This document describes what a session actually looks like from the user's chair.

---

## Interactive Mode: Working with Claude

Interactive mode is the daily driver. You open a Claude Code session (or Cowork conversation), and Claude has access to the full project — CONTEXT.md (your profile), WORKFLOW.md (the process), company files, and the Notion tracker.

### Evaluating a new role

You paste a job posting. Claude reads it against your profile and returns:

- Fit assessment (underqualified / right in the pocket / overqualified)
- Score (0–100) with reasoning
- Green flags, red flags, gaps, missing keywords
- Salary benchmark against your targets
- Company intel (funding, headcount, Glassdoor, recent news)
- Draft "Experience to Highlight" bullets

You read the analysis. You push back if the score seems off — especially on seniority. A "Senior DevOps Engineer" posting that describes building a team from scratch and owning the function is not a junior role, even if the title implies it. You discuss. You adjust. You decide: **proceed** or **skip**.

This is the most important checkpoint. No documents get generated, no tracker entries get created, until you say proceed.

### Applying for a role

Once you say proceed, the workflow runs:

1. **Tracker entry** — Claude creates a Notion page (status: Targeted) with the role details, company intel, and Experience to Highlight bullets
2. **Tailored documents** — Claude creates `companies/{company}/{company}.json` with CV and cover letter content tailored to this role, then generates PDFs
3. **ATS check** — Claude extracts text from the PDF and verifies keyword coverage
4. **You review** — You read the PDF. If something's off (wrong framing, missing achievement, awkward phrasing), you tell Claude. Claude edits the JSON, regenerates. Repeat until it reads right.
5. **You apply** — You submit the application yourself (Jobbing never submits for you). When done, you tell Claude to mark the status as Applied.
6. **Outreach** — After applying, Claude researches LinkedIn contacts (hiring manager, recruiter, peers) and drafts connection request messages. You review, then send them yourself.

At every step, you're in control. Claude does the heavy lifting (research, writing, formatting), but you make every decision about what gets sent and when.

### Following up on active applications

You come back days or weeks later. You tell Claude about an update:

- "Got an interview with Kentik next Thursday — technical screen with the platform team lead"
- "Rejected from Stripe, they went with an internal candidate"
- "Dash0 wants a system design round, here's the brief"

Claude updates the tracker, helps you prep (interview prep doc, questions to ask, company-specific technical review), and keeps the Notion page current.

### Researching without applying

Sometimes you're not ready to apply. You want to understand a company, compare two roles, or figure out how to position yourself for a domain you're adjacent to. You paste a posting and talk through it without triggering the apply workflow. Claude researches, you learn, nobody commits to anything.

---

## Autonomous Mode: The Scanner

Autonomous mode runs in the background. You configure it once, then it works while you sleep.

### Setup

You maintain two files:

- **BOOKMARKS.md** — URLs for job boards you want scanned (climate tech boards, startup aggregators, remote job sites, specific company career pages)
- **scoring_criteria.md** — How Claude should evaluate postings (what matters, what doesn't, score component weights, seniority rules)

You start the daemon: `jobbing serve`. It runs scans at 1am and 1pm daily.

### What happens during a scan

The agent fetches your bookmarked boards, extracts new postings, and scores each one against your profile and criteria. Every posting gets a `ScoringResult` with:

- Score (0–100)
- Full reasoning (why this score)
- Green flags, red flags, gaps, missing keywords
- Which criteria version produced the score

Postings scoring above threshold (default: 60) get created as Notion entries with status "Researching". Everything — matches and non-matches — gets logged to `scan_results/` with full reasoning.

You get a notification: "Found 3 matches — review in Notion."

### Reviewing scan results

You open Notion. The new entries are there with status "Researching". You read the role, check the scoring reasoning, decide if it's worth pursuing. If yes, you change status to "Targeted" and start the interactive workflow. If no, you mark it Done with a note.

For the roles that didn't make the cut, you can review what was filtered:

```bash
jobbing scan --review
```

This shows you the filtered-out postings with their scores and reasoning. If you see roles that should have scored higher, you know the criteria need tuning.

### Tuning the scoring

This is the feedback loop. If the scanner is filtering too aggressively (or not aggressively enough):

1. **Review** — `jobbing scan --review` to see what was filtered and why
2. **Adjust** — Edit `scoring_criteria.md` (e.g., "Don't penalize 'Senior' title if scope includes team-building")
3. **Re-score** — `jobbing scan --rescore latest` to re-evaluate the same postings with new criteria
4. **Compare** — See old vs. new scores side-by-side
5. **Verify** — Over time, the criteria converge on your judgment

Every `ScoringResult` records which criteria version produced it, so you can always trace back why a decision was made.

---

## The Boundary Between Modes

The autonomous scanner **finds** roles. You **decide** what to do with them.

The scanner will never:
- Apply for a job
- Send a LinkedIn message
- Generate a CV or cover letter
- Change a tracker status beyond "Researching"

It will:
- Scan boards on schedule
- Score postings transparently
- Create Notion entries for matches
- Log everything for your review

The handoff is clean: scanner creates a "Researching" entry → you review in Notion → you open a Claude session and say "let's do Kentik" → interactive mode takes over.

---

## Day-in-the-Life

### Morning (autonomous results)

You check your phone. Notification says "2 new matches from overnight scan." You open Notion on your commute, skim the entries. One looks strong (Head of Platform at a Series B climate tech company, remote, 85 score). The other is marginal (Senior SRE at a fintech, 62 score — good tech match but no leadership scope). You star the first one for later.

### Afternoon (interactive session)

You open Claude Code. "Let's look at that climate tech role." You paste the full posting. Claude pulls up the existing Notion entry (created by the scanner), enriches it with deeper company research, drafts Experience to Highlight bullets. You discuss framing — your 1KOMMA5° work maps directly to their energy platform. You say proceed.

Claude generates the JSON, builds PDFs. You read the CV — the summary needs to lead with climate + platform, not generic infrastructure. Claude adjusts, regenerates. You're happy. You submit the application, tell Claude to mark Applied.

Claude researches LinkedIn contacts: the CTO (ex-Stripe, mutual connection), a Senior Platform Engineer (posted about their OTel migration last month), the recruiter. Drafts connection messages. You review, tweak one, send all three.

### Evening (follow-up)

You got a response from the CTO. You open Claude Code: "Kentik CTO responded, wants a 30-min chat Thursday. Help me prep." Claude pulls the company research, the role description, your tailored CV, and drafts a prep doc: likely topics, questions to ask, things to emphasize, things to avoid.

### Weekly (tuning)

You run `jobbing scan --review`. Three roles were filtered at 55-58 that look interesting on second glance — all "Senior" titles but with team-building scope. You edit `scoring_criteria.md` to add: "Score +10 when 'Senior' title description mentions hiring, team-building, or defining the function." You re-score, see the three roles now land at 65-68. The system learns your judgment.
