# Onboarding

Runs the first time `finflow` is called and `~/.finflow/profile.json`
doesn't exist yet. See [schema.md](schema.md) for the exact fields being
collected.

Ask in this order. Keep it conversational, not a form dump — one topic at a
time, confirm before moving on. Accept "I don't have one" for optional
items and skip them.

1. **Currency & locale** — "What currency should I track this in? (e.g.
   PHP, USD)" Default locale can be inferred from currency if not given.

2. **Income** — For each income source: label (e.g. "day job salary"),
   amount, recurrence (once/weekly/biweekly/monthly), next pay date.
   Ask "any other income sources?" until the user says no.

3. **Recurring expenses & loan dues** — For each: label, amount, fixed or
   variable, recurrence, next/upcoming due date. Explicitly prompt for
   loan dues and bills by name ("any loan payments, credit card dues, or
   subscriptions due regularly?") since these are the ones most likely to
   collide with a purchase decision.

4. **Savings rule** — Ask which is easier for the user to think in: "a
   minimum balance you never want to dip below" or "a percentage of each
   paycheck you want to set aside." Store whichever one they pick; leave
   the other field `null`.

Write the completed profile to `~/.finflow/profile.json` in the schema
defined in [schema.md](schema.md), creating `~/.finflow/` first if needed.
Confirm the file was created and give a one-line summary of what was
saved.

## Updating later

Adding, editing, or removing entries after onboarding is a separate flow —
see [update.md](update.md). Don't re-run onboarding to make a small change.
