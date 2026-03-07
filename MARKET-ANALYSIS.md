# Jobbing Market Analysis

**Date:** March 7, 2026
**Purpose:** Product validation — is there a real market gap for a full-featured, AI-powered job application tracking webapp?

---

## Executive Summary

The job application tracking space is crowded at the commodity level — a dozen tools offer Kanban boards, Chrome extensions, and AI resume builders. But the entire market is optimized for **volume** (apply to more jobs faster), leaving a significant gap for tools optimized for **quality** (apply to fewer jobs better). Jobbing's analysis-first, honest-scoring approach has no direct competitor. The question isn't whether the capabilities are valuable — it's whether the delivery mechanism can scale beyond a CLI.

---

## Market Size and Opportunity

The U.S. has ~6M actively unemployed workers at any time, but the real addressable market is much larger: passive seekers, employed professionals exploring options, and career transitioners. The Bureau of Labor Statistics reports that the average job search lasts 5–6 months. At any given time, roughly 20–30M Americans are in some phase of active or passive job seeking.

The leading tools have meaningful traction: Teal claims 3M+ users, Careerflow reports 1.2M+, Huntr has 500K+. Combined paid conversion rates in freemium SaaS typically run 2–5%, suggesting hundreds of thousands of paying customers across the category.

Teal alone reportedly generates ~$53M/year in revenue with 258 employees and ~$21M raised. This validates that job seekers will pay $15–50/month for tools that help them search more effectively.

---

## Macroeconomic Context: Why Now

### The Tech Downsizing Wave

The tech industry is in the middle of a sustained downsizing cycle that shows no sign of reversing. The numbers are stark:

**2025:** ~245,000 tech jobs cut globally across 783 layoff events. Major cuts included Intel (~33,900), Amazon (~14,000), Microsoft (~9,100), Salesforce (~5,000), and Verizon (~13,000). AI was cited as a driver in nearly 55,000 of those U.S. layoffs.

**2026 (through early March):** Already 53,000+ tech jobs cut across 155 events — on pace to match or exceed 2025. The most seismic: Block (Square/CashApp) announced it was cutting ~4,000 employees — 40% of its workforce — in late February 2026. CEO Jack Dorsey explicitly attributed the cuts to AI efficiency gains and predicted most companies would make similar reductions within the next year. Amazon followed with 16,000 cuts in January 2026 as part of an "anti-bureaucracy push," accounting for 52% of global tech layoffs in 2026 so far.

Block's announcement is particularly notable because the stock surged 24% on the news. The market is *rewarding* companies for cutting headcount. This creates a structural incentive for more downsizing — executives who see Block's stock pop have every reason to follow suit.

### The Labor Market Data

The February 2026 BLS jobs report painted a sobering picture: the U.S. economy *lost* 92,000 jobs, unemployment ticked up to 4.4%, and labor force participation dropped to 62% — its lowest since December 2021. The tech sector specifically showed mixed signals: IT and custom software services added 5,900 jobs, but the broader information technology sector contracted. Tech unemployment rose slightly to 3.8%.

For experienced tech workers, the job search has gotten materially harder:

- **Average job search duration** is now approaching 25 weeks (~6 months). 34% of workers report searches lasting 6+ months — a 16% increase year-over-year.
- **Application volume has exploded.** In 2021, a job seeker applied to ~10–15 roles before getting hired. In 2025, that number was 43 on average. Some data suggests 400–750+ applications per offer at the extreme end, though much of this is spray-and-pray noise from auto-apply tools.
- **Employer-side competition is brutal.** The average job opening now receives 242 applications. Small businesses see 312 per role. The average recruiter manages 2,500+ applications across 14 open reqs — 2.7x more than three years ago.
- **AI is flooding the funnel.** 74% of U.S. job seekers now use AI in their application process. 49% explicitly say they apply to more positions to get past automated filters. The result: more applications per opening, lower signal-to-noise ratio, and more reliance on ATS keyword matching to filter candidates.

### Why This Is a Tailwind, Not a Headwind

The conventional read is that a tough job market means fewer potential customers (fewer job seekers). The opposite is true for Jobbing's target segment. Here's why:

**1. Scarcity of good roles increases the value of each application.** When there were 50 compelling openings for a senior engineer, a mediocre application to any one of them barely mattered — you'd land something. When there are 10 compelling openings in a 6-month search, each application is precious. The cost of a wasted application (time, energy, morale) is much higher. A tool that tells you "skip this one, it's a bad fit" and then makes your 8 remaining applications excellent is worth far more in a tight market than a loose one.

