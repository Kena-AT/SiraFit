---
name: sirafit
description: >-
  SiraFit AI Job Search & Career Operations Command Center (Native Antigravity Integration) -- evaluate offers, generate CVs, scan portals,
  track applications. Use when the user pastes a job URL or JD, asks to scan
  portals, generate a CV/PDF, track applications, prepare for interviews, draft
  outreach/emails, or run any career-ops mode.
arguments: mode
user_invocable: true
user-invocable: true
argument-hint: "[scan | discover | deep | pdf | text | latex | latex-tex | cover | email | add | expand | eu-swe | oferta | ofertas | apply | batch | tracker | agent-inbox | pipeline | contacto | training | project | interview-prep | interview | interview/plan | interview/practice | interview/debrief | interview-redflag | patterns | offer-prep | titles | upskill | followup | reply-watch | outcome | update]"
license: MIT
---

# SiraFit (Career-Ops Engine) -- Router

career-ops is a multi-CLI job-search command center. The routing below is shared across supported agent CLIs even when the invocation surface differs.

## Project Root Resolution

Before reading any repo-relative path, derive `PROJECT_ROOT` from this loaded `SKILL.md`: start at the skill file's directory and walk upward until the nearest directory containing both `AGENTS.md` and `modes/`. Resolve every path in this router (`modes/`, `config/`, `data/`, scripts, templates, and output paths) against `PROJECT_ROOT`, never against the process's current working directory. This is required even when the checkout itself is nested (for example `Development\\career-ops`) or the command starts from a subdirectory. If those two sentinels cannot be found, stop and locate the career-ops checkout before reading or writing files.

## Invocation Notes

- CLIs with slash-command registration can expose this router as `/sirafit (or /career-ops)`.
- In Cursor, this skill lives at `.cursor/skills/sirafit (or /career-ops)/` and is auto-discovered; ask for a mode by name, or paste a JD/URL to trigger auto-pipeline.
- Interactive Codex sessions use `codex` in the repo root. Slash commands are not guaranteed in Codex, so ask Codex to run the same mode by name if `/sirafit (or /career-ops)` is unavailable.
- Headless Codex workers use `codex exec "prompt"`.
- The routing semantics below stay the same regardless of whether the entrypoint is a slash command or a natural-language prompt.

Codex prompt examples that map to the same router semantics:

```text
Evaluate this JD with career-ops auto-pipeline: https://company.com/jobs/123
Run the career-ops scan mode and summarize new matches.
Run the career-ops pipeline mode for data/pipeline.md.
Run the career-ops pdf mode for the latest evaluated role.
Run the career-ops tracker mode and summarize the current statuses.
```

## Mode Routing

Determine the mode from `$mode`:

| Input | Mode |
|-------|------|
| (empty / no args) | `discovery` -- Show command menu |
| JD text or URL (no sub-command) | **`auto-pipeline`** |
| `oferta` | `oferta` |
| `ofertas` | `ofertas` |
| `contacto` | `contacto` |
| `deep` | `deep` |
| `interview-prep` | `interview-prep` |
| `interview` | `interview` |
| `eu-swe` | `regional/eu-swe` |
| `eu-fintech` | `regional/eu-fintech` |
| `interview/plan` | `interview/plan` |
| `interview/practice` | `interview/practice` |
| `interview/debrief` | `interview/debrief` |
| `pdf` | `pdf` |
| `text` | `text` |
| `latex` | `latex` |
| `latex-tex` | `latex-tex` |
| `email` | `email` |
| `add` | `add` |
| `expand` | `expand` |
| `training` | `training` |
| `project` | `project` |
| `tracker` | `tracker` |
| `agent-inbox` | `agent-inbox` |
| `inbox` | `agent-inbox` |
| `pipeline` | `pipeline` |
| `apply` | `apply` |
| `scan` | `scan` |
| `discover` | `discover` |
| `batch` | `batch` |
| `patterns` | `patterns` |
| `offer-prep` | `offer-prep` |
| `titles` | `titles` |
| `upskill` | `upskill` |
| `followup` | `followup` |
| `reply-watch` | `reply-watch` |
| `outcome` | `outcome` |
| `interview-redflag` | `interview-redflag` |
| `update` | `update` |
| `cover` | `cover` |

