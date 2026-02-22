# Scoring Criteria

Guidelines for the LLM when scoring job postings against the user profile.
Edit this file to tune how the autonomous scanner evaluates matches.

## Threshold

- **Minimum score for Notion entry:** 60 (configurable via `SCORE_THRESHOLD` in `.env`)
- **Scores 40-59:** Logged to `scan_results/` but not tracked in Notion. Review with `jobbing scan --review`.
- **Scores 0-39:** Logged only.

## Scoring guidelines

### Seniority and leveling
- Do NOT penalize for implied seniority mismatch if the role involves:
  - Leadership responsibilities (team lead, managing engineers)
  - Defining a new function ("first hire", "founding team", "building from scratch")
  - Cross-functional scope (working with Product, CTO, stakeholders)
  - Budget or vendor management responsibilities
- Leveling is negotiable during interviews — score based on **scope**, not **title**
- A "Senior DevOps Engineer" role that involves defining the function and hiring a team
  should score similarly to a "Head of DevOps" role

### Domain matching
- Weight domain match heavily: cleantech, sustainability, platform engineering, SRE,
  observability, developer tooling, infrastructure
- Adjacent domains (fintech, healthtech, edtech) with strong platform/infra needs
  score well too
- Pure application development roles (frontend, mobile, full-stack product) score low

### Technical matching
- Core stack match: Kubernetes, AWS/GCP, Terraform, Python, Go, observability tools
- Adjacent tech that maps to experience: Docker, Helm, CI/CD, IaC, service mesh
- De-weight exact years-of-experience requirements (±3 years is fine at senior level)

### Location and remote
- Remote-friendly roles score highest
- Berlin-based or EU-based roles score well
- US-remote roles score well (dual location)
- On-site only (not Berlin or NYC) scores low

### Company quality
- Series A through Series D with known investors: slight positive
- Glassdoor concerns or recent layoffs: flag but don't auto-reject
- No salary listed: flag but don't penalize score

## Score components

| Component | Points | What to evaluate |
|-----------|--------|-----------------|
| Domain fit | 0-30 | How well does the company's domain match the user's experience? |
| Technical match | 0-25 | Stack overlap, infrastructure focus, platform/SRE alignment |
| Seniority/scope | 0-20 | Leadership scope, team size, organizational impact |
| Location/remote | 0-15 | Remote compatibility, geographic fit |
| Company signals | 0-10 | Funding stage, reputation, growth trajectory |

## Output format

For each scored posting, return:
- `score`: 0-100 (sum of component scores)
- `reasoning`: 2-3 sentences explaining the score
- `green_flags`: List of strong alignment signals
- `red_flags`: List of concerns (does not necessarily lower score)
- `gaps`: Skills or experience the posting asks for that the user lacks
- `keywords_missing`: Terms to weave into CV if applying
