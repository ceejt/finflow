#!/usr/bin/env python3
"""
Unit tests for finflow.py. Pure stdlib (unittest), no dependencies.

Run: python3 scripts/test_finflow.py
"""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import finflow  # noqa: E402


def entry(**kw):
    base = {"label": "x", "amount": 100, "recurrence": "monthly", "nextDate": "2026-01-15"}
    base.update(kw)
    return base


class AddMonthsTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(finflow.add_months(date(2026, 1, 15), 1), date(2026, 2, 15))

    def test_year_rollover(self):
        self.assertEqual(finflow.add_months(date(2026, 12, 1), 1), date(2027, 1, 1))

    def test_clamped_to_shorter_month(self):
        # Jan 31 + 1 month -> Feb has 28 days in 2026 (not a leap year)
        self.assertEqual(finflow.add_months(date(2026, 1, 31), 1), date(2026, 2, 28))

    def test_leap_year_feb(self):
        self.assertEqual(finflow.add_months(date(2028, 1, 31), 1), date(2028, 2, 29))

    def test_zero_months_is_identity(self):
        self.assertEqual(finflow.add_months(date(2026, 5, 10), 0), date(2026, 5, 10))


class OccurrencesOnceTests(unittest.TestCase):
    def test_within_window(self):
        e = entry(recurrence="once", nextDate="2026-01-10")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 31)))
        self.assertEqual(dates, [date(2026, 1, 10)])

    def test_before_window_excluded(self):
        e = entry(recurrence="once", nextDate="2025-12-31")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 31)))
        self.assertEqual(dates, [])

    def test_after_window_excluded(self):
        e = entry(recurrence="once", nextDate="2026-02-01")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 31)))
        self.assertEqual(dates, [])

    def test_on_boundary_dates_included(self):
        e = entry(recurrence="once", nextDate="2026-01-31")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 31)))
        self.assertEqual(dates, [date(2026, 1, 31)])


class OccurrencesStepTests(unittest.TestCase):
    def test_weekly_within_window(self):
        e = entry(recurrence="weekly", nextDate="2026-01-01")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 15)))
        self.assertEqual(dates, [date(2026, 1, 1), date(2026, 1, 8), date(2026, 1, 15)])

    def test_weekly_fast_forwards_when_start_is_before_window(self):
        # nextDate long before window_start: must skip ahead, not enumerate from scratch.
        e = entry(recurrence="weekly", nextDate="2020-01-01")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 8)))
        self.assertTrue(all(date(2026, 1, 1) <= d <= date(2026, 1, 8) for d in dates))
        self.assertGreaterEqual(len(dates), 1)

    def test_biweekly(self):
        e = entry(recurrence="biweekly", nextDate="2026-01-01")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 29)))
        self.assertEqual(dates, [date(2026, 1, 1), date(2026, 1, 15), date(2026, 1, 29)])

    def test_respects_end_date(self):
        e = entry(recurrence="weekly", nextDate="2026-01-01", endDate="2026-01-08")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 31)))
        self.assertEqual(dates, [date(2026, 1, 1), date(2026, 1, 8)])


class OccurrencesMonthlyTests(unittest.TestCase):
    def test_monthly_within_window(self):
        e = entry(recurrence="monthly", nextDate="2026-01-15")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 3, 31)))
        self.assertEqual(dates, [date(2026, 1, 15), date(2026, 2, 15), date(2026, 3, 15)])

    def test_monthly_fast_forwards_when_start_is_before_window(self):
        e = entry(recurrence="monthly", nextDate="2025-01-15")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 1, 31)))
        self.assertEqual(dates, [date(2026, 1, 15)])

    def test_monthly_respects_end_date_mid_month(self):
        e = entry(recurrence="monthly", nextDate="2026-01-15", endDate="2026-02-15")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 4, 30)))
        self.assertEqual(dates, [date(2026, 1, 15), date(2026, 2, 15)])

    def test_monthly_end_date_before_next_occurrence_stops_entirely(self):
        e = entry(recurrence="monthly", nextDate="2026-01-15", endDate="2026-01-20")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 6, 30)))
        self.assertEqual(dates, [date(2026, 1, 15)])

    def test_monthly_clamps_across_short_month(self):
        e = entry(recurrence="monthly", nextDate="2026-01-31")
        dates = list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 3, 31)))
        self.assertEqual(dates, [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)])


