---
name: disaggregate
description: Parse job aggregator spam (Jobgether, Lensa, LinkedIn Talent Insights) to identify original hiring companies and run quick fit scores. Use when Greg pastes a batch of listings from LinkedIn emails, aggregator notifications, or job board digests that contain reposted roles with the original company hidden. Also trigger when Greg mentions Jobgether, Lensa, or says something like "got a bunch of job emails" or "LinkedIn is spamming me with roles."
---

# Disaggregate Job Listings

Take a batch of aggregator-reposted job listings (Jobgether, Lensa, LinkedIn Talent Insights, etc.) and identify the original hiring companies behind them. Run quick fit scores against Greg's profile so he can decide which are worth a full `/analyze`.

## Why This Skill Exists

Jobgether, Lensa, and similar aggregators repost the same role across multiple state-based listings to flood LinkedIn feeds. A single VP of Reliability role becomes 6-10 separate listings (Florida, California, Maryland, etc.). The original company is hidden behind the aggregator brand. This skill cuts through the noise.

## Instructions

1. **Read required context files** (if not already loaded this session):
   - `CONTEXT.md` — Greg's profile, career timeline, skills, salary benchmarks
   - `.claude/skills/scoring/SKILL.md` — scoring criteria (the `/scoring` skill: Domain 0-30, Technical 0-25, Seniority 0-20, Location 0-15, Company 0-10; threshold 60)

2. **Parse the input.** Greg will paste a batch of listings — usually copy-pasted from LinkedIn emails or aggregator notifications. Extract:
   - Role title
   - Aggregator name (Jobgether, Lensa, Pentasia, etc.)
   - Location
   - Any other details provided

3. **De-duplicate.** Aggregators post the same role across multiple states. Group by title similarity and look for patterns:
   - Same title with minor word-order variations ("VP of Engineering, Reliability" / "Engineering VP, Reliability" / "Lead VP of Engineering, Reliability") = likely the same role
   - Same aggregator + same general role family + similar requirements = likely the same role
   - Different aggregators can also repost the same underlying role

4. **Identify original companies.** For each unique role cluster:
   - Web search for the role title + key requirements, excluding the aggregator name (e.g., `"VP of Engineering Reliability" -jobgether -lensa`)
   - Check Jobgether's own offer pages (jobgether.com/offer/...) which sometimes name the company
   - Search Greenhouse, Lever, Ashby job boards for matching postings
   - Check company careers pages if you have a candidate company
   - If you can't identify the company, say so — don't guess

5. **Quick-score each unique role** using the `/scoring` skill's 5-component framework:
   - If you have the full JD: score all 5 components
   - If you only have a title and partial info: score what you can, mark unknowns
   - Apply the same rules as `/analyze` (Title Flexibility, no fake metrics, etc.)

6. **Present results as a table:**

   | # | Aggregator Listings | Original Company | Role | Score | One-Line Take |
   |---|---|---|---|---|---|
   | 1 | Jobgether ×6 (FL, CA, MD, VA, MN, NC) | Filevine | VP of Eng, Reliability | 75 | Strong SRE match, 40+ eng is a stretch, great comp |
   | 2 | Lensa ×1 | ??? | Director, Infrastructure | N/A | Could not identify original company |

7. **For roles scoring 60+**, offer to run full `/analyze`. For roles where the company couldn't be identified, note it and move on.

## Aggregator Patterns to Know

- **Jobgether**: Posts on Lever (jobs.lever.co/jobgether/...). Creates 5-15 state-variant listings per role. Their jobgether.com/offer/ pages sometimes name the company. Title-spins aggressively ("VP of Engineering, Reliability" → "Lead Engineering VP" → "Remote Engineering VP, Reliability").
- **Lensa**: Posts on lensa.com. Often strips the original company name entirely. Harder to trace back.
- **Pentasia**: Legitimate igaming/gambling recruiter. Usually posting on behalf of anonymous clients. Not really an aggregator — more of a headhunter.
- **LinkedIn Talent Insights / LinkedIn Jobs**: Can surface roles from aggregators or directly from companies. Check if the poster is the actual company or an intermediary.

## What This Skill Does NOT Do

- Full `/analyze` treatment (company intel, Experience to Highlight bullets, hub file creation). Use `/analyze` for that after identifying promising roles here.
- Application workflow. Use `/apply` after `/analyze`.
- Outreach research. Use `/outreach` after applying.

## Critical Rules

- **Use Greg's browser to fetch JDs.** LinkedIn, Greenhouse, Lever, SmartRecruiters, Workable, and most job boards are blocked from web fetch/search tools. The only reliable way to read job postings is via Greg's Chrome browser (Claude in Chrome MCP tools). Always use the browser — don't attempt web fetch and then report "couldn't find it." Go look.
- **Score based on actual JDs, not titles.** Never quick-score a role based on company name and title alone. Fetch the real job description first. A "Senior DevOps Engineer" could be scoped as Staff; a "Principal Architect" could be a glorified IC. The JD is the truth.
- **Be honest about unknowns.** If you can't find the original company, say "could not identify" — don't speculate.
- **Don't inflate scores.** Quick-scores should be conservative. Better to underscore and have Greg investigate than overscore and waste his time.
- **De-duplication is the highest-value step.** Turning 10 listings into 3 unique roles saves Greg the most time.
- **Defense contractors are excluded.** Even if a role looks like a technical match, if the company's primary customer is military/intelligence, flag it and skip.