**2. The spray-and-pray tools are making the problem worse, not better.** Auto-apply tools like LazyApply and Sonara are flooding employers with hundreds of low-quality applications per role. This has directly caused employers to add more screening steps, use stricter ATS filters, and rely more heavily on keyword matching. The arms race between applicant volume and employer filtering is a race to the bottom — and it specifically punishes experienced professionals who don't want to spam 500 applications. Jobbing's quality-over-quantity approach is the counter-strategy.

**3. Longer searches mean higher willingness to pay.** A job seeker who's been searching for 4 months and getting nowhere is far more likely to pay $25/month for a tool that actually improves their odds than someone who just started looking. The expanding average search duration creates a larger pool of frustrated, motivated buyers.

**4. Experienced professionals are disproportionately affected by "rightsizing."** The Block, Amazon, and Microsoft cuts aren't primarily hitting junior engineers — they're restructuring entire organizations, eliminating management layers, and collapsing teams. Senior ICs, engineering managers, directors, and VPs are landing in the job market in numbers not seen since 2022–2023. These are exactly Jobbing's target users: people with deep experience who need to make strategic, high-quality applications.

**5. AI-driven layoffs will accelerate, not slow down.** Dorsey's prediction that "most companies will make similar cuts in the next year" may be aggressive, but the direction is clear. 55% of hiring managers surveyed expect layoffs in 2026, and 44% cite AI as the top driver. Each wave of layoffs adds more experienced professionals to the job market and extends the average search duration — expanding the TAM.

**The net effect:** A tightening job market with fewer roles and more competition is the *ideal* environment for a tool that optimizes application quality. The worse the market gets for job seekers, the more valuable Jobbing becomes. This is a counter-cyclical advantage — demand increases precisely when conditions are hardest.

---

## Job Seeker Pain Points (Survey Data)

The pain is severe and well-documented across multiple 2025 surveys:

**The application black hole.** 59% of job seekers believe fewer than 25% of their applications ever reach a human recruiter. 44% reported getting zero interviews in the prior month. The system feels broken, and seekers know it.

**Resume tailoring is exhausting.** 26% say it takes too long to tailor their resume per application. Resume writing is the #2 pain point overall, behind "not hearing back." Most people either don't tailor (and get filtered by ATS) or burn out trying.

**Ghost jobs waste everyone's time.** 66% report applying to jobs that appeared open but were actually inactive. This is a systemic problem that no current tool addresses.

**Application abandonment.** 57% have abandoned an application mid-process due to overly complicated or time-consuming requirements. 60% abandon if the process is too lengthy.

**No transparency.** 63% say employers aren't transparent about the interview process — number of rounds, required projects, evaluation criteria. Seekers go in blind.

**Mental health impact.** 72% report that job hunting has negatively impacted their mental health. 32% have been searching for over six months. This isn't a convenience problem — it's a quality-of-life problem.

**The underserved segment.** Almost every tool targets early-career to mid-level seekers doing high-volume applications. Senior professionals (8+ years, $120K+) running strategic, low-volume searches — 10–20 carefully targeted applications — are poorly served by tools designed around spray-and-pray.

---

## Competitive Landscape

### Tier 1: Full Platforms

#### Teal HQ
The market leader. ~$53M revenue, 258 employees, ~$21M raised across 4 rounds (most recent Series A in early 2025).

**Features:**
- Chrome extension saves jobs from 50+ boards (LinkedIn, Indeed, Glassdoor, company pages)
- AI Resume Builder with keyword optimization and match scoring per job description
- Job tracker with pipeline stages, notes, excitement ratings, reminders
- Cover letter generator from resume + job description
- Networking CRM (contact management, interaction tracking)
- LinkedIn profile review tool
- Work style and salary preference questionnaires
- Job comparison tool

**Pricing:** Free tier (1 resume). Teal+ at $13/week, $29/month, or $79/quarter.

**Limitations:**
- AI accuracy issues — users report generated content that doesn't match their actual experience
- Match scoring inconsistent with how real ATS systems score (lower scores, missed keywords)
- Resume templates can't be read by common ATS systems like Workday
- Setup is complex — tailoring a resume requires navigating multiple parts of the system
- No automated applications — all manual
- No fit analysis of the *role itself* — only checks your resume against the JD

#### Huntr
Strong #2. 500K+ users. Clean, polished UX.

**Features:**
- Kanban board with drag-and-drop pipeline management
- Chrome extension for one-click job saving from any board
- AI resume builder with keyword extraction from job descriptions
- AI cover letter generator
- Autofill extension for application forms
- Contact management per application (name, title, email, notes)
- Interview scheduling tracker with calendar view
- Job map feature (geographic visualization of applications)
- Application analytics (volume, response rates, time-in-stage)
- Document storage linked to each application

**Pricing:** Free tier (limited tracking, basic tools). Pro at $40/month, $30/month quarterly, $26.67/month biannually.

