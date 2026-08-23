# Cash-Flow Projection

This is the math the advisor runs on every question, using the profile
described in [schema.md](schema.md). No AI reasoning should override these
numbers — only explain them.

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

## When no specific question is asked

Project the next 30 days, summarize upcoming loan/bill dues, and flag any
date where the projected balance would dip below the savings rule.

## Cross-currency entries

Some income/expense entries carry a `currency` different from the
profile's default `currency` (see
[schema.md](schema.md#field-notes)) — e.g. a foreign-client income paid in
USD while the profile's default is PHP. Never store a converted amount;
convert only at the moment of projection:

1. Before running the projection (step 1 above), get the current
   conversion rate for each foreign currency present in `income`/
   `expenses` to the profile's default `currency`. Ask the user for the
   rate if it can't be looked up live, and always state which rate was
   used and as of when in the final answer.
2. Convert that entry's `amount` to the default currency using the rate,
   then run the rest of the projection normally in the default currency.
3. Flag the conversion explicitly in the response (e.g. "XGrowth salary:
   $240 → ₱13,680 at 57/USD") so the user can see the assumption, since
   exchange rates drift and this is the one place in FinFlow where a
   number isn't purely local.
