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

Detailed guidance is split by task — read only what the current call needs:

- [references/schema.md](references/schema.md) — the profile JSON schema (source of truth for field names)
- [references/onboarding.md](references/onboarding.md) — first-run question flow
- [references/projection.md](references/projection.md) — cash-flow projection algorithm
- [references/update.md](references/update.md) — editing an existing profile

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
  local. The one exception is a live exchange-rate lookup for entries in a
  currency other than the profile's default (see
  [references/projection.md](references/projection.md#cross-currency-entries))
  — that is a public, read-only rate fetch, never a transmission of the
  user's financial data.

If `~/.finflow/` does not exist, create it (`mkdir -p`) before writing the
profile.

## Workflow

1. **Check for an existing profile.** Look for `~/.finflow/profile.json`.

2. **No profile found → onboarding.** Follow
   [references/onboarding.md](references/onboarding.md). Don't demand every
   field up front if the user only has partial info — a single income
   source and rough expenses is enough to start; more can be added later
   via `finflow update`.

3. **Profile found, plain `finflow` call → act as advisor.** Load the
   profile, then run the projection **by calling `scripts/finflow.py`**
   (see below) rather than computing the day-by-day balance by hand — the
   script is a deterministic, tested implementation of the algorithm in
   [references/projection.md](references/projection.md); use it as the
   arithmetic source of truth and add only the natural-language
   explanation on top.
   - If the user asked a specific question (e.g. "can I buy a ₱9,000 plane
     ticket next week?"), run `finflow.py afford --cost ... [--deadline
     ...] [--balance ...] [--rate CUR=RATE ...]` and turn its output into
     a plain-language answer: yes/no/best window, plus the reasoning
     (projected balance on that date, upcoming loan dues nearby, distance
     from the savings safety buffer).
   - If the user gave no specific question, run `finflow.py project
     --days 30 [--balance ...] [--rate CUR=RATE ...]`, summarize upcoming
     loan/bill dues from its output, and flag any `[BELOW BUFFER]` day.
   - Never let the profile's declared safety buffer be silently ignored —
     the script already enforces `projected_balance - cost >=
     safety_buffer`; don't override or second-guess its arithmetic.
   - The script needs a starting balance (`--balance`) to give absolute
     numbers — ask the user for their current balance if they haven't
     given one recently, or fall back to a relative/directional answer
     (`--balance 0`) and say so explicitly.

### Running the script

```
python3 scripts/finflow.py show
python3 scripts/finflow.py project --days 30 --balance 3000 [--start YYYY-MM-DD] [--rate USD=57]
python3 scripts/finflow.py afford --cost 9000 [--deadline YYYY-MM-DD] --balance 3000 [--rate USD=57]
```

- `--rate CURRENCY=RATE` (repeatable) is required for every foreign
  currency present among the entries that fall inside the projection
  window (see [references/projection.md](references/projection.md#cross-currency-entries))
  — the script will error out naming exactly which rate is missing rather
  than silently guessing. Get the rate live or ask the user.
- Pure stdlib, no dependencies, no network calls of its own. It only
  reads `~/.finflow/profile.json` — it never writes to it.

4. **`finflow update`** (or the user says "update my profile" / "add an
   expense" / etc.) → follow [references/update.md](references/update.md).

5. **Never commit the profile.** If this skill folder is ever inside a git
   repo the user is committing from, and `~/.finflow/` is somehow not
   outside it, stop and warn the user rather than proceeding — this
   violates the local-first design.

## Verification

After writing or updating the profile, read it back and confirm it parses
as valid JSON and matches [references/schema.md](references/schema.md)
before reporting success.
