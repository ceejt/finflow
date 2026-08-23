# Updating an Existing Profile

Runs when the user calls `finflow update` (or says "update my profile" /
"add an expense" / similar) and `~/.finflow/profile.json` already exists.
See [schema.md](schema.md) for the fields being edited.

1. Load the existing profile.
2. Ask only for what's changing. Don't re-run full
   [onboarding](onboarding.md):
   - Add/remove an income source.
   - Add/edit/remove an expense-or-loan-due entry.
   - Change the savings rule (mode, minBalance, or percentOfIncome).
   - Change currency or locale.
3. Rewrite `~/.finflow/profile.json` with the change applied and
   `updatedAt` set to today.
4. Confirm what changed with a short diff-style summary, e.g.:
   `added: Maya loan due, ₱3,500/month on the 15th`
   `changed: savings rule from ₱10,000 min balance to 10% of income`

Never touch fields the user didn't ask to change.
