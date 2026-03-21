---
company: "ReflexAI"
position: "Lead Platform Engineer"
status: "In Progress (Interviewing)"
date: 2026-02-09
url: "https://www.linkedin.com/jobs/view/lead-platform-engineer-at-reflexai-4355413345/"
environment: [Remote]
salary: "€168,765 (converted from $195K USD)"
focus: [AI]
score: 88

---

# ReflexAI
**Position:** Lead Platform Engineer

**Status:** In Progress (Interviewing) · **Date:** 2026-02-09 · **Environment:** Remote · **Focus:** AI · **Score:** 88/100

[Job Posting](https://www.linkedin.com/jobs/view/lead-platform-engineer-at-reflexai-4355413345/)

## Company Research
- Bay Phillips call (2026-02-22): 50 people total, 25 report to Bay. Platform Engineering is a new function reporting to Bay.
- Org structure: Bay (Head of Product Engineering) and Taki (Head of AI/ML Engineering) both report to the CTO. Bay has three engineering managers. Large fullstack team in Latin America under Bay.
- Globally distributed team. Germany/Berlin not an issue for employment.
- Lead Platform Engineer role covers 5 areas: SRE, DevEx, Infra, DevOps, Security. High-ownership role — Bay wants someone to fully own this function.
- Company is scaling fast: too many clients, can't onboard fast enough. Growth is not the challenge — scaling is.
- Mostly GCP due to Google partnership, but AWS required for US Government contracts (GovCloud). Some future customers may need Azure, sovereign clouds, on-prem, or euro-clouds. True multi-cloud.
- Google partnership is strategic — stewards mission-driven orgs onto GCP, sometimes introduces investors and customers. Bay wants to expand into Gemini and Vertex AI in coming year.
- Largest pain point: AWS infrastructure management. Running similar deployments across two clouds (AWS/GCP) is costly and complex.
- Other pain points: feature development speed, DevEx/productivity bottlenecks, scaling issues with 3rd-party providers, visibility/observability gaps.
- Bay wants to remove prod access for everyone to meet audit goals. Dev environments with sanitized prod data exist but process is manual/time-consuming.
- Compliance: HIPAA, GDPR, ISO27001, SOC2, HiTrust via Vanta. GovCloud and enterprise deployments seen as major growth drivers.
- Currently multi-tenant (single prod AWS, single prod GCP), not multi-account. Will likely need to move to better data isolation per customer in future.
- Tenant creation process exists: new customer → new Terraform → deploy. Fully terraformed. GitHub Actions. Datadog.
- Product wraps OpenAI API calls heavily. Uses Daily for text-to-speech, Rhyme as voice provider.
- US citizenship required for government contracts but location flexible — worth verifying independently.
- Interview process: 3x 45-minute technical interviews, then final with CTO.
- Bay was very positive and enthusiastic. Aware Greg is interviewing aggressively, targeting March start, and has another offer on the table.
- CTO interview (2026-03-04): John spends 75-80% on product/engineering, 20-25% on business ops. Sam does the opposite. They've worked together ~10 years.
- CTO interview: Core tech built on GPT-2 in 2019 at Trevor Project. John has seen full LLM evolution from BERT/transformers to current generation.
- CTO interview: MongoDB is the database. John: 'not sure why the fuck we did that.' Active tech debt — had significant query optimization issues causing 12-second page loads.
- CTO interview: 20-25% of sprint time carved for KTLO/tech debt. Company also does periodic intentional pauses for larger tech debt sprints.
- CTO interview: Company-wide Claude training sprint this week — canceled normal work. Three pods building features end-to-end with AI. Very AI-forward culture.
- CTO interview: John didn't understand platform engineering until ~6 months ago. Never been in an org with it. Enthusiastic based on peer feedback from investor dinners — other CTOs called it 'the single biggest change in ability to move quickly.'
- CTO interview: Contractor Kevin (ex-NYT infrastructure engineer, found on Upwork) handles fractional AWS/Terraform work. Not broader infra — just AWS piece. John called it 'tape, not a permanent solution.'
- CTO interview: John is sole enforcer of compliance. Runs biweekly security meeting with Bay, head of AI, and Bay's three managers. Manages vulnerability SLAs, evidence collection, branch protection, triage into pods.
- CTO interview: Security roadmap beyond current compliance: FIPS 140-2/3, hardware security modules for encryption, client-side decryption of high-sensitivity fields. Using Google Cloud KMS for encryption at rest currently.
- CTO interview: Privileged access management is top of mind. Some engineers still have standing prod accounts. John wants time-limited, least-privilege access. Greg pitched Google PAM — John hadn't seen it, responded positively.
- CTO interview: Positive signals throughout. John committed to feedback 'later this week or early next week.' No comp discussion (appropriate for 30-min vibe check). No red flags triggered.
- **Offer received (2026-03-14):** $195K base, 8,000 stock options, full US benefits (health/dental/vision, 401K w/ 3% match, $25K life insurance). Ashley Williams (Talent Acquisition) delivered verbally — initially thought Greg was US-based. Offer letter signed by Sam Dorison (CEO), expires 2026-03-24, proposed start date 2026-04-01.
- **Equity details (2026-03-19):** Total shares ~7.69M fully diluted (8,000 options = ~0.104%). 409A valuation finalized, strike price $1.25/share. 1-year cliff, 4-year vest, monthly after cliff. Early exercise / pre-vesting purchase available. Single-trigger acceleration for first 12 months only. Stock plan is 2022 SOP with 705,820-share pool.
- **Negotiation — resolved:** Post-termination exercise window extended from 90 days (stock plan default) → 120 days → 12 months (confirmed by Sam via Ashley, 2026-03-21). Side project exceptions: PIIA has a section for listing exceptions — Solo Recon and job search tool to be listed at signing.
- **Negotiation — resolved (2026-03-21):** Deel EOR confirmed. Salary will be paid in EUR (€168,765 at today's conversion from $195K). Ashley starting Deel contract process, expects contract out next week.
- **Negotiation — open:** EUR figure needs to be locked in the Deel contract as a fixed EUR amount, not a floating USD→EUR conversion. US benefits don't apply under Deel — statutory German benefits instead. Benefits gap estimated at $18-24K/year (health, 401K match, life insurance) — potential argument for rounding up to €175-180K.
- Bay Phillips sent personal congratulations email (2026-03-19) with cell number, expressing enthusiasm about working together.

## Job Description
**About ReflexAI**
ReflexAI brings the best in machine learning and natural language processing to mission-driven, people-centric organizations via innovative tools that transform how they train, develop, and empower their frontline teams.
**About the Role**
We are looking for a **Lead Platform Engineer** to establish and grow ReflexAI’s Platform Engineering function. This is a high-impact, multidisciplinary role for someone who thrives in ambiguity, enjoys wearing multiple hats, and wants to build a function from the ground up.
You will architect and own our multicloud infrastructure (GCP + AWS), expand our CI/CD and release processes, standardize observability and monitoring, and elevate our security posture across the engineering organization. As the first member of this new team, you will shape the technical vision, partner closely with engineering leadership, and eventually help hire and mentor additional platform engineers.
This is a rare opportunity to design and lead a platform function at a fast-scaling AI company—while still getting your hands dirty building tools, infrastructure, and processes used daily by every engineer.
**What You’ll Do**
**Own and Evolve Core Infrastructure**
- Lead design, automation, and maintenance of ReflexAI’s multicloud infrastructure across Google Cloud and AWS.
- Drive infrastructure-as-code adoption, reliability, and cost efficiency.
- Create scalable, secure foundations for data pipelines, application services, and model-serving workloads.
**Build a High-Quality Developer Experience**
- Establish ReflexAI’s CI/CD strategy and own the tooling that engineers use to build, test, and deploy code.
- Standardize pipelines, artifacts, and deployment patterns to accelerate developer velocity.
- Introduce guardrails, templates, and internal tooling that reduce operational overhead.
**Standardize Observability and Monitoring**
- Define and roll out Datadog-based logging, metrics, tracing, and alerting across all services.
- Partner with teams to design SLOs, operational dashboards, and production readiness frameworks.
- Improve on-call ergonomics and reduce MTTR through better instrumentation.
**Strengthen Infrastructure Security**
- Implement best practices for secrets management, IAM, network security, vulnerability scanning, and container security.
- Build automated checks and secure-by-default workflows into CI/CD and cloud environments.
- Collaborate with Compliance and Security teams to ensure ReflexAI meets industry and customer expectations.
**Establish and Lead the Platform Engineering Function**
- Set the roadmap, standards, and long-term vision for ReflexAI’s platform.
- Influence engineering-wide architecture and operational practices.
- Mentor future platform engineers as the team expands (planned headcount: 3 in 2026).
- Act as a cross-functional partner to Engineering, Product, and Security leadership.
**What We’re Looking For**
**Requirements for a great fit**
- 8–10+ years of experience in DevOps, SRE, infrastructure, or platform engineering roles.
- Deep hands-on expertise with cloud platforms (GCP and/or AWS) and infrastructure-as-code (Terraform preferred).
- Strong experience building and maintaining CI/CD pipelines for modern application stacks.
- Proficiency in modern observability ecosystems (Datadog experience is a major plus).
- Solid understanding of cloud security, IAM, container security, and network architecture.
- Ability to lead technical initiatives across teams and influence engineering best practices.
- Comfortable being the first hire on a new team—capable of switching between architect, implementer, mentor, and operator roles.
**Nice to haves**
- Experience working in a fast-growing startup environment.
- Backend-related coding experience, primarily with Typescript
- Background supporting machine learning, model serving, or data-intensive workloads.
- Exposure to compliance frameworks (SOC 2, HIPAA, GDPR, ISO 27001, HITRUST).
- Prior experience building internal developer platforms or paved-path tooling.
**Who You Are**
- You thrive in environments where you can define the direction, not just execute it.
- You enjoy building tools and systems that multiply the productivity of every engineer.
- You seek ownership and autonomy, but also value strong cross-team collaboration.
- You are both strategic and hands-on—the person who sets the roadmap and also writes the Terraform to make it real.
- You are excited to shape the foundation of ReflexAI’s infrastructure and the team that will own it.
Benefits
- Generous retirement, equity, healthcare, and PTO policies
- Flexibility to work remotely from anywhere in the United States
- ReflexAI is an equal opportunity employer. We are committed to equal employment opportunities regardless of race/ethnicity, color, ancestry, religion, sex, national origin, sexual orientation, age, citizenship, marital status, disability, gender, military status, neurodiversity, or any other federal, state or local protected class in the United States.
