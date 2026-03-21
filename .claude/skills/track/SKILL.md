---
name: track
description: Manage the Obsidian job application tracker. Status updates, research, highlights, conclusions, and other tracker operations outside the main /analyze and /apply flow.
---

# Tracker Operations

Manage the Obsidian job application tracker. Use this for status updates, adding research, updating highlights, or any tracker operations outside the main `/analyze` → `/apply` flow.

All writes are direct edits to markdown files using Read/Edit/Write tools. There is no queue, no launchd.

- **Company hub files:** `kanban/companies/{Company Name}.md`
- **Board:** `kanban/Job Tracker.md`
- **Interview files:** `kanban/interviews/{Company}/{date}-{Slug}.md`

## Common Operations

### Create a New Entry

Write a new hub file at `kanban/companies/{Company Name}.md` with YAML frontmatter and scaffold sections (see `/apply` Step 1 for the full template), then add a board card to `kanban/Job Tracker.md` in the Targeted lane:

```
- [ ] [[companies/Company Name|Company Name]] — Role Title · Score: 75 · YYYY-MM-DD
```

CLI equivalent:
```bash
jobbing track create --name "Company Name" --position "Role Title" --date 2026-02-22 [--dry-run]
```

### Update Status

When Greg asks to change an application's status, edit the `status:` field in the hub file's YAML frontmatter:

```yaml
---
status: Applied
---
```

Valid statuses: `Targeted` → `Applied` → `Followed-Up` → `In Progress (Interviewing)` → `Done`

Also update the board card in `kanban/Job Tracker.md` — move it to the appropriate lane.

CLI equivalent:
```bash
jobbing track update --name "Company Name" --status "Applied" [--dry-run]
```

### Close Out an Application

Edit the hub file: set `status: Done` in frontmatter and write the outcome in the `## Conclusion` section:

```yaml
---
status: Done
conclusion: "Rejected after final round. Good process, no offer."
---
```

```markdown
## Conclusion

Rejected after final round. Good process, no offer.
```

### Update Company Research

Edit the `## Company Research` section in the hub file:

```markdown
## Company Research

- Founded 2020, Series B ($50M raised)
- 120 employees, Berlin HQ
- Glassdoor 4.2/5 — positive engineering culture notes
- CEO background, recent news
```

CLI equivalent:
```bash
jobbing track research --name "Company Name" --research "Finding 1" "Finding 2" [--dry-run]
```

### Update Experience to Highlight

Edit the `## Experience to Highlight` section in the hub file:

```markdown
## Experience to Highlight

- Led platform team of 23 engineers at Mobimeo through full IaC migration
- Built IDP from scratch at 1KOMMA5° covering 400+ engineers
- Delivered zero-downtime Kubernetes migration at Modern Electric
```

CLI equivalent:
```bash
jobbing track highlights --name "Company Name" --highlights "Bullet 1" "Bullet 2" [--dry-run]
```

### Update Fit Assessment

Edit the `## Fit Assessment` section in the hub file and update `score:` in frontmatter:

```yaml
---
score: 82
---
```

```markdown
## Fit Assessment

**Score: 82**

Strong match on platform leadership scope and Kubernetes depth. Gap in fintech-specific compliance experience.

**Green flags:**
- Explicit call for IDP experience — 1KOMMA5° is a direct match
- Remote-first engineering culture

**Red flags:**
- Series A stage — compensation ceiling may be below target

**Gaps:**
- No PCI-DSS exposure

**Keywords missing:** FinOps, SOC 2
```

### Update Outreach Contacts

Edit the `## Outreach Contacts` section in the hub file. See `/outreach` for the full workflow.

```markdown
## Outreach Contacts

- **Jane Smith** — VP Engineering · [LinkedIn](https://www.linkedin.com/in/janesmith)
  - Note: Leads the Platform org. Ex-Google SRE. 2nd connection via Alex.
  - Message: "Hi Jane — I applied for the Platform Lead role at CompanyName. I built an IDP at 1KOMMA5° and led 23 engineers at Mobimeo. Would love to learn more about what you're building."
```

CLI equivalent (for bulk imports):
```bash
jobbing track outreach --name "Company Name" --contacts-json contacts.json [--dry-run]
```

### Update Questions I Might Get Asked

Edit the `## Questions I Might Get Asked` section in the hub file. Covered fully by `/prep` — use this only for manual additions.

```markdown
## Questions I Might Get Asked

**Tell me about scaling a DevOps team?**
At Mobimeo, scaled from 8 to 23 engineers across 3 sub-teams over 18 months. Hired 9 directly, onboarded 6 from other teams. Key was clear team topology and embedded SRE model.

**How do you handle incident response?**
Blameless postmortems, standardized on-call rotations, runbooks in the repo. At 1KOMMA5°, reduced MTTR by tightening on-call handover structure.
```

### Update Questions to Ask

Edit the `## Questions to Ask` section in the hub file. Covered fully by `/prep`.

```markdown
## Questions to Ask

- What does the on-call rotation look like for the platform team?
- How is the platform team structured relative to product engineering?
- What's the biggest infrastructure challenge in the next 6 months?
```

### Interview Prep and Debrief

These operations are handled by `/prep` and `/debrief` respectively. They write to `kanban/interviews/{Company}/{date}-{Slug}.md` and link back to the hub's `## Interviews` section. Use those skills directly.

### Follow-Up Check

```bash
jobbing track followup                    # check with default threshold (5 days)
jobbing track followup --threshold 7      # override threshold
jobbing track followup --save             # save report
```

Or invoke conversationally via `/followup` for a richer interactive summary with suggested actions.

## Rules

- **Status updates are Greg's decision.** Never auto-mark "Applied" or any other status.
- **All writes are direct file edits.** Read the hub file, make the change, write it back. No queue, no launchd.
- **Check before creating.** Confirm no hub file already exists for the company before creating one.
- **Overwrite warnings.** When replacing Research or Highlights sections, confirm with Greg if existing content would be lost.
- **Conclusions are Greg's words.** Don't write a conclusion without Greg's input — it captures his assessment, not Claude's.
- **All `--dry-run` flags are available on CLI commands** for previewing without writing.

## CLI Reference

```bash
jobbing track create --name "Company" --position "Role" --date 2026-02-22 [--dry-run]
jobbing track update --name "Company" --status "Applied" [--dry-run]
jobbing track highlights --name "Company" --highlights "Bullet 1" "Bullet 2" [--dry-run]
jobbing track research --name "Company" --research "Finding 1" "Finding 2" [--dry-run]
jobbing track outreach --name "Company" --contacts-json contacts.json [--dry-run]
jobbing track followup [--threshold N] [--save]
```

## Do Not
- Change any status without Greg's explicit instruction — never auto-mark "Applied", "Done", or any other status
- Use queue files or launchd for tracker writes — edit hub files directly using Read/Edit/Write tools
- Write a conclusion without Greg's input — conclusions capture Greg's assessment, not Claude's
- Overwrite existing highlights or research without confirming — these operations replace the entire section
- Create duplicate hub files — check if one already exists before creating
- Set `status: Done` without populating the `## Conclusion` section — always include the outcome text
- Use `--page-id` — there is no page_id concept; company identifier is the hub filename

## Related Skills

- `/analyze` — Fit assessment (always the first step)
- `/apply` — Full application workflow (hub file + JSON + PDFs)
- `/outreach` — LinkedIn contact research and messages
- `/prep` — Interview prep generation (run before interview)
- `/debrief` — Post-interview debrief capture (run after interview)
- `/followup` — Follow-up cadence monitor (check for stale conversations)
