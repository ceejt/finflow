# FinFlow

A local-first financial advisor skill for [Claude Code](https://claude.com/claude-code). It projects your cash flow from your income and recurring expenses/loan dues, then answers real questions: can I afford this now, when's the safest time to buy it, will this loan due date collide with my savings target.

Your financial data never leaves your machine. It is never stored inside this repo, never committed, and never synced anywhere.

## Install

```bash
git clone <this-repo-url> ~/.claude/skills/finflow
```

That's it. Claude Code picks up skills from `~/.claude/skills/`.

## Use

In Claude Code, just talk about your finances or invoke the skill directly:

```
finflow
```

**First run** onboards you: currency, income sources, recurring expenses and loan dues, and a savings rule (either a minimum balance to never dip below, or a percentage of income to set aside). It saves your answers to `~/.finflow/profile.json`, outside this repo, on your own machine.

**Every run after that** skips onboarding and acts as your advisor:

```
finflow can I buy a ₱9,000 plane ticket next week?
finflow is my savings still okay after rent this month?
```

**To edit your profile later:**

```
finflow update
```

Add or remove income sources, update expenses/loan dues, or change your savings rule, without redoing onboarding.

## Why local-first

Cloning and pulling this repo never touches your data, because your data was never inside it. The skill folder (`~/.claude/skills/finflow/`) holds only instructions. Your profile lives at `~/.finflow/profile.json`, a fixed path outside any git-tracked directory. Multiple people can clone the same repo and each get their own private profile with zero risk of leaking one another's numbers through a shared codebase.

## How it works

See [SKILL.md](SKILL.md) for the workflow Claude follows, and `references/` for the details split by task: [schema.md](references/schema.md) (profile format), [onboarding.md](references/onboarding.md) (first-run questions), [projection.md](references/projection.md) (the cash-flow math), and [update.md](references/update.md) (editing your profile later).

The projection math itself runs as real code, not an LLM doing arithmetic in-context: [`scripts/finflow.py`](scripts/finflow.py) is a small, dependency-free, deterministic engine that reads your profile and computes the day-by-day balance. Claude calls it and only adds the natural-language explanation on top, following the same "math engine separate from the reasoning layer" principle as the FinFlow iOS app spec this skill is paired with. You can also run it directly, no Claude required:

```bash
python3 ~/.claude/skills/finflow/scripts/finflow.py show
python3 ~/.claude/skills/finflow/scripts/finflow.py project --days 30 --balance 3000
python3 ~/.claude/skills/finflow/scripts/finflow.py afford --cost 9000 --deadline 2026-10-01 --balance 3000
```

Run the test suite (stdlib `unittest`, no dependencies):

```bash
python3 ~/.claude/skills/finflow/scripts/test_finflow.py
```
