# FinFlow Profile Schema

The profile always lives at `~/.finflow/profile.json` — never inside the
skill's own directory. See SKILL.md for why.

```json
{
  "currency": "PHP",
  "locale": "en-PH",
  "createdAt": "2026-08-23",
  "updatedAt": "2026-08-23",
  "income": [
    {
      "label": "InstaCode salary",
      "amount": 25000,
      "recurrence": "monthly",
      "nextDate": "2026-09-01"
    }
  ],
  "expenses": [
    {
      "label": "Rent",
      "amount": 8000,
      "type": "fixed",
      "recurrence": "monthly",
      "nextDate": "2026-09-05"
    },
    {
      "label": "Motorcycle loan",
      "amount": 3500,
      "type": "fixed",
      "recurrence": "monthly",
      "nextDate": "2026-09-15"
    }
  ],
  "savingsRule": {
    "mode": "minBalance",
    "minBalance": 10000,
    "percentOfIncome": null
  }
}
```

## Field notes

- `recurrence`: one of `once`, `weekly`, `biweekly`, `monthly`. A `once`
  entry does not repeat after its `nextDate`/date passes.
- `expenses[].type`: `fixed` (loan dues, rent, subscriptions — same amount
  each cycle) or `variable` (groceries, discretionary — treat as an
  estimate, not exact).
- `savingsRule.mode`: `minBalance` (never let projected balance go below
  `minBalance`) or `percentOfIncome` (set aside that % of each income entry
  before it counts as spendable — compute an effective `minBalance`
  equivalent from this when projecting; see
  [projection.md](projection.md)). Only one of `minBalance` /
  `percentOfIncome` is populated depending on mode; the other stays `null`.
- Amounts are plain numbers in the profile's `currency`, no symbols.
- Dates are `YYYY-MM-DD`.