**Auto-pipeline detection:** If `$mode` is not a known sub-command AND contains JD text (keywords: "responsibilities", "requirements", "qualifications", "about the role", "we're looking for", company name + role) or a URL to a JD, execute `auto-pipeline`.

If `$mode` is not a sub-command AND doesn't look like a JD, show discovery.

---

## Output Language Directive

Before executing any mode, read `config/profile.yml` if it exists and resolve:

- `language.output` â†’ ISO language code for human-facing output. Default: `en`.
- `language.modes_dir` â†’ optional market-mode directory. This controls market vocabulary and local evaluation rules only.

Inject this directive after loading the mode instructions and before producing any user-visible content:

> Write all human-facing output in `{language.output}` regardless of the language of these instructions or of the job description. This includes reports, tracker notes, PDFs, cover letters, outreach, interview prep, form answers, and summaries. If `language.modes_dir` supplies market-specific vocabulary, keep the market logic but explain terms in `{language.output}` when needed.

`language.output` is authoritative for prose. `modes_dir` is market context; it must not force the prose language.

---

## Discovery Mode (no arguments)

If your CLI supports `/sirafit (or /career-ops)`, show this menu. In Codex, surface the same options in plain text and map the requested mode the same way.

Concrete equivalents for Codex prompt-driven sessions:

```text
/sirafit (or /career-ops) {JD}           â†” "Evaluate this JD with career-ops auto-pipeline: {JD or URL}"
/sirafit (or /career-ops) scan           â†” "Run the career-ops scan mode and summarize new matches."
/sirafit (or /career-ops) pipeline       â†” "Run the career-ops pipeline mode for data/pipeline.md."
/sirafit (or /career-ops) pdf            â†” "Run the career-ops pdf mode for the latest evaluated role."
/sirafit (or /career-ops) email          â†” "Run the career-ops email mode for the latest evaluated role."
/sirafit (or /career-ops) tracker        â†” "Run the career-ops tracker mode and summarize the current statuses."
```

Show this menu:

