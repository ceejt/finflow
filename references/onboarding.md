# Onboarding

Runs the first time `finflow` is called and `~/.finflow/profile.json`
doesn't exist yet. See [schema.md](schema.md) for the exact fields being
collected.

Ask in this order, one topic at a time, confirming before moving on. For
each topic, present the fill-in template below so the user can answer with
values directly instead of a back-and-forth per field. Accept "I don't
have one" / a blank template for optional items and skip them. A user can
also just answer in plain sentences instead of the template — parse either
form.

1. **Currency & locale**

   ```
   Currency (e.g. PHP, USD):
   Locale (optional, e.g. en-PH — inferred from currency if left blank):
   ```

2. **Income** — one block per income source, ask "any other income
   sources?" until the user says no:

   ```
   Label:
   Amount:
   Currency (optional — defaults to profile currency; set this if paid in a different currency, e.g. a foreign-client income):
   Recurrence: once / weekly / biweekly / monthly
   Next pay date (YYYY-MM-DD):
   ```

3. **Recurring expenses & loan dues** — one block per expense, prompting
   explicitly for loan dues and bills by name ("any loan payments, credit
   card dues, or subscriptions due regularly?") since these are the ones
   most likely to collide with a purchase decision:

   ```
   Label:
   Amount:
   Type: fixed / variable
   Recurrence: once / weekly / biweekly / monthly
   Next due date (YYYY-MM-DD):
   ```

4. **Savings rule** — ask which is easier for the user to think in, then
   present only the matching template:

   ```
   Mode: minBalance / percentOfIncome
   Value: (a minimum balance amount, or a percentage of income)
   ```

   Store whichever mode they pick; leave the other schema field `null`.

Write the completed profile to `~/.finflow/profile.json` in the schema
defined in [schema.md](schema.md), creating `~/.finflow/` first if needed.
Confirm the file was created and give a one-line summary of what was
saved.

## Updating later

Adding, editing, or removing entries after onboarding is a separate flow —
see [update.md](update.md). Don't re-run onboarding to make a small change.