**Limitations:**
- Expensive — $40/month is the highest in the category for individual seekers
- AI cover letters described as "hit or miss" by users
- Mobile app less functional than desktop
- No role analysis or fit scoring beyond keyword matching
- No company research integration

#### Careerflow
Volume play. 1.2M+ users.

**Features:**
- Job tracker with custom labels, status updates, deadline tracking
- AI Resume Builder with ATS optimization
- LinkedIn profile optimizer (headline, summary, skills suggestions)
- AI cover letter generator
- Chrome extension with autofill for application forms
- AI mock interviews
- Job match suggestions

**Pricing:** Free tier (1 resume, 10 tracked jobs). Premium at $9/week, $24/month, $55/quarter, $173/year.

**Limitations:**
- AI frequently introduces errors and incorrect information into resumes
- No interview tracking, next steps, or follow-up scheduling
- No checklist or guided workflow — requires significant manual input
- No company research or role analysis
- Tracker is basic compared to Teal or Huntr

### Tier 2: Specialists

#### Jobscan
The ATS optimization specialist.

**Features:**
- Resume scanner against actual ATS algorithms (not just keyword matching)
- Match rate scoring with specific improvement suggestions
- LinkedIn profile optimization
- Job tracker (bolt-on, not core product)
- Cover letter optimization

**Pricing:** $50/month (most expensive in category). Free tier with limited scans.

**Limitations:**
- Narrow focus — the tracker is an afterthought
- Expensive for a single-purpose tool
- No resume building, only optimization of existing resumes

#### Simplify.jobs
Free-forever model targeting early-career seekers.

**Features:**
- Application tracker (free, unlimited)
- Chrome extension with one-click autofill
- Job match suggestions based on profile
- Automatic application tracking (detects when you apply)

**Pricing:** Free. Monetizes by charging employers for job postings.

**Limitations:**
- Targets students and early-career — not built for experienced professionals
- No resume building or tailoring
- No company research or role analysis
- Limited customization

#### Eztrackr
Lightweight Chrome extension. 4.8-star rating.

**Features:**
- Kanban board tracker
- Chrome extension with auto-parsing from LinkedIn, Lever, Indeed
- AI answer generator for common application questions (GPT-4 powered)
- Application analytics and statistics
- Document storage per application
- Email reminders for interviews and follow-ups

**Pricing:** Freemium (details not prominently published).

**Limitations:**
- Small team, less feature depth than Tier 1 platforms
- No resume builder
- No company research

### Tier 3: Adjacent / Auto-Apply

#### Auto-Apply Tools (LazyApply, Sonara, JobCopilot)
Spray-and-pray approach. Apply to hundreds of jobs automatically.

**Features:** Automated form filling, mass application submission, basic matching.

**Reputation:** Terrible. LazyApply has 2.1 stars on Trustpilot. Users report account bans from job boards, applications to irrelevant roles, and poor match quality. Employers are actively pushing back against application floods. This category exists but is widely seen as counterproductive and may be actively harmful to a job seeker's reputation.

#### Notion / Monday.com Templates
DIY approach using general-purpose tools.

**Features:** Kanban views, custom properties, flexible structure. Free or included in existing subscriptions.

**Limitations:** No AI, no browser extension, no ATS checking, no automation. Requires manual setup and maintenance. This is what Jobbing currently resembles from a UX standpoint (Notion-backed), though with vastly more intelligence behind it.

---

## Feature Comparison Matrix

