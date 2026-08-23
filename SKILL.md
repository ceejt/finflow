---
name: finflow
description: >
  Local-first financial advisor that projects a user's cash flow from their
  income and recurring expenses/loan dues, then answers ad-hoc financial
  questions like "can I buy this now given my loan due next week and my
  savings target?" or "when's the safest time to buy X?". Stores a private
  JSON profile outside the skill folder so the skill repo stays safe to
  clone/pull and share on GitHub without ever exposing user data. Use when
  the user runs `finflow`, `finflow update`, or asks about affordability,
  purchase timing, savings safety, upcoming loan/bill due dates, or cash
  flow projection. First run onboards a new profile; later runs act as the
  advisor.
argument-hint: "[update]"
license: MIT
---

# FinFlow

A conversational financial advisor. It keeps one private profile per user
(income, recurring expenses/loan dues, savings rule, currency/locale) and
uses it to project cash flow and answer real questions: afford this now?
when's the safest window to buy? will this loan due date and this purchase
collide?

Full profile schema, onboarding question set, and the cash-flow projection
algorithm live in [references/spec.md](references/spec.md). Read it before
doing anything below — it is the source of truth for field names and the
math.

## The one hard rule: profile location

The profile is **`~/.finflow/profile.json`** — always that path, always
outside this skill's own directory. Never write it inside
`~/.claude/skills/finflow/` or any other git-tracked path.

This is the entire point of the design: this skill folder is meant to be
cloned from GitHub and pulled for updates. If the profile ever lived inside
the skill folder, cloning or updating the skill would risk touching or
leaking someone's financial data. Keeping it at a fixed path outside the
repo means:

- `git clone`/`git pull` on the skill never reads, writes, or exposes any
  user's data.
- Every user who installs this skill gets their own private profile on
  their own machine, and it never leaves that machine unless they choose to
  share the file themselves.
- No network calls are ever made to store, sync, or back up the profile.
  Reasoning over the data is the whole feature; persistence is strictly
  local.

If `~/.finflow/` does not exist, create it (`mkdir -p`) before writing the
profile.

## Workflow

1. **Check for an existing profile.** Look for `~/.finflow/profile.json`.

2. **No profile found → onboarding.** Ask the onboarding questions in
   [references/spec.md](references/spec.md#onboarding-questions), one topic
   at a time (income, then expenses/loan dues, then savings rule, then
   currency/locale). Don't demand every field up front if the user only has
   partial info — a single income source and rough expenses is enough to
   start; more can be added later via `finflow update`. Write the answers
   to `~/.finflow/profile.json` in the schema defined in the spec. Confirm
   the file was created and give a one-line summary of what was saved.

3. **Profile found, plain `finflow` call → act as advisor.** Load the
   profile, then:
   - If the user asked a specific question (e.g. "can I buy a ₱9,000 plane
     ticket next week?"), run the cash-flow projection
     (spec: [Cash-flow projection](references/spec.md#cash-flow-projection))
     over the relevant horizon and answer directly: yes/no/best window,
     plus the reasoning (projected balance on that date, upcoming loan
     dues nearby, distance from the savings safety buffer).
   - If the user gave no specific question, project the next 30 days,
     summarize upcoming loan/bill dues, and flag any date where the
     projected balance would dip below the savings rule.
   - Never let the profile's declared safety buffer be silently ignored —
     any purchase recommendation must keep `projected_balance - cost >=
     safety_buffer` on the recommended date.

4. **`finflow update`** (or the user says "update my profile" / "add an
   expense" / etc.) → load the existing profile, ask only for what's
   changing (add/remove an income source, add/edit/remove an
   expense-or-loan-due entry, change the savings rule, change
   currency/locale), then rewrite `~/.finflow/profile.json`. Do not re-run
   full onboarding. Confirm what changed with a short diff-style summary
   ("added: Maya loan due, ₱3,500/month on the 15th").

5. **Never commit the profile.** If this skill folder is ever inside a git
   repo the user is committing from, and `~/.finflow/` is somehow not
   outside it, stop and warn the user rather than proceeding — this
   violates the local-first design.

## Verification

After writing or updating the profile, read it back and confirm it parses
as valid JSON and matches the schema in the spec before reporting success.
