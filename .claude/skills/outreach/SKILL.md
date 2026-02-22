---
name: outreach
description: Research LinkedIn contacts at a company for follow-up after applying. Drafts tailored connection request messages for hiring managers, recruiters, and peer connections.
---

# LinkedIn Outreach Research

Research LinkedIn contacts for follow-up after Greg submits an application. Run this after applying.

## Prerequisites
- Application has been submitted (or Greg has decided to proceed with outreach)
- Company name and role are known from the `/analyze` + `/apply` workflow

## Instructions

### Step 1: Research Contacts

Search for relevant contacts at the company:

- **Hiring manager** — Director/VP Eng, Head of Platform, etc.
- **Recruiter/TA** — Talent Acquisition, Technical Recruiter
- **Peer connections** — Engineers on the target team, mutual connections

### Step 2: Build Contact Profiles

For each contact, capture:

1. **name** and **title** — who they are
2. **linkedin** — profile URL
3. **note** — why this person matters: their background, why they're the right contact, mutual connections, relevant context about their role or team. Think "intel for Greg before he sends the message."
4. **message** — a ready-to-paste LinkedIn connection request (<300 chars) tailored to this specific contact

### Connection Request Message Guidelines

- Always mention the company name — never leave it implied
- Where possible, mention the contact's team or area
- Keep under 300 characters (LinkedIn limit)
- No AI tells — no "aligns perfectly" or summative self-congratulation
- Lead with the role applied for, then one or two concrete credentials
- **End with curiosity about them**, not a hard close. "Would love to learn more about {Company}" — not "Happy to connect"
- **Tone: warm and human.** Write like a peer reaching out, not a candidate pitching.
- **Tailor to the contact's role:** Engineering leaders get Greg's credentials most relevant to their domain. Recruiters get a concise experience summary. Peers get a shared-interest angle.
- **Map Greg's experience to what this person cares about.** Pick the 1-2 things from CONTEXT.md that would resonate with this person's responsibilities.

### Step 3: Present for Review

Present the contacts and messages to Greg for review before saving. Greg may want to adjust messaging or add/remove contacts.

### Step 4: Save to Notion

After Greg approves, write to `notion_queue/`:

```json
{
  "command": "outreach",
  "name": "CompanyName",
  "contacts": [
    {
      "name": "Jane Smith",
      "title": "VP Engineering",
      "linkedin": "https://www.linkedin.com/in/janesmith",
      "note": "Leads the Platform org. Ex-Google SRE. 2nd connection via Alex.",
      "message": "Hi Jane — I applied for the Platform Lead role at CompanyName. I built an IDP at 1KOMMA5° and led 23 engineers at Mobimeo. Would love to learn more about what you're building."
    }
  ]
}
```

This sets "Follow on LinkedIn" to "No" (contacts identified, outreach pending).

Or use the CLI directly: `jobbing track outreach --name "CompanyName" --contacts-json contacts.json`

## Do Not
- Write messages over 300 characters — LinkedIn connection requests have a hard limit
- Leave the company name implied — always name the company explicitly in the message
- End with "Happy to connect", "Would welcome a conversation", or similar hard closes — end with genuine curiosity about their work
- Write generic messages that could apply to any company or any contact — tailor every message to the specific person's role and domain
- Use stiff, transactional language — write like a peer reaching out, not a candidate pitching
- Use AI tells: "aligns perfectly", "uniquely positioned", "proven track record", "I'm confident that..."
- List Greg's entire resume in a 300-char message — pick the 1-2 things most relevant to this specific contact
- Send the same message template to hiring managers, recruiters, and peers — each category gets a different angle
- Skip the review checkpoint — present contacts and messages to Greg before saving to Notion
- Fabricate LinkedIn profile URLs — if you can't find the real URL, say so and leave the field for Greg to fill
- Invent mutual connections or shared interests that don't exist
- Save to Notion before Greg approves the contacts and messages
