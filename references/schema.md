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
      "currency": "PHP",
      "recurrence": "monthly",
      "nextDate": "2026-09-01"
    },
    {
      "label": "XGrowth salary",
      "amount": 240,
      "currency": "USD",
      "recurrence": "biweekly",
      "nextDate": "2026-08-31"
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
      "nextDate": "2026-09-15",
      "endDate": "2027-02-15"
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
- `expenses[].endDate` (optional): the date of the final occurrence for an
  expense with a fixed payoff, e.g. an installment loan. After this date
  the entry no longer recurs and should be excluded from projections. Omit
  for expenses with no defined end (rent, subscriptions, etc.). When the
  user tells you how many installments are paid vs. total (e.g. "1 of 9"),
  compute `endDate` from `nextDate` and the remaining installment count at
  the entry's recurrence interval, and store the result here rather than
  making the user do the math.
- `savingsRule.mode`: `minBalance` (never let projected balance go below
  `minBalance`) or `percentOfIncome` (set aside that % of each income entry
  before it counts as spendable — compute an effective `minBalance`
  equivalent from this when projecting; see
  [projection.md](projection.md)). Only one of `minBalance` /
  `percentOfIncome` is populated depending on mode; the other stays `null`.
- Amounts are plain numbers, no symbols.
- `income[].currency` / `expenses[].currency`: each entry stores its own
  native currency (e.g. a foreign-client income source paid in USD while
  the profile's default `currency` is PHP). Do not convert amounts before
  saving. Conversion to the profile's default `currency` happens only at
  query time — see [projection.md](projection.md#cross-currency-entries) —
  so the stored number always reflects what was actually earned/owed, not
  a stale converted snapshot. If an entry's `currency` is omitted, it
  defaults to the profile's top-level `currency`.
- Dates are `YYYY-MM-DD`.