| Feature | Jobbing | Teal | Huntr | Careerflow | Jobscan | Simplify |
|---|---|---|---|---|---|---|
| **Job Tracking** | | | | | | |
| Pipeline/Kanban board | Via Notion | Yes | Yes | Yes | Basic | Yes |
| Chrome extension (save jobs) | No | Yes (50+ boards) | Yes | Yes | No | Yes |
| Application autofill | No | No | Yes | Yes | No | Yes |
| Interview scheduling | Via Notion | Yes | Yes | No | No | No |
| Follow-up reminders | No | Yes | Yes | No | No | No |
| Mobile app | No | No | Yes | No | No | No |
| Analytics dashboard | No | Basic | Yes | Basic | No | No |
| **Resume & Cover Letter** | | | | | | |
| AI resume builder | No (tailors existing) | Yes | Yes | Yes | No | No |
| AI cover letter generator | Yes (from profile) | Yes | Yes | Yes | Yes | No |
| ATS keyword optimization | Yes (post-generation QA) | Yes | Yes | Yes | Yes (core) | No |
| Profile-based tailoring | Yes (deep) | Shallow | Shallow | Shallow | No | No |
| **Intelligence & Analysis** | | | | | | |
| Fit scoring (role analysis) | **Yes (unique)** | No | No | No | No | No |
| Red flag detection in postings | **Yes (unique)** | No | No | No | No | No |
| Company research (funding, Glassdoor, news) | **Yes (unique)** | No | No | No | No | No |
| Ghost job detection | No | No | No | No | No | No |
| Salary benchmarking | **Yes** | No | No | No | No | No |
| **Outreach & Networking** | | | | | | |
| Contact management | Via Notion | Yes (CRM) | Yes | No | No | No |
| LinkedIn contact research | **Yes (unique)** | No | No | No | No | No |
| Tailored outreach messages | **Yes (unique)** | No | No | No | No | No |
| **Interview Prep** | | | | | | |
| Anticipated questions + answers | **Yes** | No | No | No | No | No |
| Questions to ask interviewer | **Yes** | No | No | No | No | No |
| AI mock interviews | No | No | No | Yes | No | No |
| **Other** | | | | | | |
| Aggregator spam parsing | **Yes (unique)** | No | No | No | No | No |
| Job board scanning | **Yes** | No | No | No | No | No |
| Self-service web UI | No | Yes | Yes | Yes | Yes | Yes |
| Standalone (no AI dependency) | No | Yes | Yes | Yes | Yes | Yes |

The pattern is clear: Jobbing dominates on intelligence and analysis. Competitors dominate on accessibility, UX, and browser integration. A webapp version of Jobbing would combine both.

---

## Legal and Ethical Analysis

### LinkedIn Scraping

Jobbing's `/outreach` feature researches LinkedIn contacts at target companies and drafts tailored connection request messages. As a CLI tool used by one person, this is functionally equivalent to manual LinkedIn browsing. As a webapp serving thousands of users, the legal landscape changes significantly.

**The hiQ v. LinkedIn precedent (2017–2022).** The Ninth Circuit ruled that scraping *publicly accessible* data does not violate the Computer Fraud and Abuse Act (CFAA), because the concept of "without authorization" doesn't apply to public websites. The Supreme Court vacated and remanded in light of *Van Buren v. United States*, but the Ninth Circuit reaffirmed on remand. The case ultimately settled — hiQ paid $500K and agreed to stop scraping LinkedIn, but the settlement was *contractual*, not a CFAA ruling. The broader legal precedent that scraping public data is not a CFAA violation remains intact.

**However, "legal under CFAA" is not "safe to build a business on."**

**LinkedIn's Terms of Service explicitly prohibit scraping.** Section 8.2 of LinkedIn's User Agreement prohibits "developing, supporting, or using software, devices, scripts, robots, or any other means or processes to scrape the Services." A webapp that programmatically accesses LinkedIn profiles would violate these terms. LinkedIn actively enforces this — they send cease-and-desist letters, block IP ranges, and have sued multiple companies.

**GDPR and CCPA exposure.** Scraping personal data (names, titles, profile URLs) constitutes "processing" under GDPR, regardless of whether the data is publicly visible. This requires a lawful basis (legitimate interest, at minimum), transparency (the data subjects must be informed), and compliance with deletion requests. For a webapp operating in the EU or processing EU residents' data, this creates significant compliance overhead. GDPR penalties can reach €20M or 4% of global revenue.

**Practical risk assessment for a Jobbing webapp:**

| Approach | Legal Risk | Practical Risk |
|---|---|---|
| Automated scraping of LinkedIn profiles | High — ToS violation, potential CFAA claims if behind login wall, GDPR exposure | Very high — LinkedIn actively detects and blocks scrapers, bans accounts |
| Using LinkedIn's official APIs | Low — sanctioned access with proper permissions | Medium — LinkedIn's API access is restrictive, approval is slow, and the data available is limited |
| User-directed research (user provides profile URLs, app fetches public data) | Medium — still ToS violation, but harder to detect and enforce | Low-medium — lower volume, harder to distinguish from normal browsing |
| AI-generated suggestions without scraping (e.g., "search LinkedIn for VP Engineering at Company X") | Very low — no scraping, just advice | Very low — this is what a career coach does |

**Recommendation:** For a webapp, the outreach feature should be redesigned. The safest approach is to generate *search queries and message templates* without actually scraping LinkedIn. The user does their own LinkedIn searching and uses the app's suggested messages. This preserves 80% of the value (the tailored messages are the hard part) while eliminating 95% of the legal risk.

An alternative is to integrate with LinkedIn's official API program, but approval is difficult, the data is limited, and LinkedIn can revoke access at any time.

### Web Scraping for Company Research

Jobbing's `/analyze` workflow researches companies via web search — Glassdoor reviews, Crunchbase funding data, news articles, tech blog posts.