```
career-ops -- Command Center

Available commands:
  /sirafit (or /career-ops) {JD}      â†’ AUTO-PIPELINE: evaluate + report + PDF + tracker (paste text or URL)
  /sirafit (or /career-ops) pipeline  â†’ Process pending URLs from inbox (data/pipeline.md)
  /sirafit (or /career-ops) oferta    â†’ Evaluation only A-F (no auto PDF)
  /sirafit (or /career-ops) ofertas   â†’ Compare and rank multiple offers
  /sirafit (or /career-ops) contacto  â†’ LinkedIn power move: find contacts + draft message
  /sirafit (or /career-ops) deep      â†’ Deep research prompt about company
  /sirafit (or /career-ops) interview-prep â†’ Generate company-specific interview prep doc
  /sirafit (or /career-ops) interview    â†’ Interactive profile/CV onboarding interview
  /sirafit (or /career-ops) eu-swe    â†’ Calibrate a European SWE application before CV/apply/interview
  /sirafit (or /career-ops) eu-fintech â†’ Scan 21 EU fintech portals for Product Manager roles (zero-token)
  /sirafit (or /career-ops) interview/plan â†’ Time-blocked prep plan for an upcoming interview
  /sirafit (or /career-ops) interview/practice â†’ Practice interview, one question at a time with feedback
  /sirafit (or /career-ops) interview/debrief â†’ Post-interview debrief: close gaps, predict next round
  /sirafit (or /career-ops) pdf       â†’ PDF only, ATS-optimized CV
  /sirafit (or /career-ops) text      â†’ Tailored markdown CV (mirrors cv.md, no PDF)
  /sirafit (or /career-ops) latex     â†’ Export CV as LaTeX/Overleaf .tex
  /sirafit (or /career-ops) latex-tex â†’ Tailor your own resume.tex in place (opt-in; cv.md stays default)
  /sirafit (or /career-ops) cover     â†’ Cover letter: standalone JD paste or /sirafit (or /career-ops) cover {slug}
  /sirafit (or /career-ops) email     â†’ Formal application email draft (draft-only; never sends, submits, or clicks)
  /sirafit (or /career-ops) add       â†’ Add a project/paper/role to your CV (fetch + preview + confirm)
  /sirafit (or /career-ops) expand    â†’ Auto-discover and add missing competencies from profile links
  /sirafit (or /career-ops) training  â†’ Evaluate course/cert against North Star
  /sirafit (or /career-ops) project   â†’ Evaluate portfolio project idea
  /sirafit (or /career-ops) tracker   â†’ Application status overview
  /sirafit (or /career-ops) agent-inbox â†’ Queue/drain requests for the next session (data/agent-inbox.md)
  /sirafit (or /career-ops) apply     â†’ Live application assistant (reads form + generates answers)
  /sirafit (or /career-ops) scan      â†’ Scan portals and discover new offers
  /sirafit (or /career-ops) discover  â†’ Resolve a company list to scannable ATS boards + append to portals.yml (zero-token)
  /sirafit (or /career-ops) batch     â†’ Batch processing with parallel workers
  /sirafit (or /career-ops) patterns  â†’ Analyze rejection patterns and improve targeting
  /sirafit (or /career-ops) offer-prep â†’ Read a received offer/contract with the candidate: clause walk + lawyer questions (not legal advice)
  /sirafit (or /career-ops) titles    â†’ Suggest adjacent job titles from your CV to broaden the search
  /sirafit (or /career-ops) upskill   â†’ Aggregate skill-gap analysis from your evaluated reports
  /sirafit (or /career-ops) followup  â†’ Follow-up cadence tracker: flag overdue, generate drafts
  /sirafit (or /career-ops) outcome   â†’ Record application outcome & archive artifacts
  /sirafit (or /career-ops) update    â†’ Update career-ops system files with diff preview + compat check

Inbox: add URLs to data/pipeline.md â†’ /sirafit (or /career-ops) pipeline
Or paste a JD directly to run the full pipeline.
```

---

## Context Loading by Mode

After determining the mode, load the necessary files before executing:

If `modes/_custom.md` exists, read it after `modes/_profile.md` and before the selected mode file. It contains user house rules and procedural preferences. It may override workflow/style defaults, but it never adds factual claims about the candidate.

### Modes that require `_shared.md` + their mode file

Read `modes/_shared.md` + `modes/_profile.md` (if exists) + `modes/_custom.md` (if exists) + `modes/{mode}.md`

Applies to: `auto-pipeline`, `oferta`, `ofertas`, `pdf`, `text`, `contacto`, `apply`, `pipeline`, `scan`, `batch`

### Standalone modes with profile and custom context

Read `modes/_profile.md` (if exists) + `modes/_custom.md` (if exists) + `modes/{mode}.md`

Applies to: `tracker`, `agent-inbox`, `deep`, `interview-prep`, `interview`, `regional/eu-swe`, `interview/plan`, `interview/practice`, `interview/debrief`, `latex`, `latex-tex`, `training`, `project`, `patterns`, `titles`, `upskill`, `followup`, `reply-watch`, `outcome`, `cover`, `email`, `add`, `offer-prep`, `discover`

### Modes delegated to subagent

For `scan`, `apply` (with Playwright), and `pipeline` (3+ URLs): launch as a worker/subagent with the content of `_shared.md` + `_profile.md` (if exists) + `_custom.md` (if exists) + `modes/{mode}.md` injected into the worker prompt. If your CLI exposes an `Agent(...)` primitive, the call looks like this:

```python
Agent(
  subagent_type="general-purpose",
  prompt="[output language directive]\n\n[content of modes/_shared.md]\n\n[content of modes/_profile.md if exists]\n\n[content of modes/_custom.md if exists]\n\n[content of modes/{mode}.md]\n\n[invocation-specific data]",
  description="career-ops {mode}"
)
```

Execute the instructions from the loaded mode file.

