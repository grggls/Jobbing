# User Stories

How a user interacts with Jobbing.

For workflow mechanics and JSON schemas, see WORKFLOW.md. For system architecture, see ARCHITECTURE.md. This document describes what a session actually looks like from the user's chair.

---

## Evaluating a new role

You paste a job posting. Claude reads it against your profile and returns:

- Fit assessment (underqualified / right in the pocket / overqualified)
- Score (0–100) with reasoning
- Green flags, red flags, gaps, missing keywords
- Salary benchmark against your targets
- Company intel (funding, headcount, Glassdoor, recent news)
- Draft "Experience to Highlight" bullets

You read the analysis. You push back if the score seems off — especially on seniority. A "Senior DevOps Engineer" posting that describes building a team from scratch and owning the function is not a junior role, even if the title implies it. You discuss. You adjust. You decide: **proceed** or **skip**.

This is the most important checkpoint. No documents get generated, no tracker entries get created, until you say proceed.

## Applying for a role

Once you say proceed, the workflow runs:

1. **Tracker entry** — Claude creates a Notion page (status: Targeted) with the role details, company intel, and Experience to Highlight bullets
2. **Tailored documents** — Claude creates `companies/{company}/{company}.json` with CV and cover letter content tailored to this role, then generates PDFs
3. **ATS check** — Claude extracts text from the PDF and verifies keyword coverage
4. **You review** — You read the PDF. If something's off (wrong framing, missing achievement, awkward phrasing), you tell Claude. Claude edits the JSON, regenerates. Repeat until it reads right.
5. **You apply** — You submit the application yourself (Jobbing never submits for you). When done, you tell Claude to mark the status as Applied.
6. **Outreach** — After applying, Claude researches LinkedIn contacts (hiring manager, recruiter, peers) and drafts connection request messages. You review, then send them yourself.

At every step, you're in control. Claude does the heavy lifting (research, writing, formatting), but you make every decision about what gets sent and when.

## Following up on active applications

You come back days or weeks later. You tell Claude about an update:

- "Got an interview with Kentik next Thursday — technical screen with the platform team lead"
- "Rejected from Stripe, they went with an internal candidate"
- "Dash0 wants a system design round, here's the brief"

Claude updates the tracker, helps you prep (interview prep doc, questions to ask, company-specific technical review), and keeps the Notion page current.

## Scanning job boards

You run `/scan` in a Claude Code session. Claude fetches your bookmarked job boards (BOOKMARKS.md), extracts postings, and scores each one against your profile using `SCORING.md` criteria. You see a summary of matches, near-misses, and skips. For anything interesting, you run `/analyze` to dig deeper.

## Researching without applying

Sometimes you're not ready to apply. You want to understand a company, compare two roles, or figure out how to position yourself for a domain you're adjacent to. You paste a posting and talk through it without triggering the apply workflow. Claude researches, you learn, nobody commits to anything.

---

## Day-in-the-Life

### Morning

You open Claude Code over coffee. "Let's scan the climate boards." Claude fetches your bookmarked boards, finds a Head of Platform role at a Series B climate tech company. Score: 85. You say "let's look at that one" and Claude runs a full analysis — company research, salary benchmark, Experience to Highlight bullets. Looks strong. You say proceed.

### Afternoon

Claude generates the JSON, builds PDFs. You read the CV — the summary needs to lead with climate + platform, not generic infrastructure. Claude adjusts, regenerates. You're happy. You submit the application, tell Claude to mark Applied.

Claude researches LinkedIn contacts: the CTO (ex-Stripe, mutual connection), a Senior Platform Engineer (posted about their OTel migration last month), the recruiter. Drafts connection messages. You review, tweak one, send all three.

### Evening

You got a response from the CTO. You open Claude Code: "Kentik CTO responded, wants a 30-min chat Thursday. Help me prep." Claude pulls the company research, the role description, your tailored CV, and drafts a prep doc: likely topics, questions to ask, things to emphasize, things to avoid.