**This is significantly less risky than LinkedIn scraping.** Glassdoor, Crunchbase, and news sites publish information intended for public consumption. Search engine indexing is an implied license. However:

- **Glassdoor's Terms of Service** prohibit automated scraping. A webapp that systematically scrapes Glassdoor reviews could face legal action. Using Glassdoor's API (if available) or surfacing search engine results (which Glassdoor has consented to by allowing indexing) is safer.
- **Rate limiting and IP blocking** are common. A webapp would need to respect robots.txt, implement reasonable rate limits, and potentially use commercial data providers rather than direct scraping.
- **Crunchbase** offers a paid API ($499+/month) for commercial use. Scraping their site for a commercial product would violate their ToS.

**Recommendation:** Use commercial APIs (Crunchbase, Glassdoor if available) or aggregate from search engine results rather than direct scraping. Budget $500–2,000/month for data provider APIs at scale.

### Job Description Storage

Storing full job descriptions (as Jobbing does for analysis) raises minor copyright concerns. Job descriptions are generally considered functional text with limited copyright protection, but wholesale reproduction at scale could draw attention. Standard practice in the industry: store them for user reference, don't republish them publicly.

### AI-Generated Application Materials

No significant legal risk. AI-assisted resume writing and cover letter generation is standard practice — every competitor does this. The user submits the materials under their own name and is responsible for accuracy. The ethical obligation is to not fabricate credentials or misrepresent experience, which Jobbing's design explicitly guards against (the "no fake metrics" rule, CONTEXT.md verification).

---

## LLM Cost Estimation

Jobbing's core value proposition — conversational fit analysis, company research, tailored document generation — requires a capable LLM. Here's what it would cost to run at scale.

### Per-Conversation Token Estimates

A typical Jobbing workflow (analyze → apply) involves substantial context:

| Step | Input Tokens (est.) | Output Tokens (est.) |
|---|---|---|
| Load user profile (CONTEXT.md equivalent) | 4,000 | 0 |
| Load workflow instructions | 3,000 | 0 |
| Job posting (user pastes) | 1,500 | 0 |
| Fit analysis generation | 2,000 | 2,500 |
| Company research (web search results) | 5,000 | 1,500 |
| Experience to Highlight discussion (2–3 turns) | 6,000 | 1,500 |
| JSON document generation (CV + cover letter) | 8,000 | 4,000 |
| ATS keyword check | 3,000 | 800 |
| Outreach message drafting | 4,000 | 1,200 |
| **Total per full workflow** | **~36,500** | **~11,500** |

This is a conservative estimate. Multi-turn conversations accumulate context — by message 10, you're resending all prior messages. A realistic full workflow might hit 60,000–80,000 input tokens including context accumulation.

### Cost Per Workflow by Model (March 2026 Pricing)

Using 60K–80K input tokens and ~11,500 output tokens per full workflow (accounting for context accumulation in multi-turn conversations):

| Model | Rate (per 1M tokens: in/out) | Input Cost | Output Cost | **Total per Workflow** |
|---|---|---|---|---|
| Claude Sonnet 4.5 | $3 / $15 | $0.18–0.24 | $0.17 | **$0.35–0.41** |
| Claude Haiku 4.5 | $1 / $5 | $0.06–0.08 | $0.06 | **$0.12–0.14** |
| GPT-4o | $2.50 / $10 | $0.15–0.20 | $0.12 | **$0.27–0.32** |
| GPT-4o mini | $0.15 / $0.60 | $0.009–0.012 | $0.007 | **$0.02** |
| Claude Opus 4.5 | $5 / $25 | $0.30–0.40 | $0.29 | **$0.59–0.69** |

**Important caveat on token estimates:** The 60K–80K input range assumes a single continuous conversation. A webapp architecture could reduce this significantly by breaking the workflow into discrete API calls (analysis, research, document generation) rather than maintaining a single conversation thread. Discrete calls avoid context accumulation and could bring effective input tokens closer to the 36,500 base estimate, roughly halving costs.

### Optimization Strategies

**Model routing.** Not every step needs the same model. Fit analysis and tailored content generation need Sonnet/GPT-4o-class intelligence. ATS keyword checking, formatting, and simple classification can use Haiku/4o-mini at 1/3rd to 1/10th the cost. A hybrid approach could cut costs 40–60%:

| Step | Recommended Model | Est. Cost |
|---|---|---|
| Fit analysis + scoring | Sonnet 4.5 | $0.12 |
| Company research synthesis | Sonnet 4.5 | $0.08 |
| Experience to Highlight drafting | Sonnet 4.5 | $0.06 |
| JSON document generation | Sonnet 4.5 | $0.10 |
| ATS keyword check | Haiku 4.5 | $0.01 |
| Outreach message drafting | Haiku 4.5 | $0.02 |
| Status checks, light Q&A | Haiku 4.5 | $0.01 |
| **Blended total per workflow** | | **$0.40** |