class OccurrencesErrorTests(unittest.TestCase):
    def test_unknown_recurrence_raises(self):
        e = entry(recurrence="yearly")
        with self.assertRaises(ValueError):
            list(finflow.occurrences(e, date(2026, 1, 1), date(2026, 12, 31)))


class ConvertTests(unittest.TestCase):
    def test_same_currency_is_noop(self):
        self.assertEqual(finflow.convert(100, "PHP", "PHP", {}), 100)

    def test_none_currency_is_noop(self):
        self.assertEqual(finflow.convert(100, None, "PHP", {}), 100)

    def test_applies_rate(self):
        self.assertEqual(finflow.convert(10, "USD", "PHP", {"USD": 57}), 570)

    def test_missing_rate_raises_systemexit_naming_currency(self):
        with self.assertRaises(SystemExit) as ctx:
            finflow.convert(10, "USD", "PHP", {})
        self.assertIn("USD", str(ctx.exception))


class BuildLedgerTests(unittest.TestCase):
    def _profile(self):
        return {
            "currency": "PHP",
            "income": [entry(label="salary", amount=1000, recurrence="monthly", nextDate="2026-01-05")],
            "expenses": [entry(label="rent", amount=400, recurrence="monthly", nextDate="2026-01-10")],
        }

    def test_running_balance(self):
        profile = self._profile()
        ledger, final_balance = finflow.build_ledger(profile, date(2026, 1, 1), 31, 0, {})
        self.assertEqual(final_balance, 600)
        dates = [d for d, _, _ in ledger]
        self.assertEqual(dates, [date(2026, 1, 5), date(2026, 1, 10)])

    def test_expense_is_negative_signed(self):
        profile = self._profile()
        ledger, _ = finflow.build_ledger(profile, date(2026, 1, 1), 31, 0, {})
        rent_day = next(events for d, events, _ in ledger if d == date(2026, 1, 10))
        label, amt, _note = rent_day[0]
        self.assertEqual(label, "rent")
        self.assertLess(amt, 0)

    def test_no_events_gives_empty_ledger_and_unchanged_balance(self):
        profile = {"currency": "PHP", "income": [], "expenses": []}
        ledger, final_balance = finflow.build_ledger(profile, date(2026, 1, 1), 10, 500, {})
        self.assertEqual(ledger, [])
        self.assertEqual(final_balance, 500)

    def test_cross_currency_conversion_applied(self):
        profile = {
            "currency": "PHP",
            "income": [entry(label="foreign", amount=100, currency="USD",
                              recurrence="once", nextDate="2026-01-05")],
            "expenses": [],
        }
        _ledger, final_balance = finflow.build_ledger(
            profile, date(2026, 1, 1), 10, 0, {"USD": 57}
        )
        self.assertEqual(final_balance, 5700)


class EffectiveBufferTests(unittest.TestCase):
    def test_min_balance_mode(self):
        profile = {"savingsRule": {"mode": "minBalance", "minBalance": 1000}}
        self.assertEqual(finflow.effective_buffer(profile, [], 0), 1000)

    def test_min_balance_missing_defaults_to_zero(self):
        profile = {"savingsRule": {"mode": "minBalance"}}
        self.assertEqual(finflow.effective_buffer(profile, [], 0), 0)

    def test_percent_of_income_mode_sums_income_events(self):
        profile = {"savingsRule": {"mode": "percentOfIncome", "percentOfIncome": 10}}
        ledger = [
            (date(2026, 1, 5), [("salary", 1000, "")], 1000),
            (date(2026, 1, 10), [("rent", -400, "")], 600),
            (date(2026, 2, 5), [("salary", 1000, "")], 1600),
        ]
        self.assertEqual(finflow.effective_buffer(profile, ledger, 0), 200)

    def test_unknown_mode_defaults_to_zero(self):
        profile = {"savingsRule": {"mode": "somethingElse"}}
        self.assertEqual(finflow.effective_buffer(profile, [], 0), 0)

    def test_no_savings_rule_defaults_to_zero(self):
        self.assertEqual(finflow.effective_buffer({}, [], 0), 0)


