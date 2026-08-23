# FinFlow Spec

Profile schema, onboarding questions, and the cash-flow projection algorithm.
Read this in full before running onboarding or answering an advisory
question.

---

## Profile location

Always `~/.finflow/profile.json`. Never inside the skill's own directory.
See SKILL.md for why.

---

## Profile schema

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

Field notes:

- `recurrence`: one of `once`, `weekly`, `biweekly`, `monthly`. A `once`
  entry does not repeat after its `nextDate`/date passes.
- `expenses[].type`: `fixed` (loan dues, rent, subscriptions — same amount
  each cycle) or `variable` (groceries, discretionary — treat as an
  estimate, not exact).
- `savingsRule.mode`: `minBalance` (never let projected balance go below
  `minBalance`) or `percentOfIncome` (set aside that % of each income entry
  before it counts as spendable — compute an effective `minBalance`
  equivalent from this when projecting). Only one of `minBalance` /
  `percentOfIncome` is populated depending on mode; the other stays `null`.
- Amounts are plain numbers in the profile's `currency`, no symbols.
- Dates are `YYYY-MM-DD`.

---

## Onboarding questions

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

Write the completed profile to `~/.finflow/profile.json`, creating
`~/.finflow/` first if needed.

---

## Cash-flow projection

This is the math the advisor runs on every question. No AI reasoning
should override these numbers — only explain them.

```
1. Pick a horizon: default 30 days for a general check-in, up to 90 days
   when a purchase's target/deadline date is further out.

2. Starting from today, walk forward day by day. For each day:
   - Add any income entries whose recurrence lands on that day.
   - Subtract any expense entries (fixed or variable-as-estimate) whose
     recurrence lands on that day.
   - Running balance = previous day's balance + today's net.
   (If the user hasn't given a current balance, ask for it once, or note
   the projection is relative/directional rather than absolute.)

3. Effective safety buffer:
   - mode == minBalance -> use minBalance directly.
   - mode == percentOfIncome -> for each income event, reserve that % into
     an accumulating buffer; effective buffer = accumulated reserve as of
     that date.

4. For a specific purchase question (cost, optional deadline):
   Find dates where:
     projected_balance - cost >= effective_safety_buffer
   Group consecutive valid dates into windows. Recommend the earliest safe
   window before any hard deadline; note the next loan/bill due nearby as
   context ("your rent hits 3 days after this window, projected balance
   still clears your buffer after that").

5. If no valid window exists before a stated deadline, say so plainly and
   name the blocking obligation (which expense/loan due keeps the balance
   under buffer) rather than forcing a recommendation.
```

Always surface the reasoning, not just a date: state the projected balance
on the recommended date, the safety buffer it's measured against, and any
nearby due dates that are relevant.