**Prompt caching.** The user profile and workflow instructions (~7,000 tokens) are identical across every workflow. With Anthropic's prompt caching, cache hits cost 10% of standard input price. For an active user running 8+ workflows/month, this saves ~$0.15–0.20/workflow.

**Batch processing.** Steps that don't require real-time response (company research aggregation, ATS check) can use batch APIs at 50% discount.

**Discrete call architecture.** Instead of one long conversation, break workflows into independent API calls that each receive only the context they need. This eliminates context accumulation (the biggest cost driver in conversational architectures) and enables parallel processing.

**Realistic blended cost per workflow with all optimizations:** $0.25–0.40.

### Monthly Cost Projections at Scale

Assumptions: active users average 8 full workflows/month (2 per week during active search), plus 4 lighter interactions (status checks, quick questions) at ~$0.02 each.

| Active Users | Workflows/Month | LLM Cost/Month | Cost/User/Month |
|---|---|---|---|
| 100 | 800 | $250–$400 | $2.50–$4.00 |
| 1,000 | 8,000 | $2,200–$3,500 | $2.20–$3.50 |
| 10,000 | 80,000 | $20,000–$32,000 | $2.00–$3.20 |
| 50,000 | 400,000 | $90,000–$144,000 | $1.80–$2.88 |
| 100,000 | 800,000 | $160,000–$260,000 | $1.60–$2.60 |

Per-user costs decrease at scale due to better caching hit rates and batch processing efficiency.

**At $25/month subscription pricing** (competitive with Huntr/Teal), LLM costs represent 6–16% of revenue — well within healthy SaaS margins (gross margin target: 70%+). At $15/month, LLM costs are 11–23% of revenue — tighter but still viable, especially as model prices continue to fall (Claude 4.5 series represented a 67% cost reduction over previous generations).

**Key insight on price trajectory:** LLM costs have been dropping ~50% annually. A product that's marginally viable on LLM economics today will likely have comfortable margins within 12–18 months purely from model price decreases.

### Additional Infrastructure Costs

Beyond LLM APIs, a webapp would incur:

- **Web search API** (for company research): $5–50/month per 1,000 queries (Google Custom Search, Bing Web Search)
- **Data provider APIs** (Crunchbase, Glassdoor): $500–2,000/month at scale
- **PDF generation**: Minimal — server-side rendering is cheap
- **Hosting and compute**: $500–5,000/month depending on scale (standard webapp infrastructure)
- **Vector database** (for profile storage and semantic search): $100–500/month

**Total estimated infrastructure cost at 10,000 active users: $25,000–$40,000/month**, or $2.50–$4.00/user/month all-in.

---

## Differentiation and Positioning

### Where Jobbing Wins

**Analysis-first workflow.** Every competitor starts with "save this job" or "build your resume." Jobbing starts with "should you even apply to this?" The fit scoring, red flag detection, and company research represent a fundamentally different philosophy. No competitor does this.

**Honest scoring.** The market incentive for every competitor is to maximize applications — more applications = more engagement = more premium conversions. Jobbing's incentive is the opposite: help users *not* apply to bad-fit roles. This is counterintuitive as a business model, but it's exactly what experienced professionals want. A tool that tells you "skip this one" is more valuable than one that helps you apply to everything.

**Deep tailoring from a rich profile.** Competitors generate resumes from scratch using AI. Jobbing tailors from a comprehensive career narrative — it knows the user's full history, achievements, team sizes, tech stacks, and can weave specific details into each application. The result is qualitatively different from "AI wrote my resume."

**End-to-end intelligence.** From role analysis → company research → tailored documents → outreach messages → interview prep, Jobbing covers the full arc of a strategic application. Competitors cover 2–3 of these steps and do none of them as deeply.

### Where Jobbing Needs to Catch Up (for Webapp)

**Self-service UI.** A Kanban board, application pipeline, and dashboard are table stakes. Users expect to see their search at a glance without starting a conversation.

**Browser extension.** One-click job saving from LinkedIn/Indeed is the #1 onboarding mechanism for every successful competitor. Without it, the friction of copy-pasting job postings is a significant barrier.

**Notifications and reminders.** Follow-up nudges, interview reminders, and "you haven't applied in 5 days" prompts keep users engaged. This is standard retention mechanics.

**Analytics.** Application volume, response rates, time-in-stage, and funnel visualization help users understand their search performance over time.

### Positioning Statement