class ProfileIOTests(unittest.TestCase):
    def setUp(self):
        self._orig_path = finflow.PROFILE_PATH
        self._tmpdir = tempfile.TemporaryDirectory()
        finflow.PROFILE_PATH = Path(self._tmpdir.name) / "profile.json"

    def tearDown(self):
        finflow.PROFILE_PATH = self._orig_path
        self._tmpdir.cleanup()

    def _write_profile(self, profile):
        with open(finflow.PROFILE_PATH, "w") as f:
            json.dump(profile, f)

    def test_load_profile_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            finflow.load_profile()

    def test_load_profile_reads_written_json(self):
        profile = {"currency": "PHP", "income": [], "expenses": []}
        self._write_profile(profile)
        self.assertEqual(finflow.load_profile(), profile)


class AffordCLITests(unittest.TestCase):
    """End-to-end tests through the argparse command handlers."""

    def setUp(self):
        self._orig_path = finflow.PROFILE_PATH
        self._tmpdir = tempfile.TemporaryDirectory()
        finflow.PROFILE_PATH = Path(self._tmpdir.name) / "profile.json"
        profile = {
            "currency": "PHP",
            "income": [entry(label="salary", amount=25000, recurrence="monthly", nextDate="2026-01-01")],
            "expenses": [entry(label="loan due", amount=3500, recurrence="monthly", nextDate="2026-01-15")],
            "savingsRule": {"mode": "minBalance", "minBalance": 10000, "percentOfIncome": None},
        }
        with open(finflow.PROFILE_PATH, "w") as f:
            json.dump(profile, f)

    def tearDown(self):
        finflow.PROFILE_PATH = self._orig_path
        self._tmpdir.cleanup()

    def _run(self, func, **kwargs):
        args = type("Args", (), kwargs)()
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            func(args)
        return buf.getvalue()

    def test_project_flags_below_buffer_day(self):
        # Start after the salary already landed and before the loan due,
        # so the balance sits just above buffer, then dips under it once
        # the loan due is subtracted.
        out = self._run(
            finflow.cmd_project,
            days=20, balance=10500, start="2026-01-02", rate=None,
        )
        self.assertIn("[BELOW BUFFER]", out)

    def test_project_stays_above_buffer_with_enough_cash(self):
        out = self._run(
            finflow.cmd_project,
            days=20, balance=50000, start="2026-01-01", rate=None,
        )
        self.assertNotIn("[BELOW BUFFER]", out)

    def test_afford_finds_no_safe_window_when_cost_too_high(self):
        out = self._run(
            finflow.cmd_afford,
            cost=100000, days=30, deadline=None, balance=12000, start="2026-01-01", rate=None,
        )
        self.assertIn("No safe date found", out)

    def test_afford_finds_safe_window_when_affordable(self):
        out = self._run(
            finflow.cmd_afford,
            cost=500, days=10, deadline=None, balance=12000, start="2026-01-01", rate=None,
        )
        self.assertIn("Earliest safe window", out)

    def test_afford_respects_missing_rate_for_foreign_currency(self):
        with open(finflow.PROFILE_PATH) as f:
            profile = json.load(f)
        profile["income"].append(
            entry(label="foreign", amount=100, currency="USD", recurrence="once", nextDate="2026-01-03")
        )
        with open(finflow.PROFILE_PATH, "w") as f:
            json.dump(profile, f)

        with self.assertRaises(SystemExit):
            self._run(
                finflow.cmd_afford,
                cost=500, days=10, deadline=None, balance=12000, start="2026-01-01", rate=None,
            )


if __name__ == "__main__":
    unittest.main()
