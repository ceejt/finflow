#!/usr/bin/env python3
"""
finflow: deterministic cash-flow projection over ~/.finflow/profile.json.

Pure stdlib, no network calls, no LLM. This is the "math engine" half of
FinFlow's design — it never guesses, never explains, just computes. The
conversational advisor (the Claude Code skill) is the reasoning layer on
top of this; this script is what it *should* be calling instead of doing
the arithmetic in-context.

Profile schema: see ../references/schema.md. This script does not modify
the profile — use `finflow update` (the skill) or edit the JSON directly.
"""

import argparse
import calendar
import json
import sys
from datetime import date, timedelta
from pathlib import Path

PROFILE_PATH = Path.home() / ".finflow" / "profile.json"


def load_profile():
    if not PROFILE_PATH.exists():
        sys.exit(
            f"No profile found at {PROFILE_PATH}. Run the `finflow` skill "
            "in Claude Code first to onboard one."
        )
    with open(PROFILE_PATH) as f:
        return json.load(f)


def parse_date(s):
    return date.fromisoformat(s)


def add_months(d, n):
    """Add n calendar months to d, clamping the day to the target month's length."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


RECURRENCE_STEP_DAYS = {"weekly": 7, "biweekly": 14}


def occurrences(entry, window_start, window_end):
    """Yield every date `entry` fires on within [window_start, window_end]."""
    next_date = parse_date(entry["nextDate"])
    recurrence = entry["recurrence"]
    end_date = parse_date(entry["endDate"]) if entry.get("endDate") else None
    effective_end = min(window_end, end_date) if end_date else window_end

    if recurrence == "once":
        if window_start <= next_date <= effective_end:
            yield next_date
        return

    if recurrence in RECURRENCE_STEP_DAYS:
        step = RECURRENCE_STEP_DAYS[recurrence]
        d = next_date
        # fast-forward to the first occurrence on/after window_start
        if d < window_start:
            missed = (window_start - d).days
            d = d + timedelta(days=(missed // step) * step)
            while d < window_start:
                d += timedelta(days=step)
        while d <= effective_end:
            yield d
            d += timedelta(days=step)
        return

    if recurrence == "monthly":
        d = next_date
        n = 0
        while d < window_start:
            n += 1
            d = add_months(next_date, n)
        while d <= effective_end:
            yield d
            n += 1
            d = add_months(next_date, n)
        return

    raise ValueError(f"Unknown recurrence: {recurrence!r}")


def convert(amount, currency, profile_currency, rates):
    if currency is None or currency == profile_currency:
        return amount
    if currency not in rates:
        raise SystemExit(
            f"Missing exchange rate for {currency} -> {profile_currency}. "
            f"Pass --rate {currency}=<rate> (units of {profile_currency} per 1 {currency})."
        )
    return amount * rates[currency]


def build_ledger(profile, start_date, days, start_balance, rates):
    """Return (ledger, final_balance). ledger is a list of
    (date, [(label, signed_amount_in_profile_currency, note)], running_balance)."""
    window_end = start_date + timedelta(days=days)
    profile_currency = profile["currency"]

    events_by_date = {}

    for entry in profile.get("income", []):
        for d in occurrences(entry, start_date, window_end):
            amt = convert(entry["amount"], entry.get("currency"), profile_currency, rates)
            note = f"{entry['amount']} {entry.get('currency', profile_currency)}" if entry.get("currency") and entry["currency"] != profile_currency else ""
            events_by_date.setdefault(d, []).append((entry["label"], amt, note))

    for entry in profile.get("expenses", []):
        for d in occurrences(entry, start_date, window_end):
            amt = convert(entry["amount"], entry.get("currency"), profile_currency, rates)
            note = f"{entry['amount']} {entry.get('currency', profile_currency)}" if entry.get("currency") and entry["currency"] != profile_currency else ""
            events_by_date.setdefault(d, []).append((entry["label"], -amt, note))

    ledger = []
    balance = start_balance
    for d in sorted(events_by_date):
        for label, amt, note in events_by_date[d]:
            balance += amt
        ledger.append((d, events_by_date[d], balance))

    return ledger, balance


def effective_buffer(profile, ledger, start_balance):
    """Compute the safety buffer to hold against, per savingsRule.mode."""
    rule = profile.get("savingsRule", {})
    mode = rule.get("mode")
    if mode == "minBalance":
        return rule.get("minBalance") or 0
    if mode == "percentOfIncome":
        # Reserve pct of every income event seen so far; approximate as a
        # constant using the most recent running reserve at query time.
        pct = (rule.get("percentOfIncome") or 0) / 100
        reserve = 0
        for d, events, _ in ledger:
            for label, amt, note in events:
                if amt > 0:
                    reserve += amt * pct
        return reserve
    return 0


def cmd_project(args):
    profile = load_profile()
    rates = dict(r.split("=") for r in args.rate) if args.rate else {}
    rates = {k: float(v) for k, v in rates.items()}
    start = date.fromisoformat(args.start) if args.start else date.today()

    ledger, final_balance = build_ledger(profile, start, args.days, args.balance, rates)
    buffer_ = effective_buffer(profile, ledger, args.balance)

    print(f"Projection: {start} + {args.days}d, starting balance {args.balance} {profile['currency']}")
    print(f"Safety buffer: {buffer_} {profile['currency']}\n")

    if not ledger:
        print("No income/expense events in this window.")
    for d, events, balance in ledger:
        flags = " [BELOW BUFFER]" if balance < buffer_ else ""
        print(f"{d}  balance={balance:.2f}{flags}")
        for label, amt, note in events:
            sign = "+" if amt >= 0 else "-"
            extra = f" ({note})" if note else ""
            print(f"    {sign}{abs(amt):.2f}  {label}{extra}")

    print(f"\nFinal balance on {start + timedelta(days=args.days)}: {final_balance:.2f} {profile['currency']}")


def cmd_afford(args):
    profile = load_profile()
    rates = dict(r.split("=") for r in args.rate) if args.rate else {}
    rates = {k: float(v) for k, v in rates.items()}
    start = date.fromisoformat(args.start) if args.start else date.today()
    deadline = date.fromisoformat(args.deadline) if args.deadline else start + timedelta(days=args.days)
    horizon = (deadline - start).days

    ledger, _ = build_ledger(profile, start, horizon, args.balance, rates)
    buffer_ = effective_buffer(profile, ledger, args.balance)

    safe_dates = []
    running = args.balance
    idx = 0
    # Walk every calendar day, applying ledger events as they occur, to find
    # the earliest day the affordability check passes and stays passed.
    events_by_date = {}
    for d, events, balance in ledger:
        events_by_date[d] = balance

    d = start
    balance = args.balance
    while d <= deadline:
        if d in events_by_date:
            balance = events_by_date[d]
        if balance - args.cost >= buffer_:
            safe_dates.append(d)
        d += timedelta(days=1)

    print(f"Afford check: cost={args.cost} {profile['currency']}, buffer={buffer_} {profile['currency']}, deadline={deadline}")
    if not safe_dates:
        print("No safe date found before the deadline.")
        return
    # group consecutive safe dates into windows
    windows = []
    window_start = safe_dates[0]
    prev = safe_dates[0]
    for d in safe_dates[1:]:
        if (d - prev).days > 1:
            windows.append((window_start, prev))
            window_start = d
        prev = d
    windows.append((window_start, prev))

    print(f"Earliest safe window: {windows[0][0]} to {windows[0][1]}")
    if len(windows) > 1:
        print("Other safe windows:")
        for w in windows[1:]:
            print(f"  {w[0]} to {w[1]}")


def cmd_show(args):
    profile = load_profile()
    print(f"Profile: {PROFILE_PATH}")
    print(f"Currency: {profile['currency']}  Locale: {profile.get('locale', '-')}")
    print(f"\nIncome ({len(profile.get('income', []))}):")
    for e in profile.get("income", []):
        cur = e.get("currency", profile["currency"])
        print(f"  {e['label']}: {e['amount']} {cur} {e['recurrence']} next {e['nextDate']}")
    print(f"\nExpenses ({len(profile.get('expenses', []))}):")
    for e in profile.get("expenses", []):
        cur = e.get("currency", profile["currency"])
        end = f" ends {e['endDate']}" if e.get("endDate") else ""
        print(f"  {e['label']}: {e['amount']} {cur} {e['type']} {e['recurrence']} next {e['nextDate']}{end}")
    rule = profile.get("savingsRule", {})
    print(f"\nSavings rule: mode={rule.get('mode')} minBalance={rule.get('minBalance')} percentOfIncome={rule.get('percentOfIncome')}")


def main():
    p = argparse.ArgumentParser(description="FinFlow deterministic cash-flow engine")
    sub = p.add_subparsers(dest="command", required=True)

    p_show = sub.add_parser("show", help="print the loaded profile")
    p_show.set_defaults(func=cmd_show)

    p_project = sub.add_parser("project", help="project balance forward day by day")
    p_project.add_argument("--days", type=int, default=30)
    p_project.add_argument("--balance", type=float, default=0, help="starting balance")
    p_project.add_argument("--start", help="YYYY-MM-DD, default today")
    p_project.add_argument("--rate", action="append", help="CURRENCY=RATE, e.g. USD=57. Repeatable.")
    p_project.set_defaults(func=cmd_project)

    p_afford = sub.add_parser("afford", help="find the earliest safe date to spend `cost`")
    p_afford.add_argument("--cost", type=float, required=True)
    p_afford.add_argument("--days", type=int, default=60, help="horizon if --deadline not given")
    p_afford.add_argument("--deadline", help="YYYY-MM-DD hard deadline")
    p_afford.add_argument("--balance", type=float, default=0, help="starting balance")
    p_afford.add_argument("--start", help="YYYY-MM-DD, default today")
    p_afford.add_argument("--rate", action="append", help="CURRENCY=RATE, e.g. USD=57. Repeatable.")
    p_afford.set_defaults(func=cmd_afford)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