**For experienced professionals who want to make every application count,** Jobbing is the job search platform that analyzes roles *before* you apply — scoring fit, researching companies, flagging red flags, and generating tailored application materials from your complete career profile. Unlike Teal, Huntr, and Careerflow, which help you apply to more jobs faster, Jobbing helps you apply to fewer jobs better.

---

## Proposed Architecture: Webapp + Extension + API

The legal and UX challenges above point toward a three-component architecture where each piece does what it's best at:

### The Three Components

**1. Browser Extension (runs as the user, from their IP)**

The extension operates in the user's authenticated browser session. It doesn't scrape in the background — it activates on user action (PhantomBuster's model, which has survived years of operation). This means:

- **Job saving:** One-click capture from LinkedIn, Indeed, Glassdoor, company career pages. Parses job title, company, location, salary, and full description. Sends structured data to the API.
- **LinkedIn contact surfacing:** When a user visits a company page or searches for people at a target company, the extension can surface relevant contacts (hiring managers, recruiters, peer engineers) from what the user can already see in their own LinkedIn session. No server-side scraping — the extension reads what's already on the user's screen.
- **Application form assistance:** Autofill from the user's profile data. The extension pulls from the webapp's stored profile, not from scraping.

The key legal distinction: the extension assists the user in doing things they're already doing manually, from their own authenticated session. It doesn't create a separate scraping infrastructure. This is the model that PhantomBuster, Dux-Soup, KASPR, and dozens of LinkedIn tools have operated under for years.

**2. Webapp (the brain and the dashboard)**

The webapp is where intelligence lives:

- **Kanban pipeline:** Visual application tracking with drag-and-drop stages (Targeted → Applied → Interviewing → Done). Table-stakes UX.
- **AI conversation interface:** The fit analysis, company research, and document generation workflows happen here. This is where the LLM API calls live.
- **Profile management:** Users build and maintain their career profile (the equivalent of CONTEXT.md). This is the deep knowledge base that powers tailored content generation.
- **Document generation and storage:** Tailored CVs, cover letters, and application answers. PDF rendering. Version history per company.
- **Interview prep:** Per-company question banks, talking points, debrief notes.
- **Analytics dashboard:** Application volume, response rates, time-in-stage, score distribution.
- **Notifications:** Follow-up reminders, interview prep triggers, "you saved this job 3 days ago but haven't analyzed it yet."

**3. API (the connective tissue)**

- Receives structured job data from the extension
- Serves profile data to the extension for autofill
- Handles LLM orchestration (model routing, caching, batch processing)
- Manages webhook integrations (calendar sync, email notifications)
- Provides the data layer for both the extension and webapp

### How This Solves the Legal Problems

**LinkedIn contact research.** The extension doesn't scrape LinkedIn from a server. It assists the user in their own browsing session. When the user visits a LinkedIn search results page, the extension can highlight relevant contacts and offer to draft outreach messages — but the data never leaves the user's browser until they explicitly choose to save a contact to the webapp. This is functionally identical to what the user would do manually: browse LinkedIn, find interesting people, note their details.

The critical lesson from the KASPR fine (€240,000, CNIL, December 2024) is specific: KASPR was fined not for having a Chrome extension that read LinkedIn data, but for (1) collecting contact details of users who had restricted their visibility settings, (2) storing that data on KASPR's servers for 5 years, (3) failing to inform data subjects their data had been collected, and (4) not providing adequate responses to access requests. The violations were about *what they did with the data after collection*, not the extension mechanism itself.

A Jobbing extension that only surfaces contacts the user can already see (respecting LinkedIn's visibility settings), only stores contact details that the user explicitly saves, provides clear data management (the user controls what's stored and can delete it), and doesn't build a centralized database of scraped contacts — this operates in a fundamentally different risk category than KASPR.

**Job board data.** The extension captures job postings that the user is actively viewing. This is equivalent to copy-paste — the user chose to visit this job listing. No legal issue.

**Company research.** Stays on the server side, using web search APIs and commercial data providers (Crunchbase API, etc.). No scraping of restricted content.

### Remaining Risks in This Architecture

**LinkedIn ToS still technically prohibits extensions that "scrape the Services."** PhantomBuster, Dux-Soup, KASPR, Lusha, and others all operate in this gray zone. LinkedIn occasionally sends cease-and-desists to extension developers and can ban individual user accounts. The practical risk is moderate — LinkedIn primarily targets high-volume automation tools, not tools that assist users in manual browsing. But it's not zero.

**GDPR still applies to stored contact data.** Even if the user manually saves a LinkedIn contact's name and title to the webapp, that's personal data under GDPR. The webapp needs: a clear privacy policy explaining what data is stored, a lawful basis (legitimate interest of the user in managing their job search), data minimization (only store what's necessary), and deletion capability. This is standard GDPR compliance — not a blocker, but requires proper implementation.

**User account risk.** LinkedIn may restrict or ban accounts that use automation extensions. The extension should be conservative: no background activity, no automated connection requests, no behavior that looks non-human. Click-triggered only. This limits functionality but protects users.

### Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                  USER'S BROWSER                  │
│                                                  │
│  ┌─────────────────────────────────────────────┐ │
│  │           BROWSER EXTENSION                 │ │
│  │                                             │ │
│  │  • Save jobs (1-click from any board)       │ │
│  │  • Surface LinkedIn contacts (user's view)  │ │
│  │  • Autofill applications (from profile)     │ │
│  │  • Parse job descriptions                   │ │
│  │                                             │ │
│  │  Runs as user • User's IP • User's session  │ │
│  └──────────────────┬──────────────────────────┘ │
└─────────────────────┼───────────────────────────-┘
                      │ Structured data
                      │ (user-initiated only)
                      ▼
              ┌───────────────┐
              │      API      │
              │               │
              │  • Auth       │
              │  • LLM proxy  │
              │  • Data store │
              │  • Webhooks   │
              └───┬───────┬───┘
                  │       │
          ┌───────┘       └────────┐
          ▼                        ▼
┌─────────────────┐    ┌────────────────────┐
│     WEBAPP       │    │   LLM PROVIDERS    │
│                  │    │                    │
│  • Kanban board  │    │  • Claude API      │
│  • AI chat       │    │  • OpenAI API      │
│  • Profile mgmt  │    │  (model routing)   │
│  • Doc gen/store │    │                    │
│  • Interview prep│    └────────────────────┘
│  • Analytics     │
│  • Notifications │
└──────────────────┘
```

### What Changes From Current Jobbing

| Current (CLI + Notion) | Webapp Architecture |
|---|---|
| User pastes full job posting into Claude | Extension captures job data with one click |
| Claude conversation in terminal | AI chat embedded in webapp |
| Notion as tracker database | Native Kanban with custom data model |
| Queue files → launchd → Notion API | Direct database writes via API |
| PDF generation via CLI | Server-side PDF rendering, in-app preview |
| Manual LinkedIn browsing for outreach | Extension surfaces contacts while user browses |
| CONTEXT.md as profile source | Structured profile editor in webapp |
| Single user only | Multi-user with auth, billing, data isolation |

---

## Key Risks

**LLM dependency.** The product is only as good as the underlying model. Model degradation, pricing changes, or API outages directly impact the core experience. Mitigation: support multiple model providers (Anthropic + OpenAI) and maintain fallback capabilities. The discrete-call architecture makes provider switching easier than a conversational approach.

**Competitive response.** Teal or Huntr could ship a simpler version of fit analysis. They have the user base and distribution. However, their business model (maximize applications) works against building something that tells users not to apply. This misalignment is Jobbing's structural advantage.

**LinkedIn platform risk.** The extension model works today because LinkedIn tolerates user-triggered extensions (while actively fighting server-side scraping). If LinkedIn cracks down on all extensions, the outreach feature loses its automated edge. Mitigation: the outreach feature should degrade gracefully — even without the extension, the webapp can generate search suggestions and message templates that the user applies manually.

**Chrome Web Store policy.** Google periodically tightens extension policies. Extensions that access third-party site data must comply with Manifest V3 restrictions and justify their permissions. This is manageable but requires ongoing policy compliance work.

**Market timing.** The job market is cyclical. A product built during a tight labor market (high seeker pain) may see reduced urgency during a strong hiring market. Counter-argument: experienced professionals *always* benefit from strategic application tools, regardless of market conditions.

---

## Conclusion

The market validates that job seekers pay for tracking and optimization tools — Teal's $53M revenue proves it. But the entire competitive field is converging on the same commodity feature set (Kanban + Chrome extension + AI resume builder), optimized for application volume over application quality.

Jobbing's analysis-first, quality-over-quantity approach is genuinely differentiated and maps directly to the underserved experienced-professional segment. The fit analysis engine, company intelligence layer, and deep profile-based tailoring have no direct competitors.

A three-component architecture (browser extension + webapp + API) solves both the UX and legal challenges. The extension handles user-side data capture from their own browsing session (legally defensible, good UX). The webapp provides the AI intelligence, tracking, and document generation (the core value). The API ties them together with proper model routing and cost optimization.

LLM costs are manageable at $1.60–$4.00/user/month all-in, well within healthy SaaS economics at a $15–25/month price point. And costs are trending down — a 50% annual decline in model pricing means today's tight margins become tomorrow's comfortable ones.

The core bet: experienced professionals will pay a premium for a tool that helps them apply to 15 jobs well, rather than one that helps them apply to 150 jobs fast.
